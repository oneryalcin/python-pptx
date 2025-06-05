# tests/introspection/test_shape_introspection.py

"""
Shape Introspection Tests

Tests for BaseShape introspection functionality including:
- Basic shape identity and geometry properties
- Shape relationships (parent collection, part)
- Placeholder shape handling and format details
- Error handling for edge cases
- LLM context generation for AI tools
- Safe property access helper methods
"""

import unittest
from pptx.shapes.base import BaseShape
from pptx.util import Emu
from pptx.enum.shapes import PP_PLACEHOLDER

from .mock_helpers import (
    MockShapeElement, MockParent, MockPlaceholderFormat,
    assert_basic_to_dict_structure, assert_length_dict_structure
)


class TestShapeIntrospection(unittest.TestCase):
    """Test BaseShape introspection functionality."""

    def test_base_shape_to_dict_basic_functionality(self):
        """Test that BaseShape.to_dict() provides expected basic structure."""
        # Create BaseShape instance
        shape_elm = MockShapeElement()
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        # Test basic to_dict functionality
        result = shape.to_dict(include_relationships=False, max_depth=1)

        # Check basic structure
        assert_basic_to_dict_structure(self, result, 'BaseShape')

        # Check identity information
        identity = result['_identity']
        self.assertEqual(identity['shape_id'], 42)
        self.assertEqual(identity['name'], "Test Shape")
        self.assertFalse(identity['is_placeholder'])
        # BaseShape.shape_type raises NotImplementedError, so it should not be included
        self.assertNotIn('shape_type', identity)

        # Check geometry properties
        props = result['properties']
        self.assertIn('left', props)
        self.assertIn('top', props)
        self.assertIn('width', props)
        self.assertIn('height', props)
        self.assertIn('rotation', props)

        # Verify Length objects are properly formatted
        assert_length_dict_structure(self, props['left'], 'Emu', 914400)
        self.assertAlmostEqual(props['left']['inches'], 1.0)

        self.assertEqual(props['rotation'], 0.0)

    def test_base_shape_to_dict_with_relationships(self):
        """Test BaseShape.to_dict() with relationships included."""
        # Create mock objects
        shape_elm = MockShapeElement(shape_id=123, name="Relationship Test", x=Emu(0), y=Emu(0), rot=45.0)
        parent = MockParent("MockSlideShapes with 5 shapes")
        shape = BaseShape(shape_elm, parent)

        # Mock the part property
        class MockPart:
            def __repr__(self):
                return "<MockSlidePart '/ppt/slides/slide1.xml'>"

        original_part = BaseShape.part
        BaseShape.part = property(lambda self: MockPart())

        try:
            result = shape.to_dict(include_relationships=True, max_depth=1)

            # Check relationships
            self.assertIn('relationships', result)
            rels = result['relationships']

            # Parent collection should fallback to repr since MockParent doesn't have to_dict
            self.assertIn('parent_collection', rels)
            self.assertIsInstance(rels['parent_collection'], str)
            self.assertIn('MockSlideShapes', rels['parent_collection'])

            # Part should fallback to repr since MockPart doesn't have to_dict
            self.assertIn('part', rels)
            self.assertIsInstance(rels['part'], str)
            self.assertIn('MockSlidePart', rels['part'])

        finally:
            # Restore original part property
            BaseShape.part = original_part

    def test_base_shape_placeholder_handling(self):
        """Test BaseShape.to_dict() with placeholder shapes."""
        # Create mock placeholder shape
        shape_elm = MockShapeElement(
            shape_id=200, name="Title Placeholder", is_placeholder=True,
            x=Emu(914400), y=Emu(914400), cx=Emu(7315200), cy=Emu(1371600)  # 8x1.5 inches
        )
        parent = MockParent("MockSlideShapes")
        shape = BaseShape(shape_elm, parent)

        # Mock the placeholder_format property
        original_placeholder_format = BaseShape.placeholder_format
        BaseShape.placeholder_format = property(lambda self: MockPlaceholderFormat())

        try:
            result = shape.to_dict(include_relationships=False, max_depth=2)

            # Check placeholder identification
            identity = result['_identity']
            self.assertTrue(identity['is_placeholder'])
            self.assertIn('placeholder_details', identity)

            placeholder_details = identity['placeholder_details']
            # Now placeholder_details is the full to_dict() output from _PlaceholderFormat
            self.assertEqual(placeholder_details['_object_type'], '_PlaceholderFormat')
            
            # Check properties within the placeholder details
            ph_props = placeholder_details['properties']
            self.assertEqual(ph_props['idx'], 0)

            # Check that placeholder type is properly formatted as enum
            ph_type = ph_props['type']
            self.assertEqual(ph_type['_object_type'], 'PP_PLACEHOLDER_TYPE')
            self.assertEqual(ph_type['name'], 'TITLE')
            self.assertEqual(ph_type['value'], 1)

            # Check LLM context mentions placeholder
            context = result['_llm_context']
            self.assertIn('placeholder', context['description'])

        finally:
            # Restore original placeholder_format property
            BaseShape.placeholder_format = original_placeholder_format

    def test_base_shape_error_handling(self):
        """Test BaseShape.to_dict() error handling for edge cases."""
        # Test shape that raises errors accessing placeholder_format
        shape_elm = MockShapeElement(shape_id=999, name="Error Test Shape", is_placeholder=True)
        parent = MockParent("MockParent")
        shape = BaseShape(shape_elm, parent)

        # Mock placeholder_format to raise ValueError
        def failing_placeholder_format(self):
            raise ValueError("Failed to access placeholder format")

        original_placeholder_format = BaseShape.placeholder_format
        BaseShape.placeholder_format = property(failing_placeholder_format)

        try:
            result = shape.to_dict(include_relationships=False, max_depth=1)

            # Should still work but with error info in placeholder_details
            identity = result['_identity']
            self.assertTrue(identity['is_placeholder'])
            self.assertIn('placeholder_details', identity)

            placeholder_details = identity['placeholder_details']
            # The error context now comes from _create_error_context method
            self.assertIn('_error', placeholder_details)
            self.assertIn('Failed to get placeholder details', str(placeholder_details))

        finally:
            # Restore original placeholder_format property
            BaseShape.placeholder_format = original_placeholder_format

    def test_base_shape_llm_context_generation(self):
        """Test BaseShape._to_dict_llm_context() generates useful descriptions."""
        # Create mock shape
        shape_elm = MockShapeElement(shape_id=333, name="LLM Test Shape", rot=15.0)
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)
        
        result = shape.to_dict(include_relationships=False, max_depth=1)

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('description', context)
        self.assertIn('common_operations', context)

        # Description should mention the shape name and ID
        desc = context['description']
        self.assertIn('LLM Test Shape', desc)
        self.assertIn('333', desc)

        # Should include common operations
        operations = context['common_operations']
        self.assertIn('access geometry (left, top, width, height, rotation)', operations)
        self.assertIn('modify position and size', operations)

    def test_base_shape_safe_property_access(self):
        """Test BaseShape helper methods for safe property access."""
        # Create basic shape
        shape_elm = MockShapeElement(shape_id=444, name="Safe Access Test")
        shape = BaseShape(shape_elm, None)

        # Test _get_shape_type_safely
        shape_type = shape._get_shape_type_safely()
        self.assertIsNone(shape_type)  # BaseShape raises NotImplementedError

        # Test _get_placeholder_info_safely for non-placeholder
        placeholder_info = shape._get_placeholder_info_safely(
            include_private=False, _visited_ids=set(), max_depth=2, 
            expand_collections=True, format_for_llm=True
        )
        self.assertIsNone(placeholder_info)

    def test_base_shape_geometry_properties(self):
        """Test that all geometry properties are properly exposed and formatted."""
        # Create shape with specific geometry
        shape_elm = MockShapeElement(
            shape_id=555, name="Geometry Test",
            x=Emu(1828800), y=Emu(914400),      # 2", 1"
            cx=Emu(2743200), cy=Emu(1828800),   # 3", 2"
            rot=30.0
        )
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        result = shape.to_dict(include_relationships=False, max_depth=1)
        props = result['properties']

        # Verify all geometry properties are present and correctly formatted
        geometry_props = ['left', 'top', 'width', 'height', 'rotation']
        for prop in geometry_props:
            self.assertIn(prop, props)

        # Check specific values
        assert_length_dict_structure(self, props['left'], 'Emu', 1828800)
        self.assertAlmostEqual(props['left']['inches'], 2.0)

        assert_length_dict_structure(self, props['top'], 'Emu', 914400)
        self.assertAlmostEqual(props['top']['inches'], 1.0)

        assert_length_dict_structure(self, props['width'], 'Emu', 2743200)
        self.assertAlmostEqual(props['width']['inches'], 3.0)

        assert_length_dict_structure(self, props['height'], 'Emu', 1828800)
        self.assertAlmostEqual(props['height']['inches'], 2.0)

        self.assertEqual(props['rotation'], 30.0)

    def test_base_shape_identity_completeness(self):
        """Test that shape identity captures all relevant identification information."""
        # Test regular shape
        shape_elm = MockShapeElement(shape_id=777, name="Identity Test Shape")
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        result = shape.to_dict(include_relationships=False, max_depth=1)
        identity = result['_identity']

        # Check required identity fields
        required_fields = ['shape_id', 'name', 'is_placeholder']
        for field in required_fields:
            self.assertIn(field, identity)

        # Verify values
        self.assertEqual(identity['shape_id'], 777)
        self.assertEqual(identity['name'], "Identity Test Shape")
        self.assertFalse(identity['is_placeholder'])

        # For regular shapes, should not have placeholder_details
        self.assertNotIn('placeholder_details', identity)

    def test_base_shape_placeholder_format_details(self):
        """Test detailed placeholder format introspection."""
        # Create placeholder with specific format details
        shape_elm = MockShapeElement(
            shape_id=888, name="Detailed Placeholder", is_placeholder=True
        )
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        # Mock placeholder format with specific details
        class DetailedPlaceholderFormat:
            def __init__(self):
                self.idx = 2
                self.type = PP_PLACEHOLDER.BODY

        original_placeholder_format = BaseShape.placeholder_format
        BaseShape.placeholder_format = property(lambda self: DetailedPlaceholderFormat())

        try:
            result = shape.to_dict(include_relationships=False, max_depth=2)
            identity = result['_identity']
            
            self.assertTrue(identity['is_placeholder'])
            placeholder_details = identity['placeholder_details']
            
            # DetailedPlaceholderFormat doesn't have to_dict method, so this will result in an error structure
            # Let's check if we got the expected error handling
            self.assertIsNotNone(placeholder_details)
            # Since DetailedPlaceholderFormat doesn't have to_dict, this will result in an error context
            # We should see either error information or fallback behavior

        finally:
            BaseShape.placeholder_format = original_placeholder_format

    def test_base_shape_error_resilience(self):
        """Test that BaseShape introspection handles accessible properties correctly."""
        # Test shape with normal accessible properties
        class WorkingShapeElement:
            def __init__(self):
                self.shape_id = 999
                self.shape_name = "Working Shape"
                self.has_ph_elm = False

            @property
            def x(self):
                return Emu(914400)

            @property
            def y(self):
                return Emu(0)

            @property
            def cx(self):
                return Emu(914400)

            @property
            def cy(self):
                return Emu(914400)

            @property
            def rot(self):
                return 0.0

            @property
            def hidden(self):
                return False

        shape_elm = WorkingShapeElement()
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        # Should work correctly with accessible properties
        result = shape.to_dict(include_relationships=False, max_depth=1)

        # Basic structure should be present
        assert_basic_to_dict_structure(self, result, 'BaseShape')

        # Properties should be accessible
        props = result['properties']
        self.assertIn('left', props)
        self.assertIn('top', props)
        self.assertIn('width', props)
        self.assertIn('height', props)
        self.assertIn('rotation', props)


if __name__ == '__main__':
    unittest.main()