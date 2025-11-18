/**
 * Node Type Configuration
 *
 * This file defines all supported node types and their visual properties.
 * Maps backend node types to frontend display categories and styling.
 */

/**
 * Node categories for grouping in the UI
 * These are the 4 main categories shown in the flow diagram
 */
export enum NodeCategory {
  SOURCE = 'source',      // 源 - data_source nodes
  DATA = 'data',          // 数据 - compute nodes that output DataFrames
  VISUALIZATION = 'visualization',  // 图表/图像 - chart and image nodes
  TOOL = 'tool'           // 工具 - tool nodes
}

/**
 * Node types (matching backend definitions)
 */
export enum NodeType {
  DATA_SOURCE = 'data_source',
  COMPUTE = 'compute',
  CHART = 'chart',
  IMAGE = 'image',
  TOOL = 'tool'
}

/**
 * Output types (matching backend OutputType enum)
 */
export enum OutputType {
  DATAFRAME = 'dataframe',
  DICT_LIST = 'dict_list',
  PLOTLY = 'plotly',
  ECHARTS = 'echarts',
  IMAGE = 'image',
  FUNCTION = 'function',
  UNKNOWN = 'unknown'
}

/**
 * Display types (matching backend DisplayType enum)
 */
export enum DisplayType {
  TABLE = 'table',
  JSON_VIEWER = 'json_viewer',
  PLOTLY_CHART = 'plotly_chart',
  ECHARTS_CHART = 'echarts_chart',
  IMAGE_VIEWER = 'image_viewer',
  NONE = 'none'
}

/**
 * Result formats (matching backend ResultFormat enum)
 */
export enum ResultFormat {
  PARQUET = 'parquet',
  JSON = 'json',
  IMAGE = 'image',
  PKL = 'pkl',
  NONE = 'none'
}

/**
 * Configuration for each node type
 */
interface NodeTypeConfig {
  type: NodeType;
  category: NodeCategory;
  color: string;           // Hex color for node display
  label: string;           // Chinese label for the category
  icon?: string;           // Optional icon
  description: string;     // Human-readable description
}

/**
 * Node type configurations
 * Define visual properties and categorization for each node type
 */
export const NODE_TYPE_CONFIG: Record<NodeType, NodeTypeConfig> = {
  [NodeType.DATA_SOURCE]: {
    type: NodeType.DATA_SOURCE,
    category: NodeCategory.SOURCE,
    color: '#8db4cc',       // Deeper blue
    label: '源',
    description: 'Data source node - loads external data'
  },
  [NodeType.COMPUTE]: {
    type: NodeType.COMPUTE,
    category: NodeCategory.DATA,
    color: '#b390c8',       // Deeper purple
    label: '数据',
    description: 'Compute node - transforms data'
  },
  [NodeType.CHART]: {
    type: NodeType.CHART,
    category: NodeCategory.VISUALIZATION,
    color: '#c4ad8a',       // Deeper tan
    label: '图表',
    description: 'Chart node - creates interactive visualizations'
  },
  [NodeType.IMAGE]: {
    type: NodeType.IMAGE,
    category: NodeCategory.VISUALIZATION,
    color: '#c4ad8a',       // Same as chart - same category
    label: '图表',
    description: 'Image node - creates static image visualizations'
  },
  [NodeType.TOOL]: {
    type: NodeType.TOOL,
    category: NodeCategory.TOOL,
    color: '#8ec0b0',       // Deeper teal
    label: '工具',
    description: 'Tool node - applies specialized analysis tools'
  }
};

/**
 * Get configuration for a node type
 */
export function getNodeTypeConfig(nodeType: NodeType | string): NodeTypeConfig | null {
  return NODE_TYPE_CONFIG[nodeType as NodeType] || null;
}

/**
 * Get color for a node type
 */
export function getNodeColor(nodeType: NodeType | string): string {
  const config = getNodeTypeConfig(nodeType);
  return config?.color || '#cccccc';  // Default gray if unknown
}

/**
 * Get category for a node type
 */
export function getNodeCategory(nodeType: NodeType | string): NodeCategory | null {
  const config = getNodeTypeConfig(nodeType);
  return config?.category || null;
}

/**
 * Get category label (Chinese name)
 */
export function getCategoryLabel(category: NodeCategory): string {
  const config = Object.values(NODE_TYPE_CONFIG).find(c => c.category === category);
  return config?.label || category;
}

/**
 * Grouping nodes by category for layout
 */
export interface CategoryLayout {
  category: NodeCategory;
  label: string;
  color: string;
  nodeTypes: NodeType[];
  x: number;           // Base x position for this category
  columnCount?: number; // Number of columns for grid layout
  spacing: number;     // Spacing between nodes
}

/**
 * Define layout for each category in the flow diagram
 */
export const CATEGORY_LAYOUTS: Record<NodeCategory, CategoryLayout> = {
  [NodeCategory.SOURCE]: {
    category: NodeCategory.SOURCE,
    label: '源',
    color: '#8db4cc',
    nodeTypes: [NodeType.DATA_SOURCE],
    x: 0,
    spacing: 120,
  },
  [NodeCategory.DATA]: {
    category: NodeCategory.DATA,
    label: '数据',
    color: '#b390c8',
    nodeTypes: [NodeType.COMPUTE],
    x: 300,
    columnCount: 3,
    spacing: 300,
  },
  [NodeCategory.VISUALIZATION]: {
    category: NodeCategory.VISUALIZATION,
    label: '图表',
    color: '#c4ad8a',
    nodeTypes: [NodeType.CHART, NodeType.IMAGE],
    x: 900,
    columnCount: 2,
    spacing: 300,
  },
  [NodeCategory.TOOL]: {
    category: NodeCategory.TOOL,
    label: '工具',
    color: '#8ec0b0',
    nodeTypes: [NodeType.TOOL],
    x: 1500,
    columnCount: 2,
    spacing: 300,
  }
};
