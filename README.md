# Jupyter Analysis Visualize

A data analysis visualization platform for exploring Jupyter notebook-based analysis projects. Display project DAGs (Directed Acyclic Graphs), view node dependencies, and inspect execution results with Parquet-based result storage.

## Features

- **Project Management**: Load and switch between multiple analysis projects
- **Flow Visualization**: Interactive DAG visualization with dependency tracking
- **Result Inspection**: View and paginate through execution results (Parquet format)
- **Code & Markdown Viewing**: Display source code and markdown documentation for each analysis node
- **Execution Status Tracking**: View execution states (not_executed, pending_validation, validated)
- **Metadata Management**: System-managed metadata with automatic synchronization
- **Responsive Design**: Clean UI with ResizablePanel layout
- **Caching Strategy**: Smart project caching for optimal performance

## Current Status

### ✅ Implemented

- **Backend**:
  - FastAPI server with CORS support
  - Project and node metadata management
  - Parquet/JSON file serving with pagination
  - Code and markdown cell retrieval
  - Metadata synchronization and validation
  - Image and visualization file streaming

- **Frontend**:
  - React 18 + TypeScript with Vite
  - XYFlow-based DAG visualization
  - Interactive node selection with dependency highlighting
  - Data table with pagination
  - Project switching with caching
  - Markdown viewer for node descriptions
  - Code viewer for execution code
  - Responsive sidebar navigation

- **Notebook Format**:
  - Hybrid metadata approach: Cell metadata as source of truth
  - System-managed metadata comments with clear "understand to edit" markers
  - Automatic synchronization between Cell metadata and code comments
  - Metadata consistency validation

- **Test Data**:
  - Two complete example projects with 5 validated nodes each
  - All result files in Parquet format for uniform data handling

### 🔄 Roadmap (TODO)

#### Phase 2: Code Editing & Persistence
- [ ] Implement code editing UI in frontend
- [ ] API endpoint for saving code changes: `POST /api/projects/{projectId}/nodes/{nodeId}/save`
- [ ] Save code modifications to `.ipynb` file
- [ ] Auto-sync code comments with Cell metadata on save
- [ ] Draft state management to prevent cache pollution
- [ ] Unsaved changes warning on project switch

#### Phase 3: Execution & Result Updates
- [ ] Implement Jupyter kernel execution backend
- [ ] Execution progress tracking and status updates
- [ ] API endpoint: `POST /api/projects/{projectId}/nodes/{nodeId}/execute`
- [ ] Cache invalidation and refresh after execution
- [ ] Execution result loading from parquet/JSON
- [ ] Execution history tracking

#### Future Enhancements
- [ ] Real-time collaboration (multi-user editing)
- [ ] Version control integration for notebook changes
- [ ] Advanced filtering and search for large projects
- [ ] Performance optimization for complex DAGs
- [ ] Additional result format support (CSV, Excel, etc.)

## Architecture

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Components**: Shadcn/ui + TailwindCSS
- **Flow Visualization**: XYFlow for DAG rendering
- **State Management**: React Hooks + Custom useProjectCache hook
- **Caching**: In-memory project cache with smart loading strategy

### Backend
- **Framework**: FastAPI + Uvicorn
- **Notebook Management**: NotebookManager for incremental .ipynb operations
- **Project Management**: ProjectManager for project lifecycle
- **Data Format**: Parquet (primary), JSON (legacy, being phased to parquet)
- **Data Processing**: Pandas for DataFrame operations

## Project Structure

```
jupyter_analysis_visualize/
├── frontend/                          # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── FlowDiagram.tsx        # DAG visualization
│   │   │   ├── DataTable.tsx          # Result data display
│   │   │   ├── DataSourceSidebar.tsx  # Project selection
│   │   │   └── AnalysisSidebar.tsx    # Node details panel
│   │   ├── pages/
│   │   │   └── Index.tsx              # Main page layout
│   │   ├── hooks/
│   │   │   └── useProjectCache.ts     # Project caching logic
│   │   ├── services/
│   │   │   └── api.ts                 # API client
│   │   ├── data/                      # Hardcoded fallback data
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── .env.local                     # Frontend API configuration
│
├── backend/                           # Python backend
│   ├── app.py                         # FastAPI application
│   ├── notebook_manager.py            # .ipynb file operations
│   ├── project_manager.py             # Project management
│   ├── metadata_parser.py             # Metadata extraction
│   ├── test/
│   │   ├── generate_test_projects.py  # Test data generator
│   │   └── test_*.py                  # Unit tests
│   ├── requirements.txt
│   └── .env.example
│
├── projects/                          # Project data directory
│   ├── test_user_behavior_analysis/   # Example project 1
│   │   ├── project.ipynb              # Jupyter notebook
│   │   ├── project.json               # Project metadata
│   │   ├── parquets/                  # Result files
│   │   ├── nodes/                     # Node definitions
│   │   └── visualizations/            # Chart images
│   └── test_sales_performance_report/ # Example project 2
│       └── [same structure]
│
├── reports/                           # Documentation
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── NOTEBOOK_MANAGER_OPTIMIZATION.md
│   ├── METADATA_STORAGE_EVALUATION.md
│   ├── CACHING_STRATEGY.md
│   └── CHANGES.txt
│
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies using uv (faster) or pip
uv pip install -r requirements.txt
# OR: pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
# Server will run on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure API endpoint (update if backend is on different address)
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
# App will run on http://localhost:5173
```

### Verify Setup

1. Open http://localhost:5173 in your browser
2. You should see the flow diagram and two test projects:
   - **User Behavior Analysis**: 5 nodes showing data processing workflow
   - **Sales Performance Report**: 5 nodes showing sales analysis workflow
3. Click on any node to view its data, code, and markdown description

## API Endpoints

### Project Management
- `GET /api/projects` - List all available projects
- `GET /api/projects/{project_id}` - Get project metadata with DAG structure

### Node Data Access
- `GET /api/projects/{project_id}/nodes/{node_id}/data?page=1&page_size=10` - Get paginated node data (Parquet)
- `GET /api/projects/{project_id}/nodes/{node_id}/code` - Get node's execution code
- `GET /api/projects/{project_id}/nodes/{node_id}/markdown` - Get node's markdown description
- `GET /api/projects/{project_id}/nodes/{node_id}/image` - Stream image files
- `GET /api/projects/{project_id}/nodes/{node_id}/visualization` - Stream visualization files

### Health Check
- `GET /api/health` - Backend health status

## Data Storage Format

### Parquet Files
- **Format**: Apache Parquet (.parquet)
- **Usage**: DataFrame results from data processing nodes
- **Compression**: ~10:1 ratio
- **Benefits**: Columnar storage, efficient pagination, schema preservation
- **Location**: `projects/{project_id}/parquets/`

### JSON Files (Legacy)
- **Format**: JSON (.json)
- **Usage**: Statistics, metadata (being migrated to Parquet)
- **Location**: `projects/{project_id}/parquets/`

### Visualization Files
- **Format**: PNG images (.png)
- **Usage**: Chart and graph visualizations
- **Location**: `projects/{project_id}/visualizations/`

## Metadata Management

### System-Managed Metadata
The system uses a hybrid metadata approach:

```python
# Cell metadata (JSON, in .ipynb file)
{
  "node_type": "data_source",
  "node_id": "load_user_data",
  "execution_status": "validated",
  "depends_on": ["other_node_id"],
  "name": "Load User Data"
}

# Code comments (auto-generated, reflects Cell metadata)
# ===== System-managed metadata (auto-generated, understand to edit) =====
# @node_type: data_source
# @node_id: load_user_data
# @execution_status: validated
# @depends_on: [other_node_id]
# @name: Load User Data
# ===== End of system-managed metadata =====
```

### Key Principles
- **Cell metadata is the source of truth**: Always store primary metadata in Cell metadata
- **Code comments are for visibility**: Auto-generated from Cell metadata, users can see at a glance
- **Automatic synchronization**: System keeps comments synced with metadata
- **Safe for editing**: Code is editable without breaking metadata management

## Development Guide

### Adding Test Data

Generate new test projects:
```bash
cd backend
uv run python test/generate_test_projects.py
```

This creates two example projects with realistic data and analysis workflows.

### Understanding the Caching Strategy

The frontend implements smart project caching:

1. **First load**: Fetch project from backend, store in cache
2. **Project switch**: Check cache first, use cached data if available
3. **Editing phase** (future): Maintain Draft state separately from cache
4. **Save operation** (future): Update cache after successful save
5. **Execution** (future): Update cache with new execution results

See `frontend/CACHING_STRATEGY.md` for detailed design documentation.

### Metadata Validation

Validate metadata consistency in notebooks:
```bash
cd backend
uv run python -c "
from notebook_manager import NotebookManager
manager = NotebookManager('path/to/project.ipynb')
result = manager.validate_metadata_consistency()
print(f'Valid: {result[\"valid\"]}')
"
```

### Code Examples

#### Load and inspect a project
```python
from project_manager import ProjectManager

pm = ProjectManager('projects', 'test_user_behavior_analysis')
pm.load()

# View all nodes
for node in pm.metadata.nodes.values():
    print(f"{node['node_id']}: {node['name']}")
    print(f"  Type: {node['type']}")
    print(f"  Dependencies: {node['depends_on']}")
```

#### Validate metadata
```python
from notebook_manager import NotebookManager

manager = NotebookManager('projects/test_user_behavior_analysis/project.ipynb')
result = manager.validate_metadata_consistency()

if result['valid']:
    print("✅ All metadata is consistent")
else:
    print("❌ Metadata inconsistencies found:")
    for error in result['errors']:
        print(f"  - {error}")
```

## Configuration

### Frontend Configuration
Create `frontend/.env.local`:
```
VITE_API_BASE_URL=http://localhost:8000
```

### Backend Configuration
Create `backend/.env` (copy from `.env.example`):
```
API_HOST=0.0.0.0
API_PORT=8000
```

## Troubleshooting

### Frontend can't connect to backend
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check `VITE_API_BASE_URL` in `frontend/.env.local`
3. Check CORS configuration in `backend/app.py`

### Projects not showing up
1. Verify `projects/` directory exists with test projects
2. Check project structure: `projects/test_*/project.json` should exist
3. Run test data generator: `uv run python test/generate_test_projects.py`

### Port already in use
- **Backend**: Change API_PORT in `.env` or use different port in uvicorn command
- **Frontend**: `npm run dev -- --port 3001`

### Parquet file errors
1. Ensure pandas and pyarrow are installed: `uv pip install pandas pyarrow`
2. Verify file integrity: `python -c "import pandas as pd; pd.read_parquet('file.parquet')"`

## Technologies Used

### Frontend Stack
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **TailwindCSS**: Styling
- **shadcn/ui**: Component library
- **XYFlow**: DAG visualization library
- **Recharts**: Chart rendering

### Backend Stack
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pandas**: Data processing
- **PyArrow**: Parquet support
- **Python 3.9+**: Runtime

## Contributing

### Code Style
- Frontend: ESLint + Prettier configuration
- Backend: Follow PEP 8 standards
- Commit messages should be descriptive

### Testing
```bash
# Backend tests
cd backend
uv run pytest test/

# Frontend tests (planned)
cd frontend
npm run test
```

## Documentation

- [Metadata Storage Evaluation](reports/METADATA_STORAGE_EVALUATION.md) - Design decision documentation
- [Caching Strategy](frontend/CACHING_STRATEGY.md) - Frontend caching architecture
- [Optimization Summary](reports/OPTIMIZATION_SUMMARY.md) - Project optimization details
- [Changes Log](reports/CHANGES.txt) - Detailed change history

## License

MIT

## Contact

For questions or issues, please open a GitHub issue.
