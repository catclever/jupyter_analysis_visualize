# Jupyter Analysis Visualize

A data analysis visualization platform powered by Jupyter Kernel backend with Parquet-based result storage.

## Architecture

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Components**: Shadcn/ui + TailwindCSS
- **Flow Visualization**: XYFlow

### Backend
- **Runtime**: Jupyter Kernel
- **API**: FastAPI + Uvicorn
- **Data Storage**: Parquet + JSON
- **Data Processing**: Pandas

## Project Structure

```
jupyter_analysis_visualize/
├── src/                    # React application
│   ├── components/
│   ├── pages/
│   ├── data/
│   ├── hooks/
│   ├── lib/
│   ├── App.tsx
│   └── main.tsx
├── backend/                # Python backend
│   ├── kernel_manager.py   # Jupyter Kernel lifecycle management
│   ├── execution_manager.py # Execution and storage orchestration
│   ├── serializer.py       # Parquet/JSON serialization
│   ├── api.py              # FastAPI routes
│   ├── node_functions/     # Analysis node implementations
│   ├── executions/         # Runtime data storage (gitignored)
│   ├── requirements.txt
│   └── .env.example
├── package.json
├── vite.config.ts
├── .gitignore
└── README.md
```

## Features

- **DAG-based Analysis**: Define data processing as directed acyclic graphs
- **Persistent Execution**: All results automatically saved to Parquet/JSON
- **Execution History**: Full audit trail of all analyses
- **Reload Capability**: Restore any previous execution environment
- **Real-time Progress**: WebSocket-based execution progress tracking

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Jupyter installed (or via requirements.txt)

### Backend Setup

```bash
# Install Python dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed

# Start backend server
python api.py
# Server runs on http://localhost:8000
```

### Frontend Setup

```bash
# Install Node dependencies
npm install

# Start development server
npm run dev
# App runs on http://localhost:5173 or http://localhost:3000
```

## API Endpoints

### Core Execution
- `POST /api/execute/{node_id}` - Execute an analysis node
- `GET /api/execution/{execution_id}/node/{node_id}` - Get node result
- `POST /api/reload/{execution_id}` - Reload execution to Kernel

### WebSocket
- `WS /ws/execution/{execution_id}` - Real-time progress tracking

## Data Storage Format

### DataFrame Results
- **Format**: Parquet (.parquet)
- **Compression**: ~10:1 ratio
- **Features**: Partial column reads, cross-language support

### Dictionary/List Results
- **Format**: JSON (.json)
- **Usage**: Graph data, statistics, metadata

## Development

### Adding New Analysis Nodes

1. Implement in `backend/node_functions/compute_nodes.py`:
```python
def analyze_feature(data: pd.DataFrame) -> pd.DataFrame:
    """Your analysis logic"""
    return result
```

2. Register route in `backend/api.py`
3. Update frontend DAG configuration

### Supported Result Types
- `pd.DataFrame` → Auto-saved as Parquet
- `dict` / `list` → Auto-saved as JSON
- Mixed types → Each saved with appropriate format

## Configuration

See `backend/.env.example` for all available options.

## Troubleshooting

### Jupyter Issues
```bash
pip install jupyter
jupyter kernelspec list
```

### Port Already in Use
- Backend: Change `API_PORT` in .env
- Frontend: `npm run dev -- --port 3001`

### CORS Errors
- Update `CORS_ORIGINS` in `backend/.env`

## Technologies Used

**Frontend:**
- Vite
- React 18
- TypeScript
- TailwindCSS
- shadcn-ui
- XYFlow

**Backend:**
- FastAPI
- Jupyter Kernel
- Pandas
- PyArrow (Parquet)
