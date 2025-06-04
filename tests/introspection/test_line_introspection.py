# tests/introspection/test_line_introspection.py

"""
Line Introspection Tests

Tests for LineFormat introspection functionality including:
- Solid line with fill and width introspection
- No line (background fill) handling
- Gradient line introspection
- Pattern line introspection
- Common operations context for AI tools
- Error handling and resilience
"""

import unittest

from pptx.dml.line import LineFormat
from pptx.enum.dml import MSO_FILL, MSO_LINE_DASH_STYLE
from pptx.introspection import IntrospectionMixin
from pptx.util import Emu, Pt

from .mock_helpers import (
    MockLineFormat,
    MockPattern,
    assert_basic_to_dict_structure,
)


class TestLineIntrospection(unittest.TestCase):
    """Test LineFormat introspection functionality."""

    def test_lineformat_solid_introspection(self):
        """Test that LineFormat with solid fill is properly serialized."""
        # Create a test LineFormat with solid fill
        class MockLineFormatSolid(LineFormat):
            def __init__(self):
                # Skip parent initialization for testing
                self._width = Pt(2.5)
                self._dash_style = MSO_LINE_DASH_STYLE.DASH
                self._fill = MockFillFormatForLine("SOLID")

            @property
            def width(self):
                return self._width

            @property
            def dash_style(self):
                return self._dash_style

            @property
            def fill(self):
                return self._fill

        # Create mock fill format for line testing
        class MockFillFormatForLine(IntrospectionMixin):
            def __init__(self, fill_type):
                self._type = fill_type

            @property
            def type(self):
                return MSO_FILL.SOLID if self._type == "SOLID" else None

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "type": {"_object_type": "MSO_FILL", "name": "SOLID", "value": 1},
                    "fore_color": {"_object_type": "ColorFormat", "rgb": {"hex": "0000FF"}}
                }

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "Solid fill with Solid RGB color: #0000FF (R:0, G:0, B:255)."}

        line = MockLineFormatSolid()
        result = line.to_dict()

        # Check basic structure
        assert_basic_to_dict_structure(self, result, 'MockLineFormatSolid')

        # Check properties
        props = result['properties']
        self.assertIn('fill', props)
        self.assertIn('width', props)
        self.assertIn('dash_style', props)

        # Check fill properties
        fill_props = props['fill']
        self.assertEqual(fill_props['_object_type'], 'MockFillFormatForLine')

        # Check width (Length object)
        width_props = props['width']
        self.assertEqual(width_props['_object_type'], 'Pt')
        self.assertEqual(width_props['pt'], 2.5)

        # Check dash style (enum)
        dash_props = props['dash_style']
        self.assertEqual(dash_props['_object_type'], 'MSO_LINE_DASH_STYLE')
        self.assertEqual(dash_props['name'], 'DASH')

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('DASH line, 2.50pt', context['summary'])

    def test_lineformat_no_line_introspection(self):
        """Test that LineFormat with no line (background fill) is properly serialized."""
        # Create a test LineFormat with background fill (no line)
        class MockLineFormatNoLine(LineFormat):
            def __init__(self):
                # Skip parent initialization for testing
                self._width = Pt(0)  # Zero width = no line
                self._dash_style = None
                self._fill = MockFillFormatBackground()

            @property
            def width(self):
                return self._width

            @property
            def dash_style(self):
                return self._dash_style

            @property
            def fill(self):
                return self._fill

        # Create mock fill format for background
        class MockFillFormatBackground(IntrospectionMixin):
            @property
            def type(self):
                return MSO_FILL.BACKGROUND

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "type": {"_object_type": "MSO_FILL", "name": "BACKGROUND", "value": 5}
                }

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "Background fill (no fill)."}

        line = MockLineFormatNoLine()
        result = line.to_dict()

        # Check basic structure
        assert_basic_to_dict_structure(self, result, 'MockLineFormatNoLine')

        # Check properties
        props = result['properties']
        self.assertIn('fill', props)
        self.assertIn('width', props)
        self.assertIn('dash_style', props)

        # Check width is zero
        width_props = props['width']
        self.assertEqual(width_props['pt'], 0.0)

        # Check dash style is None
        self.assertIsNone(props['dash_style'])

        # Check LLM context indicates no line
        context = result['_llm_context']
        self.assertIn('No line', context['summary'])

    def test_lineformat_gradient_introspection(self):
        """Test that LineFormat with gradient fill is properly serialized."""
        # Use MockLineFormat with gradient fill
        line = MockLineFormat(
            width=Pt(1.5),
            dash_style=MSO_LINE_DASH_STYLE.DASH_DOT,
            fill_type="GRADIENT"
        )

        # Override the fill with a more detailed gradient mock
        class MockGradientFill(IntrospectionMixin):
            @property
            def type(self):
                return MSO_FILL.GRADIENT

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "type": {"_object_type": "MSO_FILL", "name": "GRADIENT", "value": 3},
                    "gradient_angle": 45.0,
                    "gradient_stops": [{"position": 0.0}, {"position": 1.0}]
                }

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "2-stop gradient at 45 degrees."}

        line._fill = MockGradientFill()
        result = line.to_dict()

        # Check basic structure
        self.assertIn('_object_type', result)
        self.assertIn('properties', result)
        self.assertIn('_llm_context', result)

        # Check properties
        props = result['properties']
        self.assertIn('fill', props)

        # Check fill properties for gradient
        fill_props = props['fill']
        self.assertEqual(fill_props['_object_type'], 'MockGradientFill')

        # Check dash style
        dash_props = props['dash_style']
        self.assertEqual(dash_props['name'], 'DASH_DOT')

        # Check LLM context mentions gradient
        context = result['_llm_context']
        self.assertIn('DASH_DOT gradient line', context['summary'])

    def test_lineformat_pattern_introspection(self):
        """Test that LineFormat with pattern fill is properly serialized."""
        # Use MockLineFormat with pattern fill
        line = MockLineFormat(
            width=Pt(3.0),
            dash_style=MSO_LINE_DASH_STYLE.SOLID,
            fill_type="PATTERNED"
        )

        # Override the fill with a more detailed pattern mock
        class MockPatternFill(IntrospectionMixin):
            def __init__(self):
                self._pattern = MockPattern("DIAGONAL_CROSS")

            @property
            def type(self):
                return MSO_FILL.PATTERNED

            @property
            def pattern(self):
                return self._pattern

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "type": {"_object_type": "MSO_FILL", "name": "PATTERNED", "value": 2},
                    "pattern": {"name": "DIAGONAL_CROSS"}
                }

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "DIAGONAL_CROSS patterned fill."}

        line._fill = MockPatternFill()
        result = line.to_dict()

        # Check properties
        props = result['properties']

        # Check width
        width_props = props['width']
        self.assertEqual(width_props['pt'], 3.0)

        # Check LLM context mentions pattern
        context = result['_llm_context']
        self.assertIn('DIAGONAL_CROSS patterned line', context['summary'])
        self.assertIn('3.00pt', context['summary'])

    def test_lineformat_common_operations_context(self):
        """Test that LineFormat provides useful common operations in LLM context."""
        # Create a basic test LineFormat
        class MockBasicLineFormat(LineFormat):
            def __init__(self):
                self._width = Emu(0)
                self._dash_style = None
                self._fill = MockBasicFill()

            @property
            def width(self):
                return self._width

            @property
            def dash_style(self):
                return self._dash_style

            @property
            def fill(self):
                return self._fill

        class MockBasicFill(IntrospectionMixin):
            @property
            def type(self):
                return None

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {"type": None}

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "No fill."}

        line = MockBasicLineFormat()
        result = line.to_dict()

        # Check LLM context includes common operations
        context = result['_llm_context']
        self.assertIn('common_operations', context)

        operations = context['common_operations']

        # Check for key operations
        expected_operations = [
            "set line color",
            "set line width",
            "set dash style",
            "remove line",
            "set solid fill"
        ]

        for expected_op in expected_operations:
            found = any(expected_op in op for op in operations)
            self.assertTrue(found, f"Expected operation '{expected_op}' not found in: {operations}")

    def test_lineformat_error_handling(self):
        """Test that LineFormat introspection handles errors gracefully."""
        # Create a test LineFormat that will raise errors
        class ErrorLineFormat(LineFormat):
            def __init__(self):
                pass  # Skip initialization

            @property
            def width(self):
                raise ValueError("Width access error")

            @property
            def dash_style(self):
                raise AttributeError("Dash style access error")

            @property
            def fill(self):
                raise RuntimeError("Fill access error")

        line = ErrorLineFormat()

        # This should not crash - it should handle errors gracefully
        result = line.to_dict()

        # Check basic structure is still present
        self.assertIn('_object_type', result)
        self.assertIn('properties', result)
        self.assertIn('_llm_context', result)

        # Check that errors are handled in properties
        props = result['properties']
        self.assertIn('fill', props)
        self.assertIn('width', props)
        self.assertIn('dash_style', props)

        # Properties should contain error contexts due to the exceptions
        # (The exact structure depends on _create_error_context implementation)
        # The main thing is that it didn't crash

        # Check that error is handled in LLM context
        context = result['_llm_context']
        self.assertIn('error in analysis', context['summary'])

    def test_lineformat_width_precision(self):
        """Test that LineFormat width values are precisely captured."""
        # Test various width values
        test_widths = [Pt(0.5), Pt(1.0), Pt(2.25), Pt(5.75)]

        for width in test_widths:
            with self.subTest(width=width):
                line = MockLineFormat(width=width)
                result = line.to_dict()

                props = result['properties']
                width_props = props['width']

                # Check precise value conversion
                self.assertEqual(width_props['pt'], width.pt)
                self.assertEqual(width_props['_object_type'], 'Pt')

    def test_lineformat_dash_style_varieties(self):
        """Test that various dash styles are properly captured."""
        dash_styles = [
            MSO_LINE_DASH_STYLE.SOLID,
            MSO_LINE_DASH_STYLE.DASH,
            MSO_LINE_DASH_STYLE.ROUND_DOT,
            MSO_LINE_DASH_STYLE.DASH_DOT,
            MSO_LINE_DASH_STYLE.DASH_DOT_DOT
        ]

        for dash_style in dash_styles:
            with self.subTest(dash_style=dash_style):
                line = MockLineFormat(dash_style=dash_style)
                result = line.to_dict()

                props = result['properties']
                dash_props = props['dash_style']

                # Check enum structure
                self.assertEqual(dash_props['_object_type'], 'MSO_LINE_DASH_STYLE')
                self.assertEqual(dash_props['name'], dash_style.name)
                self.assertEqual(dash_props['value'], dash_style.value)

    def test_lineformat_relationships_empty(self):
        """Test that LineFormat has empty relationships."""
        line = MockLineFormat()
        result = line.to_dict()

        # LineFormat should have empty relationships
        self.assertEqual(result['relationships'], {})

    def test_lineformat_llm_context_quality(self):
        """Test that LineFormat LLM context provides high-quality information."""
        # Test with solid blue line
        line = MockLineFormat(
            width=Pt(2.0),
            dash_style=MSO_LINE_DASH_STYLE.DASH,
            fill_type="SOLID"
        )

        # Override fill to provide rich color information
        class RichColorFill(IntrospectionMixin):
            @property
            def type(self):
                return MSO_FILL.SOLID

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "type": {"name": "SOLID"},
                    "fore_color": {
                        "_llm_context": {"summary": "Solid RGB color: #0066CC (R:0, G:102, B:204)"},
                        "properties": {
                            "rgb": {"hex": "0066CC"}
                        }
                    }
                }

            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "Solid fill with Solid RGB color: #0066CC (R:0, G:102, B:204)."}

        line._fill = RichColorFill()
        result = line.to_dict()

        context = result['_llm_context']

        # Should have comprehensive context
        self.assertIn('description', context)
        self.assertIn('summary', context)
        self.assertIn('common_operations', context)

        # Summary should be rich and informative
        summary = context['summary']
        self.assertIn('DASH line', summary)
        self.assertIn('2.00pt', summary)
        self.assertIn('#0066CC', summary)  # Color information should be extracted

    def test_lineformat_identity_consistency(self):
        """Test that LineFormat identity is consistent."""
        line = MockLineFormat()
        result = line.to_dict()

        identity = result['_identity']
        self.assertIn('class_name', identity)
        self.assertIn('memory_address', identity)
        self.assertIn('description', identity)

        # Should describe line formatting purpose
        desc = identity['description']
        self.assertIn('line', desc.lower())


if __name__ == '__main__':
    unittest.main()
