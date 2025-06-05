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

# Linting for specific files only (PREFERRED for PRs)
ruff check --fix src/pptx/text/text.py && ruff format src/pptx/text/text.py

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
| 009 | _Run | ✅ | Text content, font, hyperlink introspection |
| 010 | _Paragraph | ✅ | Text content, formatting, runs collection, spacing |
| 011 | TextFrame | ✅ | Text container, paragraphs, margins, formatting defaults |

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
- **FEP-012:** Slide introspection (shape collections, properties)
- **FEP-013:** Presentation introspection

### Medium Priority  
- **FEP-014:** Picture & Media introspection
- **FEP-015:** Table introspection
- **FEP-016:** Enhanced LLM Context Generation
- **FEP-017:** Relationship Mapping & Inheritance
- **FEP-018:** Performance Optimization

### Low Priority
- **FEP-019:** Placeholder Format Details
- **FEP-020:** Interactive Manipulation Hints

**Progress:** 10/19 FEPs completed (52.6%)

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

#### Testing Best Practices & Learnings
- **Complex Property Dependencies:** When properties have interdependencies (e.g., `text` depends on `paragraphs`), mocking can become complex
- **Skip When Appropriate:** Use `@unittest.skip()` with clear explanations for difficult-to-mock scenarios that are covered by live tests
- **PropertyMock Usage:** Use `unittest.mock.PropertyMock` for read-only properties: `patch.object(type(obj), 'prop', new_callable=PropertyMock)`
- **Live Test Validation:** Always include comprehensive live test scripts for real-world validation when unit tests are limited

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
5. **Linting Scope:** Only run ruff on files you modified, not entire repo (`ruff check file.py` not `ruff check src/`)
6. **Staging Discipline:** Only stage files directly related to your FEP (`git add specific_files` not `git add .`)
7. **Live Testing:** Always include live test scripts in PRs for engineer validation

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
├── test_font_introspection.py   # Font tests (10 tests)
├── test_run_introspection.py    # Run tests (15 tests)
├── test_paragraph_introspection.py # Paragraph tests (20 tests)
└── test_textframe_introspection.py # TextFrame tests (17 tests + 7 skipped)
```

**Benefits:** 84% file size reduction, centralized utilities, enhanced coverage, easy extension.

### Current Test Results
- **138/138 tests passing** (10 modular modules + legacy coverage)
- **121 passed, 12 skipped (7 in TextFrame), 5 skipped (autoshape)** 
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

### 6. PR Best Practices

#### Essential PR Components
1. **Live Test Script:** Always include executable validation script for engineers
2. **Comprehensive Description:** Feature summary, implementation details, test results  
3. **Clear Instructions:** Step-by-step testing commands for reviewers
4. **Staged Changes:** Only commit files directly related to your FEP
5. **Test Evidence:** Include test pass/fail counts and any pre-existing failures
6. **Live Test Results:** Add live test execution results as PR comments for validation
7. **Use GitHub CLI:** Prefer `gh` commands over other methods (e.g., `gh issue view` vs WebFetch) 

#### PR Description Template
```markdown
## Summary
Brief description of FEP implementation and key features.

## Test Plan
### For Reviewers
```bash
# Commands for engineers to validate
```

### Expected Results
- Test counts and expected outcomes
- Notes on any pre-existing failures
```

## Learning Resources

### Key Files to Study (Don't eagerly read as they could be very big only read when needed)
- `src/pptx/introspection.py` - Core architecture
- `src/pptx/dml/color.py` - Color implementation  
- `src/pptx/dml/fill.py` - Fill implementation
- `src/pptx/dml/line.py` - Line implementation  
- `src/pptx/text/text.py` - Font implementation
- `tests/introspection/mock_helpers.py` - Testing patterns

### Development References (again huge XMLs so don't eagerly read)
- `spec/` directory - Office Open XML specifications
- **DrawingML:** Shapes, colors, fills, lines
- **PresentationML:** Slides, layouts, masters

## Status Summary

### Achievements 🎉
- **Foundation Complete:** Core introspection architecture established
- **DML Trilogy Complete:** Color, Fill, Line formatting introspection  
- **Typography Complete:** Font and paragraph introspection with smart relationships
- **Text Hierarchy Complete:** Run, paragraph, and text frame introspection with collection management
- **Container Introspection:** TextFrame introspection with margins, formatting, and paragraph collections
- **Test Modernization:** Modular architecture with shared utilities and testing best practices
- **Zero Regressions:** All existing functionality preserved

### Next Steps
1. **FEP-008:** AutoShape introspection
2. **FEP-012:** Slide introspection
3. **FEP-013:** Presentation introspection

This systematic approach enables AI tools to understand and manipulate PowerPoint objects with complete transparency and rich context.


BACKGROUND ON FEPs:
"Feature Enhancement Proposals" (FEPs). Each FEP will aim to be a reasonably sized Pull Request (PR).

Overall Goal for This Series of FEPs:
To progressively add comprehensive introspection capabilities (a to_dict()-like method) to key python-pptx objects, making them more "transparent" and easier for both developers and future LLM-based tools to understand and manipulate.

Guiding Principles for FEPs:

Incremental: Each FEP should be a manageable chunk of work.
Practical Value: Each FEP should deliver a tangible improvement in introspection for specific object types.
Builds Foundation: Early FEPs should lay groundwork for later, more complex ones.
Testable: Each FEP must include corresponding unit tests.
Non-Breaking: Changes should add functionality without altering existing public APIs or behavior (unless explicitly fixing a bug).
List of Proposed Feature Enhancement Proposals (FEPs) for Introspection:

(Ordered roughly by foundational nature and increasing complexity/dependencies)

FEP-001: Basic Introspection Mixin & RGBColor.to_dict()
Goal: Introduce the core IntrospectionMixin (or similar mechanism) and implement to_dict() for a simple value object.
FEP-002: Length.to_dict() and Enum Introspection Helper
Goal: Provide structured dictionary output for Length objects and a utility for representing enum members.
FEP-003: BaseShape.to_dict() - Identity & Basic Geometry
Goal: Implement to_dict() on BaseShape to expose fundamental shape identity (ID, name, type) and geometry (left, top, width, height, rotation).
FEP-004: ColorFormat.to_dict()
Goal: Provide detailed dictionary output for ColorFormat objects, showing type, RGB, theme color, and brightness.
FEP-005: FillFormat.to_dict()
Goal: Implement to_dict() for FillFormat, showing fill type and recursively calling to_dict() for relevant color/gradient/pattern details.
FEP-006: LineFormat.to_dict()
Goal: Implement to_dict() for LineFormat, showing line fill (color), width, and dash style.
FEP-007: Font.to_dict() (Core Attributes)
Goal: Implement to_dict() for Font, exposing name, size, bold, italic, underline, and color (recursively).
FEP-008: Shape.to_dict() (AutoShape Specifics)
Goal: Extend BaseShape.to_dict() for Shape (AutoShapes) to include auto_shape_type, adjustments, and a summary of text_frame (if present, recursive call).
FEP-009: _Run.to_dict()
Goal: Implement to_dict() for _Run, showing text content and its font.to_dict().
FEP-010: _Paragraph.to_dict()
Goal: Implement to_dict() for _Paragraph, showing its runs (collection, recursive), alignment, level, and spacing properties.
FEP-011: TextFrame.to_dict()
Goal: Implement to_dict() for TextFrame, showing its paragraphs (collection, recursive), margins, vertical anchor, word wrap, and auto-size settings.
FEP-012: Slide.to_dict() (Basic Info & Shapes Summary)
Goal: Implement to_dict() for Slide, showing slide_id, name, a reference to its slide_layout (summarized), and a list of its shapes (summarized identities initially).
FEP-013: Presentation.to_dict() (Basic Info & Slides Summary)
Goal: Implement to_dict() for Presentation, showing core properties (summarized), slide dimensions, and a list of its slides (summarized identities).
FEP-014: Enhancing Collection Expansion in to_dict()
Goal: Refine how collections (slides, shapes, paragraphs, runs) are expanded based on max_depth and expand_collections parameters.
FEP-015: PlaceholderFormat.to_dict() and Shape.to_dict() Placeholder Details
Goal: Add detailed placeholder information (idx, type) to Shape.to_dict() when is_placeholder is true.
FEP-016: Relationship Extraction in to_dict() (Basic Parent/Child)
Goal: Implement basic _extract_relationships for key objects like Slide, Shape to show their immediate container and direct children.
FEP-017: Inheritance Tracing for Key Properties (e.g., Font, Position)
Goal: Add the "source" of a property (direct, layout, master, theme) to the to_dict() output for critical properties. This is more advanced.
FEP-018: _generate_llm_context() for Key Objects
Goal: Start implementing natural language descriptions and common operations for Slide and Shape.
This list is a roadmap. The order can be adjusted, and some FEPs might be combined or further broken down. The key is to make each PR a logical, testable unit.