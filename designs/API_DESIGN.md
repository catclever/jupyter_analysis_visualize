# Backend API Design Document

## Overview

This document outlines the backend API design for Jupyter Analysis Visualize. The system manages data analysis projects stored as Jupyter notebooks with automatic state management and breakpoint recovery.

## Core Concepts

### Node Types

1. **Data Source Node** (`data_source`)
   - Loads external data (CSV, database, API, etc.)
   - **Must return**: `pd.DataFrame`
   - **Auto-saves**: Result as `{node_id}.parquet`
   - **Execution**: Static (discourage re-execution)
   - Example:
   ```python
   # @node_type: data_source
   # @node_id: data_1
   # @name: User Basic Information
   def load_user_data():
       return pd.read_csv('users.csv')

   data_1 = load_user_data()
   ```

2. **Compute Node** (`compute`)
   - Performs data analysis and transformations
   - **Must return**: `pd.DataFrame` (or dict-like)
   - **Auto-saves**: Result as `{node_id}.parquet`
   - **Execution**: Can depend on other compute/data nodes
   - Example:
   ```python
   # @node_type: compute
   # @node_id: compute_1
   # @depends_on: [data_1, data_2]
   # @name: Feature Analysis
   def analyze_features(data_1, data_2):
       merged = data_1.merge(data_2)
       return merged.groupby('age').agg({'violation': 'mean'})

   compute_1 = analyze_features(data_1, data_2)
   ```

3. **Chart Node** (`chart`)
   - Generates **interactive visualization** (HTML/JSON format)
   - **Must return**: Chart object (Plotly, PyEcharts, Altair, Folium, etc.)
   - **Auto-saves**:
     - HTML format: `{node_id}.html` (self-contained, directly viewable)
     - JSON format: `{node_id}.json` (for frontend rendering with Plotly.js/ECharts.js)
   - **Execution**: Depends on compute/data nodes
   - **Recommended library**: Plotly (supports both HTML and JSON export, excellent interactivity)
   - Example:
   ```python
   # @node_type: chart
   # @node_id: chart_1
   # @depends_on: [compute_1]
   # @name: Age Distribution Chart
   import plotly.graph_objects as go

   def create_age_chart(compute_1):
       """Create interactive age distribution chart"""
       fig = go.Figure(data=[
           go.Bar(x=compute_1.index, y=compute_1.values)
       ])
       fig.update_layout(
           title='Age Distribution',
           xaxis_title='Age Group',
           yaxis_title='Count',
           hovermode='x unified'
       )
       return fig

   chart_1 = create_age_chart(compute_1)
   ```

4. **Tool Node** (`tool`)
   - Defines reusable function libraries
   - **Must return**: Entry function (same name as node_id)
   - **Does NOT auto-save**: Functions stay in kernel memory
   - **Execution**: Runs once at breakpoint recovery
   - Example:
   ```python
   # @node_type: tool
   # @node_id: tool_feature_eng
   # @name: Feature Engineering Toolkit

   def polynomial_features(df):
       df['age_squared'] = df['age'] ** 2
       return df

   def create_bins(df):
       df['age_group'] = pd.cut(df['age'], bins=[0, 30, 50, 100])
       return df

   # Entry function - REQUIRED - must have same name as node_id
   def tool_feature_eng(df, operation='polynomial_features'):
       """Main entry point for feature engineering toolkit"""
       if operation == 'polynomial_features':
           return polynomial_features(df)
       elif operation == 'create_bins':
           return create_bins(df)
       else:
           raise ValueError(f"Unknown operation: {operation}")
   ```

### Project Structure

```
backend/projects/
├── data-analysis/                    # Project ID
│   ├── project.ipynb                 # Main notebook (contains all cells)
│   ├── project.json                  # Metadata: DAG, node definitions
│   ├── parquets/                     # Persistent data storage
│   │   ├── data_1.parquet            # Data source results
│   │   ├── data_2.parquet
│   │   ├── compute_1.parquet         # Compute results
│   │   ├── compute_2.parquet
│   │   ├── chart_1.json              # Chart data
│   │   └── tool_feature_eng.md       # Tool documentation
│   ├── nodes/                        # Node documentation (optional, can be in ipynb)
│   │   ├── data_1.md                 # Node description
│   │   ├── compute_1.md
│   │   └── chart_1.md
│   └── kernel_state/                 # Temporary kernel state (gitignored)
│       └── session_info.json
│
└── risk-model/
    ├── project.ipynb
    ├── project.json
    ├── parquets/
    └── nodes/
```

## Execution Model

### Breakpoint & Recovery

The system supports **breakpoint execution** with state recovery:

```
Scenario:
1. User executes compute_3 (which depends on compute_1, compute_2)
2. Compute_1 fails → execution stops, kernel state saved
3. User fixes the issue
4. User resumes execution from compute_3
   ├─ System loads project.ipynb
   ├─ Automatically executes ALL tool nodes (to restore function libraries)
   ├─ Loads parquets for data_1, data_2, compute_1, compute_2 (in memory)
   ├─ Re-executes compute_3
```

### Execution Flow

```
POST /api/projects/{project_id}/execute/{node_id}
  │
  ├─ 1. Load Project Metadata
  │     - Parse project.ipynb for node definitions
  │     - Load project.json for DAG structure
  │
  ├─ 2. Analyze Dependencies
  │     - Get all upstream dependencies of {node_id}
  │     - Check which dependencies have parquet/json files
  │
  ├─ 3. Prepare Kernel State
  │     - Get or create kernel instance for this project
  │     - Execute all TOOL nodes first (restore function libraries)
  │     - Load parquets for missing dependencies
  │
  ├─ 4. Execute Target Node
  │     - Extract cell code for {node_id}
  │     - Execute in kernel
  │     - Capture output and any errors
  │
  ├─ 5. Save Results
  │     - If data_source or compute: Save as {node_id}.parquet
  │     - If chart: Save as {node_id}.json
  │     - If tool: No save (functions already in kernel)
  │
  └─ 6. Return Response
        - status: 'completed' | 'failed'
        - data: Result (if successful)
        - error: Error message (if failed)
```

### Data Lifecycle

```
DataSource Node (data_1):
  Execute → DataFrame → Save as data_1.parquet

  Next execution of dependent node:
    Check if data_1.parquet exists
    YES → Load from disk to kernel memory (read_parquet)
    NO → Execute data_1 first

  Re-execution discouraged:
    - Data source is expensive (DB queries, API calls)
    - Results should be static and reproducible
    - If data changes, create new data_source node with version

Compute Node (compute_1):
  Depends on: [data_1, data_2]

  Load data_1, data_2 from parquets
  Execute compute_1 cell
  Automatically save as compute_1.parquet

  Re-execution discouraged (same reason as data source)
  But supported for debugging

Chart Node (chart_1):
  Create interactive visualization using Plotly/PyEcharts/etc
  Return chart object (e.g., go.Figure())

  Auto-saves TWO formats:
    - HTML: chart_1.html (self-contained, viewable in browser)
    - JSON: chart_1.json (for frontend JS library rendering)

  No re-execution recommended (like data and compute nodes)
  Results are static after first execution

Tool Node (tool_feature_eng):
  Define functions: polynomial_features(), create_bins()
  Define entry function: tool_feature_eng(df, operation='...')

  Executed on breakpoint recovery
  Functions live in kernel memory
  Can be called by other compute nodes
  No persistent storage needed
```

## API Endpoints

### Project Management

#### Get Project List
```
GET /api/projects
Response:
{
  "projects": [
    {
      "project_id": "data-analysis",
      "name": "Data Analysis",
      "description": "Risk assessment analysis",
      "created_at": "2024-11-07T10:00:00Z",
      "updated_at": "2024-11-07T14:00:00Z"
    }
  ]
}
```

#### Get Project Details
```
GET /api/projects/{project_id}
Response:
{
  "project_id": "data-analysis",
  "name": "Data Analysis",
  "description": "...",
  "nodes": [
    {
      "node_id": "data_1",
      "type": "data_source",
      "name": "User Basic Information",
      "depends_on": [],
      "status": "ready",          # ready | pending | failed
      "last_executed": "2024-11-07T14:00:00Z"
    },
    {
      "node_id": "compute_1",
      "type": "compute",
      "name": "Feature Analysis",
      "depends_on": ["data_1", "data_2"],
      "status": "ready",
      "last_executed": "2024-11-07T14:01:00Z"
    },
    {
      "node_id": "tool_feature_eng",
      "type": "tool",
      "name": "Feature Engineering Toolkit",
      "depends_on": [],
      "status": "ready",
      "last_executed": null  # Tools don't track execution
    }
  ],
  "kernel_state": {
    "status": "idle",            # idle | running | failed
    "pid": 12345,
    "uptime_seconds": 1200
  }
}
```

#### Get Node Details
```
GET /api/projects/{project_id}/nodes/{node_id}
Response:
{
  "node_id": "compute_1",
  "type": "compute",
  "name": "Feature Analysis",
  "description": "Performs cross-tabulation analysis between age and income",
  "depends_on": ["data_1", "data_2"],
  "status": "ready",
  "last_executed": "2024-11-07T14:01:00Z",
  "last_error": null,
  "cell_index": 5,
  "documentation": "# Feature Analysis\n\n..."  # From .md file or ipynb markdown cell
}
```

### Execution

#### Execute Node
```
POST /api/projects/{project_id}/execute/{node_id}
Request:
{
  "force": false,               # force re-execution even if parquet exists
  "timeout": 300                # execution timeout in seconds
}

Response (201 Created):
{
  "execution_id": "exec_20241107_14_01_23",
  "project_id": "data-analysis",
  "node_id": "compute_1",
  "status": "completed",        # completed | failed | timeout
  "started_at": "2024-11-07T14:01:23Z",
  "completed_at": "2024-11-07T14:01:45Z",
  "duration_seconds": 22,
  "result": {
    "type": "dataframe",        # dataframe | dict | list
    "shape": [12, 5],           # For DataFrames
    "rows_sample": [...]        # First few rows
  },
  "error": null
}

# If force=true and node is data_source or compute:
# Overwrites existing {node_id}.parquet
```

#### Get Node Result (Data/Compute Nodes)
```
GET /api/projects/{project_id}/nodes/{node_id}/result
Response:
{
  "node_id": "compute_1",
  "status": "ready",
  "last_executed": "2024-11-07T14:01:23Z",
  "data": {
    "type": "dataframe",
    "shape": [12, 5],
    "columns": ["age", "income", "violation_rate", ...],
    "data": [
      {"age": "25-30", "income": "8-12k", "violation_rate": 0.24, ...},
      {"age": "25-30", "income": "12-20k", "violation_rate": 0.18, ...},
      ...
    ]
  }
}
```

#### Get Chart Result
```
GET /api/projects/{project_id}/nodes/{node_id}/chart?format={format}

Query Parameters:
  format: 'html' (default) | 'json'
    - 'html': Returns self-contained HTML (can be viewed directly in browser)
    - 'json': Returns JSON data for frontend rendering with Plotly.js

Response (format='html'):
HTTP 200
Content-Type: text/html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div id="chart_1-chart" class="plotly-graph-div"></div>
    <script>
        var data = {...}
        var layout = {...}
        Plotly.newPlot('chart_1-chart', data, layout)
    </script>
</body>
</html>

Response (format='json'):
HTTP 200
Content-Type: application/json
{
  "data": [
    {
      "x": ["25-30", "31-40", "41-50", "50+"],
      "y": [1500, 2000, 1800, 1200],
      "type": "bar",
      "name": "Distribution"
    }
  ],
  "layout": {
    "title": "Age Distribution",
    "xaxis": {"title": "Age Group"},
    "yaxis": {"title": "Count"},
    "hovermode": "x unified"
  }
}
```

Frontend Usage Examples:
```typescript
// Option 1: Display HTML in iframe
<iframe
  src={`/api/projects/${projectId}/nodes/chart_1/chart?format=html`}
  width="100%"
  height="600px"
  frameborder="0"
/>

// Option 2: Render JSON with Plotly.js
const response = await fetch(`/api/projects/${projectId}/nodes/chart_1/chart?format=json`);
const data = await response.json();
Plotly.newPlot('chart-container', data.data, data.layout);

// Option 3: Render JSON with ECharts
const response = await fetch(`/api/projects/${projectId}/nodes/chart_1/chart/option?format=json`);
const option = await response.json();
const chart = echarts.init(document.getElementById('chart-container'));
chart.setOption(option);
```

### Kernel Management

#### Start Kernel (for a project)
```
POST /api/projects/{project_id}/kernel/start
Request:
{
  "memory_limit": "4GB"         # Optional
}

Response:
{
  "kernel_id": "kernel_20241107_14_00_00",
  "project_id": "data-analysis",
  "status": "running",
  "pid": 12345,
  "timestamp": "2024-11-07T14:00:00Z"
}
```

#### Stop Kernel
```
POST /api/projects/{project_id}/kernel/stop
Response:
{
  "status": "stopped",
  "kernel_id": "kernel_20241107_14_00_00"
}
```

#### Get Kernel Status
```
GET /api/projects/{project_id}/kernel/status
Response:
{
  "status": "running",          # running | idle | stopped
  "kernel_id": "kernel_20241107_14_00_00",
  "uptime_seconds": 3600,
  "memory_usage": "512MB",
  "variables": [                # Variables currently in kernel memory
    "data_1",
    "data_2",
    "compute_1",
    "tool_feature_eng"
  ]
}
```

### Recovery & Debugging

#### Get Execution Error Details
```
GET /api/projects/{project_id}/nodes/{node_id}/last_error
Response:
{
  "node_id": "compute_1",
  "error_type": "ValueError",
  "error_message": "Column 'age' not found in DataFrame",
  "traceback": "Traceback (most recent call last):\n  ...",
  "occurred_at": "2024-11-07T14:01:45Z"
}
```

#### List All Parquet Files (Project Snapshot)
```
GET /api/projects/{project_id}/parquets
Response:
{
  "parquets": [
    {
      "node_id": "data_1",
      "filename": "data_1.parquet",
      "size_bytes": 15728640,
      "rows": 285000,
      "columns": ["user_id", "age", "income", ...],
      "created_at": "2024-11-07T10:00:00Z"
    },
    {
      "node_id": "compute_1",
      "filename": "compute_1.parquet",
      "size_bytes": 5242880,
      "rows": 12,
      "columns": ["age_group", "income_group", "violation_rate"],
      "created_at": "2024-11-07T14:01:45Z"
    },
    {
      "node_id": "chart_1",
      "filename": "chart_1.json",
      "size_bytes": 81920,
      "created_at": "2024-11-07T14:02:00Z"
    }
  ]
}
```

## Project File Formats

### project.ipynb (Jupyter Notebook)

Standard Jupyter notebook with special cell metadata:

```
[
  {
    "cell_type": "markdown",
    "metadata": {},
    "source": ["# Data Analysis Project\n", "Risk assessment and feature analysis"]
  },
  {
    "cell_type": "code",
    "metadata": {"node_type": "data_source", "node_id": "data_1"},
    "source": [
      "# @node_type: data_source\n",
      "# @node_id: data_1\n",
      "# @name: User Basic Information\n",
      "def load_user_data():\n",
      "    return pd.read_csv('data/users.csv')\n",
      "\n",
      "data_1 = load_user_data()"
    ]
  },
  {
    "cell_type": "markdown",
    "metadata": {"node_description": "compute_1"},
    "source": [
      "## Feature Analysis\n",
      "Cross-tabulation analysis between age and income to identify risk segments..."
    ]
  },
  {
    "cell_type": "code",
    "metadata": {"node_type": "compute", "node_id": "compute_1"},
    "source": [
      "# @node_type: compute\n",
      "# @node_id: compute_1\n",
      "# @depends_on: [data_1, data_2]\n",
      "# @name: Feature Analysis\n",
      "def analyze_features(data_1, data_2):\n",
      "    merged = data_1.merge(data_2)\n",
      "    return merged.groupby(['age_group', 'income_group']).agg({'violation': 'mean'})\n",
      "\n",
      "compute_1 = analyze_features(data_1, data_2)"
    ]
  }
]
```

### project.json (Metadata)

```json
{
  "project_id": "data-analysis",
  "name": "Data Analysis",
  "description": "Risk assessment analysis",
  "version": "1.0.0",
  "created_at": "2024-11-07T10:00:00Z",
  "updated_at": "2024-11-07T14:00:00Z",
  "nodes": [
    {
      "node_id": "data_1",
      "type": "data_source",
      "name": "User Basic Information",
      "depends_on": [],
      "cell_index": 2,
      "status": "ready"
    },
    {
      "node_id": "data_2",
      "type": "data_source",
      "name": "Loan Application Data",
      "depends_on": [],
      "cell_index": 4,
      "status": "ready"
    },
    {
      "node_id": "compute_1",
      "type": "compute",
      "name": "Feature Analysis",
      "depends_on": ["data_1", "data_2"],
      "cell_index": 6,
      "status": "ready"
    }
  ],
  "dag": {
    "nodes": ["data_1", "data_2", "compute_1", "chart_1"],
    "edges": [
      ["data_1", "compute_1"],
      ["data_2", "compute_1"],
      ["compute_1", "chart_1"]
    ]
  }
}
```

### Node Documentation (nodes/{node_id}.md)

```markdown
# Feature Analysis (compute_1)

## Description
Cross-tabulation analysis between age and income to identify risk segments.

## Dependencies
- **data_1**: User Basic Information
- **data_2**: Loan Application Data

## Output
- **Type**: DataFrame
- **Shape**: 12 rows × 5 columns
- **Columns**: age_group, income_group, violation_rate, count, percentage

## Algorithm
1. Merge data_1 and data_2 on user_id
2. Group by (age_group, income_group)
3. Calculate mean violation rate per group
4. Sort by violation rate descending

## Key Findings
- Young + low income: 24% violation rate (highest risk)
- Middle-aged + middle income: 18% violation rate (safest segment)
- High income: <15% violation rate (protective factor)

## Last Updated
2024-11-07 14:01:45 UTC
```

## Implementation Priority

1. **Phase 1: Core Infrastructure**
   - ProjectMetadataParser (parse .ipynb, extract nodes)
   - ProjectManager (manage single project)
   - KernelManager (Jupyter kernel lifecycle)

2. **Phase 2: Execution Engine**
   - ExecutionManager (run nodes with dependencies)
   - Auto-serialization (parquet/json saving)
   - Error handling & recovery

3. **Phase 3: API Routes**
   - FastAPI endpoints (based on above)
   - WebSocket for progress tracking
   - Error responses & logging

4. **Phase 4: Enhancements**
   - Multi-project support
   - Caching & optimization
   - Advanced debugging tools

## Error Handling

### Common Errors

```
1. MissingDependencyError
   - A node depends on a result that doesn't exist
   - Solution: Execute upstream node first

2. ParquetNotFoundError
   - Data source was never executed
   - Solution: Execute data source node

3. KernelTimeoutError
   - Execution took too long
   - Solution: Increase timeout or optimize code

4. SerializationError
   - Result cannot be saved as parquet/json
   - Solution: Check return type matches node type
```

## Notes for Implementation

- Use `nbformat` library to parse .ipynb files
- Use regex to extract node metadata from cell comments
- Maintain kernel instance per project (not per execution)
- Load parquets on-demand (don't load unused dependencies)
- Tool nodes execute once on kernel start
- Discourage re-execution through documentation, but allow via `force=true`
