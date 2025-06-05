"""
Test Font introspection functionality - FEP-007

This module tests the Font.to_dict() introspection capabilities following
the modular testing pattern established for the introspection test suite.
"""

import unittest
from unittest.mock import Mock

from pptx.dml.fill import FillFormat
from pptx.enum.lang import MSO_LANGUAGE_ID
from pptx.enum.text import MSO_TEXT_UNDERLINE_TYPE
from pptx.text.text import Font
from pptx.util import Pt

from .mock_helpers import assert_basic_to_dict_structure


class MockTextCharacterProperties:
    """Mock for CT_TextCharacterProperties (a:rPr element)."""
    
    def __init__(self):
        # Font properties
        self.b = None  # bold
        self.i = None  # italic
        self.u = None  # underline
        self.strike = None  # strikethrough
        self.sz = None  # size in centipoints
        self.lang = None  # language ID
        self.latin = None  # typeface info
        
    def get_or_add_latin(self):
        """Mock for getting/adding latin typeface element."""
        if self.latin is None:
            self.latin = Mock()
            self.latin.typeface = None
        return self.latin
        
    def _remove_latin(self):
        """Mock for removing latin typeface element."""
        self.latin = None


class MockFillFormat(FillFormat):
    """Mock FillFormat that returns realistic introspection data."""
    
    def __init__(self, fill_type="SOLID", color_info=None):
        # Don't call super().__init__ to avoid XML dependencies
        self._fill_type = fill_type
        self._color_info = color_info or {"rgb": "#FF0000", "summary": "RGB color: #FF0000 (R:255, G:0, B:0)."}
    
    def to_dict(self, include_relationships=True, max_depth=3, include_private=False, 
                expand_collections=True, format_for_llm=True, _visited_ids=None):
        """Return mock fill format introspection data."""
        return {
            "_object_type": "FillFormat", 
            "properties": {"type": {"_object_type": "MSO_FILL", "name": self._fill_type}},
            "_llm_context": {"summary": self._color_info["summary"]}
        }


class MockFont(Font):
    """Mock Font class for testing introspection without XML dependencies."""
    
    def __init__(self, name=None, size=None, bold=None, italic=None, underline=None, 
                 strikethrough=None, language_id=None, fill_format=None):
        # Create mock CT_TextCharacterProperties without calling super().__init__
        self._rPr = MockTextCharacterProperties()
        self._element = self._rPr
        
        # Set properties
        if name is not None:
            self._rPr.get_or_add_latin().typeface = name
        if size is not None:
            # Convert to centipoints (size in EMU / 12700 * 100)
            self._rPr.sz = int(size.emu / 12700 * 100)
        if bold is not None:
            self._rPr.b = bold
        if italic is not None:
            self._rPr.i = italic
        if underline is not None:
            self._rPr.u = underline
        if strikethrough is not None:
            # Convert boolean to appropriate enum value
            from pptx.oxml.simpletypes import ST_TextFontStrike
            if strikethrough:
                self._rPr.strike = ST_TextFontStrike.SINGLE_STRIKE
            else:
                self._rPr.strike = ST_TextFontStrike.NO_STRIKE
        if language_id is not None:
            self._rPr.lang = language_id
            
        # Set up fill format
        self._fill_format = fill_format or MockFillFormat()
    
    @property
    def fill(self):
        """Return mock fill format."""
        return self._fill_format


class TestFontIntrospection(unittest.TestCase):
    """Test Font introspection functionality."""

    def test_font_basic_introspection(self):
        """Test that Font objects are properly serialized with basic structure."""
        font = MockFont()
        result = font.to_dict()
        
        # Use shared assertion helper
        assert_basic_to_dict_structure(self, result, 'MockFont')
        
        # Verify Font-specific structure
        props = result['properties']
        expected_props = ['name', 'size', 'bold', 'italic', 'underline', 'strikethrough', 'language_id', 'color']
        for prop in expected_props:
            self.assertIn(prop, props, f"Font introspection missing property: {prop}")
        
        # Verify LLM context
        context = result['_llm_context']
        self.assertIn('summary', context)
        self.assertIn('description', context)
        self.assertIn('common_operations', context)

    def test_font_default_properties_introspection(self):
        """Test Font with all default/None properties (inherited font)."""
        # Create font with no useful color information
        fill_format = MockFillFormat("BACKGROUND", {"summary": "Background fill."})
        font = MockFont(fill_format=fill_format)
        result = font.to_dict()
        
        props = result['properties']
        
        # All properties should be None for default font
        self.assertIsNone(props['name'])
        self.assertIsNone(props['size'])
        self.assertIsNone(props['bold'])
        self.assertIsNone(props['italic'])
        self.assertIsNone(props['underline'])
        self.assertIsNone(props['strikethrough'])
        
        # Language ID defaults to MSO_LANGUAGE_ID.NONE
        lang_result = props['language_id']
        self.assertEqual(lang_result['_object_type'], 'MSO_LANGUAGE_ID')
        self.assertEqual(lang_result['name'], 'NONE')
        
        # Color should be FillFormat object
        color_result = props['color']
        self.assertEqual(color_result['_object_type'], 'FillFormat')
        
        # LLM context should indicate inheritance
        context = result['_llm_context']
        self.assertEqual(context['summary'], 'Font settings are inherited.')

    def test_font_formatted_properties_introspection(self):
        """Test Font with all properties set to specific values."""
        font = MockFont(
            name="Arial",
            size=Pt(14),
            bold=True,
            italic=True,
            underline=MSO_TEXT_UNDERLINE_TYPE.SINGLE_LINE,
            strikethrough=True,
            language_id=MSO_LANGUAGE_ID.ENGLISH_US,
            fill_format=MockFillFormat("SOLID", {"summary": "RGB color: #0000FF (R:0, G:0, B:255)."})
        )
        result = font.to_dict()
        
        props = result['properties']
        
        # Verify name
        self.assertEqual(props['name'], "Arial")
        
        # Verify size (Length object)
        size_result = props['size']
        self.assertEqual(size_result['_object_type'], 'Centipoints')
        self.assertEqual(size_result['pt'], 14.0)
        
        # Verify boolean properties
        self.assertTrue(props['bold'])
        self.assertTrue(props['italic'])
        self.assertTrue(props['strikethrough'])
        
        # Verify underline (returns True for SINGLE_LINE)
        underline_result = props['underline']
        self.assertTrue(underline_result)
        
        # Verify language ID enum
        lang_result = props['language_id']
        self.assertEqual(lang_result['_object_type'], 'MSO_LANGUAGE_ID')
        self.assertEqual(lang_result['name'], 'ENGLISH_US')
        
        # Verify color fill format
        color_result = props['color']
        self.assertEqual(color_result['_object_type'], 'FillFormat')
        
        # Verify LLM context includes all elements
        context = result['_llm_context']
        summary = context['summary']
        self.assertIn('Arial', summary)
        self.assertIn('14.0pt', summary)
        self.assertIn('bold', summary)
        self.assertIn('italic', summary)
        self.assertIn('strikethrough', summary)

    def test_font_partial_formatting_introspection(self):
        """Test Font with some properties set, others inherited."""
        font = MockFont(
            name="Times New Roman",
            size=Pt(12),
            bold=True,
            # italic=None (inherited)
            # underline=None (inherited)
            # strikethrough=None (inherited)
        )
        result = font.to_dict()
        
        props = result['properties']
        
        # Verify set properties
        self.assertEqual(props['name'], "Times New Roman")
        size_result = props['size']
        self.assertEqual(size_result['pt'], 12.0)
        self.assertTrue(props['bold'])
        
        # Verify inherited properties
        self.assertIsNone(props['italic'])
        self.assertIsNone(props['underline'])
        self.assertIsNone(props['strikethrough'])
        
        # LLM context should include set properties only
        context = result['_llm_context']
        summary = context['summary']
        self.assertIn('Times New Roman', summary)
        self.assertIn('12.0pt', summary)
        self.assertIn('bold', summary)
        self.assertNotIn('italic', summary)

    def test_font_underline_enum_introspection(self):
        """Test Font with various underline enum values."""
        test_cases = [
            (MSO_TEXT_UNDERLINE_TYPE.SINGLE_LINE, True, "underlined"),  # SINGLE_LINE -> True
            (MSO_TEXT_UNDERLINE_TYPE.DOUBLE_LINE, "double line underline"),
            (MSO_TEXT_UNDERLINE_TYPE.WAVY_LINE, "wavy line underline"),
        ]
        
        for test_case in test_cases:
            if len(test_case) == 3:
                underline_enum, expected_result, expected_summary_part = test_case
            else:
                underline_enum, expected_summary_part = test_case
                expected_result = {"_object_type": "MSO_TEXT_UNDERLINE_TYPE"}
                
            with self.subTest(underline=underline_enum):
                font = MockFont(name="Arial", underline=underline_enum)
                result = font.to_dict()
                
                # Check property serialization
                underline_result = result['properties']['underline']
                if isinstance(expected_result, bool):
                    # SINGLE_LINE gets converted to boolean True
                    self.assertEqual(underline_result, expected_result)
                else:
                    # Other enum values should be preserved as enums
                    self.assertEqual(underline_result['_object_type'], 'MSO_TEXT_UNDERLINE_TYPE')
                
                # Check LLM context
                summary = result['_llm_context']['summary']
                if expected_summary_part:
                    self.assertIn(expected_summary_part, summary)

    def test_font_color_integration_with_fillformat(self):
        """Test Font color integration with FillFormat introspection."""
        # Test different color scenarios
        color_scenarios = [
            ("SOLID", {"summary": "RGB color: #FF0000 (R:255, G:0, B:0)."}),
            ("BACKGROUND", {"summary": "Background fill."}),
            ("GRADIENT", {"summary": "Gradient fill with 2 stops."}),
        ]
        
        for fill_type, color_info in color_scenarios:
            with self.subTest(fill_type=fill_type):
                fill_format = MockFillFormat(fill_type, color_info)
                font = MockFont(name="Arial", fill_format=fill_format)
                result = font.to_dict()
                
                # Verify color property is FillFormat object
                color_result = result['properties']['color']
                self.assertEqual(color_result['_object_type'], 'FillFormat')
                
                # Verify LLM context includes color information when appropriate
                summary = result['_llm_context']['summary']
                if fill_type == "SOLID":
                    self.assertIn('color RGB color: #FF0000', summary)
                elif fill_type in ["BACKGROUND", "GRADIENT"]:
                    # Background and gradient don't add useful color info to summary
                    self.assertNotIn('color', summary)

    def test_font_depth_limiting(self):
        """Test Font introspection respects max_depth parameter."""
        font = MockFont(name="Arial")
        
        # Test with max_depth=1 (should limit color introspection)
        result = font.to_dict(max_depth=1)
        color_result = result['properties']['color']
        self.assertEqual(color_result['_object_type'], 'FillFormat')
        self.assertTrue(color_result.get('_depth_exceeded', False))
        
        # Test with max_depth=2 (should allow color introspection)
        result = font.to_dict(max_depth=2)
        color_result = result['properties']['color']
        self.assertEqual(color_result['_object_type'], 'FillFormat')
        self.assertNotIn('_depth_exceeded', color_result)

    def test_font_error_handling(self):
        """Test Font introspection handles property access errors gracefully."""
        # Create a separate class for this test to avoid affecting other tests
        class ErrorFont(MockFont):
            @property 
            def name(self):
                raise RuntimeError("Simulated property access error")
        
        font = ErrorFont()
        result = font.to_dict()
        
        # Should contain error context for name property
        name_result = result['properties']['name']
        self.assertIn('_error', name_result)
        self.assertIn('RuntimeError', str(name_result))
        
        # Other properties should still work
        self.assertIsNone(result['properties']['size'])

    def test_font_llm_context_error_recovery(self):
        """Test Font LLM context generation handles errors gracefully."""
        font = MockFont(name="Arial")
        
        # Mock an error in color extraction
        original_extract = font._extract_color_summary
        font._extract_color_summary = lambda: None  # Simulate extraction failure
        
        result = font.to_dict()
        context = result['_llm_context']
        
        # Should still generate meaningful summary without color info
        self.assertIn('Arial', context['summary'])
        self.assertIn('description', context)
        self.assertIn('common_operations', context)
        
        # Restore original method
        font._extract_color_summary = original_extract

    def test_font_relationships_empty(self):
        """Test Font has no relationships."""
        font = MockFont(name="Arial")
        result = font.to_dict()
        
        # Relationships should be empty
        relationships = result.get('relationships', {})
        self.assertEqual(len(relationships), 0)


if __name__ == '__main__':
    unittest.main()