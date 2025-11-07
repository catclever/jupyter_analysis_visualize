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
- `backend/test/test_notebook_manager.py` - Tests for NotebookManager (✅ Implemented)
- `backend/test/test_project_manager.py` - Tests for ProjectManager (📋 Planned)
- `backend/test/test_kernel_manager.py` - Tests for KernelManager (📋 Planned)
- `backend/test/test_execution_manager.py` - Tests for ExecutionManager (📋 Planned)

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
│   ├── project_manager.py       # (To be implemented)
│   ├── kernel_manager.py        # (To be implemented)
│   ├── execution_manager.py     # (To be implemented)
│   ├── toolkits/                # Optional: Complex/reusable tool libraries
│   │   ├── __init__.py
│   │   ├── data_analysis/       # Toolkit modules for 'data-analysis' project
│   │   │   ├── feature_engineering.py   # Entry: feature_engineering(df, operation=...)
│   │   │   ├── preprocessing.py         # Entry: preprocessing(df, operation=...)
│   │   │   └── __init__.py
│   │   └── risk_model/          # Toolkit modules for 'risk-model' project (example)
│   │       └── ...
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

### toolkits/ Directory (Optional Reusable Tool Libraries)
Contains complex, reusable analysis function libraries organized by project:
- **Purpose**: Store TOOL NODE implementations as external modules
- **Organization**: One subdirectory per project (e.g., `data_analysis/`, `risk_model/`)
- **Format**: Each Python file follows the TOOL NODE pattern:
  - Must include helper functions
  - Must have ONE entry function with the same name as the module
  - Entry function acts as the tool's main interface

**Directory Structure:**
```
backend/toolkits/
├── data_analysis/
│   ├── feature_engineering.py      # Entry: feature_engineering(df, operation=...)
│   ├── preprocessing.py             # Entry: preprocessing(df, operation=...)
│   └── visualization_tools.py       # Entry: visualization_tools(data, operation=...)
└── risk_model/
    ├── risk_metrics.py              # Entry: risk_metrics(df, operation=...)
    └── model_utils.py               # Entry: model_utils(data, operation=...)
```

**Example toolkit file format:**
```python
# backend/toolkits/data_analysis/feature_engineering.py

# Helper functions (private/internal)
def _polynomial_features(df):
    """Internal helper"""
    df_copy = df.copy()
    df_copy['age_squared'] = df_copy['age'] ** 2
    return df_copy

def _create_bins(df):
    """Internal helper"""
    df_copy = df.copy()
    df_copy['age_group'] = pd.cut(df_copy['age'], bins=[0, 30, 50, 100])
    return df_copy

# Entry function (REQUIRED - name must match module name)
def feature_engineering(df, operation='polynomial_features', **kwargs):
    """
    Feature engineering toolkit entry point

    Args:
        df: Input DataFrame
        operation: Which operation to perform
        **kwargs: Additional arguments for the operation

    Returns:
        Processed DataFrame
    """
    if operation == 'polynomial_features':
        return _polynomial_features(df)
    elif operation == 'create_bins':
        return _create_bins(df)
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

**Recommended approach: HYBRID**

**Simple functions** → Write directly in notebook (most common):
```python
# In project.ipynb
# @node_type: data_source
# @node_id: data_1
def load_user_data():
    return pd.read_csv('data.csv')

data_1 = load_user_data()

# @node_type: compute
# @node_id: compute_1
def analyze_features(df):
    return df.groupby('age').mean()

compute_1 = analyze_features(data_1)
```

**Complex/reusable tools** → External toolkit modules:
```python
# In project.ipynb - Tool node that uses external toolkit
# @node_type: tool
# @node_id: tool_feature_eng
from toolkits.data_analysis.feature_engineering import feature_engineering

# feature_engineering is now available in kernel
# Can call: feature_engineering(df, operation='polynomial_features')
```

**Philosophy:**
- Notebook contains all DATA + COMPUTE + CHART node logic (direct implementation)
- TOOL nodes can import from toolkits/ for complex, reusable operations
- Keep notebook focused and readable
- Most projects won't need toolkits/ at all (functions defined directly in notebook)

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
