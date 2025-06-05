# tests/introspection/test_image_introspection.py

"""
Unit tests for Image.to_dict() introspection functionality (FEP-015).

Tests the introspection capabilities of Image objects, verifying
that image properties, metadata, and content information are properly
serialized in the to_dict() output.
"""

import unittest

from .mock_helpers import MockImage, assert_basic_to_dict_structure


class TestImageIntrospection(unittest.TestCase):
    """Test Image.to_dict() implementation for comprehensive image introspection."""

    def setUp(self):
        """Set up test fixtures for Image introspection tests."""
        self.mock_image = MockImage()

    def test_image_to_dict_basic_structure(self):
        """Test that Image.to_dict() returns expected basic structure."""
        result = self.mock_image.to_dict()

        assert_basic_to_dict_structure(self, result, "MockImage")
        self.assertIn("relationships", result)

    def test_image_identity_section(self):
        """Test Image._to_dict_identity() includes proper identification."""
        result = self.mock_image.to_dict()
        identity = result["_identity"]

        self.assertEqual(identity["class_name"], "MockImage")
        self.assertIn("description", identity)
        self.assertIn("test.png", identity["description"])
        self.assertEqual(identity["filename"], "test.png")

    def test_image_identity_section_without_filename(self):
        """Test Image._to_dict_identity() for streamed image without filename."""
        streamed_image = MockImage(filename=None)
        result = streamed_image.to_dict()
        identity = result["_identity"]

        self.assertIn("streamed image", identity["description"])
        self.assertNotIn("filename", identity)

    def test_image_properties_section(self):
        """Test Image._to_dict_properties() includes all image properties."""
        result = self.mock_image.to_dict()
        props = result["properties"]

        # Check basic properties
        self.assertEqual(props["content_type"], "image/png")
        self.assertEqual(props["extension"], "png")
        self.assertEqual(props["sha1_hash"], "abcd1234567890abcd1234567890abcd12345678")

        # Check dimensions
        self.assertIn("dimensions_px", props)
        self.assertEqual(props["dimensions_px"]["width"], 800)
        self.assertEqual(props["dimensions_px"]["height"], 600)

        # Check DPI
        self.assertIn("dpi", props)
        self.assertEqual(props["dpi"]["horizontal"], 72)
        self.assertEqual(props["dpi"]["vertical"], 72)

        # Check blob size
        self.assertIn("blob_size_bytes", props)
        self.assertIsInstance(props["blob_size_bytes"], int)
        self.assertGreater(props["blob_size_bytes"], 0)

    def test_image_relationships_section(self):
        """Test Image._to_dict_relationships() returns empty dict."""
        result = self.mock_image.to_dict()
        relationships = result["relationships"]

        # Image objects don't have relationships
        self.assertEqual(relationships, {})

    def test_image_llm_context_section(self):
        """Test Image._to_dict_llm_context() provides helpful descriptions."""
        result = self.mock_image.to_dict()
        llm_context = result["_llm_context"]

        self.assertIn("description", llm_context)
        self.assertIn("summary", llm_context)
        self.assertIn("common_operations", llm_context)

        # Check description content
        description = llm_context["description"]
        self.assertIn("PNG image", description)
        self.assertIn("800x600 pixels", description)
        self.assertIn("72x72 DPI", description)
        self.assertIn("'test.png'", description)

        # Check summary
        summary = llm_context["summary"]
        self.assertIn("PNG image", summary)
        self.assertIn("800x600px", summary)

        # Check operations
        operations = llm_context["common_operations"]
        self.assertIsInstance(operations, list)
        self.assertTrue(len(operations) > 0)
        self.assertTrue(any("blob" in op for op in operations))
        self.assertTrue(any("dimensions" in op for op in operations))

    def test_image_different_formats(self):
        """Test Image introspection for different image formats."""
        jpg_image = MockImage(filename="photo.jpg", content_type="image/jpeg", ext="jpg")
        result = jpg_image.to_dict()

        props = result["properties"]
        self.assertEqual(props["content_type"], "image/jpeg")
        self.assertEqual(props["extension"], "jpg")

        llm_context = result["_llm_context"]
        self.assertIn("JPG image", llm_context["description"])

    def test_image_custom_dimensions_and_dpi(self):
        """Test Image introspection with custom dimensions and DPI."""
        custom_image = MockImage(
            filename="large.png",
            size=(1920, 1080),
            dpi=(300, 300),
            blob_size=2000000
        )
        result = custom_image.to_dict()

        props = result["properties"]
        self.assertEqual(props["dimensions_px"]["width"], 1920)
        self.assertEqual(props["dimensions_px"]["height"], 1080)
        self.assertEqual(props["dpi"]["horizontal"], 300)
        self.assertEqual(props["dpi"]["vertical"], 300)

        llm_context = result["_llm_context"]
        self.assertIn("1920x1080 pixels", llm_context["description"])
        self.assertIn("300x300 DPI", llm_context["description"])

    def test_image_max_depth_parameter(self):
        """Test Image introspection respects max_depth parameter."""
        # Image is a leaf object, so max_depth shouldn't affect its properties
        result_depth_1 = self.mock_image.to_dict(max_depth=1)
        result_depth_3 = self.mock_image.to_dict(max_depth=3)

        # Properties should be the same since Image doesn't have nested objects
        self.assertEqual(result_depth_1["properties"], result_depth_3["properties"])

    def test_image_include_private_parameter(self):
        """Test Image introspection with include_private parameter."""
        result_no_private = self.mock_image.to_dict(include_private=False)
        result_with_private = self.mock_image.to_dict(include_private=True)

        # Image mock doesn't expose private attributes by default
        # but both should have the same structure
        self.assertEqual(
            result_no_private["properties"].keys(),
            result_with_private["properties"].keys()
        )

    def test_image_format_for_llm_parameter(self):
        """Test Image introspection with format_for_llm parameter."""
        result_no_llm = self.mock_image.to_dict(format_for_llm=False)
        result_with_llm = self.mock_image.to_dict(format_for_llm=True)

        # Without LLM formatting, should not have _llm_context
        self.assertNotIn("_llm_context", result_no_llm)
        self.assertIn("_llm_context", result_with_llm)

    def test_image_include_relationships_parameter(self):
        """Test Image introspection with include_relationships parameter."""
        result_no_rels = self.mock_image.to_dict(include_relationships=False)
        result_with_rels = self.mock_image.to_dict(include_relationships=True)

        # Without relationships, should not have relationships section
        self.assertNotIn("relationships", result_no_rels)
        self.assertIn("relationships", result_with_rels)


if __name__ == "__main__":
    unittest.main()
