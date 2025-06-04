# tests/introspection/test_enum_formatting.py

"""
Enum Formatting Tests

Tests for BaseEnum and BaseXmlEnum introspection functionality including:
- BaseEnum serialization (name, value, description)
- BaseXmlEnum serialization (includes xml_value)
- Enum members with None/empty xml_values
- Collections containing enum members
- Non-standard enum fallback behavior
"""

import unittest
from pptx.enum.shapes import MSO_SHAPE_TYPE, MSO_AUTO_SHAPE_TYPE, PROG_ID
from pptx.enum.dml import MSO_COLOR_TYPE, MSO_LINE_DASH_STYLE

from .mock_helpers import (
    EnumTestObj, XmlEnumTestObj, EnumCollectionTestObj,
    assert_basic_to_dict_structure, assert_enum_dict_structure
)


class TestEnumFormatting(unittest.TestCase):
    """Test enum introspection and serialization functionality."""

    def test_base_enum_formatting(self):
        """Test that BaseEnum members are properly serialized to dictionaries."""
        # Test MSO_SHAPE_TYPE (BaseEnum)
        obj = EnumTestObj(MSO_SHAPE_TYPE.PICTURE)
        result = obj.to_dict()

        expected_shape_type_dict = {
            "_object_type": "MSO_SHAPE_TYPE",
            "name": "PICTURE",
            "value": 13,
            "description": "Picture"
        }

        self.assertEqual(result['properties']['shape_type'], expected_shape_type_dict)
        # Verify it doesn't have xml_value since it's BaseEnum, not BaseXmlEnum
        self.assertNotIn("xml_value", result['properties']['shape_type'])

    def test_base_xml_enum_formatting(self):
        """Test that BaseXmlEnum members are properly serialized to dictionaries."""
        # Test MSO_AUTO_SHAPE_TYPE (BaseXmlEnum)
        obj = XmlEnumTestObj(MSO_AUTO_SHAPE_TYPE.RECTANGLE)
        result = obj.to_dict()

        expected_auto_shape_dict = {
            "_object_type": "MSO_AUTO_SHAPE_TYPE",
            "name": "RECTANGLE",
            "value": 1,
            "description": "Rectangle",
            "xml_value": "rect"
        }

        self.assertEqual(result['properties']['auto_shape_type'], expected_auto_shape_dict)
        # Verify it has xml_value since it's BaseXmlEnum
        self.assertIn("xml_value", result['properties']['auto_shape_type'])

    def test_enum_with_none_xml_value(self):
        """Test enum members that have None or empty xml_value."""
        # Create a test object with enum that has empty xml_value
        class NoneXmlEnumTestObj:
            def __init__(self, enum_val):
                self.line_style = enum_val

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "line_style": self._format_property_value_for_to_dict(
                        self.line_style, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                }

        # Add the IntrospectionMixin methods
        from pptx.introspection import IntrospectionMixin
        class NoneXmlEnumTestObjWithMixin(IntrospectionMixin, NoneXmlEnumTestObj):
            pass

        # Test enum member with empty xml_value (DASH_STYLE_MIXED has empty xml_value "")
        obj = NoneXmlEnumTestObjWithMixin(MSO_LINE_DASH_STYLE.DASH_STYLE_MIXED)
        result = obj.to_dict()

        expected_dict = {
            "_object_type": "MSO_LINE_DASH_STYLE",
            "name": "DASH_STYLE_MIXED",
            "value": -2,
            "description": "Not supported.",
            "xml_value": ""  # This enum has empty string, not None
        }

        self.assertEqual(result['properties']['line_style'], expected_dict)

    def test_enum_collections(self):
        """Test that collections containing enum members are properly handled."""
        obj = EnumCollectionTestObj()
        result = obj.to_dict(max_depth=3)  # Ensure we have enough depth for collection expansion

        # Check that enum members in collections are properly serialized
        shape_types = result['properties']['shape_types']
        self.assertIsInstance(shape_types, list)
        self.assertEqual(len(shape_types), 2)

        # First enum in collection
        assert_enum_dict_structure(self, shape_types[0], "PICTURE", 13, has_xml_value=False)

        # Second enum in collection
        assert_enum_dict_structure(self, shape_types[1], "TABLE", 19, has_xml_value=False)

        # Mixed collection should handle enum, string, and int properly
        mixed = result['properties']['mixed_collection']
        self.assertIsInstance(mixed, list)
        self.assertEqual(len(mixed), 3)

        # First item is enum
        assert_enum_dict_structure(self, mixed[0], "RGB", 1, has_xml_value=False)
        # Second item is string
        self.assertEqual(mixed[1], "string")
        # Third item is int
        self.assertEqual(mixed[2], 42)

    def test_prog_id_enum_handling(self):
        """Test that PROG_ID enum (which doesn't inherit from BaseEnum/BaseXmlEnum) falls back to repr."""
        # Create a test object with PROG_ID
        class ProgIdTestObj:
            def __init__(self, prog_id):
                self.prog_id = prog_id

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "prog_id": self._format_property_value_for_to_dict(
                        self.prog_id, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                }

        # Add the IntrospectionMixin methods
        from pptx.introspection import IntrospectionMixin
        class ProgIdTestObjWithMixin(IntrospectionMixin, ProgIdTestObj):
            pass

        # PROG_ID doesn't inherit from BaseEnum or BaseXmlEnum, so it should fall back to repr
        obj = ProgIdTestObjWithMixin(PROG_ID.XLSX)
        result = obj.to_dict()

        # Should fall back to repr() since PROG_ID is not BaseEnum/BaseXmlEnum
        self.assertIsInstance(result['properties']['prog_id'], str)
        self.assertIn('PROG_ID.XLSX', result['properties']['prog_id'])
        # Should NOT be a dict with _object_type
        self.assertNotIsInstance(result['properties']['prog_id'], dict)

    def test_enum_dict_structure_validation(self):
        """Test that enum dictionaries have consistent structure across different enum types."""
        # Test various enum types to ensure consistent structure
        test_cases = [
            (MSO_SHAPE_TYPE.PICTURE, "MSO_SHAPE_TYPE", "PICTURE", 13, False),
            (MSO_AUTO_SHAPE_TYPE.RECTANGLE, "MSO_AUTO_SHAPE_TYPE", "RECTANGLE", 1, True),
            (MSO_COLOR_TYPE.RGB, "MSO_COLOR_TYPE", "RGB", 1, False),
            (MSO_LINE_DASH_STYLE.SOLID, "MSO_LINE_DASH_STYLE", "SOLID", 1, True),
        ]

        for enum_val, expected_type, expected_name, expected_value, has_xml in test_cases:
            with self.subTest(enum_type=expected_type):
                obj = EnumTestObj(enum_val)
                result = obj.to_dict()
                enum_dict = result['properties']['shape_type']

                # Check basic structure
                self.assertEqual(enum_dict['_object_type'], expected_type)
                assert_enum_dict_structure(self, enum_dict, expected_name, expected_value, has_xml)

    def test_enum_error_handling(self):
        """Test that enum introspection handles edge cases gracefully."""
        # Test with None enum value
        obj = EnumTestObj(None)
        result = obj.to_dict()

        # None should be serialized as None, not as an enum dict
        self.assertIsNone(result['properties']['shape_type'])

        # Test with invalid enum-like object
        class FakeEnum:
            def __init__(self):
                self.name = "FAKE"
                self.value = 999

        obj = EnumTestObj(FakeEnum())
        result = obj.to_dict()

        # Should fall back to string representation for non-BaseEnum objects
        self.assertIsInstance(result['properties']['shape_type'], str)

    def test_enum_descriptions(self):
        """Test that enum descriptions are properly captured when available."""
        # Test that description field is populated correctly
        obj = EnumTestObj(MSO_SHAPE_TYPE.PICTURE)
        result = obj.to_dict()
        enum_dict = result['properties']['shape_type']

        self.assertIn('description', enum_dict)
        self.assertEqual(enum_dict['description'], "Picture")

        # Test enum with different description
        obj = EnumTestObj(MSO_SHAPE_TYPE.AUTO_SHAPE)
        result = obj.to_dict()
        enum_dict = result['properties']['shape_type']

        self.assertEqual(enum_dict['description'], "AutoShape")


if __name__ == '__main__':
    unittest.main()