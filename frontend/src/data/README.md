# Data Management

This directory contains all page display data extracted from components, organized as independent data modules.

## Directory Structure

```
src/data/
├── nodes/              # Flow diagram nodes configuration
│   └── index.ts       # Node definitions, labels, and edges
├── conclusions/        # Analysis conclusions data
│   └── index.ts       # Conclusions list for left sidebar
├── requests/          # Analysis requests data
│   └── index.ts       # All analysis tasks and execution steps
├── index.ts           # Unified export hub
└── README.md          # This file
```

## Data Overview

### 1. Nodes Configuration (`nodes/index.ts`)

**Total: 13 nodes + 20 edges**

#### Data Source Nodes (3)
- `data-1`: User Basic Information (用户基本信息)
- `data-2`: Loan Application Data (贷款申请数据)
- `data-3`: Repayment History Data (还款历史数据)

#### Computation/Analysis Nodes (7)
- `compute-1`: User Characteristic Analysis (申请人特征分析)
- `compute-2`: Age-Income Cross Analysis (年龄-收入交叉分析)
- `compute-3`: Occupation Risk Analysis (职业风险分析)
- `compute-4`: Overdue Rate Statistics (逾期率统计)
- `compute-5`: Amount-Default Relationship (金额与违约关系)
- `compute-6`: First-time vs Repeat Borrower Comparison (首贷vs复贷对比)
- `compute-7`: Feature Importance Ranking (特征重要性排序)

#### Chart/Visualization Nodes (3)
- `chart-1`: Age-Income Scatter Plot (年龄-收入散点图)
- `chart-2`: Overdue Rate Trend Chart (逾期率趋势图)
- `chart-3`: Feature Importance Bar Chart (特征重要性柱状图)

### 2. Conclusions Data (`conclusions/index.ts`)

**Total: 18 conclusions** across 10 compute/chart nodes

Each conclusion includes:
- `id`: Unique identifier (e.g., "c1-1", "ch3-1")
- `conclusion`: Main insight/finding
- `nodeId`: Associated node ID
- `nodeName`: Display name of the node

### 3. Analysis Requests Data (`requests/index.ts`)

**Total: 10 analysis tasks** with **60 execution steps**

#### Data Import Requests (3)
- `req-data-1`: User Basic Information Import (5 steps)
- `req-data-2`: Loan Application Data Import (6 steps)
- `req-data-3`: Repayment History Import (5 steps)

#### Computation Requests (7)
- `req-1`: User Characteristic Distribution Analysis (5 steps)
- `req-2`: Age-Income Impact on Default Analysis (6 steps)
- `req-3`: Occupation Default Rate Statistics (6 steps)
- `req-4`: Overdue Rate Time Series Analysis (6 steps)
- `req-5`: Amount-Default Relationship Analysis (8 steps)
- `req-6`: First-time vs Repeat Borrower Comparison (8 steps)
- `req-7`: Feature Importance Ranking (7 steps)

#### Chart Generation Requests (3)
- `req-8`: Age-Income Scatter Plot Generation (7 steps)
- `req-9`: Overdue Rate Trend Chart Generation (6 steps)
- `req-10`: Feature Importance Bar Chart Generation (6 steps)

Each request includes:
- `id`: Unique identifier
- `description`: High-level task description
- `status`: "completed" | "pending" | "suggestion"
- `timestamp`: Unix timestamp of when the request was created
- `sourceNodes`: Array of input node IDs
- `outputNode`: Final output node ID
- `outputNodeLabel`: Display name of output node
- `steps`: Array of execution steps (title + detailed description)

## Usage

### Import All Data
```typescript
import {
  nodeLabels,
  nodes,
  edges,
  conclusions,
  analysisRequests,
} from '@/data';
```

### Import Specific Data Modules
```typescript
// Only nodes
import { nodes, edges, nodeLabels } from '@/data/nodes';

// Only conclusions
import { conclusions } from '@/data/conclusions';

// Only analysis requests
import { analysisRequests } from '@/data/requests';
```

### Component Integration Examples

#### In FlowDiagram Component
```typescript
import { nodes, edges } from '@/data';

// Use directly
const [nodesState, setNodesState] = useNodesState(nodes);
const [edgesState, setEdgesState] = useEdgesState(edges);
```

#### In DataSourceSidebar Component
```typescript
import { conclusions } from '@/data';

// Replace the hardcoded conclusionsData with:
const conclusionsList = conclusions;
```

#### In AnalysisSidebar Component
```typescript
import { analysisRequests, nodeLabels } from '@/data';

// Replace:
// const nodeLabels = {...}
// const analysisRequests = [...]
// With direct imports above
```

## Data Relationships

```
┌─────────────────────────────────────────────────────────┐
│                    Nodes (Flow Diagram)                 │
│  data-1, data-2, data-3                                 │
│  compute-1 through compute-7                            │
│  chart-1, chart-2, chart-3                              │
└────────────┬─────────────────────────────────────────────┘
             │
      References by:
             │
    ┌────────┴────────┬──────────────┐
    │                 │              │
    ▼                 ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ Conclusions │ │   Requests   │ │   nodeLabels │
│  (nodeId)   │ │(outputNode,  │ │ (node IDs)   │
│             │ │sourceNodes)  │ │              │
└─────────────┘ └──────────────┘ └──────────────┘
```

## Data Consistency Rules

1. **Node IDs**: Must start with 'data-', 'compute-', or 'chart-'
2. **nodeLabels Keys**: Must match node IDs exactly
3. **analysisRequests.outputNode**: Must exist in nodes
4. **analysisRequests.sourceNodes**: All items must exist in nodes
5. **conclusions.nodeId**: Must exist in nodes
6. **ConclusionItem.nodeName**: Should match nodeLabels[nodeId]

## Migration Guide

If you need to add new data or modify existing data:

1. **Add new node**:
   - Add to `nodes/index.ts` nodes array
   - Add label to `nodeLabels` object

2. **Add new conclusion**:
   - Add to `conclusions/index.ts` conclusions array
   - Reference existing node ID

3. **Add new analysis request**:
   - Add to `requests/index.ts` analysisRequests array
   - Reference valid source nodes and output node
   - Create steps array with title and description

4. **Update component imports**:
   - Replace hardcoded data arrays with imports from `@/data`
   - Update any file references to point to new data modules

## Future Enhancements

- [ ] Add support for dynamic data loading from API
- [ ] Add JSON Schema validation for data consistency
- [ ] Create data migration utilities
- [ ] Add data versioning support
- [ ] Create visualization for data relationships
