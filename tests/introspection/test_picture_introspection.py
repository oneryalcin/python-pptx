# tests/introspection/test_picture_introspection.py

"""
Unit tests for Picture.to_dict() introspection functionality (FEP-015).

Tests the introspection capabilities of Picture objects, verifying
that picture properties, image details, crop settings, and line formatting
are properly serialized in the to_dict() output.
"""

import unittest
from unittest.mock import Mock

from .mock_helpers import MockImage, MockPicture, assert_basic_to_dict_structure


class TestPictureIntrospection(unittest.TestCase):
    """Test Picture.to_dict() implementation for comprehensive picture introspection."""

    def setUp(self):
        """Set up test fixtures for Picture introspection tests."""
        self.mock_picture = MockPicture()

    def test_picture_to_dict_basic_structure(self):
        """Test that Picture.to_dict() returns expected basic structure."""
        result = self.mock_picture.to_dict()

        assert_basic_to_dict_structure(self, result, "MockPicture")
        self.assertIn("relationships", result)

    def test_picture_identity_section(self):
        """Test Picture._to_dict_identity() includes proper identification."""
        result = self.mock_picture.to_dict()
        identity = result["_identity"]

        self.assertEqual(identity["class_name"], "Picture")
        self.assertEqual(identity["shape_id"], 1)
        self.assertEqual(identity["name"], "Picture 1")
        self.assertIn("description", identity)
        self.assertIn("test.png", identity["description"])

    def test_picture_identity_section_without_image(self):
        """Test Picture._to_dict_identity() for picture without embedded image."""
        picture_no_image = MockPicture(image=None)
        picture_no_image._image = None  # Simulate no image
        result = picture_no_image.to_dict()
        identity = result["_identity"]

        self.assertIn("no embedded image", identity["description"])

    def test_picture_properties_section(self):
        """Test Picture._to_dict_properties() includes all picture properties."""
        result = self.mock_picture.to_dict()
        props = result["properties"]

        # Check crop properties
        self.assertEqual(props["crop_left"], 0.0)
        self.assertEqual(props["crop_top"], 0.0)
        self.assertEqual(props["crop_right"], 0.0)
        self.assertEqual(props["crop_bottom"], 0.0)

        # Check image details
        self.assertIn("image_details", props)
        image_details = props["image_details"]
        self.assertEqual(image_details["_object_type"], "MockImage")

        # Check auto shape mask type
        self.assertIn("auto_shape_mask_type", props)

        # Check line properties
        self.assertIn("line", props)
        line_props = props["line"]
        self.assertEqual(line_props["_object_type"], "MockLineFormat")

    def test_picture_properties_with_cropping(self):
        """Test Picture._to_dict_properties() with cropping values."""
        cropped_picture = MockPicture(
            crop_left=0.1,
            crop_top=0.05,
            crop_right=0.15,
            crop_bottom=0.2
        )
        result = cropped_picture.to_dict()
        props = result["properties"]

        self.assertEqual(props["crop_left"], 0.1)
        self.assertEqual(props["crop_top"], 0.05)
        self.assertEqual(props["crop_right"], 0.15)
        self.assertEqual(props["crop_bottom"], 0.2)

    def test_picture_properties_with_auto_shape_mask(self):
        """Test Picture._to_dict_properties() with auto shape masking."""
        # Mock an auto shape type enum
        mock_oval = Mock()
        mock_oval.name = "OVAL"
        mock_oval.value = 9

        masked_picture = MockPicture(auto_shape_type=mock_oval)
        result = masked_picture.to_dict()
        props = result["properties"]

        # The auto_shape_mask_type should be formatted properly
        self.assertIn("auto_shape_mask_type", props)

    def test_picture_properties_max_depth_limitation(self):
        """Test Picture._to_dict_properties() respects max_depth for nested objects."""
        result_depth_1 = self.mock_picture.to_dict(max_depth=1)
        result_depth_3 = self.mock_picture.to_dict(max_depth=3)

        props_depth_1 = result_depth_1["properties"]
        props_depth_3 = result_depth_3["properties"]

        # At depth 1, line should be truncated (since it uses max_depth-1 = 0)
        # MockLineFormat inherits from IntrospectionMixin so at depth 0 it returns _truncated
        if "_depth_exceeded" in props_depth_1["line"]:
            self.assertEqual(props_depth_1["line"]["_depth_exceeded"], True)
        elif "_truncated" in props_depth_1["line"]:
            self.assertIn("_truncated", props_depth_1["line"])
        else:
            # Should have one of these truncation indicators
            self.fail(f"Expected depth limitation in line object: {props_depth_1['line']}")

        # At depth 3, line should be fully expanded
        self.assertIn("properties", props_depth_3["line"])

    def test_picture_relationships_section(self):
        """Test Picture._to_dict_relationships() includes image part."""
        result = self.mock_picture.to_dict()
        relationships = result["relationships"]

        self.assertIn("image_part", relationships)
        self.assertEqual(relationships["image_part"], "Mock image part reference")

    def test_picture_llm_context_section(self):
        """Test Picture._to_dict_llm_context() provides helpful descriptions."""
        result = self.mock_picture.to_dict()
        llm_context = result["_llm_context"]

        self.assertIn("description", llm_context)
        self.assertIn("summary", llm_context)
        self.assertIn("common_operations", llm_context)

        # Check description content
        description = llm_context["description"]
        self.assertIn("PICTURE shape", description)
        self.assertIn("'Picture 1'", description)
        self.assertIn("(ID: 1)", description)
        self.assertIn("test.png", description)

        # Check operations
        operations = llm_context["common_operations"]
        self.assertIsInstance(operations, list)
        self.assertTrue(len(operations) > 0)
        self.assertTrue(any("crop" in op for op in operations))
        self.assertTrue(any("image source" in op for op in operations))
        self.assertTrue(any("mask shape" in op for op in operations))

    def test_picture_llm_context_with_cropping(self):
        """Test Picture._to_dict_llm_context() describes cropping."""
        cropped_picture = MockPicture(
            crop_left=0.1,
            crop_bottom=0.2
        )
        result = cropped_picture.to_dict()
        llm_context = result["_llm_context"]
        description = llm_context["description"]

        self.assertIn("Cropped", description)
        self.assertIn("10.0% from left", description)
        self.assertIn("20.0% from bottom", description)

    def test_picture_llm_context_with_masking(self):
        """Test Picture._to_dict_llm_context() describes shape masking."""
        # Mock an auto shape type enum
        mock_oval = Mock()
        mock_oval.name = "OVAL"

        masked_picture = MockPicture(auto_shape_type=mock_oval)
        result = masked_picture.to_dict()
        llm_context = result["_llm_context"]
        description = llm_context["description"]

        self.assertIn("Masked as OVAL", description)

    def test_picture_llm_context_without_image(self):
        """Test Picture._to_dict_llm_context() handles missing image gracefully."""
        picture_no_image = MockPicture(image=None)
        picture_no_image._image = None  # Simulate no image
        result = picture_no_image.to_dict()
        llm_context = result["_llm_context"]
        description = llm_context["description"]

        self.assertIn("no embedded image", description)

    def test_picture_max_depth_parameter(self):
        """Test Picture introspection respects max_depth parameter."""
        result_depth_0 = self.mock_picture.to_dict(max_depth=0)
        result_depth_2 = self.mock_picture.to_dict(max_depth=2)

        # At depth 0, the entire object should be truncated
        self.assertIn("_truncated", result_depth_0)
        self.assertNotIn("properties", result_depth_0)

        # At depth 2, nested objects should be expanded
        props_depth_2 = result_depth_2["properties"]
        self.assertIn("properties", props_depth_2["line"])

    def test_picture_include_relationships_parameter(self):
        """Test Picture introspection with include_relationships parameter."""
        result_no_rels = self.mock_picture.to_dict(include_relationships=False)
        result_with_rels = self.mock_picture.to_dict(include_relationships=True)

        # Without relationships, should not have relationships section
        self.assertNotIn("relationships", result_no_rels)
        self.assertIn("relationships", result_with_rels)

    def test_picture_format_for_llm_parameter(self):
        """Test Picture introspection with format_for_llm parameter."""
        result_no_llm = self.mock_picture.to_dict(format_for_llm=False)
        result_with_llm = self.mock_picture.to_dict(format_for_llm=True)

        # Without LLM formatting, should not have _llm_context
        self.assertNotIn("_llm_context", result_no_llm)
        self.assertIn("_llm_context", result_with_llm)

    def test_picture_different_image_types(self):
        """Test Picture introspection with different image types."""
        jpg_image = MockImage(filename="photo.jpg", ext="jpg")
        jpg_picture = MockPicture(image=jpg_image, name="JPEG Picture")

        result = jpg_picture.to_dict()
        identity = result["_identity"]

        self.assertIn("photo.jpg", identity["description"])
        self.assertEqual(identity["name"], "JPEG Picture")

    def test_picture_streamed_image(self):
        """Test Picture introspection with streamed image (no filename)."""
        streamed_image = MockImage(filename=None, ext="png")
        streamed_picture = MockPicture(image=streamed_image)

        result = streamed_picture.to_dict()
        identity = result["_identity"]

        self.assertIn("streamed png image", identity["description"])

    def test_picture_error_handling_for_image_access(self):
        """Test Picture introspection handles image access errors gracefully."""
        # This test would be more relevant with real Picture objects
        # where image access can fail, but we can still test the structure
        result = self.mock_picture.to_dict()

        # Should not raise exceptions and should have proper structure
        self.assertIn("image_details", result["properties"])
        self.assertIn("_object_type", result["properties"]["image_details"])


if __name__ == "__main__":
    unittest.main()
