# Live Test Scripts for FEP Introspection

This directory contains live validation scripts for Feature Enhancement Proposals (FEPs) that test actual python-pptx introspection functionality with real presentations.

## Purpose

Live tests complement unit tests by:
- Testing with real PowerPoint files and objects
- Validating end-to-end introspection workflows  
- Providing executable examples for engineers
- Ensuring introspection methods work in practice

## Test Organization

### Core Introspection Tests
- `live_test_run_introspection.py` - Text run introspection (FEP-009)
- `live_test_paragraph_introspection.py` - Paragraph introspection (FEP-010)  
- `live_test_textframe_introspection.py` - Text frame introspection (FEP-011)

### Container Tests
- `live_test_slide_introspection.py` - Slide introspection (FEP-012)
- `live_test_presentation_introspection.py` - Presentation introspection (FEP-013)

### Shape Tests  
- `live_test_placeholder_introspection.py` - Placeholder introspection (FEP-014)
- `live_test_picture_introspection.py` - Picture/Image introspection (FEP-015)

### Layout Tests
- `live_test_layout_introspection.py` - Layout introspection (FEP-016)
- `live_test_master_introspection.py` - Master introspection (FEP-017)

### Table Tests
- `live_test_table_introspection.py` - Table introspection (FEP-018)

### Advanced Features
- `live_test_precision_inspection.py` - Precision inspection controls (FEP-019)
- `live_test_tree_functionality.py` - Tree view functionality (FEP-020)

## Running Live Tests

### Individual Tests
```bash
source venv/bin/activate
python tests/introspection/live_tests/live_test_[component]_introspection.py
```

### All Tests
```bash
source venv/bin/activate
for test in tests/introspection/live_tests/live_test_*.py; do
    echo "Running $test..."
    python "$test"
done
```

## Test Results

Historical test results are preserved in `live_test_results*.txt` files for validation and regression tracking.

## Notes

- These tests use real PowerPoint files from `features/steps/test_files/`
- Tests output detailed introspection results for manual validation
- Some tests may require specific test files to be present
- Results help validate that introspection methods work with diverse content types