/**
 * API Service Layer
 *
 * Provides typed API calls to backend endpoints.
 * Uses environment variable VITE_API_BASE_URL for API base URL.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ============ Types ============

export interface Project {
  id: string;
  name: string;
  description: string;
  version: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectNode {
  id: string;
  label: string;
  type: 'data_source' | 'compute' | 'chart' | 'image' | 'tool' | 'data';
  execution_status: 'not_executed' | 'pending_validation' | 'validated';
  result_format?: string;
  result_path?: string;
  result_is_dict?: boolean;
  output?: unknown;
  error_message?: string | null;
  last_execution_time?: string | null;
  position?: { x: number; y: number } | null;
}

export interface ProjectEdge {
  id: string;
  source: string;
  target: string;
  animated: boolean;
}

export interface ProjectDetail {
  id: string;
  name: string;
  description: string;
  version: string;
  created_at: string;
  updated_at: string;
  nodes: ProjectNode[];
  edges: ProjectEdge[];
}

export interface PaginatedData<T> {
  node_id: string;
  format: 'parquet' | 'json' | 'image' | 'visualization' | 'pkl';
  total_records: number;
  page: number;
  page_size: number;
  total_pages: number;
  columns?: string[];
  data: T;
}

export interface ParquetData {
  [key: string]: string | number | boolean | null;
}

export interface JsonData {
  [key: string]: unknown;
}

// ============ API Calls ============

/**
 * Get health status
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * List all projects
 */
export async function listProjects(): Promise<Project[]> {
  const response = await fetch(`${API_BASE_URL}/api/projects`);
  if (!response.ok) {
    throw new Error(`Failed to fetch projects: ${response.statusText}`);
  }
  const data = await response.json();
  return data.projects || [];
}

/**
 * Get project details including DAG
 */
export async function getProject(projectId: string, noCache: boolean = true): Promise<ProjectDetail> {
  // Add timestamp to prevent browser caching when noCache is true
  const url = noCache
    ? `${API_BASE_URL}/api/projects/${projectId}?t=${Date.now()}`
    : `${API_BASE_URL}/api/projects/${projectId}`;

  const response = await fetch(url, {
    headers: noCache ? {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache'
    } : {}
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch project ${projectId}: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get node data with pagination
 */
export async function getNodeData<T = unknown>(
  projectId: string,
  nodeId: string,
  page: number = 1,
  pageSize: number = 10
): Promise<PaginatedData<T>> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/data?${params}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch node data: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get dict of DataFrames result for a node
 */
export interface DictResult {
  keys: string[];
  tables: Record<string, Array<Record<string, unknown>>>;
}

export async function getDictResult(
  projectId: string,
  nodeId: string
): Promise<DictResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/dict-result`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch dict result: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get image file URL for a node
 */
export function getImageUrl(projectId: string, nodeId: string): string {
  return `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/image`;
}

/**
 * Get visualization file URL for a node
 */
export function getVisualizationUrl(projectId: string, nodeId: string): string {
  return `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/visualization`;
}

/**
 * Get file URL based on format
 */
export function getFileUrl(
  projectId: string,
  nodeId: string,
  format: string
): string {
  if (format === 'image') {
    return getImageUrl(projectId, nodeId);
  } else if (format === 'visualization') {
    return getVisualizationUrl(projectId, nodeId);
  }
  throw new Error(`Unsupported format: ${format}`);
}

/**
 * Get node code from notebook
 */
export async function getNodeCode(
  projectId: string,
  nodeId: string
): Promise<{ node_id: string; code: string; language: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/code`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch node code: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get node markdown summary from notebook
 */
export async function getNodeMarkdown(
  projectId: string,
  nodeId: string
): Promise<{ node_id: string; markdown: string; format: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/markdown`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch node markdown: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update node markdown content in notebook
 */
export async function updateNodeMarkdown(
  projectId: string,
  nodeId: string,
  markdown: string
): Promise<{ node_id: string; markdown: string; format: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/markdown`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ markdown }),
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to update node markdown: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update node position in flow diagram
 */
export async function updateNodePosition(
  projectId: string,
  nodeId: string,
  position: { x: number; y: number }
): Promise<{ node_id: string; position: { x: number; y: number }; status: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/position`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ position }),
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to update node position: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update node code in notebook
 */
export async function updateNodeCode(
  projectId: string,
  nodeId: string,
  code: string
): Promise<{ node_id: string; code: string; language: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/code`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code }),
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to update node code: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get dependency information for a node
 */
export async function getNodeDependencies(
  projectId: string,
  nodeId: string
): Promise<{
  node_id: string;
  direct_dependencies: string[];
  all_dependencies: string[];
  execution_order: string[];
  dependents: string[];
  has_circular_dependency: boolean;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/dependencies`
  );
  if (!response.ok) {
    throw new Error(`Failed to get dependencies: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get execution plan for a node
 */
export async function getExecutionPlan(
  projectId: string,
  nodeId: string,
  alreadyExecuted: string[] = []
): Promise<{
  target_node: string;
  execution_order: string[];
  nodes_to_execute: string[];
  already_executed: string[];
  will_skip: number;
  will_execute: number;
}> {
  const params = new URLSearchParams();
  if (alreadyExecuted.length > 0) {
    params.append('already_executed', alreadyExecuted.join(','));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/execution-plan?${params}`
  );
  if (!response.ok) {
    throw new Error(`Failed to get execution plan: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Execute a node with dependency resolution and dynamic edge discovery
 */
export async function executeNode(
  projectId: string,
  nodeId: string
): Promise<{
  node_id: string;
  status: 'success' | 'pending_validation' | 'error';
  error_message: string | null;
  execution_time: number | null;
  result_cell_added: boolean;
  // Dynamic dependency system additions
  executed_nodes: string[];
  new_edges: ProjectEdge[];
  execution_plan: {
    execution_order: string[];
    nodes_to_execute: string[];
    already_executed: string[];
    will_execute: number;
    will_skip: number;
  };
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/execute`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to execute node: ${response.statusText}`);
  }
  return response.json();
}
