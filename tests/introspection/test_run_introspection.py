"""
Test _Run introspection functionality - FEP-009

This module tests the _Run.to_dict() introspection capabilities following
the modular testing pattern established for the introspection test suite.
"""

import unittest
from unittest.mock import Mock

from pptx.text.text import _Run, Font, _Hyperlink
from pptx.util import Pt

from .mock_helpers import assert_basic_to_dict_structure


class MockTextRun:
    """Mock for CT_RegularTextRun (a:r element)."""
    
    def __init__(self, text="Sample text"):
        self.text = text
        self.rPr = None
        
    def get_or_add_rPr(self):
        """Mock for getting/adding run properties element."""
        if self.rPr is None:
            self.rPr = MockRunProperties()
        return self.rPr


class MockRunProperties:
    """Mock for CT_TextCharacterProperties (a:rPr element)."""
    
    def __init__(self):
        self.hlinkClick = None
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

    def add_hlinkClick(self, rId):
        """Mock for adding hyperlink click element."""
        self.hlinkClick = Mock()
        self.hlinkClick.rId = rId


class MockHyperlinkElement:
    """Mock for hyperlink click element."""
    
    def __init__(self, rId="rId1"):
        self.rId = rId


class MockFont(Font):
    """Mock Font that returns realistic introspection data."""
    
    def __init__(self, name="Arial", size_pt=12, bold=False, italic=False):
        # Don't call super().__init__ to avoid XML dependencies
        self._name = name
        self._size_pt = size_pt
        self._bold = bold
        self._italic = italic
        
    @property
    def name(self):
        return self._name
        
    @property
    def size(self):
        return Pt(self._size_pt) if self._size_pt else None
        
    @property
    def bold(self):
        return self._bold
        
    @property
    def italic(self):
        return self._italic
        
    def to_dict(self, **kwargs):
        """Mock Font.to_dict() method."""
        return {
            "_object_type": "Font",
            "properties": {
                "name": self.name,
                "size": {"_object_type": "Length", "pt": self.size.pt} if self.size else None,
                "bold": self.bold,
                "italic": self.italic,
            },
            "_llm_context": {
                "summary": f"{self.name} {self.size.pt}pt{'bold' if self.bold else ''}{'italic' if self.italic else ''}".strip()
            }
        }


class MockHyperlink(_Hyperlink):
    """Mock _Hyperlink that returns realistic behavior."""
    
    def __init__(self, address=None):
        # Don't call super().__init__ to avoid parent dependencies
        self._address = address
        
    @property
    def address(self):
        return self._address


class MockRun(_Run):
    """Mock _Run with controllable behavior for testing."""
    
    def __init__(self, text="Sample text", font=None, hyperlink_address=None):
        # Don't call super().__init__ to avoid parent dependencies
        self._r = MockTextRun(text)
        self._font = font or MockFont()
        self._hyperlink = MockHyperlink(hyperlink_address)
        
        # Set up hyperlink XML element if address exists
        if hyperlink_address:
            self._r.get_or_add_rPr()
            self._r.rPr.hlinkClick = MockHyperlinkElement("rId1")
        
    @property
    def text(self):
        return self._r.text
        
    @property
    def font(self):
        return self._font
        
    @property
    def hyperlink(self):
        return self._hyperlink


class TestRunIntrospection(unittest.TestCase):
    """Test cases for _Run.to_dict() functionality."""

    def test_basic_run_to_dict_structure(self):
        """Test that a basic run returns correct to_dict structure."""
        run = MockRun("Hello world")
        result = run.to_dict()
        
        # Check basic structure
        assert_basic_to_dict_structure(self, result, "MockRun")
        
        # Check properties exist
        self.assertIn("properties", result)
        props = result["properties"]
        self.assertIn("text", props)
        self.assertIn("font", props)
        self.assertIn("hyperlink_address", props)
        
        # Check identity has text preview
        self.assertIn("_identity", result)
        self.assertIn("description", result["_identity"])
        self.assertIn("Hello world", result["_identity"]["description"])
        
    def test_run_with_basic_text(self):
        """Test run with basic text content."""
        run = MockRun("Simple text content")
        result = run.to_dict()
        
        props = result["properties"]
        self.assertEqual(props["text"], "Simple text content")
        self.assertIsNone(props["hyperlink_address"])
        
    def test_run_with_long_text_preview(self):
        """Test that long text is properly truncated in identity."""
        long_text = "This is a very long text that should be truncated in the preview"
        run = MockRun(long_text)
        result = run.to_dict()
        
        description = result["_identity"]["description"]
        self.assertIn("This is a very long text that ...", description)
        
    def test_run_with_font_properties(self):
        """Test run with various font properties."""
        font = MockFont(name="Times New Roman", size_pt=14, bold=True, italic=True)
        run = MockRun("Formatted text", font=font)
        result = run.to_dict()
        
        props = result["properties"]
        self.assertIsInstance(props["font"], dict)
        self.assertEqual(props["font"]["_object_type"], "Font")
        
        # Font should be recursive call
        font_props = props["font"]["properties"]
        self.assertEqual(font_props["name"], "Times New Roman")
        self.assertEqual(font_props["size"]["pt"], 14)
        self.assertTrue(font_props["bold"])
        self.assertTrue(font_props["italic"])
        
    def test_run_with_hyperlink(self):
        """Test run with hyperlink."""
        run = MockRun("Click here", hyperlink_address="http://example.com")
        result = run.to_dict()
        
        props = result["properties"]
        self.assertEqual(props["hyperlink_address"], "http://example.com")
        
        # Check relationships for hyperlink
        rels = result.get("relationships", {})
        if "hyperlink" in rels:
            hyperlink_rel = rels["hyperlink"]
            self.assertEqual(hyperlink_rel["target_url"], "http://example.com")
            self.assertEqual(hyperlink_rel["rId"], "rId1")
            self.assertTrue(hyperlink_rel["is_external"])
        
    def test_run_without_hyperlink(self):
        """Test run without hyperlink."""
        run = MockRun("Regular text")
        result = run.to_dict()
        
        props = result["properties"]
        self.assertIsNone(props["hyperlink_address"])
        
        # Relationships should be empty or not contain hyperlink
        rels = result.get("relationships", {})
        self.assertNotIn("hyperlink", rels)
        
    def test_run_max_depth_control(self):
        """Test that max_depth properly controls font expansion."""
        font = MockFont(name="Arial", size_pt=12, bold=True)
        run = MockRun("Test text", font=font)
        
        # With max_depth=1, font should be truncated
        result = run.to_dict(max_depth=1)
        props = result["properties"]
        self.assertEqual(props["font"]["_depth_exceeded"], True)
        
        # With max_depth=2, font should be expanded
        result = run.to_dict(max_depth=2)
        props = result["properties"]
        self.assertIn("properties", props["font"])
        
    def test_run_llm_context_basic(self):
        """Test LLM context generation for basic run."""
        run = MockRun("Sample text")
        result = run.to_dict()
        
        context = result["_llm_context"]
        self.assertIn("description", context)
        self.assertIn("summary", context)
        self.assertIn("common_operations", context)
        
        # Check description contains text preview
        self.assertIn("Sample text", context["description"])
        self.assertIn("Text run:", context["description"])
        
        # Check common operations
        operations = context["common_operations"]
        self.assertIn("change text content (run.text = ...)", operations)
        self.assertIn("modify font (run.font.bold = True, etc.)", operations)
        self.assertIn("add/remove hyperlink (run.hyperlink.address = ...)", operations)
        
    def test_run_llm_context_with_hyperlink(self):
        """Test LLM context includes hyperlink information."""
        run = MockRun("Click me", hyperlink_address="https://example.com")
        result = run.to_dict()
        
        context = result["_llm_context"]
        description = context["description"]
        self.assertIn("Click me", description)
        self.assertIn("hyperlinked to 'https://example.com'", description)
        
    def test_run_llm_context_with_special_characters(self):
        """Test LLM context handles special characters in text."""
        run = MockRun("Text with\nnewlines\vand\vtabs")
        result = run.to_dict()
        
        context = result["_llm_context"]
        description = context["description"]
        # Special characters should be normalized to spaces
        self.assertIn("Text with newlines and tabs", description)
        
    def test_run_relationships_without_hyperlink(self):
        """Test relationships are empty when no hyperlink present."""
        run = MockRun("Plain text")
        result = run.to_dict()
        
        rels = result.get("relationships", {})
        self.assertEqual(len(rels), 0)
        
    def test_run_error_handling(self):
        """Test error handling in to_dict methods."""
        # Create a run that will trigger errors
        run = MockRun("Test")
        
        # Mock font to raise exception
        def error_font(*args, **kwargs):
            raise Exception("Font error")
        run._font.to_dict = error_font
        
        result = run.to_dict()
        
        # Should still return valid structure with error context
        assert_basic_to_dict_structure(self, result, "MockRun")
        props = result["properties"]
        
        # Font should have error context
        self.assertIn("_error", props["font"])
        
    def test_run_format_for_llm_flag(self):
        """Test format_for_llm flag affects output."""
        run = MockRun("Test text")
        
        # Both should work without errors
        result_llm = run.to_dict(format_for_llm=True)
        result_no_llm = run.to_dict(format_for_llm=False)
        
        # LLM format should have basic structure including _llm_context
        assert_basic_to_dict_structure(self, result_llm, "MockRun")
        
        # Non-LLM format should have basic structure except _llm_context
        self.assertEqual(result_no_llm['_object_type'], "MockRun")
        self.assertIn('_identity', result_no_llm)
        self.assertIn('properties', result_no_llm)
        self.assertNotIn('_llm_context', result_no_llm)


if __name__ == "__main__":
    unittest.main()