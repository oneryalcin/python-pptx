# tests/test_introspection.py

import unittest
from pptx.introspection import IntrospectionMixin
from pptx.dml.color import RGBColor, ColorFormat
from pptx.util import Emu, Inches # For testing Length formatting
from pptx.enum.shapes import MSO_SHAPE_TYPE, MSO_AUTO_SHAPE_TYPE, PROG_ID, PP_PLACEHOLDER  # For testing enum formatting
from pptx.enum.dml import MSO_COLOR_TYPE, MSO_LINE_DASH_STYLE, MSO_THEME_COLOR, MSO_FILL  # For testing enum formatting
from pptx.dml.fill import FillFormat, _GradientStop  # For testing FillFormat introspection
from pptx.shapes.base import BaseShape, _PlaceholderFormat  # For testing BaseShape introspection

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

    def test_base_enum_formatting(self):
        """Test that BaseEnum members are properly serialized to dictionaries."""
        # Create a test object with BaseEnum property
        class EnumTestObj(IntrospectionMixin):
            def __init__(self, enum_val):
                self.shape_type = enum_val

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "shape_type": self._format_property_value_for_to_dict(
                        self.shape_type, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                }

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
        # Create a test object with BaseXmlEnum property
        class XmlEnumTestObj(IntrospectionMixin):
            def __init__(self, enum_val):
                self.auto_shape_type = enum_val

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "auto_shape_type": self._format_property_value_for_to_dict(
                        self.auto_shape_type, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                }

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
        """Test enum members that have None as xml_value."""
        # Create a test object with enum that has None xml_value
        class NoneXmlEnumTestObj(IntrospectionMixin):
            def __init__(self, enum_val):
                self.line_style = enum_val

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "line_style": self._format_property_value_for_to_dict(
                        self.line_style, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                }

        # Test enum member with None xml_value (DASH_STYLE_MIXED has empty xml_value "")
        obj = NoneXmlEnumTestObj(MSO_LINE_DASH_STYLE.DASH_STYLE_MIXED)
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
        class EnumCollectionTestObj(IntrospectionMixin):
            def __init__(self):
                self.shape_types = [MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.TABLE]
                self.mixed_collection = [MSO_COLOR_TYPE.RGB, "string", 42]

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "shape_types": self._format_property_value_for_to_dict(
                        self.shape_types, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    ),
                    "mixed_collection": self._format_property_value_for_to_dict(
                        self.mixed_collection, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                }

        obj = EnumCollectionTestObj()
        result = obj.to_dict(max_depth=3)  # Ensure we have enough depth for collection expansion
        
        # Check that enum members in collections are properly serialized
        shape_types = result['properties']['shape_types']
        self.assertIsInstance(shape_types, list)
        self.assertEqual(len(shape_types), 2)
        
        # First enum in collection
        self.assertEqual(shape_types[0]['_object_type'], "MSO_SHAPE_TYPE")
        self.assertEqual(shape_types[0]['name'], "PICTURE")
        self.assertEqual(shape_types[0]['value'], 13)
        
        # Second enum in collection
        self.assertEqual(shape_types[1]['_object_type'], "MSO_SHAPE_TYPE")
        self.assertEqual(shape_types[1]['name'], "TABLE")
        self.assertEqual(shape_types[1]['value'], 19)
        
        # Mixed collection should handle enum, string, and int properly
        mixed = result['properties']['mixed_collection']
        self.assertIsInstance(mixed, list)
        self.assertEqual(len(mixed), 3)
        
        # First item is enum
        self.assertEqual(mixed[0]['_object_type'], "MSO_COLOR_TYPE")
        self.assertEqual(mixed[0]['name'], "RGB")
        # Second item is string
        self.assertEqual(mixed[1], "string")
        # Third item is int
        self.assertEqual(mixed[2], 42)

    def test_prog_id_enum_handling(self):
        """Test that PROG_ID enum (which doesn't inherit from BaseEnum/BaseXmlEnum) falls back to repr."""
        class ProgIdTestObj(IntrospectionMixin):
            def __init__(self, prog_id):
                self.prog_id = prog_id

            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {
                    "prog_id": self._format_property_value_for_to_dict(
                        self.prog_id, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                }

        # PROG_ID doesn't inherit from BaseEnum or BaseXmlEnum, so it should fall back to repr
        obj = ProgIdTestObj(PROG_ID.XLSX)
        result = obj.to_dict()
        
        # Should fall back to repr() since PROG_ID is not BaseEnum/BaseXmlEnum
        self.assertIsInstance(result['properties']['prog_id'], str)
        self.assertIn('PROG_ID.XLSX', result['properties']['prog_id'])
        # Should NOT be a dict with _object_type
        self.assertNotIsInstance(result['properties']['prog_id'], dict)

    def test_base_shape_to_dict_basic_functionality(self):
        """Test that BaseShape.to_dict() provides expected basic structure."""
        # Create a mock shape element and parent for testing
        class MockShapeElement:
            def __init__(self):
                self.shape_id = 42
                self.shape_name = "Test Shape 1"
                self.has_ph_elm = False
                self.x = Emu(914400)  # 1 inch
                self.y = Emu(914400)  # 1 inch
                self.cx = Emu(1828800)  # 2 inches
                self.cy = Emu(914400)  # 1 inch
                self.rot = 0.0
                self.hidden = False

        class MockParent:
            def __repr__(self):
                return "<MockSlideShapes object at 0x123>"

        # Create BaseShape instance
        shape_elm = MockShapeElement()
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        # Test basic to_dict functionality
        result = shape.to_dict(include_relationships=False, max_depth=1)

        # Check basic structure
        self.assertEqual(result['_object_type'], 'BaseShape')
        self.assertIn('_identity', result)
        self.assertIn('properties', result)
        self.assertIn('_llm_context', result)

        # Check identity information
        identity = result['_identity']
        self.assertEqual(identity['shape_id'], 42)
        self.assertEqual(identity['name'], "Test Shape 1")
        self.assertFalse(identity['is_placeholder'])
        # BaseShape.shape_type raises NotImplementedError, so it should be None
        self.assertNotIn('shape_type', identity)

        # Check geometry properties
        props = result['properties']
        self.assertIn('left', props)
        self.assertIn('top', props)
        self.assertIn('width', props)
        self.assertIn('height', props)
        self.assertIn('rotation', props)

        # Verify Length objects are properly formatted
        self.assertEqual(props['left']['_object_type'], 'Emu')
        self.assertEqual(props['left']['emu'], 914400)
        self.assertAlmostEqual(props['left']['inches'], 1.0)

        self.assertEqual(props['rotation'], 0.0)

    def test_base_shape_to_dict_with_relationships(self):
        """Test BaseShape.to_dict() with relationships included."""
        # Create mock objects
        class MockShapeElement:
            def __init__(self):
                self.shape_id = 123
                self.shape_name = "Relationship Test"
                self.has_ph_elm = False
                self.x = Emu(0)
                self.y = Emu(0)
                self.cx = Emu(914400)
                self.cy = Emu(914400)
                self.rot = 45.0
                self.hidden = False

        class MockParent:
            def __repr__(self):
                return "<MockSlideShapes with 5 shapes>"

        class MockPart:
            def __repr__(self):
                return "<MockSlidePart '/ppt/slides/slide1.xml'>"

        # Create shape with mock part
        shape_elm = MockShapeElement()
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        # Mock the part property
        original_part = BaseShape.part
        BaseShape.part = property(lambda self: MockPart())

        try:
            result = shape.to_dict(include_relationships=True, max_depth=1)

            # Check relationships
            self.assertIn('relationships', result)
            rels = result['relationships']

            # Parent collection should fallback to repr since MockParent doesn't have to_dict
            self.assertIn('parent_collection', rels)
            self.assertIsInstance(rels['parent_collection'], str)
            self.assertIn('MockSlideShapes', rels['parent_collection'])

            # Part should fallback to repr since MockPart doesn't have to_dict
            self.assertIn('part', rels)
            self.assertIsInstance(rels['part'], str)
            self.assertIn('MockSlidePart', rels['part'])

        finally:
            # Restore original part property
            BaseShape.part = original_part

    def test_base_shape_placeholder_handling(self):
        """Test BaseShape.to_dict() with placeholder shapes."""
        # Create mock placeholder shape
        class MockPlaceholderElement:
            def __init__(self):
                self.shape_id = 200
                self.shape_name = "Title Placeholder"
                self.has_ph_elm = True
                self.x = Emu(914400)
                self.y = Emu(914400)
                self.cx = Emu(7315200)  # 8 inches
                self.cy = Emu(1371600)  # 1.5 inches
                self.rot = 0.0
                self.hidden = False

        class MockPlaceholderFormat:
            def __init__(self):
                self.idx = 0
                self.type = PP_PLACEHOLDER.TITLE

        class MockParent:
            def __repr__(self):
                return "<MockSlideShapes>"

        # Create placeholder shape
        shape_elm = MockPlaceholderElement()
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        # Mock the placeholder_format property
        original_placeholder_format = BaseShape.placeholder_format
        BaseShape.placeholder_format = property(lambda self: MockPlaceholderFormat())

        try:
            result = shape.to_dict(include_relationships=False, max_depth=2)

            # Check placeholder identification
            identity = result['_identity']
            self.assertTrue(identity['is_placeholder'])
            self.assertIn('placeholder_details', identity)

            placeholder_details = identity['placeholder_details']
            self.assertEqual(placeholder_details['idx'], 0)
            
            # Check that placeholder type is properly formatted as enum
            ph_type = placeholder_details['type']
            self.assertEqual(ph_type['_object_type'], 'PP_PLACEHOLDER_TYPE')
            self.assertEqual(ph_type['name'], 'TITLE')
            self.assertEqual(ph_type['value'], 1)

            # Check LLM context mentions placeholder
            context = result['_llm_context']
            self.assertIn('placeholder', context['description'])

        finally:
            # Restore original placeholder_format property
            BaseShape.placeholder_format = original_placeholder_format

    def test_base_shape_error_handling(self):
        """Test BaseShape.to_dict() error handling for edge cases."""
        # Test shape that raises errors accessing placeholder_format
        class MockErrorShapeElement:
            def __init__(self):
                self.shape_id = 999
                self.shape_name = "Error Test Shape"
                self.has_ph_elm = True  # Says it's a placeholder
                self.x = Emu(0)
                self.y = Emu(0)
                self.cx = Emu(914400)
                self.cy = Emu(914400)
                self.rot = 0.0
                self.hidden = False

        class MockParent:
            def __repr__(self):
                return "<MockParent>"

        shape_elm = MockErrorShapeElement()
        parent = MockParent()
        shape = BaseShape(shape_elm, parent)

        # Mock placeholder_format to raise ValueError
        def failing_placeholder_format(self):
            raise ValueError("Failed to access placeholder format")

        original_placeholder_format = BaseShape.placeholder_format
        BaseShape.placeholder_format = property(failing_placeholder_format)

        try:
            result = shape.to_dict(include_relationships=False, max_depth=1)

            # Should still work but with error info in placeholder_details
            identity = result['_identity']
            self.assertTrue(identity['is_placeholder'])
            self.assertIn('placeholder_details', identity)

            placeholder_details = identity['placeholder_details']
            self.assertIn('error', placeholder_details)
            self.assertIn('Failed to access placeholder format', placeholder_details['error'])

        finally:
            # Restore original placeholder_format property
            BaseShape.placeholder_format = original_placeholder_format

    def test_base_shape_llm_context_generation(self):
        """Test BaseShape._to_dict_llm_context() generates useful descriptions."""
        # Create mock shape
        class MockShapeElement:
            def __init__(self):
                self.shape_id = 333
                self.shape_name = "LLM Test Shape"
                self.has_ph_elm = False
                self.x = Emu(914400)
                self.y = Emu(914400) 
                self.cx = Emu(914400)
                self.cy = Emu(914400)
                self.rot = 15.0
                self.hidden = False

        class MockParent:
            pass

        shape = BaseShape(MockShapeElement(), MockParent())
        result = shape.to_dict(include_relationships=False, max_depth=1)

        # Check LLM context
        context = result['_llm_context']
        self.assertIn('description', context)
        self.assertIn('common_operations', context)

        # Description should mention the shape name and ID
        desc = context['description']
        self.assertIn('LLM Test Shape', desc)
        self.assertIn('333', desc)

        # Should include common operations
        operations = context['common_operations']
        self.assertIn('access geometry (left, top, width, height, rotation)', operations)
        self.assertIn('modify position and size', operations)

    def test_base_shape_safe_property_access(self):
        """Test BaseShape helper methods for safe property access."""
        # Create basic shape
        class MockShapeElement:
            def __init__(self):
                self.shape_id = 444
                self.shape_name = "Safe Access Test"
                self.has_ph_elm = False
                self.x = Emu(0)
                self.y = Emu(0)
                self.cx = Emu(914400)
                self.cy = Emu(914400)
                self.rot = 0.0
                self.hidden = False

        shape = BaseShape(MockShapeElement(), None)

        # Test _get_shape_type_safely
        shape_type = shape._get_shape_type_safely()
        self.assertIsNone(shape_type)  # BaseShape raises NotImplementedError

        # Test _get_placeholder_info_safely for non-placeholder
        placeholder_info = shape._get_placeholder_info_safely(
            include_private=False, _visited_ids=set(), max_depth=2, expand_collections=True, format_for_llm=True
        )
        self.assertIsNone(placeholder_info)

    def test_colorformat_rgb_introspection(self):
        """Test that ColorFormat with RGB color is properly serialized."""
        # Create a test ColorFormat with RGB color
        class MockColorFormatRGB(ColorFormat):
            def __init__(self, rgb_color):
                # Initialize with mock parent and color objects
                super().__init__(None, None)  # Mock parent and color
                self._color_type = MSO_COLOR_TYPE.RGB
                self._rgb_color = rgb_color
                self._brightness_val = 0.0
                
            @property
            def type(self):
                return self._color_type
                
            @property
            def rgb(self):
                if self._color_type == MSO_COLOR_TYPE.RGB:
                    return self._rgb_color
                raise AttributeError("no .rgb property on color type")
                
            @property
            def theme_color(self):
                if self._color_type == MSO_COLOR_TYPE.SCHEME:
                    return self._theme_color
                raise AttributeError("no .theme_color property on color type")
                
            @property
            def brightness(self):
                return self._brightness_val
        
        rgb_color = RGBColor(0x12, 0x34, 0x56)
        color_format = MockColorFormatRGB(rgb_color)
        result = color_format.to_dict()
        
        # Check basic structure
        self.assertEqual(result['_object_type'], 'MockColorFormatRGB')
        self.assertIn('_identity', result)
        self.assertIn('properties', result)
        self.assertIn('_llm_context', result)
        
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
        # Create a test ColorFormat with theme color
        class MockColorFormatTheme(ColorFormat):
            def __init__(self, theme_color, brightness_val=0.0):
                super().__init__(None, None)  # Mock parent and color
                self._color_type = MSO_COLOR_TYPE.SCHEME
                self._theme_color = theme_color
                self._brightness_val = brightness_val
                
            @property
            def type(self):
                return self._color_type
                
            @property
            def rgb(self):
                if self._color_type == MSO_COLOR_TYPE.RGB:
                    return self._rgb_color
                raise AttributeError("no .rgb property on color type")
                
            @property
            def theme_color(self):
                if self._color_type == MSO_COLOR_TYPE.SCHEME:
                    return self._theme_color
                raise AttributeError("no .theme_color property on color type")
                
            @property
            def brightness(self):
                return self._brightness_val
        
        theme_color = MSO_THEME_COLOR.ACCENT_1
        color_format = MockColorFormatTheme(theme_color, -0.25)  # 25% darker
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

    def test_fillformat_solid_introspection(self):
        """Test that FillFormat with solid fill is properly serialized."""
        # Create a test FillFormat with solid fill
        class MockFillFormatSolid(FillFormat):
            def __init__(self, fore_color):
                # Skip parent initialization for testing
                self._fill_type = MSO_FILL.SOLID
                self._fore_color = fore_color
                
            @property
            def type(self):
                return self._fill_type
                
            @property
            def fore_color(self):
                return self._fore_color
                
            @property
            def back_color(self):
                raise TypeError("fill type _SolidFill has no background color")
                
            @property
            def pattern(self):
                raise TypeError("fill type _SolidFill has no pattern")
                
            @property
            def gradient_stops(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def gradient_angle(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def rId(self):
                raise NotImplementedError(".rId property must be implemented on _SolidFill")
        
        # Create mock color format
        class MockColorFormat(IntrospectionMixin):
            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {"type": {"name": "RGB"}, "rgb": {"hex": "FF0000"}}
            
            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "Solid RGB color: #FF0000"}
        
        fill_format = MockFillFormatSolid(MockColorFormat())
        result = fill_format.to_dict()
        
        # Check basic structure
        self.assertEqual(result['_object_type'], 'MockFillFormatSolid')
        self.assertIn('_identity', result)
        self.assertIn('properties', result)
        self.assertIn('_llm_context', result)
        
        # Check identity
        identity = result['_identity']
        self.assertEqual(identity['description'], 'Represents the fill formatting of an object.')
        
        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'SOLID')
        self.assertIsNotNone(props['fore_color'])
        self.assertEqual(props['fore_color']['_object_type'], 'MockColorFormat')
        
        # Other properties should be None for solid fill
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])
        
        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Solid fill', context['summary'])

    def test_fillformat_gradient_introspection(self):
        """Test that FillFormat with gradient fill is properly serialized."""
        # Create a test FillFormat with gradient fill
        class MockFillFormatGradient(FillFormat):
            def __init__(self, gradient_stops, gradient_angle=45.0):
                self._fill_type = MSO_FILL.GRADIENT
                self._gradient_stops = gradient_stops
                self._gradient_angle = gradient_angle
                
            @property
            def type(self):
                return self._fill_type
                
            @property
            def gradient_stops(self):
                return self._gradient_stops
                
            @property
            def gradient_angle(self):
                return self._gradient_angle
                
            @property
            def fore_color(self):
                raise TypeError("fill type _GradFill has no foreground color")
                
            @property
            def back_color(self):
                raise TypeError("fill type _GradFill has no background color")
                
            @property
            def pattern(self):
                raise TypeError("fill type _GradFill has no pattern")
                
            @property
            def rId(self):
                raise NotImplementedError(".rId property must be implemented on _GradFill")
        
        # Create mock gradient stops
        class MockGradientStop:
            def __init__(self, position, color_summary):
                self.position = position
                self.color_summary = color_summary
                
            def to_dict(self, **kwargs):
                return {
                    "_object_type": "_GradientStop",
                    "properties": {"position": self.position, "color": {"hex": "123456"}},
                    "_llm_context": {"summary": f"Gradient stop at {self.position*100:.0f}% with {self.color_summary}"}
                }
        
        class MockGradientStops:
            def __init__(self, stops):
                self.stops = stops
                
            def __len__(self):
                return len(self.stops)
                
            def __iter__(self):
                return iter(self.stops)
        
        stops = MockGradientStops([
            MockGradientStop(0.0, "red color"),
            MockGradientStop(1.0, "blue color")
        ])
        
        fill_format = MockFillFormatGradient(stops, 90.0)
        result = fill_format.to_dict(max_depth=3)  # Ensure enough depth for stops expansion
        
        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'GRADIENT')
        self.assertEqual(props['gradient_angle'], 90.0)
        self.assertIsInstance(props['gradient_stops'], list)
        self.assertEqual(len(props['gradient_stops']), 2)
        
        # Check first gradient stop
        stop1 = props['gradient_stops'][0]
        self.assertEqual(stop1['_object_type'], '_GradientStop')
        self.assertEqual(stop1['properties']['position'], 0.0)
        
        # Other properties should be None for gradient fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['image_rId'])
        
        # Check LLM context
        context = result['_llm_context']
        self.assertIn('2-stop gradient', context['summary'])
        self.assertIn('90 degrees', context['summary'])

    def test_fillformat_pattern_introspection(self):
        """Test that FillFormat with pattern fill is properly serialized."""
        # Create a test FillFormat with pattern fill
        class MockFillFormatPattern(FillFormat):
            def __init__(self, fore_color, back_color, pattern):
                self._fill_type = MSO_FILL.PATTERNED
                self._fore_color = fore_color
                self._back_color = back_color
                self._pattern = pattern
                
            @property
            def type(self):
                return self._fill_type
                
            @property
            def fore_color(self):
                return self._fore_color
                
            @property
            def back_color(self):
                return self._back_color
                
            @property
            def pattern(self):
                return self._pattern
                
            @property
            def gradient_stops(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def gradient_angle(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def rId(self):
                raise NotImplementedError(".rId property must be implemented on _PattFill")
        
        # Create mock color and pattern
        class MockColorFormat(IntrospectionMixin):
            def __init__(self, color_name):
                super().__init__()
                self.color_name = color_name
                
            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {"color": self.color_name}
        
        class MockPattern:
            def __init__(self, name):
                self.name = name
                
            def __repr__(self):
                return f"MockPattern({self.name})"
        
        fill_format = MockFillFormatPattern(
            MockColorFormat("red"), MockColorFormat("white"), MockPattern("CROSS")
        )
        result = fill_format.to_dict()
        
        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'PATTERNED')
        self.assertIsNotNone(props['fore_color'])
        self.assertEqual(props['fore_color']['_object_type'], 'MockColorFormat')
        self.assertIsNotNone(props['back_color'])
        self.assertEqual(props['back_color']['_object_type'], 'MockColorFormat')
        # Pattern is a simple object, so it gets converted to repr string
        self.assertIn('CROSS', str(props['pattern']))
        
        # Other properties should be None for pattern fill
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])
        
        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Patterned fill', context['summary'])
        self.assertIn('CROSS', context['summary'])

    def test_fillformat_picture_introspection(self):
        """Test that FillFormat with picture fill is properly serialized."""
        # Create a test FillFormat with picture fill
        class MockFillFormatPicture(FillFormat):
            def __init__(self, rId):
                self._fill_type = MSO_FILL.PICTURE
                self._rId = rId
                
            @property
            def type(self):
                return self._fill_type
                
            @property
            def rId(self):
                return self._rId
                
            @property
            def fore_color(self):
                raise TypeError("fill type _BlipFill has no foreground color")
                
            @property
            def back_color(self):
                raise TypeError("fill type _BlipFill has no background color")
                
            @property
            def pattern(self):
                raise TypeError("fill type _BlipFill has no pattern")
                
            @property
            def gradient_stops(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def gradient_angle(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
        
        fill_format = MockFillFormatPicture("rId5")
        result = fill_format.to_dict()
        
        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'PICTURE')
        self.assertEqual(props['image_rId'], 'rId5')
        
        # Other properties should be None for picture fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        
        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Picture fill', context['summary'])
        self.assertIn('rId5', context['summary'])

    def test_fillformat_background_introspection(self):
        """Test that FillFormat with background fill is properly serialized."""
        # Create a test FillFormat with background fill
        class MockFillFormatBackground(FillFormat):
            def __init__(self):
                self._fill_type = MSO_FILL.BACKGROUND
                
            @property
            def type(self):
                return self._fill_type
                
            @property
            def fore_color(self):
                raise TypeError("fill type _NoFill has no foreground color")
                
            @property
            def back_color(self):
                raise TypeError("fill type _NoFill has no background color")
                
            @property
            def pattern(self):
                raise TypeError("fill type _NoFill has no pattern")
                
            @property
            def gradient_stops(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def gradient_angle(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def rId(self):
                raise NotImplementedError(".rId property must be implemented on _NoFill")
        
        fill_format = MockFillFormatBackground()
        result = fill_format.to_dict()
        
        # Check properties
        props = result['properties']
        self.assertEqual(props['type']['name'], 'BACKGROUND')
        
        # All specific properties should be None for background fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])
        
        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Background fill (transparent)', context['summary'])

    def test_fillformat_none_introspection(self):
        """Test that FillFormat with no fill defined is properly serialized."""
        # Create a test FillFormat with None fill type
        class MockFillFormatNone(FillFormat):
            def __init__(self):
                self._fill_type = None
                
            @property
            def type(self):
                return self._fill_type
                
            @property
            def fore_color(self):
                raise TypeError("fill type _NoneFill has no foreground color")
                
            @property
            def back_color(self):
                raise TypeError("fill type _NoneFill has no background color")
                
            @property
            def pattern(self):
                raise TypeError("fill type _NoneFill has no pattern")
                
            @property
            def gradient_stops(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def gradient_angle(self):
                raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
                
            @property
            def rId(self):
                raise NotImplementedError(".rId property must be implemented on _NoneFill")
        
        fill_format = MockFillFormatNone()
        result = fill_format.to_dict()
        
        # Check properties
        props = result['properties']
        self.assertIsNone(props['type'])
        
        # All specific properties should be None for no fill
        self.assertIsNone(props['fore_color'])
        self.assertIsNone(props['back_color'])
        self.assertIsNone(props['pattern'])
        self.assertIsNone(props['gradient_stops'])
        self.assertIsNone(props['gradient_angle'])
        self.assertIsNone(props['image_rId'])
        
        # Check LLM context
        context = result['_llm_context']
        self.assertIn('No explicit fill defined', context['summary'])

    def test_gradient_stop_introspection(self):
        """Test that _GradientStop is properly serialized."""
        # Create a test _GradientStop
        class MockGradientStop(_GradientStop):
            def __init__(self, position, color):
                # Skip parent initialization for testing
                self._position = position
                self._color = color
                
            @property
            def position(self):
                return self._position
                
            @property
            def color(self):
                return self._color
        
        # Create mock color
        class MockColorFormat(IntrospectionMixin):
            def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
                return {"type": {"name": "RGB"}, "rgb": {"hex": "00FF00"}}
            
            def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
                return {"summary": "Solid RGB color: #00FF00"}
        
        gradient_stop = MockGradientStop(0.5, MockColorFormat())
        result = gradient_stop.to_dict()
        
        # Check basic structure
        self.assertEqual(result['_object_type'], 'MockGradientStop')
        self.assertIn('_identity', result)
        self.assertIn('properties', result)
        self.assertIn('_llm_context', result)
        
        # Check identity
        identity = result['_identity']
        self.assertEqual(identity['description'], 'Represents a color stop in a gradient.')
        
        # Check properties
        props = result['properties']
        self.assertEqual(props['position'], 0.5)
        self.assertIsNotNone(props['color'])
        self.assertEqual(props['color']['_object_type'], 'MockColorFormat')
        
        # Check LLM context
        context = result['_llm_context']
        self.assertIn('Gradient stop at 50% position', context['summary'])
        # The color summary should be accessible
        self.assertIn('color', context['summary'])
        
        # Relationships should be empty for GradientStop
        self.assertEqual(result['relationships'], {})


if __name__ == '__main__':
    unittest.main()
