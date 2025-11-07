# Claude Code Development Guidelines

## Project Structure

### Backend Testing

All backend test scripts should be placed in the `backend/test/` directory.

**Guidelines:**
- Test files should follow the naming convention: `test_*.py`
- Each module should have corresponding test file
- Tests can be run individually or as a suite
- Generated test artifacts (`.ipynb`, `.parquet`, etc.) should be cleaned up after tests

**Current test files:**
- `backend/test/test_notebook_manager.py` - Tests for NotebookManager

**Example:**
```bash
# Run a specific test
python backend/test/test_notebook_manager.py

# Run all tests
cd backend/test && python -m pytest
```

### Directory Structure

```
jupyter_analysis_visualize/
├── frontend/                    # React application
│   ├── src/
│   ├── package.json
│   └── ...
├── backend/                     # Python backend
│   ├── notebook_manager.py      # Core modules
│   ├── kernel_manager.py        # (To be implemented)
│   ├── execution_manager.py     # (To be implemented)
│   ├── project_manager.py       # (To be implemented)
│   ├── test/                    # Test directory
│   │   ├── test_notebook_manager.py
│   │   ├── test_kernel_manager.py        # (To be created)
│   │   ├── test_execution_manager.py     # (To be created)
│   │   ├── test_project_manager.py       # (To be created)
│   │   └── README.md            # Test documentation
│   ├── requirements.txt
│   ├── API_DESIGN.md
│   └── .env.example
├── .gitignore                   # Updated to ignore backend/test outputs
└── README.md
```

### Gitignore Rules

The `.gitignore` file includes rules to ignore:
- `backend/test/test_*.ipynb` - Generated test notebooks
- `backend/test/test_*.parquet` - Generated test parquets
- `backend/test/*.json` - Generated test artifacts
- All other backend/test/* temporary files are not tracked

**Why ignore test artifacts?**
- Test notebooks and data files are temporary and can be regenerated
- They bloat the git history
- Each developer may run tests with different data
- The test scripts themselves ARE tracked (not ignored)

## Implementation Notes

### NotebookManager (Completed)
- Handles incremental cell addition to .ipynb files
- Supports all 4 node types: data_source, compute, chart, tool
- Properly formats cell metadata for parsing
- No code validation (accepts any Python code as input)

### ProjectManager (In Progress)
- Manages project directory structure
- Handles project initialization
- Manages project.json configuration
- Manages parquets storage directory

### KernelManager (Planned)
- Jupyter kernel lifecycle management
- Per-project kernel instances
- Connection pooling
- Timeout handling

### ExecutionManager (Planned)
- Execute nodes with dependency resolution
- Auto-save results to parquet/json
- Error handling and recovery
- Breakpoint support

### ProjectMetadataParser (Planned)
- Parse .ipynb cells and extract node metadata
- Build DAG from dependencies
- Validate notebook structure
- (To be integrated with frontend for debugging)

## Development Workflow

1. **Create test file**: `backend/test/test_*.py`
2. **Implement module**: `backend/*.py`
3. **Run tests**: `python backend/test/test_*.py`
4. **Clean up artifacts**: Tests should clean up generated files
5. **Commit**: Only commit the module and test code, not artifacts

## Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings for public methods
- Keep modules focused and single-responsibility

## Testing Best Practices

- Each test should be independent
- Use `setUp` and `tearDown` for cleanup
- Generate test artifacts in temporary locations when possible
- Test both success and failure cases
- Keep test output clear and descriptive
