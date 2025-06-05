# tests/introspection/test_core_mixin.py

"""
Core IntrospectionMixin Tests

Tests for the fundamental IntrospectionMixin functionality including:
- Basic to_dict structure and behavior
- Error handling and context creation
- Property detection and filtering logic
- Depth limiting and truncation
- Circular reference detection
- Collection expansion and handling
- Basic type formatting (RGBColor, Length)
"""

import unittest
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches

from .mock_helpers import (
    MyObjectWithRGB, DummyInspectable, DepthTestA, DepthTestB, DepthTestC,
    CycleA, CycleB, create_error_triggering_obj, create_property_test_obj,
    assert_basic_to_dict_structure, assert_length_dict_structure, assert_error_context_structure
)


class TestIntrospectionMixinCore(unittest.TestCase):
    """Test core IntrospectionMixin functionality and basic type support."""

    def test_enhanced_error_context(self):
        """Test that the enhanced error context provides meaningful debugging information."""
        obj = create_error_triggering_obj()
        result = obj.to_dict()

        # Verify the error context structure
        self.assertIn("error_test", result['properties'])
        error_info = result['properties']['error_test']

        assert_error_context_structure(self, error_info, "test_error")
        
        error_details = error_info["_error"]
        self.assertEqual(error_details["message"], "Simulated error for testing")
        self.assertEqual(error_details["exception_type"], "RuntimeError")
        self.assertIn("ProblematicValue", error_details["value_type"])

    def test_simplified_property_detection(self):
        """Test that the simplified property detection logic works correctly."""
        obj = create_property_test_obj()

        # Test without private attributes
        result = obj.to_dict(include_private=False)
        props = result['properties']

        # Should include public attr and property
        self.assertTrue(props.get('public_attr_should_include'))
        self.assertTrue(props.get('test_property_should_include'))

        # Should not include private attr (unless it's a property)
        self.assertFalse(props.get('_private_attr_should_include'))

        # Should not include dunder
        self.assertFalse(props.get('__dunder_attr_should_include'))

        # Property detection should work
        self.assertTrue(props.get('test_property_is_property'))
        self.assertFalse(props.get('public_attr_is_property'))

        # Method detection should work
        self.assertTrue(props.get('test_method_is_callable_method'))
        self.assertFalse(props.get('test_property_is_callable_method'))

    def test_rgb_color_formatting(self):
        """Test that RGBColor objects are properly serialized."""
        rgb = RGBColor(0x12, 0x34, 0x56)
        obj = MyObjectWithRGB(rgb_color_val=rgb)
        result = obj.to_dict()
        
        expected_rgb_dict = {"_object_type": "RGBColor", "r": 0x12, "g": 0x34, "b": 0x56, "hex": "123456"}
        self.assertEqual(result['properties']['rgb_color_attr'], expected_rgb_dict)

    def test_length_formatting(self):
        """Test that Length objects (Emu, Inches, etc.) are properly serialized."""
        # Test Emu
        length_emu = Emu(914400)  # 1 inch
        obj_emu = MyObjectWithRGB(rgb_color_val=RGBColor(0, 0, 0), length_val=length_emu)
        result_emu = obj_emu.to_dict()
        
        length_dict = result_emu['properties']['length_attr']
        assert_length_dict_structure(self, length_dict, "Emu", 914400)
        
        # Verify precise conversions (comparing floats with tolerance)
        self.assertAlmostEqual(length_dict['inches'], 1.0, places=5)
        self.assertAlmostEqual(length_dict['pt'], 72.0, places=5)
        self.assertAlmostEqual(length_dict['cm'], 2.54, places=5)
        self.assertAlmostEqual(length_dict['mm'], 25.4, places=5)

        # Test Inches
        length_inches = Inches(2)
        obj_inches = MyObjectWithRGB(rgb_color_val=RGBColor(0, 0, 0), length_val=length_inches)
        result_inches = obj_inches.to_dict()
        
        inches_dict = result_inches['properties']['length_attr']
        self.assertEqual(inches_dict['_object_type'], "Inches")
        self.assertEqual(inches_dict['emu'], 1828800)

    def test_mixin_basic_structure_and_private(self):
        """Test basic to_dict structure and private field handling."""
        dummy = DummyInspectable()
        result = dummy.to_dict(include_private=False)

        assert_basic_to_dict_structure(self, result, "DummyInspectable")
        
        # Check identity
        identity = result['_identity']
        self.assertEqual(identity['class_name'], "DummyInspectable")
        self.assertIn('memory_address', identity)

        # Check properties
        props = result['properties']
        self.assertIn("name", props)
        self.assertEqual(props['name'], "Dummy")
        self.assertIn("value", props)
        self.assertEqual(props['value'], 123)
        self.assertNotIn("_private_field", props)

        # Check LLM context and relationships
        self.assertEqual(result['_llm_context'], {"description": "A DummyInspectable object."})
        self.assertEqual(result['relationships'], {})

        # Test include_private = True
        result_priv = dummy.to_dict(include_private=True)
        self.assertIn("_private_field", result_priv['properties'])
        self.assertEqual(result_priv['properties']['_private_field'], "secret")

    def test_max_depth(self):
        """Test that max_depth parameter properly limits object traversal depth."""
        c_obj = DepthTestC()
        b_obj = DepthTestB(c_instance=c_obj)
        a_obj = DepthTestA(b_instance=b_obj)

        # Max depth 1: A is expanded, B is truncated
        result_depth1 = a_obj.to_dict(max_depth=1)
        self.assertEqual(result_depth1['_object_type'], "DepthTestA")
        self.assertIn("b_prop", result_depth1['properties'])
        self.assertEqual(result_depth1['properties']['b_prop'], {"_truncated": "Max depth reached for DepthTestB"})

        # Max depth 2: A and B expanded, C is truncated
        result_depth2 = a_obj.to_dict(max_depth=2)
        self.assertEqual(result_depth2['properties']['b_prop']['_object_type'], "DepthTestB")
        self.assertIn("c_prop", result_depth2['properties']['b_prop']['properties'])
        self.assertEqual(result_depth2['properties']['b_prop']['properties']['c_prop'], {"_truncated": "Max depth reached for DepthTestC"})

        # Max depth 3: A, B, C all expanded
        result_depth3 = a_obj.to_dict(max_depth=3)
        self.assertEqual(result_depth3['properties']['b_prop']['properties']['c_prop']['_object_type'], "DepthTestC")
        self.assertEqual(result_depth3['properties']['b_prop']['properties']['c_prop']['properties']['name'], "C")

    def test_cycle_detection(self):
        """Test that circular references are properly detected and handled."""
        a = CycleA()
        b = CycleB()
        a.b_ref = b
        b.a_ref = a

        result = a.to_dict()
        self.assertEqual(result['_object_type'], "CycleA")
        self.assertIn("b_ref", result['properties'])
        
        b_ref_dict = result['properties']['b_ref']
        self.assertEqual(b_ref_dict['_object_type'], "CycleB")
        self.assertIn("a_ref", b_ref_dict['properties'])
        
        a_ref_in_b_ref_dict = b_ref_dict['properties']['a_ref']
        self.assertIn("_reference", a_ref_in_b_ref_dict)
        self.assertTrue(a_ref_in_b_ref_dict["_reference"].startswith("Circular reference to CycleA at"))

    def test_list_and_dict_expansion(self):
        """Test collection expansion and handling with various depth and expansion settings."""
        dummy = DummyInspectable()

        # Test expansion True (default)
        result_expanded = dummy.to_dict(max_depth=2)  # max_depth=2 to allow expansion of items in list/dict
        self.assertIsInstance(result_expanded['properties']['my_list'], list)
        self.assertEqual(len(result_expanded['properties']['my_list']), 2)
        self.assertEqual(result_expanded['properties']['my_list'][0], 1)
        self.assertEqual(result_expanded['properties']['my_list'][1]['_object_type'], "RGBColor")
        self.assertEqual(result_expanded['properties']['my_list'][1]['hex'], "0A141E")

        self.assertIsInstance(result_expanded['properties']['my_dict'], dict)
        self.assertEqual(result_expanded['properties']['my_dict']['key'], "val")
        self.assertEqual(result_expanded['properties']['my_dict']['color_key']['_object_type'], "RGBColor")
        self.assertEqual(result_expanded['properties']['my_dict']['color_key']['hex'], "28323C")

        # Test expansion False - FEP-019: structured collection summaries
        result_not_expanded = dummy.to_dict(expand_collections=False, max_depth=2)
        
        # Check list collection summary structure
        list_summary = result_not_expanded['properties']['my_list']
        self.assertIn('_collection_summary', list_summary)
        self.assertEqual(list_summary['_collection_summary']['count'], 2)
        self.assertEqual(list_summary['_collection_summary']['collection_type'], 'list')
        self.assertIn('item_type', list_summary['_collection_summary'])  # Type may vary
        
        # Check dict collection summary structure  
        dict_summary = result_not_expanded['properties']['my_dict']
        self.assertIn('_collection_summary', dict_summary)
        self.assertEqual(dict_summary['_collection_summary']['count'], 2)
        self.assertEqual(dict_summary['_collection_summary']['collection_type'], 'dict')
        self.assertIn('item_type', dict_summary['_collection_summary'])  # Type may vary

        # Test depth-limited expansion with complex objects
        from .mock_helpers import DepthTestC
        complex_list_item = DepthTestC()
        dummy.my_list_complex = [complex_list_item]

        # Override _to_dict_properties for DummyInspectable to include my_list_complex for this test
        original_to_dict_properties = DummyInspectable._to_dict_properties
        self.addCleanup(setattr, DummyInspectable, '_to_dict_properties', original_to_dict_properties)

        def new_to_dict_properties(self_dummy, include_private, _visited_ids, max_depth_param, expand_collections, format_for_llm):
            props = original_to_dict_properties(self_dummy, include_private, _visited_ids, max_depth_param, expand_collections, format_for_llm)
            if hasattr(self_dummy, 'my_list_complex'):
                props["my_list_complex"] = self_dummy._format_property_value_for_to_dict(
                    self_dummy.my_list_complex, include_private, _visited_ids, max_depth_param - 1, expand_collections, format_for_llm
                )
            return props
        DummyInspectable._to_dict_properties = new_to_dict_properties

        # Test that depth limitation stops expansion of complex objects in collections
        result_depth_limited_complex = dummy.to_dict(max_depth=1)
        
        # FEP-019: Check structured collection summary for depth-limited expansion
        complex_list_summary = result_depth_limited_complex['properties']['my_list_complex']
        self.assertIn('_collection_summary', complex_list_summary)
        self.assertEqual(complex_list_summary['_collection_summary']['count'], 1)
        self.assertEqual(complex_list_summary['_collection_summary']['collection_type'], 'list')

        # Clean up the attribute we added to the instance for this test
        delattr(dummy, "my_list_complex")


if __name__ == '__main__':
    unittest.main()