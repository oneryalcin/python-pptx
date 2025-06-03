# src/pptx/introspection.py

import inspect

# Import RGBColor locally in _format_property_value_for_to_dict to avoid circular imports
# from pptx.dml.color import RGBColor
# Enum handling will also be added here in a future FEP.

class IntrospectionMixin:
    def to_dict(self, include_relationships=True, max_depth=3,
                include_private=False, expand_collections=True,
                format_for_llm=True, _visited_ids=None):

        if _visited_ids is None:
            _visited_ids = set()

        obj_id = id(self)
        if obj_id in _visited_ids:
            return {"_reference": f"Circular reference to {type(self).__name__} at {hex(obj_id)}"}

        if max_depth <= 0:
            return {"_truncated": f"Max depth reached for {type(self).__name__}"}

        _visited_ids.add(obj_id)

        try:
            result = {
                "_object_type": type(self).__name__,
                "_identity": self._to_dict_identity(
                    _visited_ids, max_depth, expand_collections, format_for_llm, include_private
                ),
                "properties": self._to_dict_properties(
                    include_private, _visited_ids, max_depth, expand_collections, format_for_llm
                ),
            }

            if format_for_llm:
                result["_llm_context"] = self._to_dict_llm_context(
                    _visited_ids, max_depth, expand_collections, format_for_llm, include_private
                )

            if include_relationships:
                result["relationships"] = self._to_dict_relationships(
                    max_depth - 1, expand_collections, _visited_ids, format_for_llm, include_private
                )
        finally:
            _visited_ids.remove(obj_id)

        return result

    def _to_dict_identity(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
        return {"class_name": type(self).__name__, "memory_address": hex(id(self))}

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        props = {}
        # Common methods to exclude from properties
        common_mixin_methods = {
            'to_dict', '_to_dict_identity', '_to_dict_properties',
            '_to_dict_relationships', '_to_dict_llm_context',
            '_format_property_value_for_to_dict'
        }

        try:
            for attr_name in dir(self):
                if not include_private and attr_name.startswith('_') and not attr_name.startswith('__'): # allow dunder if not explicitly private
                    # For dunder methods that are not explicitly private, check if they are properties
                    if hasattr(type(self), attr_name) and isinstance(getattr(type(self), attr_name), property):
                        pass # It's a property, include it
                    else:
                        continue # Skip other dunder unless include_private is True
                elif include_private and attr_name.startswith('_') and not attr_name.startswith('__'):
                    pass # include explicitly private if include_private is True
                elif attr_name.startswith('__'): # Always skip double underscore methods/attributes for now
                    continue

                if attr_name in common_mixin_methods:
                    continue

                try:
                    attr_value = getattr(self, attr_name)
                    if callable(attr_value) and not isinstance(attr_value, property):
                        # Further check if it's a method wrapped by @property or similar
                        if not (hasattr(type(self), attr_name) and isinstance(getattr(type(self), attr_name), property)):
                            continue

                    # If it's a property, access its value
                    if hasattr(type(self), attr_name) and isinstance(getattr(type(self), attr_name), property):
                         attr_value = getattr(self, attr_name)


                    props[attr_name] = self._format_property_value_for_to_dict(
                        attr_value, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                    )
                except Exception: # nosec B110
                    # Some properties might not be accessible or might raise errors
                    # Or it could be a method that requires arguments
                    pass
        except Exception: # nosec B110
             pass # Catch errors from dir() itself if any (highly unlikely for most objects)
        return props

    def _format_property_value_for_to_dict(self, value, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        # Moved import here to be method-local
        from pptx.dml.color import RGBColor # type: ignore
        from pptx.util import Length # type: ignore

        if isinstance(value, RGBColor):
            return {
                "_object_type": "RGBColor",
                "r": value[0], "g": value[1], "b": value[2],
                "hex": str(value)
            }
        elif isinstance(value, Length): # Future FEP might make Length use IntrospectionMixin
             return {
                "_object_type": type(value).__name__,
                "emu": int(value),
                "inches": float(value.inches),
                "pt": float(value.pt),
                "cm": float(value.cm),
                "mm": float(value.mm)
            }
        elif hasattr(value, 'to_dict') and callable(value.to_dict) and not inspect.isclass(value):
             # Ensure it's not the class method itself, but an instance method
            if value is self: # Avoid self-recursion if an object refers to itself in a property
                 return {"_reference": f"Self reference to {type(self).__name__} at {hex(id(self))}"}

            # Check if 'value' is an instance of IntrospectionMixin or has a compatible to_dict
            # This check helps ensure we are calling to_dict on objects we intend to serialize
            if isinstance(value, IntrospectionMixin) or hasattr(type(value), '_to_dict_identity'):
                return value.to_dict(
                    include_relationships=False, # Usually don't expand relationships of properties by default
                    max_depth=max_depth,
                    include_private=include_private,
                    expand_collections=expand_collections,
                    format_for_llm=format_for_llm,
                    _visited_ids=_visited_ids # Pass along the set of visited object IDs
                )
            else: # For objects with to_dict but not part of our introspection framework yet
                return repr(value)

        elif isinstance(value, (list, tuple)):
            if expand_collections and max_depth > 0 : # check max_depth for collections too
                return [self._format_property_value_for_to_dict(
                            item, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
                        ) for item in value]
            else:
                return f"Collection of {len(value)} items (not expanded due to max_depth or expand_collections=False)"
        elif isinstance(value, dict):
            if expand_collections and max_depth > 0: # check max_depth for dicts too
                return {str(k): self._format_property_value_for_to_dict( # Ensure key is string
                            v, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
                        ) for k, v in value.items()}
            else:
                return f"Dictionary with {len(value)} keys (not expanded due to max_depth or expand_collections=False)"

        # Basic types or types without to_dict
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value

        return repr(value) # Default for other types

    def _to_dict_relationships(self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private):
        return {} # Default: no relationships

    def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
        # Default: generic description. Subclasses can override this.
        return {"description": f"A {type(self).__name__} object."}
