import { useState, useCallback } from 'react';
import type { Edge } from '@xyflow/react';
import {
  getNodeDependencies,
  getExecutionPlan,
  executeNode
} from '@/services/api';

export interface DependencyInfo {
  node_id: string;
  direct_dependencies: string[];
  all_dependencies: string[];
  execution_order: string[];
  dependents: string[];
  has_circular_dependency: boolean;
}

export interface ExecutionPlan {
  target_node: string;
  execution_order: string[];
  nodes_to_execute: string[];
  already_executed: string[];
  will_skip: number;
  will_execute: number;
}

export interface ExecutionResult {
  node_id: string;
  status: string;
  error_message?: string;
  execution_time: number;
  executed_nodes: string[];
  new_edges: Edge[];
  execution_plan: ExecutionPlan;
}

/**
 * Hook for managing node dependencies and execution
 *
 * Provides:
 * - Getting dependency information for nodes
 * - Getting execution plans before execution
 * - Executing nodes with automatic dependency handling
 * - Tracking execution state
 */
export function useDependencyManager(projectId: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dependencyInfo, setDependencyInfo] = useState<DependencyInfo | null>(null);
  const [executionPlan, setExecutionPlan] = useState<ExecutionPlan | null>(null);
  const [executedNodes, setExecutedNodes] = useState<Set<string>>(new Set());

  // Get dependency information for a node
  const getDependencies = useCallback(
    async (nodeId: string): Promise<DependencyInfo | null> => {
      try {
        setLoading(true);
        setError(null);

        const info = await getNodeDependencies(projectId, nodeId);
        setDependencyInfo(info);

        console.log('[useDependencyManager] Got dependencies for', nodeId, ':', info);

        return info;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to get dependencies';
        setError(errorMsg);
        console.error('[useDependencyManager] Error getting dependencies:', err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [projectId]
  );

  // Get execution plan for a node
  const getPlan = useCallback(
    async (nodeId: string): Promise<ExecutionPlan | null> => {
      try {
        setLoading(true);
        setError(null);

        // Include already-executed nodes in the query
        const alreadyExecuted = Array.from(executedNodes);
        const plan = await getExecutionPlan(projectId, nodeId, alreadyExecuted);
        setExecutionPlan(plan);

        console.log('[useDependencyManager] Got execution plan for', nodeId, ':', plan);
        console.log('  - Will execute:', plan.will_execute, 'nodes');
        console.log('  - Will skip:', plan.will_skip, 'nodes');

        return plan;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to get execution plan';
        setError(errorMsg);
        console.error('[useDependencyManager] Error getting execution plan:', err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [projectId, executedNodes]
  );

  // Execute a node with dependency handling
  const execute = useCallback(
    async (nodeId: string): Promise<ExecutionResult | null> => {
      try {
        setLoading(true);
        setError(null);

        console.log('[useDependencyManager] Executing node:', nodeId);

        const result = await executeNode(projectId, nodeId);

        console.log('[useDependencyManager] Execution result:', result);
        console.log('  - Executed nodes:', result.executed_nodes);
        console.log('  - New edges:', result.new_edges.length);

        // Update executed nodes
        const newExecutedNodes = new Set(executedNodes);
        result.executed_nodes.forEach(n => newExecutedNodes.add(n));
        setExecutedNodes(newExecutedNodes);

        return result;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to execute node';
        setError(errorMsg);
        console.error('[useDependencyManager] Error executing node:', err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [projectId, executedNodes]
  );

  // Clear execution state
  const reset = useCallback(() => {
    setExecutedNodes(new Set());
    setDependencyInfo(null);
    setExecutionPlan(null);
    setError(null);
  }, []);

  return {
    loading,
    error,
    dependencyInfo,
    executionPlan,
    executedNodes,
    getDependencies,
    getPlan,
    execute,
    reset,
  };
}
