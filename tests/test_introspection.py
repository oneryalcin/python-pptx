# tests/test_introspection.py

import unittest
from pptx.introspection import IntrospectionMixin
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches # For testing Length formatting

class MyObjectWithRGB(IntrospectionMixin):
    def __init__(self, rgb_color_val, length_val=None):
        self.rgb_color_attr = rgb_color_val
        self.length_attr = length_val
        self._private_rgb = RGBColor(0,0,0) # for testing private

    # Override _to_dict_properties to ensure these specific attrs are processed
    # and to control the exact set of properties for predictable testing.
    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        props = {
            "rgb_color_attr": self._format_property_value_for_to_dict(
                self.rgb_color_attr, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )
        }
        if self.length_attr is not None:
            props["length_attr"] = self._format_property_value_for_to_dict(
                self.length_attr, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )

        if include_private:
             props["_private_rgb"] = self._format_property_value_for_to_dict(
                self._private_rgb, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )
        return props

class DummyInspectable(IntrospectionMixin):
    def __init__(self):
        self.name = "Dummy"
        self.value = 123
        self._private_field = "secret"
        self.my_list = [1, RGBColor(10,20,30)]
        self.my_dict = {"key": "val", "color_key": RGBColor(40,50,60)}

    # For simpler testing, explicitly define what properties to show
    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        props = {
            "name": self._format_property_value_for_to_dict(
                self.name, include_private, _visited_ids, max_depth -1, expand_collections, format_for_llm
            ),
            "value": self._format_property_value_for_to_dict(
                self.value, include_private, _visited_ids, max_depth -1, expand_collections, format_for_llm
            ),
            "my_list": self._format_property_value_for_to_dict(
                self.my_list, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            ),
            "my_dict": self._format_property_value_for_to_dict(
                self.my_dict, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )
        }
        if include_private:
            props["_private_field"] = self._format_property_value_for_to_dict(
                self._private_field, include_private, _visited_ids, max_depth -1, expand_collections, format_for_llm
            )
        return props


class DepthTestA(IntrospectionMixin):
    def __init__(self, b_instance=None):
        self.b_prop = b_instance
        self.name = "A"

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {
            "name": self.name,
            "b_prop": self._format_property_value_for_to_dict(
                self.b_prop, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )
        }

class DepthTestB(IntrospectionMixin):
    def __init__(self, c_instance=None):
        self.c_prop = c_instance
        self.name = "B"

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {
            "name": self.name,
            "c_prop": self._format_property_value_for_to_dict(
                self.c_prop, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )
        }

class DepthTestC(IntrospectionMixin):
    def __init__(self):
        self.name = "C"

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {"name": self.name}


class CycleA(IntrospectionMixin):
    def __init__(self):
        self.name = "CycleA"
        self.b_ref = None

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {
            "name": self.name,
            "b_ref": self._format_property_value_for_to_dict(
                self.b_ref, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
            )
        }


class CycleB(IntrospectionMixin):
    def __init__(self):
        self.name = "CycleB"
        self.a_ref = None

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {
            "name": self.name,
            "a_ref": self._format_property_value_for_to_dict(
                self.a_ref, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
            )
        }


class TestIntrospectionMixin(unittest.TestCase):

    def test_enhanced_error_context(self):
        """Test that the enhanced error context provides meaningful debugging information."""
        # Create an object that will trigger errors during serialization
        class ErrorTriggeringObj(IntrospectionMixin):
            def __init__(self):
                self.working_prop = "fine"
                
            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                # Override to include a problematic property that will cause an error
                props = super()._to_dict_properties(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)
                
                # Simulate an error during formatting by creating a problematic value
                class ProblematicValue:
                    def __len__(self):
                        raise RuntimeError("Simulated error for testing")
                
                # Test error context creation directly
                try:
                    problematic = ProblematicValue()
                    len(problematic)  # This will raise an error
                except RuntimeError as e:
                    error_context = self._create_error_context("test_error", e, problematic)
                    props["error_test"] = error_context
                
                return props
        
        obj = ErrorTriggeringObj()
        result = obj.to_dict()
        
        # Verify the error context structure
        self.assertIn("error_test", result['properties'])
        error_info = result['properties']['error_test']
        
        self.assertIn("_error", error_info)
        self.assertIn("_object_type", error_info)
        self.assertEqual(error_info["_object_type"], "SerializationError_test_error")
        
        error_details = error_info["_error"]
        self.assertEqual(error_details["type"], "test_error")
        self.assertEqual(error_details["message"], "Simulated error for testing")
        self.assertEqual(error_details["exception_type"], "RuntimeError")
        self.assertIn("ProblematicValue", error_details["value_type"])

    def test_simplified_property_detection(self):
        """Test that the simplified property detection logic works correctly."""
        class PropertyTestObj(IntrospectionMixin):
            def __init__(self):
                self.public_attr = "public"
                self._private_attr = "private"
                self.__dunder_attr = "dunder"
            
            @property
            def test_property(self):
                return "property_value"
            
            def test_method(self):
                return "method_result"
            
            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                # Test the helper methods directly
                attrs_to_test = ['public_attr', '_private_attr', '__dunder_attr', 'test_property', 'test_method']
                helper_results = {}
                
                for attr in attrs_to_test:
                    if hasattr(self, attr):
                        helper_results[f"{attr}_should_include"] = self._should_include_attribute(attr, include_private)
                        helper_results[f"{attr}_is_property"] = self._is_property(attr)
                        helper_results[f"{attr}_is_introspection"] = self._is_introspection_method(attr)
                        if hasattr(self, attr):
                            attr_value = getattr(self, attr)
                            helper_results[f"{attr}_is_callable_method"] = self._is_callable_method(attr, attr_value)
                
                # Get normal properties too
                normal_props = super()._to_dict_properties(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)
                normal_props.update(helper_results)
                return normal_props
        
        obj = PropertyTestObj()
        
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
        rgb = RGBColor(0x12, 0x34, 0x56)
        obj = MyObjectWithRGB(rgb_color_val=rgb)
        d = obj.to_dict()
        expected_rgb_dict = {"_object_type": "RGBColor", "r": 0x12, "g": 0x34, "b": 0x56, "hex": "123456"}
        self.assertEqual(d['properties']['rgb_color_attr'], expected_rgb_dict)

    def test_length_formatting(self):
        length_emu = Emu(914400) # 1 inch
        obj_emu = MyObjectWithRGB(rgb_color_val=RGBColor(0,0,0), length_val=length_emu)
        d_emu = obj_emu.to_dict()
        expected_length_dict_emu = {
            "_object_type": "Emu", "emu": 914400, "inches": 1.0,
            "pt": 72.0, "cm": 2.54, "mm": 25.4
        }
        # Comparing floats needs assertAlmostEqual or careful checking
        self.assertEqual(d_emu['properties']['length_attr']['_object_type'], expected_length_dict_emu['_object_type'])
        self.assertEqual(d_emu['properties']['length_attr']['emu'], expected_length_dict_emu['emu'])
        self.assertAlmostEqual(d_emu['properties']['length_attr']['inches'], expected_length_dict_emu['inches'])
        self.assertAlmostEqual(d_emu['properties']['length_attr']['pt'], expected_length_dict_emu['pt'])
        self.assertAlmostEqual(d_emu['properties']['length_attr']['cm'], expected_length_dict_emu['cm'])
        self.assertAlmostEqual(d_emu['properties']['length_attr']['mm'], expected_length_dict_emu['mm'])

        length_inches = Inches(2)
        obj_inches = MyObjectWithRGB(rgb_color_val=RGBColor(0,0,0), length_val=length_inches)
        d_inches = obj_inches.to_dict()
        self.assertEqual(d_inches['properties']['length_attr']['_object_type'], "Inches")
        self.assertEqual(d_inches['properties']['length_attr']['emu'], 1828800)


    def test_mixin_basic_structure_and_private(self):
        dummy = DummyInspectable()
        d = dummy.to_dict(include_private=False)

        self.assertEqual(d['_object_type'], "DummyInspectable")
        self.assertEqual(d['_identity']['class_name'], "DummyInspectable")
        self.assertIn('memory_address', d['_identity'])

        self.assertIn("name", d['properties'])
        self.assertEqual(d['properties']['name'], "Dummy")
        self.assertIn("value", d['properties'])
        self.assertEqual(d['properties']['value'], 123)
        self.assertNotIn("_private_field", d['properties'])

        self.assertEqual(d['_llm_context'], {"description": "A DummyInspectable object."})
        self.assertEqual(d['relationships'], {})

        # Test include_private = True
        d_priv = dummy.to_dict(include_private=True)
        self.assertIn("_private_field", d_priv['properties'])
        self.assertEqual(d_priv['properties']['_private_field'], "secret")

    def test_max_depth(self):
        c_obj = DepthTestC()
        b_obj = DepthTestB(c_instance=c_obj)
        a_obj = DepthTestA(b_instance=b_obj)

        # Max depth 1: A is expanded, B is truncated
        d1 = a_obj.to_dict(max_depth=1)
        self.assertEqual(d1['_object_type'], "DepthTestA")
        self.assertIn("b_prop", d1['properties'])
        self.assertEqual(d1['properties']['b_prop'], {"_truncated": "Max depth reached for DepthTestB"})

        # Max depth 2: A and B expanded, C is truncated
        d2 = a_obj.to_dict(max_depth=2)
        self.assertEqual(d2['properties']['b_prop']['_object_type'], "DepthTestB")
        self.assertIn("c_prop", d2['properties']['b_prop']['properties'])
        self.assertEqual(d2['properties']['b_prop']['properties']['c_prop'], {"_truncated": "Max depth reached for DepthTestC"})

        # Max depth 3: A, B, C all expanded
        d3 = a_obj.to_dict(max_depth=3)
        self.assertEqual(d3['properties']['b_prop']['properties']['c_prop']['_object_type'], "DepthTestC")
        self.assertEqual(d3['properties']['b_prop']['properties']['c_prop']['properties']['name'], "C")

        # Max depth 0 (from _format_property_value_for_to_dict for a property)
        # This means the to_dict on 'a_obj' has max_depth=1, so its properties are processed with max_depth=0
        d0_internal = a_obj.to_dict(max_depth=1) # b_prop will be called with max_depth=0 by _format_property_value
        self.assertEqual(d0_internal['properties']['b_prop'], {"_truncated": "Max depth reached for DepthTestB"})


    def test_cycle_detection(self):
        a = CycleA()
        b = CycleB()
        a.b_ref = b
        b.a_ref = a

        da = a.to_dict()
        self.assertEqual(da['_object_type'], "CycleA")
        self.assertIn("b_ref", da['properties'])
        b_ref_dict = da['properties']['b_ref']
        self.assertEqual(b_ref_dict['_object_type'], "CycleB")
        self.assertIn("a_ref", b_ref_dict['properties'])
        a_ref_in_b_ref_dict = b_ref_dict['properties']['a_ref']
        self.assertIn("_reference", a_ref_in_b_ref_dict)
        self.assertTrue(a_ref_in_b_ref_dict["_reference"].startswith("Circular reference to CycleA at"))

    def test_list_and_dict_expansion(self):
        dummy = DummyInspectable()

        # Test expansion True (default)
        d_expanded = dummy.to_dict(max_depth=2) # max_depth=2 to allow expansion of items in list/dict
        self.assertIsInstance(d_expanded['properties']['my_list'], list)
        self.assertEqual(len(d_expanded['properties']['my_list']), 2)
        self.assertEqual(d_expanded['properties']['my_list'][0], 1)
        self.assertEqual(d_expanded['properties']['my_list'][1]['_object_type'], "RGBColor")
        self.assertEqual(d_expanded['properties']['my_list'][1]['hex'], "0A141E")

        self.assertIsInstance(d_expanded['properties']['my_dict'], dict)
        self.assertEqual(d_expanded['properties']['my_dict']['key'], "val")
        self.assertEqual(d_expanded['properties']['my_dict']['color_key']['_object_type'], "RGBColor")
        self.assertEqual(d_expanded['properties']['my_dict']['color_key']['hex'], "28323C")

        # Test expansion False
        d_not_expanded = dummy.to_dict(expand_collections=False, max_depth=2)
        self.assertEqual(d_not_expanded['properties']['my_list'], "Collection of 2 items (not expanded due to max_depth or expand_collections=False)")
        self.assertEqual(d_not_expanded['properties']['my_dict'], "Dictionary with 2 keys (not expanded due to max_depth or expand_collections=False)")

        # Test expansion True but max_depth stops expansion within collections
        # dummy.my_list contains an RGBColor. If max_depth for the list's items is 0, RGBColor.to_dict won't be called.
        # to_dict(max_depth=1) means _format_property_value_for_to_dict for my_list is called with max_depth=0
        d_expanded_depth_limited = dummy.to_dict(max_depth=1)
        # The list itself is processed, but items within that require further to_dict calls (like RGBColor) will be truncated.
        # RGBColor is handled directly by _format_property_value_for_to_dict, not by calling its own to_dict,
        # so it will still be expanded. If it were a generic IntrospectionMixin object, it would be truncated.
        # Let's add a generic inspectable object to the list for a better test here.

        complex_list_item = DepthTestC()
        dummy.my_list_complex = [complex_list_item]

        # Override _to_dict_properties for DummyInspectable to include my_list_complex for this test
        original_to_dict_properties = DummyInspectable._to_dict_properties
        self.addCleanup(setattr, DummyInspectable, '_to_dict_properties', original_to_dict_properties) # Ensures cleanup


        def new_to_dict_properties(self_dummy, include_private, _visited_ids, max_depth_param, expand_collections, format_for_llm):
            # Call the original method first (from the class, not the instance)
            props = original_to_dict_properties(self_dummy, include_private, _visited_ids, max_depth_param, expand_collections, format_for_llm)
            # Add the new property, correctly decrementing max_depth for its formatting call
            if hasattr(self_dummy, 'my_list_complex'): # Check if attribute exists
                 props["my_list_complex"] = self_dummy._format_property_value_for_to_dict(
                    self_dummy.my_list_complex, include_private, _visited_ids, max_depth_param - 1, expand_collections, format_for_llm
                )
            return props
        DummyInspectable._to_dict_properties = new_to_dict_properties

        # dummy.to_dict(max_depth=1) -> new_to_dict_properties(max_depth_param=1)
        # -> _format_property_value_for_to_dict for my_list_complex gets max_depth = 1 - 1 = 0.
        # -> For list with max_depth=0, it should return "Collection ... (not expanded)"
        d_expanded_depth_limited_complex = dummy.to_dict(max_depth=1)

        self.assertEqual(d_expanded_depth_limited_complex['properties']['my_list_complex'],
                         "Collection of 1 items (not expanded due to max_depth or expand_collections=False)")

        # Clean up the attribute we added to the instance for this test
        delattr(dummy, "my_list_complex")


if __name__ == '__main__':
    unittest.main()
