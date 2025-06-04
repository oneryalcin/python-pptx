# tests/introspection/test_fill_introspection.py

"""
Fill Introspection Tests

Tests for FillFormat and _GradientStop introspection functionality including:
- Solid fill with foreground color introspection
- Gradient fill with stops and angle introspection
- Pattern fill with foreground/background colors
- Picture fill with image reference introspection
- Background/transparent fill handling
- No fill defined scenarios
- GradientStop position and color introspection
"""

import unittest
from pptx.dml.fill import FillFormat, _GradientStop
from pptx.introspection import IntrospectionMixin
from pptx.enum.dml import MSO_FILL

from .mock_helpers import (
    MockFillFormat, MockColorFormat, MockPattern, MockGradientStop,
    assert_basic_to_dict_structure
)


class TestFillIntrospection(unittest.TestCase):
    """Test FillFormat and related introspection functionality."""

    def test_fillformat_solid_introspection(self):
        """Test that FillFormat with solid fill is properly serialized."""
        # Create a test FillFormat with solid fill
        class MockFillFormatSolid(FillFormat):
            def __init__(self, fore_color):
                # Skip parent initialization for testing
                self._fill_type = MSO_FILL.SOLID
                self._fore_color = fore_color

            @property
            def type(self):
                return self._fill_type

            @property
            def fore_color(self):
                return self._fore_color

            @property
            def back_color(self):
                raise TypeError("fill type _SolidFill has no background color")

            @property
            def pattern(self):
                raise TypeError("fill type _SolidFill has no pattern")

            @property
            def gradient_stops(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")

            @property
            def gradient_angle(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")

            @property
            def rId(self):
                raise NotImplementedError(".rId property must be implemented on _SolidFill")

        # Create mock color format
        class MockColorFormat(IntrospectionMixin):
            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {"type": {"name": "RGB"}, "rgb": {"hex": "FF0000"}}

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "Solid RGB color: #FF0000"}

        fill_format = MockFillFormatSolid(MockColorFormat())
        result = fill_format.to_dict()

        # Check basic structure
        assert_basic_to_dict_structure(self, result, 'MockFillFormatSolid')

        # Check identity
        identity = result['_identity']
        self.assertEqual(identity['description'], 'Represents the fill formatting of an object.')

        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'SOLID')
        self.assertIsNotNone(props['fore_color'])
        self.assertEqual(props['fore_color']['_object_type'], 'MockColorFormat')

        # Other properties should be None for solid fill
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Solid fill', context['summary'])

    def test_fillformat_gradient_introspection(self):
        """Test that FillFormat with gradient fill is properly serialized."""
        # Create a test FillFormat with gradient fill
        class MockFillFormatGradient(FillFormat):
            def __init__(self, gradient_stops, gradient_angle=45.0):
                self._fill_type = MSO_FILL.GRADIENT
                self._gradient_stops = gradient_stops
                self._gradient_angle = gradient_angle

            @property
            def type(self):
                return self._fill_type

            @property
            def gradient_stops(self):
                return self._gradient_stops

            @property
            def gradient_angle(self):
                return self._gradient_angle

            @property
            def fore_color(self):
                raise TypeError("fill type _GradFill has no foreground color")

            @property
            def back_color(self):
                raise TypeError("fill type _GradFill has no background color")

            @property
            def pattern(self):
                raise TypeError("fill type _GradFill has no pattern")

            @property
            def rId(self):
                raise NotImplementedError(".rId property must be implemented on _GradFill")

        # Create mock gradient stops
        class MockGradientStop:
            def __init__(self, position, color_summary):
                self.position = position
                self.color_summary = color_summary

            def to_dict(self, **kwargs):
                return {
                    "_object_type": "_GradientStop",
                    "properties": {"position": self.position, "color": {"hex": "123456"}},
                    "_llm_context": {"summary": f"Gradient stop at {self.position*100:.0f}% with {self.color_summary}"}
                }

        class MockGradientStops:
            def __init__(self, stops):
                self.stops = stops

            def __len__(self):
                return len(self.stops)

            def __iter__(self):
                return iter(self.stops)

        stops = MockGradientStops([
            MockGradientStop(0.0, "red color"),
            MockGradientStop(1.0, "blue color")
        ])

        fill_format = MockFillFormatGradient(stops, 90.0)
        result = fill_format.to_dict(max_depth=3)  # Ensure enough depth for stops expansion

        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'GRADIENT')
        self.assertEqual(props['gradient_angle'], 90.0)
        self.assertIsInstance(props['gradient_stops'], list)
        self.assertEqual(len(props['gradient_stops']), 2)

        # Check first gradient stop
        stop1 = props['gradient_stops'][0]
        self.assertEqual(stop1['_object_type'], '_GradientStop')
        self.assertEqual(stop1['properties']['position'], 0.0)

        # Other properties should be None for gradient fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['image_rId'])

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('2-stop gradient', context['summary'])
        self.assertIn('90 degrees', context['summary'])

    def test_fillformat_pattern_introspection(self):
        """Test that FillFormat with pattern fill is properly serialized."""
        # Use the MockFillFormat from mock_helpers with pattern type
        fill_format = MockFillFormat("PATTERNED")
        result = fill_format.to_dict()

        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'PATTERNED')
        self.assertIsNotNone(props['fore_color'])
        self.assertEqual(props['fore_color']['_object_type'], 'MockColorFormat')
        self.assertIsNotNone(props['back_color'])
        self.assertEqual(props['back_color']['_object_type'], 'MockColorFormat')
        
        # Pattern is a simple object, so it gets converted to string representation
        self.assertIn('CROSS', str(props['pattern']))

        # Other properties should be None for pattern fill
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Patterned fill', context['summary'])
        self.assertIn('CROSS', context['summary'])

    def test_fillformat_picture_introspection(self):
        """Test that FillFormat with picture fill is properly serialized."""
        # Use the MockFillFormat from mock_helpers with picture type
        fill_format = MockFillFormat("PICTURE", rId="rId5")
        result = fill_format.to_dict()

        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'PICTURE')
        self.assertEqual(props['image_rId'], 'rId5')

        # Other properties should be None for picture fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Picture fill', context['summary'])
        self.assertIn('rId5', context['summary'])

    def test_fillformat_background_introspection(self):
        """Test that FillFormat with background fill is properly serialized."""
        # Use the MockFillFormat from mock_helpers with background type
        fill_format = MockFillFormat("BACKGROUND")
        result = fill_format.to_dict()

        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'BACKGROUND')

        # All specific properties should be None for background fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Background fill (transparent)', context['summary'])

    def test_fillformat_none_introspection(self):
        """Test that FillFormat with no fill defined is properly serialized."""
        # Use the MockFillFormat from mock_helpers with None type
        fill_format = MockFillFormat("NONE")
        result = fill_format.to_dict()

        # Check properties
        props = result['properties']
        self.assertIsNone(props['type'])

        # All specific properties should be None for no fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('No explicit fill defined', context['summary'])

    def test_gradient_stop_introspection(self):
        """Test that _GradientStop is properly serialized."""
        # Create mock color
        class MockColorFormat(IntrospectionMixin):
            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {"type": {"name": "RGB"}, "rgb": {"hex": "00FF00"}}

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "Solid RGB color: #00FF00"}

        gradient_stop = MockGradientStop(0.5, MockColorFormat())
        result = gradient_stop.to_dict()

        # Check basic structure
        assert_basic_to_dict_structure(self, result, 'MockGradientStop')

        # Check identity
        identity = result['_identity']
        self.assertEqual(identity['description'], 'Represents a color stop in a gradient.')

        # Check properties
        props = result['properties']
        self.assertEqual(props['position'], 0.5)
        self.assertIsNotNone(props['color'])
        self.assertEqual(props['color']['_object_type'], 'MockColorFormat')

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Gradient stop at 50% position', context['summary'])
        # The color summary should be accessible
        self.assertIn('color', context['summary'])

        # Relationships should be empty for GradientStop
        self.assertEqual(result['relationships'], {})

    def test_fillformat_error_handling(self):
        """Test that FillFormat handles property access errors gracefully."""
        # Create a FillFormat that raises errors
        class ErrorFillFormat(FillFormat):
            def __init__(self):
                pass  # Skip initialization

            @property
            def type(self):
                return MSO_FILL.SOLID

            @property
            def fore_color(self):
                raise RuntimeError("Cannot access fore_color")

            @property
            def back_color(self):
                raise RuntimeError("Cannot access back_color")

            @property
            def pattern(self):
                raise RuntimeError("Cannot access pattern")

            @property
            def gradient_stops(self):
                raise RuntimeError("Cannot access gradient_stops")

            @property
            def gradient_angle(self):
                raise RuntimeError("Cannot access gradient_angle")

            @property
            def rId(self):
                raise RuntimeError("Cannot access rId")

        fill_format = ErrorFillFormat()
        result = fill_format.to_dict()

        # Should not crash
        assert_basic_to_dict_structure(self, result, 'ErrorFillFormat')

        # Properties should be handled gracefully
        props = result['properties']
        self.assertIn('type', props)
        self.assertEqual(props['type']['name'], 'SOLID')

        # Error properties should be None or contain error context
        self.assertIn('fore_color', props)
        self.assertIn('back_color', props)
        self.assertIn('pattern', props)

    def test_fillformat_comprehensive_type_coverage(self):
        """Test that all major fill types are properly handled."""
        fill_types = ["SOLID", "GRADIENT", "PATTERNED", "PICTURE", "BACKGROUND", "NONE"]

        for fill_type in fill_types:
            with self.subTest(fill_type=fill_type):
                fill_format = MockFillFormat(fill_type)
                result = fill_format.to_dict()

                # Should have proper basic structure
                assert_basic_to_dict_structure(self, result, 'MockFillFormat')

                # Should have type information (except for NONE)
                props = result['properties']
                if fill_type == "NONE":
                    self.assertIsNone(props['type'])
                else:
                    self.assertEqual(props['type']['name'], fill_type)

                # Should have meaningful LLM context
                context = result['_llm_context']
                self.assertIn('summary', context)
                self.assertTrue(len(context['summary']) > 0)

    def test_fillformat_relationships_empty(self):
        """Test that FillFormat has empty relationships."""
        fill_format = MockFillFormat("SOLID")
        result = fill_format.to_dict()

        # FillFormat should have empty relationships
        self.assertEqual(result['relationships'], {})

    def test_fillformat_identity_consistency(self):
        """Test that FillFormat identity is consistent across types."""
        fill_format = MockFillFormat("SOLID")
        result = fill_format.to_dict()

        identity = result['_identity']
        self.assertIn('class_name', identity)
        self.assertIn('memory_address', identity)
        self.assertIn('description', identity)
        self.assertEqual(identity['description'], 'Represents the fill formatting of an object.')


if __name__ == '__main__':
    unittest.main()