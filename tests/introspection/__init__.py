# tests/introspection/__init__.py

"""
Introspection Test Suite

This package contains modular tests for the python-pptx introspection functionality.
Tests are organized by functionality rather than implementation order (FEP).

Test Modules:
- test_core_mixin: Core IntrospectionMixin functionality and basic types
- test_enum_formatting: Enum serialization support
- test_shape_introspection: BaseShape identity and geometry introspection
- test_color_introspection: ColorFormat color and theme introspection
- test_fill_introspection: FillFormat fill type and properties introspection
- test_line_introspection: LineFormat line styling introspection

Shared Utilities:
- mock_helpers: Common mock classes and testing utilities
"""

# Test modules will be automatically discovered by unittest
# Import classes only when needed to avoid import errors during development

__all__ = [
    'test_core_mixin',
    'test_enum_formatting', 
    'test_shape_introspection',
    'test_color_introspection',
    'test_fill_introspection',
    'test_line_introspection',
    'mock_helpers'
]