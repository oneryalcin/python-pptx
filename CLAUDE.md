# CLAUDE.md - python-pptx Development Guide

AI assistant guide for the python-pptx codebase - a Python library for programmatic PowerPoint manipulation.

## Quick Start

### Environment Setup
```bash
# Project has existing venv - ALWAYS activate first
source venv/bin/activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Basic validation
python -c "import pptx; print('Success')"
```

**Critical:** ALL Python commands must use `source venv/bin/activate &&` prefix.

### Essential Commands
```bash
# Development cycle
python -m pytest tests/ && ruff check --fix src/ && ruff format src/

# Test introspection (modular approach preferred)
python -m pytest tests/introspection/ -v

# Component testing
python -m pytest tests/shapes/test_autoshape.py -v
```

## Project Structure

```
src/pptx/                   # Main package
├── chart/                  # Chart functionality
├── dml/                    # DrawingML (colors, fills, lines)
├── enum/                   # Enumerations
├── oxml/                   # XML handling
├── shapes/                 # Shape objects
├── text/                   # Text handling
└── introspection.py        # FEP core functionality

tests/                      # pytest suite (2700+ tests)
├── introspection/          # Modular FEP tests (96 tests)
└── test_introspection.py   # Legacy tests (38 tests)

features/                   # BDD tests (behave)
```

## Core Development Patterns

### Dependencies & Tools
- **Core:** lxml, Pillow, XlsxWriter, typing_extensions  
- **Quality:** ruff (linting/formatting), pyright (type checking)
- **Testing:** pytest, behave, coverage tools

### Architecture
1. **Proxy Pattern:** Shape objects proxy XML elements
2. **Factory Pattern:** Shape creation via factories  
3. **Lazy Properties:** `@lazyproperty` for expensive operations
4. **XML Abstraction:** `oxml` layer abstracts XML manipulation

### Code Standards
- Line length: 100 characters
- Type hints required (Python 3.8+ compatible)
- Docstrings for public APIs
- No unnecessary comments

---

# FEP (Feature Enhancement Proposal) System

## Overview
Systematic addition of introspection capabilities (`to_dict()` methods) across all major object types for AI analysis and debugging.

## Completed FEPs ✅

| FEP | Component | Status | Key Features |
|-----|-----------|--------|--------------|
| 001 | IntrospectionMixin | ✅ | Core architecture, RGBColor/Length support |
| 002 | Enum Introspection | ✅ | BaseEnum/BaseXmlEnum serialization |
| 003 | BaseShape | ✅ | Identity, geometry, safe property access |
| 004 | ColorFormat | ✅ | RGB/theme colors, brightness |
| 005 | FillFormat | ✅ | All fill types (solid, gradient, pattern, picture) |
| 006 | LineFormat | ✅ | Line styling, leverages FillFormat |
| 007 | Font | ✅ | Typography properties with smart color integration |

**Test Architecture:** Refactored from 1,952-line monolith to modular structure (84% size reduction).

### Core Architecture Pattern
```python
class IntrospectionMixin:
    def to_dict(self, include_relationships=True, max_depth=3,
                include_private=False, expand_collections=True,
                format_for_llm=True, _visited_ids=None):
        # Template method with 5 extension points:
        # 1. _to_dict_identity() - Object identification
        # 2. _to_dict_properties() - Core properties  
        # 3. _to_dict_relationships() - Object relationships
        # 4. _to_dict_llm_context() - AI-friendly descriptions
        # 5. _format_property_value_for_to_dict() - Type formatting
```

## Remaining FEPs 🚀

### High Priority
- **FEP-008:** AutoShape introspection (adjustments, text frames)
- **FEP-009:** TextFrame & Paragraph introspection
- **FEP-012:** Slide introspection (shape collections, properties)
- **FEP-013:** Presentation introspection

### Medium Priority  
- **FEP-010:** Picture & Media introspection
- **FEP-011:** Table introspection
- **FEP-014:** Enhanced LLM Context Generation
- **FEP-015:** Relationship Mapping & Inheritance
- **FEP-017:** Performance Optimization

### Low Priority
- **FEP-016:** Placeholder Format Details
- **FEP-018:** Interactive Manipulation Hints

**Progress:** 7/18 FEPs completed (38.9%)

## FEP Development Workflow

### 1. Setup
```bash
git checkout master && git pull origin master
git checkout -b fep-XXX-feature-name
source venv/bin/activate
```

### 2. Research & Implementation
```bash
# Study existing patterns
grep -r "IntrospectionMixin" src/pptx/
grep -r "target_class_name" src/pptx/

# Implement
# - Add IntrospectionMixin inheritance
# - Override _to_dict_properties()
# - Override _to_dict_llm_context() 
# - Add safe property access helpers
```

### 3. Testing Strategy

#### Modular Testing (Preferred)
```bash
# Create focused test module
tests/introspection/test_[component]_introspection.py

# Use shared utilities from mock_helpers.py
from .mock_helpers import assert_basic_to_dict_structure, MockComponent

# Run modular tests
python -m pytest tests/introspection/test_new_component.py -v
```

#### Test Categories
1. **Unit Tests:** Mock-based isolation testing
2. **Live Tests:** Real python-pptx object validation  
3. **Regression Tests:** Ensure no functionality breaks
4. **Edge Cases:** None values, errors, circular references

### 4. Code Patterns

#### Class Enhancement
```python
class TargetClass(IntrospectionMixin):
    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        return {
            "property1": self._format_property_value_for_to_dict(
                self.property1, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )
        }
```

#### Safe Property Access
```python
def _get_property_safely(self, method_name="accessing property"):
    try:
        return self.property
    except (NotImplementedError, ValueError, AttributeError):
        return None
```

#### Error Handling
```python
try:
    props["complex_property"] = self._format_property_value_for_to_dict(...)
except Exception as e:
    props["complex_property"] = self._create_error_context("complex_property", e, "access failed")
```

### 5. Critical Pitfalls to Avoid
1. **Circular Dependencies:** Use local imports in `_format_property_value_for_to_dict()`
2. **Infinite Recursion:** Always pass `max_depth - 1` to recursive calls
3. **Memory Leaks:** Use `_visited_ids` for circular reference detection
4. **Type Safety:** Check `isinstance()` before accessing type-specific attributes

## Testing Infrastructure

### Modular Test Structure ✅
```
tests/introspection/
├── mock_helpers.py          # 47 shared mock classes (503 lines)
├── test_core_mixin.py       # Core tests (8 tests)
├── test_enum_formatting.py  # Enum tests (8 tests)  
├── test_shape_introspection.py  # Shape tests (10 tests)
├── test_color_introspection.py  # Color tests (10 tests)
├── test_fill_introspection.py   # Fill tests (11 tests)
├── test_line_introspection.py   # Line tests (11 tests)
└── test_font_introspection.py   # Font tests (10 tests)
```

**Benefits:** 84% file size reduction, centralized utilities, enhanced coverage, easy extension.

### Current Test Results
- **78/78 tests passing** (38 legacy + 40 modular)
- **100% success rate**
- **Zero regressions**

### Test Commands
```bash
# All introspection tests
python -m pytest tests/introspection/ tests/test_introspection.py -v

# Specific component
python -m pytest tests/introspection/test_color_introspection.py -v

# Legacy validation
python -m pytest tests/test_introspection.py -k "enum" -v
```

## Learning Resources

### Key Files to Study
- `src/pptx/introspection.py` - Core architecture
- `src/pptx/dml/color.py` - Color implementation  
- `src/pptx/dml/fill.py` - Fill implementation
- `src/pptx/dml/line.py` - Line implementation  
- `src/pptx/text/text.py` - Font implementation
- `tests/introspection/mock_helpers.py` - Testing patterns

### Development References
- `spec/` directory - Office Open XML specifications
- **DrawingML:** Shapes, colors, fills, lines
- **PresentationML:** Slides, layouts, masters

## Status Summary

### Achievements 🎉
- **Foundation Complete:** Core introspection architecture established
- **DML Trilogy Complete:** Color, Fill, Line formatting introspection  
- **Typography Complete:** Font introspection with smart color integration
- **Test Modernization:** Modular architecture with shared utilities
- **Zero Regressions:** All existing functionality preserved

### Next Steps
1. **FEP-008:** AutoShape introspection
2. **FEP-009:** TextFrame introspection
3. **FEP-012:** Slide introspection
4. **FEP-013:** Presentation introspection

This systematic approach enables AI tools to understand and manipulate PowerPoint objects with complete transparency and rich context.