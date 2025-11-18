# Backend Test Suite

This directory contains all test scripts for the Jupyter Analysis Visualize backend.

## Running Tests

### Run a specific test
```bash
cd backend/test
python test_notebook_manager.py
```

### Run all tests (with pytest)
```bash
cd backend
python -m pytest test/
```

## Test Files

### test_notebook_manager.py
Tests for the `NotebookManager` module:
- Creating new notebooks
- Appending code and markdown cells
- Node metadata formatting and parsing
- Cell insertion at specific positions
- Notebook JSON format validation

**Run:** `python test_notebook_manager.py`

### test_project_manager.py (Planned)
Tests for the `ProjectManager` module

### test_kernel_manager.py (Planned)
Tests for the `KernelManager` module

### test_execution_manager.py (Planned)
Tests for the `ExecutionManager` module

## Test Output

Test scripts may generate temporary files:
- `test_*.ipynb` - Generated test notebooks (git-ignored)
- `test_*.parquet` - Generated test data files (git-ignored)
- `test_*.json` - Generated test artifacts (git-ignored)

These are automatically added to `.gitignore` and should be cleaned up or regenerated as needed.

## Best Practices

1. **Independence**: Each test should be self-contained
2. **Cleanup**: Tests should clean up generated files after completion
3. **Documentation**: Each test should print clear status messages
4. **Assertions**: Include validation of expected outcomes
5. **Error Handling**: Test both success and failure cases

## Guidelines

- Test files follow naming convention: `test_*.py`
- Each module should have a corresponding test file
- Tests can be run in isolation or as a suite
- No test artifacts should be committed to git
- Test code itself IS committed and tracked
