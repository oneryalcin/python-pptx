# tests/introspection/test_precision_inspection.py
"""
Unit tests for FEP-019: Precision Inspection Controls (to_dict Enhancement).

Tests the new field selection and structured collection summary capabilities
added to IntrospectionMixin.to_dict() method.
"""

import unittest
from unittest.mock import Mock, PropertyMock, patch
from pptx.introspection import IntrospectionMixin


class MockIntrospectableObject(IntrospectionMixin):
    """Mock object for testing precision inspection controls."""
    
    def __init__(self):
        self.name = "test_object"
        self.value = 42
        self.nested_list = ["item1", "item2", "item3"]
        self.nested_dict = {"key1": "value1", "key2": "value2"}
        
    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {
            "name": self.name,
            "value": self.value,
            "nested_list": self._format_property_value_for_to_dict(
                self.nested_list, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            ),
            "nested_dict": self._format_property_value_for_to_dict(
                self.nested_dict, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            ),
        }
        
    def _to_dict_relationships(self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private):
        return {"parent": "parent_object", "children": ["child1", "child2"]}


class TestFieldPathParsing(unittest.TestCase):
    """Test field path parsing functionality."""
    
    def setUp(self):
        self.obj = MockIntrospectableObject()

    def test_parse_simple_field_paths(self):
        """Test parsing simple field paths."""
        fields = ["_identity", "properties"]
        expected = {
            "_identity": True,
            "properties": True
        }
        result = self.obj._parse_field_paths(fields)
        self.assertEqual(result, expected)

    def test_parse_nested_field_paths(self):
        """Test parsing nested field paths."""
        fields = ["_identity.shape_id", "properties.fill.type"]
        expected = {
            "_identity": {"shape_id": True},
            "properties": {"fill": {"type": True}}
        }
        result = self.obj._parse_field_paths(fields)
        self.assertEqual(result, expected)

    def test_parse_wildcard_field_paths(self):
        """Test parsing wildcard field paths."""
        fields = ["properties.fill.*", "_identity.shape_id"]
        expected = {
            "properties": {"fill": {"*": True}},
            "_identity": {"shape_id": True}
        }
        result = self.obj._parse_field_paths(fields)
        self.assertEqual(result, expected)

    def test_parse_complex_field_paths(self):
        """Test parsing complex combination of field paths."""
        fields = [
            "_identity.shape_id",
            "properties.fill.type",
            "properties.line.*",
            "relationships.parent"
        ]
        expected = {
            "_identity": {"shape_id": True},
            "properties": {
                "fill": {"type": True},
                "line": {"*": True}
            },
            "relationships": {"parent": True}
        }
        result = self.obj._parse_field_paths(fields)
        self.assertEqual(result, expected)

    def test_parse_empty_field_list(self):
        """Test parsing empty field list."""
        fields = []
        expected = {}
        result = self.obj._parse_field_paths(fields)
        self.assertEqual(result, expected)


class TestFieldTreeFiltering(unittest.TestCase):
    """Test field tree filtering functionality."""
    
    def setUp(self):
        self.obj = MockIntrospectableObject()

    def test_filter_dict_with_true_tree(self):
        """Test filtering with True tree (should return full dict)."""
        full_dict = {"a": 1, "b": 2, "c": 3}
        result = self.obj._filter_dict_by_tree(full_dict, True)
        self.assertEqual(result, full_dict)

    def test_filter_dict_with_wildcard(self):
        """Test filtering with wildcard tree (should return full dict)."""
        full_dict = {"a": 1, "b": 2, "c": 3}
        tree = {"*": True}
        result = self.obj._filter_dict_by_tree(full_dict, tree)
        self.assertEqual(result, full_dict)

    def test_filter_dict_with_specific_keys(self):
        """Test filtering with specific key selection."""
        full_dict = {"a": 1, "b": 2, "c": 3}
        tree = {"a": True, "c": True}
        expected = {"a": 1, "c": 3}
        result = self.obj._filter_dict_by_tree(full_dict, tree)
        self.assertEqual(result, expected)

    def test_filter_dict_with_nested_structure(self):
        """Test filtering with nested dictionary structure."""
        full_dict = {
            "section1": {"prop1": "value1", "prop2": "value2"},
            "section2": {"prop3": "value3", "prop4": "value4"}
        }
        tree = {
            "section1": {"prop1": True},
            "section2": True
        }
        expected = {
            "section1": {"prop1": "value1"},
            "section2": {"prop3": "value3", "prop4": "value4"}
        }
        result = self.obj._filter_dict_by_tree(full_dict, tree)
        self.assertEqual(result, expected)


class TestSparseDocumentBuilding(unittest.TestCase):
    """Test sparse document building functionality."""
    
    def setUp(self):
        self.obj = MockIntrospectableObject()

    def test_to_dict_with_identity_fields(self):
        """Test sparse dict building with identity fields only."""
        fields = ["_identity.class_name"]
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=False)
        
        self.assertIn("_object_type", result)
        self.assertIn("_identity", result)
        self.assertIn("class_name", result["_identity"])
        self.assertNotIn("properties", result)
        self.assertNotIn("relationships", result)

    def test_to_dict_with_property_fields(self):
        """Test sparse dict building with specific property fields."""
        fields = ["properties.name", "properties.value"]
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=False)
        
        self.assertIn("_object_type", result)
        self.assertIn("properties", result)
        self.assertIn("name", result["properties"])
        self.assertIn("value", result["properties"])
        self.assertNotIn("nested_list", result["properties"])

    def test_to_dict_with_wildcard_properties(self):
        """Test sparse dict building with wildcard property selection."""
        fields = ["properties.*"]
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=False)
        
        self.assertIn("_object_type", result)
        self.assertIn("properties", result)
        # Should contain all properties due to wildcard
        self.assertIn("name", result["properties"])
        self.assertIn("value", result["properties"])
        self.assertIn("nested_list", result["properties"])

    def test_to_dict_with_relationship_fields(self):
        """Test sparse dict building with relationship fields."""
        fields = ["relationships.parent"]
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=True)
        
        self.assertIn("_object_type", result)
        self.assertIn("relationships", result)
        self.assertIn("parent", result["relationships"])
        self.assertNotIn("children", result["relationships"])

    def test_to_dict_mixed_field_selection(self):
        """Test sparse dict building with mixed field types."""
        fields = ["_identity.class_name", "properties.name", "relationships.parent"]
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=True)
        
        self.assertIn("_object_type", result)
        self.assertIn("_identity", result)
        self.assertIn("properties", result)
        self.assertIn("relationships", result)
        
        # Check specific field inclusion
        self.assertIn("class_name", result["_identity"])
        self.assertIn("name", result["properties"])
        self.assertIn("parent", result["relationships"])
        
        # Check specific field exclusion
        self.assertNotIn("value", result["properties"])
        self.assertNotIn("children", result["relationships"])


class TestStructuredCollectionSummaries(unittest.TestCase):
    """Test structured collection summary functionality."""
    
    def setUp(self):
        self.obj = MockIntrospectableObject()

    def test_list_collection_summary(self):
        """Test structured summary for list collections."""
        test_list = ["item1", "item2", "item3"]
        result = self.obj._format_property_value_for_to_dict(
            test_list, False, set(), 1, False, True  # expand_collections=False
        )
        
        self.assertIn("_collection_summary", result)
        summary = result["_collection_summary"]
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["item_type"], "str")
        self.assertEqual(summary["collection_type"], "list")

    def test_dict_collection_summary(self):
        """Test structured summary for dictionary collections."""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = self.obj._format_property_value_for_to_dict(
            test_dict, False, set(), 1, False, True  # expand_collections=False
        )
        
        self.assertIn("_collection_summary", result)
        summary = result["_collection_summary"]
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["item_type"], "str")
        self.assertEqual(summary["collection_type"], "dict")

    def test_empty_collection_summary(self):
        """Test structured summary for empty collections."""
        test_list = []
        result = self.obj._format_property_value_for_to_dict(
            test_list, False, set(), 1, False, True  # expand_collections=False
        )
        
        self.assertIn("_collection_summary", result)
        summary = result["_collection_summary"]
        self.assertEqual(summary["count"], 0)
        self.assertEqual(summary["item_type"], "object")  # Default for empty collections
        self.assertEqual(summary["collection_type"], "list")

    def test_mixed_type_collection_summary(self):
        """Test structured summary for collections with mixed types."""
        class TestClass:
            pass
        
        test_list = [TestClass(), "string", 42]
        result = self.obj._format_property_value_for_to_dict(
            test_list, False, set(), 1, False, True  # expand_collections=False
        )
        
        self.assertIn("_collection_summary", result)
        summary = result["_collection_summary"]
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["item_type"], "TestClass")  # Type of first item
        self.assertEqual(summary["collection_type"], "list")


class TestBackwardCompatibility(unittest.TestCase):
    """Test that FEP-019 maintains backward compatibility."""
    
    def setUp(self):
        self.obj = MockIntrospectableObject()

    def test_to_dict_without_fields_unchanged(self):
        """Test that to_dict() without fields parameter works as before."""
        result = self.obj.to_dict()
        
        # Should contain all standard sections
        self.assertIn("_object_type", result)
        self.assertIn("_identity", result)
        self.assertIn("properties", result)
        self.assertIn("relationships", result)
        self.assertIn("_llm_context", result)
        
        # Should contain all properties
        props = result["properties"]
        self.assertIn("name", props)
        self.assertIn("value", props)
        self.assertIn("nested_list", props)
        self.assertIn("nested_dict", props)

    def test_to_dict_with_existing_parameters(self):
        """Test that existing parameters still work correctly."""
        result = self.obj.to_dict(
            include_relationships=False,
            max_depth=2,
            include_private=False,
            expand_collections=True,
            format_for_llm=False
        )
        
        self.assertIn("_object_type", result)
        self.assertIn("properties", result)
        self.assertNotIn("relationships", result)
        self.assertNotIn("_llm_context", result)

    def test_expanded_collections_still_work(self):
        """Test that expanded collections still work as before."""
        result = self.obj.to_dict(expand_collections=True)
        
        # Lists should be expanded
        nested_list = result["properties"]["nested_list"]
        self.assertIsInstance(nested_list, list)
        self.assertEqual(len(nested_list), 3)
        
        # Dicts should be expanded
        nested_dict = result["properties"]["nested_dict"]
        self.assertIsInstance(nested_dict, dict)
        self.assertEqual(len(nested_dict), 2)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        self.obj = MockIntrospectableObject()

    def test_invalid_field_paths(self):
        """Test handling of invalid field paths."""
        # Non-existent top-level field
        fields = ["nonexistent_section"]
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=False)
        
        # Should only contain _object_type
        self.assertIn("_object_type", result)
        self.assertNotIn("nonexistent_section", result)

    def test_empty_field_list(self):
        """Test handling of empty field list."""
        fields = []
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=False)
        
        # Should only contain _object_type
        self.assertIn("_object_type", result)
        self.assertEqual(len(result), 1)

    def test_deeply_nested_field_paths(self):
        """Test handling of deeply nested field paths."""
        fields = ["properties.nested_dict.nonexistent.deep.path"]
        result = self.obj.to_dict(fields=fields, format_for_llm=False, include_relationships=False)
        
        # Should create the structure but may not have the deep values
        self.assertIn("_object_type", result)
        self.assertIn("properties", result)

    def test_fields_with_llm_context(self):
        """Test field selection with LLM context."""
        fields = ["_llm_context.description"]
        result = self.obj.to_dict(fields=fields, format_for_llm=True, include_relationships=False)
        
        self.assertIn("_object_type", result)
        self.assertIn("_llm_context", result)


if __name__ == "__main__":
    unittest.main()