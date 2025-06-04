# tests/introspection/test_color_introspection.py

"""
Color Introspection Tests

Tests for ColorFormat introspection functionality including:
- RGB color formatting and serialization
- Theme color with brightness adjustment introspection
- None/inherited color handling
- Error handling for color property access
- Various color types (HSL, PRESET, etc.)
- Relationship validation and empty relationships
"""

import unittest
from pptx.dml.color import RGBColor, ColorFormat
from pptx.enum.dml import MSO_COLOR_TYPE, MSO_THEME_COLOR

from .mock_helpers import (
    MockColorFormat, assert_basic_to_dict_structure
)


class TestColorIntrospection(unittest.TestCase):
    """Test ColorFormat introspection functionality."""

    def test_colorformat_rgb_introspection(self):
        """Test that ColorFormat with RGB color is properly serialized."""
        rgb_color = RGBColor(0x12, 0x34, 0x56)
        color_format = MockColorFormat(
            color_type=MSO_COLOR_TYPE.RGB,
            rgb_color=rgb_color,
            brightness=0.0
        )
        result = color_format.to_dict()

        # Check basic structure
        assert_basic_to_dict_structure(self, result, 'MockColorFormat')

        # Check identity
        identity = result['_identity']
        self.assertEqual(identity['description'], 'Represents a color definition.')

        # Check properties
        props = result['properties']
        self.assertIn('type', props)
        self.assertIn('rgb', props)
        self.assertIn('theme_color', props)
        self.assertIn('brightness', props)

        # Verify RGB color properties
        self.assertEqual(props['type']['_object_type'], 'MSO_COLOR_TYPE')
        self.assertEqual(props['type']['name'], 'RGB')
        self.assertEqual(props['type']['value'], 1)

        self.assertEqual(props['rgb']['_object_type'], 'RGBColor')
        self.assertEqual(props['rgb']['r'], 0x12)
        self.assertEqual(props['rgb']['g'], 0x34)
        self.assertEqual(props['rgb']['b'], 0x56)
        self.assertEqual(props['rgb']['hex'], '123456')

        self.assertIsNone(props['theme_color'])
        self.assertEqual(props['brightness'], 0.0)

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('description', context)
        self.assertIn('summary', context)
        self.assertIn('common_operations', context)
        self.assertIn('RGB color', context['summary'])
        self.assertIn('#123456', context['summary'])

    def test_colorformat_theme_color_introspection(self):
        """Test that ColorFormat with theme color is properly serialized."""
        theme_color = MSO_THEME_COLOR.ACCENT_1
        color_format = MockColorFormat(
            color_type=MSO_COLOR_TYPE.SCHEME,
            theme_color=theme_color,
            brightness=-0.25  # 25% darker
        )
        result = color_format.to_dict()

        # Check properties
        props = result['properties']

        # Verify theme color properties
        self.assertEqual(props['type']['_object_type'], 'MSO_COLOR_TYPE')
        self.assertEqual(props['type']['name'], 'SCHEME')
        self.assertEqual(props['type']['value'], 2)

        self.assertIsNone(props['rgb'])

        # Note: The actual enum type is MSO_THEME_COLOR_INDEX, not MSO_THEME_COLOR
        self.assertEqual(props['theme_color']['_object_type'], 'MSO_THEME_COLOR_INDEX')
        self.assertEqual(props['theme_color']['name'], 'ACCENT_1')
        self.assertEqual(props['theme_color']['value'], 5)

        self.assertEqual(props['brightness'], -0.25)

        # Check LLM context for theme color with brightness
        context = result['_llm_context']
        self.assertIn('Theme color', context['summary'])
        self.assertIn('ACCENT_1', context['summary'])
        self.assertIn('25% darker', context['summary'])

    def test_colorformat_none_color_introspection(self):
        """Test that ColorFormat with None/inherited color is properly serialized."""
        # Create a test ColorFormat with no color set
        class MockColorFormatNone(ColorFormat):
            def __init__(self):
                super().__init__(None, None)  # Mock parent and color
                self._color_type = None
                self._brightness_val = 0.0

            @property
            def type(self):
                return self._color_type

            @property
            def rgb(self):
                raise AttributeError("no .rgb property on color type")

            @property
            def theme_color(self):
                raise AttributeError("no .theme_color property on color type")

            @property
            def brightness(self):
                # Might raise an error for None color types
                if self._color_type is None:
                    raise ValueError("can't access brightness when color.type is None")
                return self._brightness_val

        color_format = MockColorFormatNone()
        result = color_format.to_dict()

        # Check properties
        props = result['properties']

        # Verify None color properties
        self.assertIsNone(props['type'])
        self.assertIsNone(props['rgb'])
        self.assertIsNone(props['theme_color'])
        self.assertEqual(props['brightness'], 0.0)  # Should default to 0.0 due to error handling

        # Check LLM context for None color
        context = result['_llm_context']
        self.assertIn('No explicit color defined', context['summary'])

    def test_colorformat_error_handling(self):
        """Test that ColorFormat handles errors gracefully during introspection."""
        # Create a test ColorFormat that raises errors
        class MockColorFormatError(ColorFormat):
            def __init__(self):
                super().__init__(None, None)  # Mock parent and color
                self._color_type = MSO_COLOR_TYPE.RGB

            @property
            def type(self):
                return self._color_type

            @property
            def rgb(self):
                # Simulate an error accessing RGB
                raise AttributeError("simulated error accessing RGB")

            @property
            def theme_color(self):
                raise AttributeError("no .theme_color property on color type")

            @property
            def brightness(self):
                raise ValueError("simulated brightness access error")

        color_format = MockColorFormatError()
        result = color_format.to_dict()

        # Should not crash and handle errors gracefully
        props = result['properties']

        # Type should still be accessible
        self.assertEqual(props['type']['name'], 'RGB')

        # RGB should be None due to error handling
        self.assertIsNone(props['rgb'])
        self.assertIsNone(props['theme_color'])

        # Brightness should default to 0.0 due to error handling
        self.assertEqual(props['brightness'], 0.0)

        # LLM context should handle the error gracefully
        context = result['_llm_context']
        self.assertIn('RGB color', context['summary'])

    def test_colorformat_other_color_types(self):
        """Test that ColorFormat handles other color types (HSL, PRESET, etc.)."""
        # Create a test ColorFormat with HSL color type
        class MockColorFormatHSL(ColorFormat):
            def __init__(self):
                super().__init__(None, None)  # Mock parent and color
                self._color_type = MSO_COLOR_TYPE.HSL
                self._brightness_val = 0.0

            @property
            def type(self):
                return self._color_type

            @property
            def rgb(self):
                raise AttributeError("no .rgb property on color type")

            @property
            def theme_color(self):
                raise AttributeError("no .theme_color property on color type")

            @property
            def brightness(self):
                return self._brightness_val

        color_format = MockColorFormatHSL()
        result = color_format.to_dict()

        # Check properties
        props = result['properties']

        # Verify HSL color properties
        self.assertEqual(props['type']['_object_type'], 'MSO_COLOR_TYPE')
        self.assertEqual(props['type']['name'], 'HSL')

        # RGB and theme_color should be None for HSL
        self.assertIsNone(props['rgb'])
        self.assertIsNone(props['theme_color'])
        self.assertEqual(props['brightness'], 0.0)

        # Check LLM context for other color types
        context = result['_llm_context']
        self.assertIn('Color of type HSL', context['summary'])

    def test_colorformat_relationships_empty(self):
        """Test that ColorFormat._to_dict_relationships() returns empty dict."""
        # Create a minimal test ColorFormat
        class MockColorFormatMinimal(ColorFormat):
            def __init__(self):
                super().__init__(None, None)  # Mock parent and color

            @property
            def type(self):
                return None

            @property
            def brightness(self):
                return 0.0

        color_format = MockColorFormatMinimal()
        result = color_format.to_dict()

        # Relationships should be empty for ColorFormat
        self.assertEqual(result['relationships'], {})

    def test_colorformat_brightness_range_validation(self):
        """Test ColorFormat brightness property across valid range."""
        # Test various brightness values
        brightness_values = [-1.0, -0.5, 0.0, 0.5, 1.0]

        for brightness in brightness_values:
            with self.subTest(brightness=brightness):
                color_format = MockColorFormat(
                    color_type=MSO_COLOR_TYPE.RGB,
                    brightness=brightness
                )
                result = color_format.to_dict()

                props = result['properties']
                self.assertEqual(props['brightness'], brightness)

                # Check LLM context reflects brightness
                context = result['_llm_context']
                if brightness < 0:
                    self.assertIn('darker', context['summary'])
                elif brightness > 0:
                    self.assertIn('lighter', context['summary'])

    def test_colorformat_identity_consistency(self):
        """Test that ColorFormat identity information is consistent."""
        color_format = MockColorFormat()
        result = color_format.to_dict()

        # Check identity structure
        identity = result['_identity']
        self.assertIn('class_name', identity)
        self.assertIn('memory_address', identity)
        self.assertIn('description', identity)

        # Description should be consistent
        self.assertEqual(identity['description'], 'Represents a color definition.')

    def test_colorformat_llm_context_completeness(self):
        """Test that ColorFormat provides comprehensive LLM context."""
        # Test RGB color
        rgb_color = RGBColor(255, 128, 0)  # Orange
        color_format = MockColorFormat(
            color_type=MSO_COLOR_TYPE.RGB,
            rgb_color=rgb_color,
            brightness=0.2  # 20% lighter
        )
        result = color_format.to_dict()

        context = result['_llm_context']

        # Should have required context fields
        required_fields = ['description', 'summary', 'common_operations']
        for field in required_fields:
            self.assertIn(field, context)

        # Summary should be descriptive
        summary = context['summary']
        self.assertIn('RGB color', summary)
        self.assertIn('#FF8000', summary)  # Orange hex
        self.assertIn('20% lighter', summary)

        # Common operations should be helpful
        operations = context['common_operations']
        self.assertIsInstance(operations, list)
        self.assertTrue(len(operations) > 0)

        # Should include relevant operations
        operations_text = ' '.join(operations)
        self.assertIn('rgb', operations_text.lower())
        self.assertIn('color', operations_text.lower())

    def test_colorformat_preset_color_handling(self):
        """Test ColorFormat with PRESET color type."""
        # Create a test ColorFormat with PRESET color type
        class MockColorFormatPreset(ColorFormat):
            def __init__(self):
                super().__init__(None, None)
                self._color_type = MSO_COLOR_TYPE.PRESET

            @property
            def type(self):
                return self._color_type

            @property
            def rgb(self):
                raise AttributeError("no .rgb property on color type")

            @property
            def theme_color(self):
                raise AttributeError("no .theme_color property on color type")

            @property
            def brightness(self):
                return 0.0

        color_format = MockColorFormatPreset()
        result = color_format.to_dict()

        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'PRESET')
        self.assertIsNone(props['rgb'])
        self.assertIsNone(props['theme_color'])

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Color of type PRESET', context['summary'])


if __name__ == '__main__':
    unittest.main()