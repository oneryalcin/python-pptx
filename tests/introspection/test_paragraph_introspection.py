"""
Test _Paragraph introspection functionality - FEP-010

This module tests the _Paragraph.to_dict() introspection capabilities following
the modular testing pattern established for the introspection test suite.
"""

import unittest
from unittest.mock import Mock

from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT
from pptx.text.text import Font, _Paragraph, _Run
from pptx.util import Pt

from .mock_helpers import assert_basic_to_dict_structure


class MockTextParagraph:
    """Mock for CT_TextParagraph (a:p element)."""

    def __init__(self, text="Sample paragraph"):
        self.text = text
        self.pPr = None
        self.r_lst = []  # List of runs

    def get_or_add_pPr(self):
        """Mock for getting/adding paragraph properties element."""
        if self.pPr is None:
            self.pPr = MockParagraphProperties()
        return self.pPr


class MockParagraphProperties:
    """Mock for CT_TextParagraphProperties (a:pPr element)."""

    def __init__(self):
        self.algn = None  # alignment
        self.lvl = 0      # level
        self.line_spacing = None
        self.space_before = None
        self.space_after = None
        self.bullet = None
        self.defRPr = None  # default run properties

    def get_or_add_defRPr(self):
        """Mock for getting/adding default run properties element."""
        if self.defRPr is None:
            self.defRPr = Mock()
        return self.defRPr


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
                "summary": f"{self.name} {self.size.pt}pt "
                f"{'bold' if self.bold else ''}{'italic' if self.italic else ''}".strip()
            }
        }


class MockRun(_Run):
    """Mock _Run that returns realistic introspection data."""

    def __init__(self, text="Sample run"):
        # Don't call super().__init__ to avoid parent dependencies
        self._text = text

    @property
    def text(self):
        return self._text

    def to_dict(self, **kwargs):
        """Mock _Run.to_dict() method."""
        return {
            "_object_type": "_Run",
            "properties": {
                "text": self.text,
                "font": {"_object_type": "Font", "_summary": "inherited font"},
                "hyperlink_address": None,
            },
            "_llm_context": {
                "summary": f'Text run: "{self.text}" with inherited font.'
            }
        }


class MockParagraph(_Paragraph):
    """Mock _Paragraph with controllable behavior for testing."""

    def __init__(self, text="Sample paragraph", alignment=None, level=0,
                 line_spacing=None, space_before=None, space_after=None,
                 bullet=None, runs=None):
        # Don't call super().__init__ to avoid parent dependencies
        self._p = MockTextParagraph(text)
        self._text = text
        self._alignment = alignment
        self._level = level
        self._line_spacing = line_spacing
        self._space_before = space_before
        self._space_after = space_after
        self._bullet = bullet
        self._font = MockFont()
        self._runs = runs or [MockRun(text)]

        # Set up mock pPr with properties
        if (alignment is not None or level != 0 or line_spacing is not None or
            space_before is not None or space_after is not None or bullet is not None):
            pPr = self._p.get_or_add_pPr()
            pPr.algn = alignment
            pPr.lvl = level
            pPr.line_spacing = line_spacing
            pPr.space_before = space_before
            pPr.space_after = space_after
            pPr.bullet = bullet

    @property
    def text(self):
        return self._text

    @property
    def alignment(self):
        return self._alignment

    @property
    def level(self):
        return self._level

    @property
    def line_spacing(self):
        return self._line_spacing

    @property
    def space_before(self):
        return self._space_before

    @property
    def space_after(self):
        return self._space_after

    @property
    def bullet(self):
        return self._bullet

    @property
    def font(self):
        return self._font

    @property
    def runs(self):
        return self._runs


class TestParagraphIntrospection(unittest.TestCase):
    """Test cases for _Paragraph.to_dict() functionality."""

    def test_basic_paragraph_to_dict_structure(self):
        """Test that a basic paragraph returns correct to_dict structure."""
        paragraph = MockParagraph("Hello world")
        result = paragraph.to_dict()

        # Check basic structure
        assert_basic_to_dict_structure(self, result, "MockParagraph")

        # Check properties exist
        self.assertIn("properties", result)
        props = result["properties"]
        self.assertIn("text", props)
        self.assertIn("alignment", props)
        self.assertIn("level", props)
        self.assertIn("line_spacing", props)
        self.assertIn("space_before", props)
        self.assertIn("space_after", props)
        self.assertIn("bullet", props)
        self.assertIn("font", props)
        self.assertIn("runs", props)

        # Check identity has text preview
        self.assertIn("_identity", result)
        self.assertIn("description", result["_identity"])
        self.assertIn("Hello world", result["_identity"]["description"])

    def test_paragraph_with_basic_text(self):
        """Test paragraph with basic text content."""
        paragraph = MockParagraph("Simple paragraph content")
        result = paragraph.to_dict()

        props = result["properties"]
        self.assertEqual(props["text"], "Simple paragraph content")
        self.assertIsNone(props["alignment"])
        self.assertEqual(props["level"], 0)

    def test_paragraph_with_long_text_preview(self):
        """Test that long text is properly truncated in identity."""
        long_text = ("This is a very long paragraph that should be truncated "
                     "in the preview for the identity")
        paragraph = MockParagraph(long_text)
        result = paragraph.to_dict()

        description = result["_identity"]["description"]
        # Should be truncated at 50 characters with "..."
        self.assertIn("This is a very long paragraph that should be trunc...", description)

    def test_paragraph_with_alignment(self):
        """Test paragraph with specific alignment."""
        paragraph = MockParagraph("Centered text", alignment=PP_PARAGRAPH_ALIGNMENT.CENTER)
        result = paragraph.to_dict()

        props = result["properties"]
        # Alignment should be formatted as enum dict by _format_property_value_for_to_dict
        self.assertIsInstance(props["alignment"], dict)
        self.assertEqual(props["alignment"]["_object_type"], "PP_PARAGRAPH_ALIGNMENT")
        self.assertEqual(props["alignment"]["name"], "CENTER")

    def test_paragraph_with_indentation(self):
        """Test paragraph with indentation level."""
        paragraph = MockParagraph("Indented text", level=2)
        result = paragraph.to_dict()

        props = result["properties"]
        self.assertEqual(props["level"], 2)

    def test_paragraph_with_line_spacing(self):
        """Test paragraph with line spacing."""
        paragraph = MockParagraph("Spaced text", line_spacing=1.5)
        result = paragraph.to_dict()

        props = result["properties"]
        self.assertEqual(props["line_spacing"], 1.5)

    def test_paragraph_with_spacing_before_after(self):
        """Test paragraph with space before and after."""
        space_before = Pt(12)
        space_after = Pt(6)
        paragraph = MockParagraph("Text with spacing",
                                space_before=space_before,
                                space_after=space_after)
        result = paragraph.to_dict()

        props = result["properties"]
        # Properties should be formatted via _format_property_value_for_to_dict
        self.assertIsNotNone(props["space_before"])
        self.assertIsNotNone(props["space_after"])

    def test_paragraph_with_bullet(self):
        """Test paragraph with bullet formatting."""
        paragraph = MockParagraph("Bulleted text", bullet="•")
        result = paragraph.to_dict()

        props = result["properties"]
        self.assertEqual(props["bullet"], "•")

    def test_paragraph_with_font_properties(self):
        """Test paragraph with font properties."""
        font = MockFont(name="Times New Roman", size_pt=14, bold=True)
        paragraph = MockParagraph("Formatted text")
        paragraph._font = font
        result = paragraph.to_dict()

        props = result["properties"]
        self.assertIsInstance(props["font"], dict)
        self.assertEqual(props["font"]["_object_type"], "Font")

    def test_paragraph_with_multiple_runs(self):
        """Test paragraph with multiple text runs."""
        runs = [MockRun("First run"), MockRun("Second run"), MockRun("Third run")]
        paragraph = MockParagraph("Combined text")
        paragraph._runs = runs
        result = paragraph.to_dict()

        props = result["properties"]
        self.assertIsInstance(props["runs"], list)
        self.assertEqual(len(props["runs"]), 3)

        # Each run should be a dict with _object_type
        for run_dict in props["runs"]:
            self.assertIsInstance(run_dict, dict)
            self.assertEqual(run_dict["_object_type"], "_Run")

    def test_paragraph_max_depth_control_font(self):
        """Test that max_depth properly controls font expansion."""
        paragraph = MockParagraph("Test text")

        # With max_depth=1, font should be truncated
        result = paragraph.to_dict(max_depth=1)
        props = result["properties"]
        self.assertEqual(props["font"]["_depth_exceeded"], True)

        # With max_depth=2, font should be expanded
        result = paragraph.to_dict(max_depth=2)
        props = result["properties"]
        self.assertIn("properties", props["font"])

    def test_paragraph_max_depth_control_runs(self):
        """Test that max_depth properly controls runs expansion."""
        runs = [MockRun("Run 1"), MockRun("Run 2")]
        paragraph = MockParagraph("Test text")
        paragraph._runs = runs

        # With max_depth=1, runs should be truncated
        result = paragraph.to_dict(max_depth=1, expand_collections=True)
        props = result["properties"]
        self.assertIsInstance(props["runs"], list)
        for run_dict in props["runs"]:
            self.assertEqual(run_dict["_depth_exceeded"], True)

        # With max_depth=2, runs should be expanded
        result = paragraph.to_dict(max_depth=2, expand_collections=True)
        props = result["properties"]
        self.assertIsInstance(props["runs"], list)
        for run_dict in props["runs"]:
            self.assertIn("properties", run_dict)

    def test_paragraph_expand_collections_false(self):
        """Test expand_collections=False provides summary instead of full runs."""
        runs = [MockRun("Run 1"), MockRun("Run 2"), MockRun("Run 3")]
        paragraph = MockParagraph("Test text")
        paragraph._runs = runs

        result = paragraph.to_dict(expand_collections=False)
        props = result["properties"]

        # Should get summary instead of full list
        self.assertIsInstance(props["runs"], dict)
        self.assertIn("_collection_summary", props["runs"])
        self.assertEqual(props["runs"]["_collection_summary"], "3 runs")

    def test_paragraph_llm_context_basic(self):
        """Test LLM context generation for basic paragraph."""
        paragraph = MockParagraph("Sample paragraph text")
        result = paragraph.to_dict()

        context = result["_llm_context"]
        self.assertIn("description", context)
        self.assertIn("summary", context)
        self.assertIn("common_operations", context)

        # Check description contains text preview
        self.assertIn("Sample paragraph text", context["summary"])
        self.assertIn("Paragraph:", context["summary"])

        # Check common operations
        operations = context["common_operations"]
        self.assertIn("modify text content (paragraph.text = ...)", operations)
        self.assertIn("change alignment (paragraph.alignment = ...)", operations)
        self.assertIn("set indentation (paragraph.level = ...)", operations)

    def test_paragraph_llm_context_with_formatting(self):
        """Test LLM context includes formatting information."""
        paragraph = MockParagraph("Formatted text",
                                alignment=PP_PARAGRAPH_ALIGNMENT.CENTER,
                                level=1,
                                line_spacing=1.5,
                                bullet="•")
        result = paragraph.to_dict()

        context = result["_llm_context"]
        summary = context["summary"]
        self.assertIn("Formatted text", summary)
        # Should include some formatting info
        formatting_words = ["center", "indent", "spacing", "bullet"]
        self.assertTrue(any(word in summary.lower() for word in formatting_words))

    def test_paragraph_llm_context_empty(self):
        """Test LLM context for empty paragraph."""
        paragraph = MockParagraph("")
        result = paragraph.to_dict()

        context = result["_llm_context"]
        summary = context["summary"]
        self.assertIn("Empty paragraph", summary)

    def test_paragraph_llm_context_with_special_characters(self):
        """Test LLM context handles special characters in text."""
        paragraph = MockParagraph("Text with\nnewlines\vand\vtabs")
        result = paragraph.to_dict()

        context = result["_llm_context"]
        summary = context["summary"]
        # Special characters should be normalized to spaces
        self.assertIn("Text with newlines and tabs", summary)

    def test_paragraph_relationships_basic(self):
        """Test basic relationships structure."""
        runs = [MockRun("Run 1"), MockRun("Run 2")]
        paragraph = MockParagraph("Test text")
        paragraph._runs = runs
        result = paragraph.to_dict()

        rels = result.get("relationships", {})

        # Should have runs relationship
        if "runs" in rels:
            runs_rel = rels["runs"]
            self.assertIn("_collection_summary", runs_rel)
            self.assertEqual(runs_rel["_collection_summary"], "2 child runs")

    def test_paragraph_error_handling(self):
        """Test error handling in to_dict methods."""
        paragraph = MockParagraph("Test")

        # Mock font to raise exception
        def error_font(*args, **kwargs):
            raise Exception("Font error")
        paragraph._font.to_dict = error_font

        result = paragraph.to_dict()

        # Should still return valid structure with error context
        assert_basic_to_dict_structure(self, result, "MockParagraph")
        props = result["properties"]

        # Font should have error context
        self.assertIn("_error", props["font"])

    def test_paragraph_format_for_llm_flag(self):
        """Test format_for_llm flag affects output."""
        paragraph = MockParagraph("Test text")

        # Both should work without errors
        result_llm = paragraph.to_dict(format_for_llm=True)
        result_no_llm = paragraph.to_dict(format_for_llm=False)

        # LLM format should have basic structure including _llm_context
        assert_basic_to_dict_structure(self, result_llm, "MockParagraph")

        # Non-LLM format should have basic structure except _llm_context
        self.assertEqual(result_no_llm['_object_type'], "MockParagraph")
        self.assertIn('_identity', result_no_llm)
        self.assertIn('properties', result_no_llm)
        self.assertNotIn('_llm_context', result_no_llm)


if __name__ == "__main__":
    unittest.main()
