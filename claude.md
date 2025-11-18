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
- `backend/test/test_project_manager.py` - Tests for ProjectManager (✅ Implemented)
- `backend/test/test_kernel_manager.py` - Tests for KernelManager (✅ Implemented)
- `backend/test/test_execution_manager.py` - Tests for ExecutionManager (✅ Implemented)
- `backend/test/test_metadata_parser.py` - Tests for ProjectMetadataParser (✅ Implemented)

**Running Tests with `uv`:**
```bash
# Navigate to backend directory
cd backend

# Run a specific test
uv run python test/test_notebook_manager.py
uv run python test/test_project_manager.py

# Run all tests
uv run python -m pytest test/
```

Note: All tests are executed using `uv run` to ensure consistent dependency management and Python version usage.

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

### NotebookManager (✅ Completed)
- Handles incremental cell addition to .ipynb files
- Supports all 4 node types: data_source, compute, chart, tool
- Properly formats cell metadata for parsing
- No code validation (accepts any Python code as input)

### ProjectManager (✅ Completed)
- Manages project directory structure
- Handles project initialization and loading
- Manages project.json configuration with DAG metadata
- Manages parquets storage directory for results
- Supports both DataFrame (parquet) and dict (JSON) result serialization
- Auto-detects result format based on data type

### KernelManager (✅ Completed)
- Jupyter kernel lifecycle management
- Per-project kernel instances (one kernel per project)
- Code execution with timeout handling
- Variable inspection and listing
- Idle kernel cleanup with configurable timeouts
- Connection lifecycle management

### ExecutionManager (✅ Completed)
- Execute nodes with dependency resolution (DAG-based topological sort)
- Auto-save results to parquet/json
- Error handling and recovery
- Breakpoint support with tool node recovery
- Execution progress tracking and summary generation
- Skip existing results to avoid re-execution

### ProjectMetadataParser (✅ Completed)
- Parse .ipynb cells and extract node metadata from comments
- Build DAG from dependencies with topological ordering
- Validate notebook structure and detect circular dependencies
- Node information retrieval and filtering by type
- (Ready for frontend integration for debugging)

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

## Backend Module Implementation Status

### ✅ Phase 1 Complete - Core Backend Infrastructure

**5 Backend Modules Fully Implemented and Tested:**

1. **NotebookManager** (`notebook_manager.py`)
   - Manages Jupyter notebook files (.ipynb)
   - Incremental cell addition for all node types
   - Metadata extraction and storage in cell comments
   - Functions: `append_code_cell()`, `append_markdown_cell()`, `insert_code_cell()`, `list_node_cells()`

2. **ProjectManager** (`project_manager.py`)
   - Manages project directory structure and lifecycle
   - Project metadata persistence (project.json with DAG)
   - Result file management (parquet/JSON auto-detection)
   - Functions: `create()`, `load()`, `add_node()`, `save_node_result()`, `load_node_result()`, `get_project_info()`

3. **KernelManager** (`kernel_manager.py`)
   - Manages Jupyter kernel instances per project
   - Code execution with timeout handling
   - Variable inspection and listing
   - Idle kernel cleanup with configurable timeouts
   - Functions: `get_or_create_kernel()`, `execute_code()`, `get_variable()`, `list_variables()`, `shutdown_kernel()`

4. **ExecutionManager** (`execution_manager.py`)
   - DAG-based node execution with dependency resolution
   - Topological sorting for safe execution order
   - Result auto-saving (parquet/JSON)
   - Breakpoint recovery with tool node restoration
   - Output type inference using node type system
   - Functions: `execute_node()`, `execute_project()`, `execute_with_breakpoint()`, `infer_output_type()`, `get_execution_summary()`

5. **ProjectMetadataParser** (`metadata_parser.py`)
   - Parses notebook structure and extracts node metadata
   - Builds and validates DAG structure
   - Detects circular dependencies and duplicate nodes
   - Functions: `parse()`, `get_dependency_order()`, `get_node_info()`, `get_nodes_by_type()`

### Test Coverage: 35+ Test Cases

All modules have comprehensive test suites in `backend/test/`:
- Dependency resolution and DAG operations
- Code execution and variable persistence
- File I/O and result serialization
- Error handling and edge cases
- Resource cleanup and lifecycle management

### ✅ Phase 2 Complete - Node Type System

**Node Type System** (`backend/node_types/`)
- Standardized, extensible architecture for node types
- Three core node types implemented: DataSourceNode, ComputeNode, ChartNode
- Automatic output type inference from execution results
- Type safety and constraint validation per node type
- Extensible registry pattern for adding new node types

**System Components:**
1. **base.py**: Abstract BaseNode class
   - `validate_inputs()`: Validate input data matches node requirements
   - `infer_output()`: Determine output type and display type
   - `NodeOutput`: Dataclass with output_type and display_type
   - `NodeMetadata`: Dataclass for node information

2. **registry.py**: Node type registration and factory
   - `NodeTypeRegistry`: Central registry for all node types
   - `@register_node_type`: Decorator for automatic registration
   - `get_node_type()`: Retrieve node class by type name
   - Auto-registration of built-in types on import

3. **Concrete Node Types:**
   - **data_source.py**: DataSourceNode
     - No dependencies, must output DataFrame
     - Can be depended on by any node type
     - Output: dataframe → table

   - **compute.py**: ComputeNode
     - Must have dependencies, requires DataFrame inputs
     - Must output DataFrame (no dict/list)
     - Can depend on other compute or data source nodes
     - Output: dataframe → table

   - **chart.py**: ChartNode
     - Can depend on any node type
     - Outputs Plotly Figure or ECharts config
     - Typically leaf node (not depended on)
     - Output: plotly/echarts → plotly_chart/echarts_chart

**Test Coverage:**
- Unit tests in `backend/test/test_node_system.py`
- 5/5 tests passing:
  ✓ Node type registration and discovery
  ✓ DataSourceNode instantiation and validation
  ✓ ComputeNode instantiation and validation
  ✓ ChartNode instantiation and validation
  ✓ ExecutionManager integration

**Updated Test Data:**
- Both test projects (test_sales_performance_report, test_user_behavior_analysis) updated to v2.0.0
- All nodes include standardized output metadata
- Proper dependencies defined (visualization nodes depend on compute/data nodes)
- Clean relative paths for result files

### Ready for Next Phase

Frontend integration can now proceed with:
- API endpoints returning output type information
- WebSocket support for real-time execution updates
- Integration with React + XYFlow frontend for DAG visualization
- Frontend components for displaying different output types

---

## Documentation Organization Rules

### File Placement Guidelines

#### 1. Reports Directory (`reports/`)
Local analysis documents (not tracked in git):
- **Analysis documents**: Design analysis, architecture analysis, comparative studies
- **Documentation**: Technical guides, implementation details, API references
- **Reports**: Summary reports, optimization reports, feature overviews
- **Reference materials**: Quick reference guides, cheat sheets

**Note**: These are local reference materials generated during development. Use for:
- Understanding the current system
- Sharing knowledge within the team
- Documenting findings and analysis

**Examples:**
- `reports/NODE_DESIGN_ANALYSIS.md` - Analysis of node types and design
- `reports/ARCHITECTURE_OVERVIEW.md` - High-level architecture analysis
- `reports/OPTIMIZATION_SUMMARY.md` - Optimization findings and summaries

#### 2. Designs Directory (`designs/`)
New design proposals (tracked in git):
- **Design proposals**: New features, architectural changes
- **Implementation plans**: How to build new functionality
- **RFCs**: Request for Comments on design decisions
- **Specifications**: Detailed specs for upcoming features

**Note**: These are important architectural decisions and should be committed to git for team review and historical reference.

**Examples:**
- `designs/EXECUTION_ENGINE_REDESIGN.md` - Proposal for redesigning execution
- `designs/NEW_NODE_TYPE_PROPOSAL.md` - Proposal for adding new node types
- `designs/FRONTEND_CACHING_PLAN.md` - Implementation plan for caching

#### 3. Key Distinction
- **`reports/`**:
  - Analysis of EXISTING design (retrospective, explanatory)
  - Local only (not tracked in git)
  - For reference and knowledge sharing

- **`designs/`**:
  - Plans for NEW design (prospective, prescriptive)
  - Tracked in git
  - For team discussion and decision records

**Rule of thumb:**
- If you're explaining what currently exists → `reports/` (local)
- If you're proposing what should be built → `designs/` (git-tracked)

---

## Design Evolution and Cleanup Rules

### Rule 1: Design Optimization and File Management
When optimizing designs through new files:
1. **Create new design files** as needed to refine and improve proposals
2. **Delete or modify obsolete files** that are no longer applicable
3. **Consolidate learnings** from multiple iterations into final design documents
4. **Avoid accumulation** of outdated design proposals

**Rationale**: Design directories should reflect the current state of thinking, not historical iterations. Old designs create confusion and maintenance burden.

### Rule 2: Design Cleanup After Implementation
When implementing features from design documents:
1. **After development is complete**, delete the corresponding design file(s)
2. **Move relevant documentation** to `reports/` if it documents the implemented feature
3. **Keep only designs** that are:
   - Under discussion or review
   - Planned but not yet implemented
   - Awaiting approval before development starts

**Rationale**: Once a design is implemented, it becomes part of the actual codebase (code is the truth). The design document served its purpose and should be archived or removed to keep the designs directory clean.

**Examples:**
- Create: `designs/NODE_STANDARDIZATION_PLAN.md` → Implementation starts
- During: Multiple iterations and refinements of the design
- After: Implementation complete → Delete `designs/NODE_STANDARDIZATION_PLAN.md`
- Document: Move relevant implementation notes to `reports/NODE_STANDARDIZATION_IMPLEMENTATION.md` if needed for future reference

---

## Documentation Policy: No Analysis Reports for Modifications

### Rule: Code Changes Should Be Documented in Git Commits, Not Reports

**Policy:**
All modifications, optimizations, bug fixes, and improvements should be documented through **git commit messages** rather than creating analysis or report documents.

**Guidelines:**
1. **Every change gets a commit message**, not a report file
   - Use clear, descriptive commit messages that explain what changed and why
   - Follow conventional commit format if applicable (feat:, fix:, refactor:, etc.)
   - Include context and rationale in the commit message body

2. **reports/ directory usage**
   - Only use `reports/` for ongoing reference materials
   - Examples: API documentation, architecture guides, quick references
   - Do NOT create change logs, analysis reports, or summary documents for modifications
   - Analysis documents are temporary working notes (not tracked in git)

3. **git history is the source of truth**
   - Git commits preserve all modification history
   - Commit messages provide context and rationale
   - No need to duplicate this information in report files
   - Developers can use `git log` to understand what changed and why

**Benefits:**
- Single source of truth (git history)
- Reduced file clutter in `reports/`
- More maintainable documentation
- Better traceability of changes

**Example:**
❌ **Bad**: Create `reports/OPTIMIZATION_SUMMARY_2025_11_18.md`
✅ **Good**: Create commit `fix: optimize kernel variable checking performance`

With detailed message:
```
fix: optimize kernel variable checking performance

- Reduced list_variables() calls by caching results per execution
- Improved response time from 500ms to 100ms for large projects
- Updated test_kernel_manager.py to verify optimizations
```

---

## Documentation Generation Policy

### Rule: No Automatic Generation of Manuals or Documentation

**Policy:**
Do NOT automatically generate, create, or write documentation files (manuals, guides, reference docs, etc.) unless explicitly requested by the user.

**Guidelines:**
1. **Default behavior: No documentation generation**
   - Do not create `.md` files for features unless asked
   - Do not generate API documentation unless requested
   - Do not write guides or tutorials proactively
   - Do not create README files or change logs automatically

2. **When documentation IS explicitly requested**
   - Create only what was specifically asked for
   - Place files in appropriate directories per other rules
   - Document the current state of the system accurately
   - Keep documentation focused and concise

3. **What counts as "explicit request"**
   - User: "Create a README for this feature"
   - User: "Write API documentation"
   - User: "Generate a guide for X"
   - User: "Document this module"

4. **What does NOT count**
   - User asks to implement a feature (code only)
   - User asks to fix a bug (just fix the code)
   - User asks to optimize something (no report/doc)
   - User asks to refactor code (no analysis doc)

**Rationale:**
- Documentation generation wastes time and adds unnecessary files
- Code is self-documenting when clear and well-commented
- Git history preserves all changes and context
- Unnecessary files clutter the repository
- Users know what documentation they actually need
