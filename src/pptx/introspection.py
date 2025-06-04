# src/pptx/introspection.py
"""
IntrospectionMixin - Foundation for comprehensive object introspection in python-pptx.

This module implements FEP-001, providing the foundational introspection capabilities
that enable objects to serialize their state into dictionary format. This is the first
of 18 planned Feature Enhancement Proposals (FEPs) designed to make python-pptx objects
transparent and easily understood by both human developers and AI tools.

Example Usage:
    class MyPresentationObject(IntrospectionMixin):
        def __init__(self):
            self.name = "Example Slide"
            self.color = RGBColor(255, 128, 0)
            self.size = Inches(2.5)
    
    obj = MyPresentationObject()
    result = obj.to_dict()
    # Returns comprehensive object state with type information
"""

import inspect

# Import RGBColor locally in _format_property_value_for_to_dict to avoid circular imports
# from pptx.dml.color import RGBColor
# Enum handling will also be added here in a future FEP.

class IntrospectionMixin:
    """Mixin class providing comprehensive object introspection capabilities.
    
    This mixin enables any python-pptx object to serialize its state into a dictionary
    format suitable for debugging, AI analysis, and external tool integration.
    
    Features:
        - Recursive object introspection with circular reference detection
        - Configurable depth limits and privacy controls
        - Special handling for python-pptx types (RGBColor, Length)
        - Collection expansion with depth awareness
        - LLM-friendly formatting with contextual descriptions
        
    Usage:
        class SlideElement(IntrospectionMixin):
            def __init__(self):
                self.name = "Title"
                self.color = RGBColor(255, 0, 0)
        
        element = SlideElement()
        data = element.to_dict()  # Full introspection
        simple = element.to_dict(max_depth=1, include_relationships=False)
    """
    
    def to_dict(self, include_relationships=True, max_depth=3,
                include_private=False, expand_collections=True,
                format_for_llm=True, _visited_ids=None):
        """Serialize object state to dictionary format with comprehensive options.
        
        Args:
            include_relationships (bool): Include related objects in output.
                Default True. Set False for property-only introspection.
            max_depth (int): Maximum recursion depth for nested objects.
                Default 3. Prevents infinite recursion in complex hierarchies.
            include_private (bool): Include private attributes (starting with '_').
                Default False. When True, exposes internal object state.
            expand_collections (bool): Expand lists, tuples, and dictionaries.
                Default True. When False, shows collection summaries only.
            format_for_llm (bool): Include LLM-friendly context and descriptions.
                Default True. Adds '_llm_context' section for AI tools.
            _visited_ids (set): Internal parameter for circular reference detection.
                Do not set manually.
        
        Returns:
            dict: Comprehensive object representation with structure:
                {
                    "_object_type": "ClassName",
                    "_identity": {"class_name": "...", "memory_address": "..."},
                    "properties": {"attr1": value1, "attr2": value2, ...},
                    "relationships": {...},  # if include_relationships=True
                    "_llm_context": {...}    # if format_for_llm=True
                }
        
        Examples:
            Basic usage:
                >>> obj.to_dict()
                {'_object_type': 'MyClass', 'properties': {...}, ...}
            
            Shallow inspection:
                >>> obj.to_dict(max_depth=1, include_relationships=False)
                {'_object_type': 'MyClass', 'properties': {...}}
            
            Include private attributes:
                >>> obj.to_dict(include_private=True)
                {'properties': {'_internal_state': ..., 'public_attr': ...}}
            
            Collection summaries only:
                >>> obj.to_dict(expand_collections=False)
                {'properties': {'items': 'Collection of 5 items (not expanded)'}}
        """

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
        """Extract and format object properties for introspection.
        
        Returns a dictionary of property names to their formatted values,
        filtered according to privacy settings and excluding introspection methods.
        
        Performance Notes:
            - dir() is called once per object; consider caching for repeated calls
            - Property detection uses multiple hasattr/getattr calls; future optimization opportunity
            - For objects with many properties, this can be expensive; consider lazy evaluation
        """
        props = {}
        
        try:
            # PERFORMANCE: dir() returns a new list each time. For objects inspected repeatedly,
            # consider caching the result. However, for FEP-001 scope, this is acceptable.
            for attr_name in dir(self):
                if not self._should_include_attribute(attr_name, include_private):
                    continue
                    
                if self._is_introspection_method(attr_name):
                    continue

                try:
                    attr_value = getattr(self, attr_name)
                    
                    # Skip callable methods (but allow properties)
                    if self._is_callable_method(attr_name, attr_value):
                        continue

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

    def _should_include_attribute(self, attr_name: str, include_private: bool) -> bool:
        """Determine if an attribute should be included based on privacy settings."""
        # Always skip dunder methods/attributes
        if attr_name.startswith('__'):
            return False
            
        # Handle private attributes (single underscore)
        if attr_name.startswith('_'):
            if include_private:
                return True
            else:
                # Include private properties even when include_private=False
                return self._is_property(attr_name)
        
        return True

    def _is_property(self, attr_name: str) -> bool:
        """Check if an attribute is a property descriptor."""
        try:
            class_attr = getattr(type(self), attr_name, None)
            return isinstance(class_attr, property)
        except (AttributeError, TypeError):
            return False

    def _is_introspection_method(self, attr_name: str) -> bool:
        """Check if an attribute is an introspection method that should be excluded."""
        introspection_methods = {
            'to_dict', '_to_dict_identity', '_to_dict_properties',
            '_to_dict_relationships', '_to_dict_llm_context',
            '_format_property_value_for_to_dict', '_should_include_attribute',
            '_is_property', '_is_introspection_method', '_is_callable_method'
        }
        return attr_name in introspection_methods

    def _is_callable_method(self, attr_name: str, attr_value) -> bool:
        """Check if an attribute is a callable method (not a property)."""
        if not callable(attr_value):
            return False
            
        # If it's a property, it's not a "method" for our purposes
        return not self._is_property(attr_name)

    def _format_property_value_for_to_dict(self, value, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Format a property value for inclusion in to_dict output.
        
        Handles special types (RGBColor, Length), recursive objects, collections,
        and provides enhanced error context for debugging.
        
        Performance Notes:
            - Local imports repeated on each call; acceptable for FEP-001 but could be optimized
            - isinstance() checks are performed in sequence; consider optimization for hot paths
            - Collection processing creates new lists/dicts; memory usage scales with object size
            
        Future FEP Integration Points:
            - Type handler registry for extensible type support (planned for later FEPs)
            - Enum introspection will be added here (FEP-002)
            - Custom serialization protocols for complex objects
        """
        # PERFORMANCE: Local imports prevent circular dependencies but are repeated per call.
        # For high-frequency usage, consider module-level imports with lazy loading pattern.
        from pptx.dml.color import RGBColor # type: ignore
        from pptx.util import Length # type: ignore

        try:
            if isinstance(value, RGBColor):
                try:
                    return {
                        "_object_type": "RGBColor",
                        "r": value[0], "g": value[1], "b": value[2],
                        "hex": str(value)
                    }
                except Exception as e:
                    return self._create_error_context("RGBColor", e, value)
                    
            elif isinstance(value, Length): # Future FEP might make Length use IntrospectionMixin
                try:
                    return {
                        "_object_type": type(value).__name__,
                        "emu": int(value),
                        "inches": float(value.inches),
                        "pt": float(value.pt),
                        "cm": float(value.cm),
                        "mm": float(value.mm)
                    }
                except Exception as e:
                    return self._create_error_context("Length", e, value)
                    
            elif hasattr(value, 'to_dict') and callable(value.to_dict) and not inspect.isclass(value):
                 # Ensure it's not the class method itself, but an instance method
                if value is self: # Avoid self-recursion if an object refers to itself in a property
                     return {"_reference": f"Self reference to {type(self).__name__} at {hex(id(self))}"}

                # Check if 'value' is an instance of IntrospectionMixin or has a compatible to_dict
                # This check helps ensure we are calling to_dict on objects we intend to serialize
                if isinstance(value, IntrospectionMixin) or hasattr(type(value), '_to_dict_identity'):
                    try:
                        return value.to_dict(
                            include_relationships=False, # Usually don't expand relationships of properties by default
                            max_depth=max_depth,
                            include_private=include_private,
                            expand_collections=expand_collections,
                            format_for_llm=format_for_llm,
                            _visited_ids=_visited_ids # Pass along the set of visited object IDs
                        )
                    except Exception as e:
                        return self._create_error_context("introspectable_object", e, value)
                else: # For objects with to_dict but not part of our introspection framework yet
                    return repr(value)

            elif isinstance(value, (list, tuple)):
                if expand_collections and max_depth > 0 : # check max_depth for collections too
                    try:
                        return [self._format_property_value_for_to_dict(
                                    item, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
                                ) for item in value]
                    except Exception as e:
                        return self._create_error_context("collection", e, value)
                else:
                    try:
                        return f"Collection of {len(value)} items (not expanded due to max_depth or expand_collections=False)"
                    except Exception as e:
                        return self._create_error_context("collection_summary", e, value)
                        
            elif isinstance(value, dict):
                if expand_collections and max_depth > 0: # check max_depth for dicts too
                    try:
                        return {str(k): self._format_property_value_for_to_dict( # Ensure key is string
                                    v, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
                                ) for k, v in value.items()}
                    except Exception as e:
                        return self._create_error_context("dictionary", e, value)
                else:
                    try:
                        return f"Dictionary with {len(value)} keys (not expanded due to max_depth or expand_collections=False)"
                    except Exception as e:
                        return self._create_error_context("dictionary_summary", e, value)

            # Basic types or types without to_dict
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value

            return repr(value) # Default for other types
            
        except Exception as e:
            # Catch-all for any unexpected errors
            return self._create_error_context("unknown", e, value)

    def _create_error_context(self, context_type: str, exception: Exception, value) -> dict:
        """Create enhanced error context for debugging serialization failures."""
        return {
            "_error": {
                "type": context_type,
                "message": str(exception),
                "exception_type": type(exception).__name__,
                "value_type": type(value).__name__,
                "value_repr": repr(value)[:200] + "..." if len(repr(value)) > 200 else repr(value)
            },
            "_object_type": f"SerializationError_{context_type}"
        }

    def _to_dict_relationships(self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private):
        return {} # Default: no relationships

    def _to_dict_llm_context(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
        """Provide LLM-friendly context and descriptions for this object.
        
        Default implementation provides basic object description. Subclasses should
        override this method to provide rich contextual information for AI tools.
        
        Future FEP Enhancements:
            - Object purpose and role descriptions (FEP-014)
            - Usage examples and code snippets (FEP-015)
            - Relationship context and object dependencies (FEP-016)
            - Interactive manipulation hints for AI assistants (FEP-017)
        
        Returns:
            dict: LLM context with at minimum a 'description' field
        """
        # EXTENSIBILITY: This method is designed to be overridden by subclasses
        # to provide rich, domain-specific context for different python-pptx objects
        return {"description": f"A {type(self).__name__} object."}
