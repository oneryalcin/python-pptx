# CLAUDE.md - Development Guide for python-pptx

This file contains project-specific information for AI assistants working on the python-pptx codebase.

## Project Overview

**python-pptx** is a Python library for creating, reading, and updating PowerPoint (.pptx) files. It allows programmatic manipulation of PowerPoint presentations without requiring PowerPoint to be installed.

### Key Features
- Create and modify PowerPoint presentations
- Add slides, shapes, text, images, charts, and tables
- Extensive chart support with data manipulation
- Text formatting and styling
- Image and media handling
- Template and layout management

## Repository Structure

```
src/pptx/                   # Main package source
├── chart/                  # Chart-related functionality
├── dml/                    # DrawingML (Office graphics format)
├── enum/                   # Enumerations and constants
├── opc/                    # Open Packaging Conventions
├── oxml/                   # XML handling layer
├── parts/                  # Document parts (slides, charts, etc.)
├── shapes/                 # Shape objects and manipulation
├── text/                   # Text handling and formatting
└── templates/              # Default templates and resources

tests/                      # Test suite (pytest)
features/                   # Behavior-driven tests (behave)
docs/                       # Documentation (Sphinx)
spec/                       # Office Open XML specifications
```

## Development Environment Setup

### Prerequisites
- Python 3.8+ (supports up to 3.12)
- Virtual environment recommended

### Quick Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e .
pip install -r requirements-dev.txt
```

### Important: Virtual Environment Usage
**This project has an existing virtual environment at `./venv/`**

**ALL Python commands should be run within the virtual environment:**
```bash
# Activate virtual environment first
source venv/bin/activate

# Then run any Python commands
python -m pytest tests/
python -c "import pptx; print('Success')"
```

**Claude Code AI Assistants:** Always use `source venv/bin/activate &&` prefix for Python commands in this project.

### Dependencies
- **Core:** lxml, Pillow, XlsxWriter, typing_extensions
- **Development:** pytest, behave, ruff, tox, coverage tools
- **Documentation:** Sphinx and related packages

## Testing

### Test Suite Structure
- **Unit Tests:** `tests/` directory (pytest) - 2700+ tests
- **Integration Tests:** `features/` directory (behave/Gherkin)
- **Test Coverage:** pytest-cov for coverage reporting

### Running Tests
```bash
# Run all unit tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/shapes/test_autoshape.py

# Run with coverage
python -m pytest tests/ --cov=pptx

# Run behavior tests
behave features/

# Run tests in parallel
python -m pytest tests/ -n auto
```

### Test Conventions
- Test classes use `Describe*` naming pattern
- Test methods use `it_*`, `they_*`, `but_*`, `and_*` prefixes
- Fixtures heavily used for test setup
- Mock objects from `tests.unitutil.mock`

## Code Quality

### Linting and Formatting
- **Ruff:** Primary linter and formatter
- **Black:** Code formatting (line-length: 100)
- **Pyright:** Type checking (strict mode)

```bash
# Check linting issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/

# Type checking
pyright src/
```

### Code Style Guidelines
- Line length: 100 characters
- Use type hints (Python 3.8+ compatible)
- Follow PEP 8 with project-specific adaptations
- Docstrings for public APIs
- No unnecessary comments unless explaining complex logic

## Architecture Patterns

### Key Design Patterns
1. **Proxy Pattern:** Shape objects proxy XML elements
2. **Factory Pattern:** Shape creation via factories
3. **Lazy Properties:** `@lazyproperty` for expensive operations
4. **XML Abstraction:** `oxml` layer abstracts XML manipulation

### Important Modules
- `pptx.api`: Main public API entry point
- `pptx.presentation`: Top-level presentation object
- `pptx.shapes.*`: Shape hierarchy and manipulation
- `pptx.oxml.*`: XML element wrappers
- `pptx.parts.*`: Document part objects

## Common Development Tasks

### Adding New Features
1. Understand the Office Open XML specification
2. Create/modify XML element classes in `oxml/`
3. Add business logic in appropriate module
4. Write comprehensive tests
5. Update documentation

### Bug Fixes
1. Write failing test that reproduces the bug
2. Implement minimal fix
3. Ensure all tests pass
4. Consider edge cases and compatibility

### Working with XML
- Use `lxml.etree` for XML parsing
- XML namespaces defined in `pptx.oxml.ns`
- Custom XML element classes inherit from `BaseOxmlElement`

## Testing Specific Components

### Shapes
```bash
# Test all shape functionality
python -m pytest tests/shapes/

# Test specific shape types
python -m pytest tests/shapes/test_autoshape.py
python -m pytest tests/shapes/test_picture.py
```

### Charts
```bash
# Test chart functionality
python -m pytest tests/chart/

# Test specific chart features
python -m pytest tests/chart/test_data.py
python -m pytest tests/chart/test_series.py
```

### Text and Formatting
```bash
# Test text handling
python -m pytest tests/text/

# Test DML (formatting)
python -m pytest tests/dml/
```

## Known Issues

### Current Test Failures
- `tests/text/test_text.py::DescribeFont::it_provides_access_to_its_color` - Font.color property returns None instead of ColorFormat (pre-existing issue)

### Common Gotchas
- XML namespace handling requires careful attention
- Shape creation vs. modification have different patterns
- Chart data replacement can be complex
- Image handling requires proper MIME type detection

## Release Process

### Version Management
- Version defined in `src/pptx/__init__.py`
- Semantic versioning (MAJOR.MINOR.PATCH)
- Changelog maintained in `HISTORY.rst`

### Build and Distribution
```bash
# Build package
python -m build

# Run full test suite across Python versions
tox

# Upload to PyPI (maintainers only)
twine upload dist/*
```

## Useful Commands

### Development Workflow
```bash
# Full development check
python -m pytest tests/ && ruff check src/ && ruff format src/

# Quick test of changes
python -m pytest tests/path/to/relevant/tests.py -v

# Check import organization
ruff check --select I src/

# Find specific functionality
grep -r "pattern" src/pptx/
```

### Debugging
- Use `pytest --pdb` for debugging test failures
- XML inspection: `print(element.xml)` for oxml elements
- Use `pytest -s` to see print statements during tests

## Contributing Guidelines

### Pull Request Process
1. Create feature branch from `master`
2. Make focused, atomic commits
3. Ensure all tests pass
4. Update documentation if needed
5. Submit PR with clear description

### Commit Message Format
- Use descriptive commit messages
- Reference issue numbers when applicable
- Separate bug fixes from feature additions
- Keep commits focused and atomic

### Branch Naming
- `fix/description` for bug fixes
- `feature/description` for new features
- `improve/description` for code quality improvements

## Resources

- **Documentation:** https://python-pptx.readthedocs.io/
- **Office Open XML Specs:** `spec/` directory
- **Issue Tracker:** GitHub Issues
- **API Reference:** Generated from docstrings

---

# FEP (Feature Enhancement Proposal) Development Guide

## Overview: Introspection Enhancement Roadmap

**python-pptx** is undergoing a comprehensive enhancement to add structured introspection capabilities across all major object types. This enables objects to serialize their state into dictionary format, making them transparent for debugging, AI analysis, and external tool integration.

### ✅ Completed FEPs

#### **FEP-001: Basic Introspection Mixin & RGBColor/Length Support**
- **Status:** ✅ **COMPLETED** (PR #6)
- **Files:** `src/pptx/introspection.py`, `tests/test_introspection.py`
- **Branch:** `fep-001-introspection-mixin`

**Key Achievements:**
- ✅ Core `IntrospectionMixin` class with `to_dict()` method
- ✅ Circular reference detection and depth limiting
- ✅ `RGBColor` and `Length` object serialization
- ✅ Enhanced error context system
- ✅ Comprehensive test suite (13 test methods)

**Architecture Patterns Established:**
```python
class IntrospectionMixin:
    def to_dict(self, include_relationships=True, max_depth=3,
                include_private=False, expand_collections=True,
                format_for_llm=True, _visited_ids=None):
        # Template method pattern with 5 extension points:
        # 1. _to_dict_identity() - Object identification
        # 2. _to_dict_properties() - Core properties  
        # 3. _to_dict_relationships() - Object relationships
        # 4. _to_dict_llm_context() - AI-friendly descriptions
        # 5. _format_property_value_for_to_dict() - Type-specific formatting
```

#### **FEP-002: Enum Member Introspection**
- **Status:** ✅ **COMPLETED** (PR #8)
- **Files:** Enhanced `src/pptx/introspection.py`, `tests/test_introspection.py`
- **Branch:** `fep-002-enum-introspection`

**Key Achievements:**
- ✅ `BaseEnum` and `BaseXmlEnum` detection and serialization
- ✅ Structured enum output: `_object_type`, `name`, `value`, `description`, `xml_value`
- ✅ Collection support (enums within lists/dicts)
- ✅ Edge case handling (empty xml_values, missing docstrings)
- ✅ 5 additional comprehensive test methods

**Implementation Pattern:**
```python
elif isinstance(value, (BaseEnum, BaseXmlEnum)):
    enum_dict = {
        "_object_type": type(value).__name__,
        "name": value.name,
        "value": int(value),
        "description": getattr(value, '__doc__', None) or ""
    }
    if isinstance(value, BaseXmlEnum):
        enum_dict["xml_value"] = getattr(value, 'xml_value', None)
    return enum_dict
```

#### **FEP-003: BaseShape.to_dict() - Identity & Basic Geometry**
- **Status:** ✅ **COMPLETED** (PR #10)
- **Files:** Enhanced `src/pptx/shapes/base.py`, `tests/test_introspection.py`
- **Branch:** `fep-003-base-shape-introspection`

**Key Achievements:**
- ✅ Enhanced `BaseShape` with `IntrospectionMixin` inheritance
- ✅ Shape identity introspection (shape_id, name, shape_type, placeholder details)
- ✅ Geometric properties introspection (left, top, width, height, rotation)
- ✅ Safe error handling for edge cases (`NotImplementedError`, placeholder access)
- ✅ Relationship introspection (parent collection, part) with fallback to `repr()`
- ✅ Rich LLM context generation for AI tools
- ✅ 6 comprehensive test methods covering all scenarios

**Implementation Highlights:**
```python
class BaseShape(IntrospectionMixin):
    def _to_dict_identity(self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private):
        identity = super()._to_dict_identity(...)
        identity["shape_id"] = self.shape_id
        identity["name"] = self.name
        identity["is_placeholder"] = self.is_placeholder
        
        # Safe shape_type access
        shape_type = self._get_shape_type_safely()
        if shape_type is not None:
            identity["shape_type"] = self._format_property_value_for_to_dict(...)
        
        # Safe placeholder access
        placeholder_info = self._get_placeholder_info_safely(...)
        if placeholder_info is not None:
            identity["placeholder_details"] = placeholder_info
        return identity

    def _get_shape_type_safely(self):
        try:
            return self.shape_type
        except NotImplementedError:
            return None  # BaseShape doesn't implement shape_type
```

**Live Demo Output:**
```json
{
  "_object_type": "Shape",
  "_identity": {
    "shape_id": 42,
    "name": "Demo Rectangle",
    "is_placeholder": false,
    "shape_type": {"_object_type": "MSO_SHAPE_TYPE", "name": "AUTO_SHAPE", "value": 1}
  },
  "properties": {
    "left": {"_object_type": "Emu", "emu": 914400, "inches": 1.0},
    "width": {"_object_type": "Emu", "emu": 2743200, "inches": 3.0},
    "rotation": 15.0
  },
  "_llm_context": {
    "description": "A AUTO_SHAPE shape named 'Demo Rectangle' (ID: 42).",
    "common_operations": ["access geometry", "modify position and size", "change name"]
  }
}
```

#### **FEP-004: ColorFormat.to_dict() - Color and Theme Introspection**
- **Status:** ✅ **COMPLETED** (PR #12)
- **Files:** Enhanced `src/pptx/dml/color.py`, `tests/test_introspection.py`
- **Branch:** `fep-004-colorformat-introspection`

**Key Achievements:**
- ✅ Enhanced `ColorFormat` with `IntrospectionMixin` inheritance
- ✅ Color type introspection (RGB, SCHEME, HSL, PRESET, etc.)
- ✅ Type-safe property exposure (rgb only for RGB, theme_color only for SCHEME)
- ✅ Brightness adjustment introspection (-1.0 to 1.0 range)
- ✅ Human-readable LLM context with color descriptions
- ✅ Robust error handling for incompatible property access
- ✅ 6 comprehensive test methods covering all color scenarios

**Implementation Highlights:**
```python
class ColorFormat(IntrospectionMixin):
    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        props = {}
        color_type_val = self.type
        
        # Type-safe property exposure
        if color_type_val == MSO_COLOR_TYPE.RGB:
            props["rgb"] = self._format_property_value_for_to_dict(self.rgb, ...)
            props["theme_color"] = None
        elif color_type_val == MSO_COLOR_TYPE.SCHEME:
            props["theme_color"] = self._format_property_value_for_to_dict(self.theme_color, ...)
            props["rgb"] = None
        # ...robust error handling and brightness introspection
```

**Live Demo Output:**
```json
{
  "_object_type": "ColorFormat",
  "properties": {
    "type": {"_object_type": "MSO_COLOR_TYPE", "name": "RGB", "value": 1},
    "rgb": {"_object_type": "RGBColor", "r": 18, "g": 52, "b": 86, "hex": "123456"},
    "theme_color": null,
    "brightness": 0.0
  },
  "_llm_context": {
    "summary": "Solid RGB color: #123456 (R:18, G:52, B:86)."
  }
}
```

### 🔄 Development Patterns & Lessons Learned

#### **Architecture Decisions Made:**
1. **Mixin Pattern**: Incremental enhancement without breaking existing APIs
2. **Template Method**: Consistent extension points across all object types
3. **Local Imports**: Prevent circular dependencies with performance trade-off
4. **Error Context**: Enhanced debugging with structured error information
5. **Type Registration**: Centralized type handling in `_format_property_value_for_to_dict()`
6. **Safe Property Access**: Helper methods for robust edge case handling

#### **Testing Strategy:**
1. **Custom Test Classes**: Purpose-built classes for controlled testing scenarios
2. **Edge Case Coverage**: Explicit tests for None values, empty collections, circular references
3. **Real Object Testing**: Validation with actual python-pptx objects
4. **Regression Prevention**: Full test suite validation for each FEP
5. **Performance Validation**: No measurable overhead for existing functionality
6. **Mock-Based Testing**: Comprehensive mocking for complex object hierarchies

#### **Performance Considerations:**
- **Local Imports**: Repeated per call but prevents circular dependencies
- **Type Checking**: Sequential `isinstance()` checks, optimize for hot paths
- **Memory Management**: Object ID tracking for circular reference detection
- **Collection Processing**: Memory scales with object graph size
- **Safe Property Access**: Minimal overhead for error checking

---

## 🚀 Remaining FEP Roadmap (14 FEPs)

### **Phase 2: Core Object Types (FEP-005 to FEP-007)**

#### **FEP-005: FillFormat.to_dict() Introspection**
- **Priority:** HIGH  
- **Files to Modify:** `src/pptx/dml/fill.py`
- **Estimated Effort:** 2-3 days

**Objective:** Add introspection to `FillFormat` covering fill types, colors, gradients, and patterns.

#### **FEP-006: LineFormat.to_dict() Introspection**
- **Priority:** MEDIUM
- **Files to Modify:** `src/pptx/dml/line.py`
- **Estimated Effort:** 1-2 days

**Objective:** Add introspection to `LineFormat` covering line styles, colors, and effects.

#### **FEP-007: Font.to_dict() Introspection**  
- **Priority:** HIGH
- **Files to Modify:** `src/pptx/text/fonts.py`
- **Estimated Effort:** 2 days

**Objective:** Add introspection to `Font` objects covering typeface, size, and styling.

### **Phase 3: Complex Shapes (FEP-008 to FEP-011)**

#### **FEP-008: AutoShape.to_dict() Introspection**
- **Priority:** HIGH
- **Files to Modify:** `src/pptx/shapes/autoshape.py`
- **Estimated Effort:** 2-3 days

**Objective:** Add introspection to `Shape` (AutoShape) objects including adjustments, text frames, and shape-specific properties.

**Key Requirements:**
```python
{
    "_object_type": "Shape", 
    "properties": {
        "auto_shape_type": {"_object_type": "MSO_AUTO_SHAPE_TYPE", "name": "RECTANGLE"},
        "adjustments": [0.5, 0.25],  # Shape adjustments if applicable
        "text_frame": {"_object_type": "TextFrame", "text": "Hello World"},
        "fill": {"_object_type": "FillFormat", "type": "SOLID"}
    }
}
```

#### **FEP-009: TextFrame & Paragraph Introspection**
- **Priority:** HIGH
- **Files to Modify:** `src/pptx/text/text.py`, `src/pptx/text/layout.py`
- **Estimated Effort:** 3-4 days

**Objective:** Add introspection to text hierarchy: `TextFrame`, `_Paragraph`, `_Run`.

#### **FEP-010: Picture & Media Introspection**
- **Priority:** MEDIUM
- **Files to Modify:** `src/pptx/shapes/picture.py`
- **Estimated Effort:** 2 days

**Objective:** Add introspection to `Picture` shapes including image metadata and media properties.

#### **FEP-011: Table Introspection**
- **Priority:** MEDIUM  
- **Files to Modify:** `src/pptx/table.py`
- **Estimated Effort:** 2-3 days

**Objective:** Add introspection to `Table`, `_Row`, `_Column`, `_Cell` objects.

### **Phase 4: Document Structure (FEP-012 to FEP-013)**

#### **FEP-012: Slide Introspection**
- **Priority:** HIGH
- **Files to Modify:** `src/pptx/slide.py`
- **Estimated Effort:** 3-4 days

**Objective:** Add introspection to `Slide` objects including shape collections and slide properties.

**Key Requirements:**
```python
{
    "_object_type": "Slide",
    "properties": {
        "slide_id": 256,
        "name": "Slide 1",
        "layout": {"_object_type": "SlideLayout", "name": "Title and Content"}
    },
    "relationships": {
        "shapes": [
            {"_object_type": "Shape", "name": "Title 1"},
            {"_object_type": "Shape", "name": "Content Placeholder 2"}
        ],
        "slide_master": {"_object_type": "SlideMaster"},
        "notes_slide": {"_object_type": "NotesSlide"}
    }
}
```

#### **FEP-013: Presentation Introspection**
- **Priority:** HIGH
- **Files to Modify:** `src/pptx/presentation.py`
- **Estimated Effort:** 3-4 days

**Objective:** Add introspection to `Presentation` objects with slide collections and document properties.

### **Phase 5: Advanced Features (FEP-014 to FEP-018)**

#### **FEP-014: Enhanced LLM Context Generation**
- **Priority:** MEDIUM
- **Files to Modify:** `src/pptx/introspection.py`, multiple override methods
- **Estimated Effort:** 2-3 days

**Objective:** Enhance `_to_dict_llm_context()` methods across all object types for rich AI descriptions.

#### **FEP-015: Relationship Mapping & Inheritance Tracing**  
- **Priority:** MEDIUM
- **Files to Modify:** `src/pptx/introspection.py`, multiple classes
- **Estimated Effort:** 3-4 days

**Objective:** Add comprehensive relationship extraction and property inheritance tracking (slide → layout → master → theme).

#### **FEP-016: Placeholder Format Details**
- **Priority:** LOW
- **Files to Modify:** `src/pptx/shapes/placeholder.py`
- **Estimated Effort:** 2 days

**Objective:** Add introspection to placeholder-specific formatting and behavior.

#### **FEP-017: Performance Optimization for Large Documents**
- **Priority:** MEDIUM
- **Files to Modify:** `src/pptx/introspection.py`
- **Estimated Effort:** 2-3 days

**Objective:** Add caching, lazy evaluation, and selective introspection for large presentations.

#### **FEP-018: Interactive Manipulation Hints for AI**
- **Priority:** LOW
- **Files to Modify:** Multiple classes, enhance LLM context
- **Estimated Effort:** 2-3 days

**Objective:** Add AI-friendly manipulation hints and usage examples to introspection output.

---

## 🛠️ FEP Development Workflow

### **Starting a New FEP:**

1. **Preparation Phase:**
   ```bash
   # Create new branch from master
   git checkout master
   git pull origin master
   git checkout -b fep-XXX-feature-name
   
   # Activate development environment
   source venv/bin/activate
   ```

2. **Research Phase:**
   ```bash
   # Study existing patterns in completed FEPs
   grep -r "IntrospectionMixin" src/pptx/
   
   # Understand target classes and their XML structure
   grep -r "target_class_name" src/pptx/
   
   # Review existing tests for similar objects
   find tests/ -name "*target*" -type f
   ```

3. **Implementation Phase:**
   - Add `IntrospectionMixin` inheritance to target classes
   - Override `_to_dict_properties()` for object-specific attributes
   - Override `_to_dict_identity()` if needed for custom identification
   - Override `_to_dict_relationships()` for object relationships
   - Override `_to_dict_llm_context()` for AI-friendly descriptions
   - Enhance `_format_property_value_for_to_dict()` for new types if needed
   - Add safe helper methods for error-prone property access

4. **Testing Phase:**
   ```bash
   # Create comprehensive test cases
   # Follow patterns from tests/test_introspection.py
   
   # Test categories to cover:
   # - Basic object introspection
   # - Property formatting 
   # - Collection handling
   # - Edge cases (None values, empty objects)
   # - Error scenarios
   # - Real object validation
   
   # Run tests
   python -m pytest tests/test_introspection.py -v
   python -m pytest tests/path/to/new/tests.py -v
   
   # Ensure no regressions
   python -m pytest tests/ -x  # Stop on first failure
   ```

5. **Documentation Phase:**
   - Add comprehensive docstrings with examples
   - Update this CLAUDE.md file with lessons learned
   - Create PR with detailed technical description

### **Code Patterns to Follow:**

#### **Class Enhancement Pattern:**
```python
# Before
class TargetClass:
    def __init__(self):
        self.property1 = value1

# After  
class TargetClass(IntrospectionMixin):
    def __init__(self):
        self.property1 = value1
    
    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {
            "property1": self._format_property_value_for_to_dict(
                self.property1, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )
        }
```

#### **Safe Property Access Pattern (FEP-003 Innovation):**
```python
def _get_property_safely(self, method_name="accessing property"):
    """Get property with safe error handling."""
    try:
        return self.property
    except (NotImplementedError, ValueError, AttributeError) as e:
        return None  # or return {"error": f"Could not access {method_name}: {str(e)}"}
```

#### **Type Handler Pattern:**
```python
# In _format_property_value_for_to_dict()
elif isinstance(value, TargetType):
    try:
        return {
            "_object_type": type(value).__name__,
            "key_property": value.key_property,
            "formatted_property": self._format_complex_property(value)
        }
    except Exception as e:
        return self._create_error_context("target_type", e, value)
```

#### **Test Pattern:**
```python
def test_target_class_formatting(self):
    """Test that TargetClass instances are properly serialized."""
    class TestObj(IntrospectionMixin):
        def __init__(self, target_val):
            self.target = target_val
            
        def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
            return {
                "target": self._format_property_value_for_to_dict(
                    self.target, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
                )
            }
    
    obj = TestObj(TargetClass())
    result = obj.to_dict()
    
    expected = {
        "_object_type": "TargetClass",
        "property1": "expected_value"
    }
    
    self.assertEqual(result['properties']['target'], expected)
```

### **Common Pitfalls to Avoid:**

1. **Circular Dependencies:** Always use local imports in `_format_property_value_for_to_dict()`
2. **Infinite Recursion:** Ensure `max_depth - 1` is passed to recursive calls
3. **Memory Leaks:** Always use `_visited_ids` parameter for circular reference detection
4. **Performance Impact:** Be mindful of expensive operations in hot paths
5. **Type Safety:** Use `isinstance()` checks before accessing type-specific attributes
6. **Error Handling:** Always wrap complex operations in try/catch with `_create_error_context()`
7. **Property Access:** Use safe helper methods for error-prone property access (lesson from FEP-003)

### **Testing Strategy:**

1. **Unit Tests:** Test individual object introspection in isolation
2. **Integration Tests:** Test objects within collections and complex hierarchies  
3. **Edge Case Tests:** None values, empty collections, circular references
4. **Error Handling Tests:** NotImplementedError, ValueError, AttributeError scenarios
5. **Performance Tests:** Large object graphs and deep nesting scenarios
6. **Regression Tests:** Ensure existing functionality remains unaffected

---

## 📚 Key Learning Resources

### **Existing Code to Study:**
- `src/pptx/introspection.py` - Core architecture and patterns
- `tests/test_introspection.py` - Comprehensive testing strategies
- `src/pptx/enum/base.py` - BaseEnum and BaseXmlEnum implementations
- `src/pptx/shapes/base.py` - Shape object hierarchy and safe property access
- `src/pptx/dml/color.py` - Color formatting implementations
- `src/pptx/dml/fill.py` - Fill formatting and GradientStop implementations

### **Office Open XML References:**
- `spec/` directory - Complete OOXML specifications
- **DrawingML:** Shapes, colors, fills, lines, effects
- **PresentationML:** Slides, layouts, masters, notes
- **SpreadsheetML:** Chart data and formatting

### **Development Commands:**
```bash
# Quick development cycle
source venv/bin/activate && python -m pytest tests/test_introspection.py -v && ruff check src/ && ruff format src/

# Find implementation patterns
grep -r "_format_property_value_for_to_dict" src/pptx/

# Study object relationships  
grep -r "class.*IntrospectionMixin" src/pptx/

# Test specific FEP functionality
python -m pytest tests/test_introspection.py -k "enum" -v
python -m pytest tests/test_introspection.py -k "base_shape" -v
python -m pytest tests/test_introspection.py -k "fillformat" -v
```

## 📈 Progress Tracking

### **Completed FEPs Summary**
- **FEP-001** ✅ Basic Introspection Mixin & Core Types (PR #6)
- **FEP-002** ✅ Enum Member Introspection (PR #8)  
- **FEP-003** ✅ BaseShape Identity & Geometry (PR #10)
- **FEP-004** ✅ ColorFormat Color & Theme Introspection (PR #12)
- **FEP-005** ✅ FillFormat Fill Type & Properties Introspection (PR #14)

### **Current Status**
- **Total Progress:** 5/18 FEPs completed (27.8%)
- **Foundation Phase:** ✅ COMPLETE - All foundational patterns established
- **Core Object Phase:** 🔄 IN PROGRESS - Next priority FEPs 006-007
- **Test Coverage:** 32/32 introspection tests passing (7 new FillFormat/GradientStop tests)
- **Zero Regressions:** All existing functionality preserved

### **Next Immediate Priorities**
1. **FEP-006:** LineFormat introspection (MEDIUM priority)
2. **FEP-007:** Font introspection (HIGH priority)
3. **FEP-008:** AutoShape introspection (HIGH priority)
4. **FEP-009:** TextFrame & Paragraph introspection (HIGH priority)

This roadmap provides the complete foundation for systematically implementing all remaining FEPs while maintaining consistency, quality, and performance across the entire python-pptx introspection enhancement.

---

## Contact

For questions about development practices or architecture decisions, refer to:
- Project documentation
- Existing test patterns
- Code comments and docstrings
- GitHub discussions and issues