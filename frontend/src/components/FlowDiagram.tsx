import React, { useEffect, useState, useRef } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  ConnectionMode,
  ReactFlowInstance,
  NodeProps,
  Handle,
  Position,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Eye, EyeOff, Layout } from 'lucide-react';
import { getProject, updateNodePosition, autoLayoutNodes, type ProjectNode, type ProjectEdge } from '@/services/api';
import {
  getNodeColor,
  getNodeCategory,
  getNodeTypeConfig,
  NodeType,
  NodeCategory,
  CATEGORY_LAYOUTS
} from '@/config';

interface FlowNodeData extends Record<string, unknown> {
  label: string;
  type: string;
  phase?: string;
  executionStatus?: string;  // 'validated' | 'pending_validation' | 'not_executed'
  errorMessage?: string;     // Error message if status is pending_validation
  isVisible?: boolean;       // Visibility toggle for eye icon
  onVisibilityToggle?: (nodeId: string) => void;  // Callback for visibility toggle
  onNodeDelete?: (nodeId: string) => void;  // Callback for node deletion
}

// Custom node component with eye icon
function NodeWithEyeIcon({ id, data }: NodeProps<FlowNodeData>) {
  const handleVisibilityToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    data.onVisibilityToggle?.(id);
  };

  const isVisible = data.isVisible ?? true;

  return (
    <div className="relative w-full h-full">
      <Handle position={Position.Left} type="target" />
      <div className="relative px-4 py-3">
        <p className="text-sm font-medium text-center whitespace-nowrap">{data.label}</p>

        {/* Bottom left: Eye icon, very small, as node attachment */}
        <div className="absolute bottom-0 left-0">
          <button
            onClick={handleVisibilityToggle}
            className="p-0 rounded hover:bg-black/10 transition-colors"
            title={isVisible ? '隐藏节点' : '显示节点'}
            style={{
              background: isVisible ? 'transparent' : 'rgba(0,0,0,0.05)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {isVisible ? (
              <Eye className="h-2 w-2 text-foreground/60" />
            ) : (
              <EyeOff className="h-2 w-2 text-foreground/30" />
            )}
          </button>
        </div>
      </div>

      <Handle position={Position.Right} type="source" />
    </div>
  );
}

interface FlowDiagramProps {
  onNodeClick: (nodeId: string) => void;
  selectedNodeId: string | null;
  minimapOpen?: boolean;
  currentDatasetId?: string;
  onEdgesAdded?: (edges: any[]) => void;  // Callback when edges are dynamically added
}

export function FlowDiagram({ onNodeClick, selectedNodeId, minimapOpen = true, currentDatasetId = "ecommerce_analytics", onEdgesAdded }: FlowDiagramProps) {
  const reactFlowRef = useRef<ReactFlowInstance | null>(null);
  const TOOL_NODE_GAP = 20;
  const LAYER_GAP = 50;

  const adjustToolRowSpacing = React.useCallback(async () => {
    const instance = reactFlowRef.current;
    if (!instance) return;
    const rendered = instance.getNodes();
    const toolNodes = rendered.filter((n) => {
      const d = n.data as FlowNodeData;
      return d && (d.type === NodeType.TOOL || d.type === 'tool');
    });
    if (toolNodes.length === 0) return;
    toolNodes.sort((a, b) => (a.position.x - b.position.x));
    const updates = new Map<string, { x: number; y: number }>();
    const getNodeWidth = (id: string, fallback: number) => {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`) as HTMLElement | null;
      const domWidth = el?.offsetWidth ?? fallback ?? 0;
      return domWidth;
    };
    let prevRight = toolNodes[0].position.x + getNodeWidth(toolNodes[0].id, toolNodes[0].width || 0);
    updates.set(toolNodes[0].id, { x: toolNodes[0].position.x, y: toolNodes[0].position.y });
    for (let i = 1; i < toolNodes.length; i++) {
      const n = toolNodes[i];
      const newLeft = prevRight + TOOL_NODE_GAP;
      updates.set(n.id, { x: newLeft, y: n.position.y });
      prevRight = newLeft + getNodeWidth(n.id, n.width || 0);
    }
    setNodes((nds) => nds.map((node) => {
      const u = updates.get(node.id);
      if (u) {
        const p = { x: u.x, y: u.y };
        return { ...node, position: p, positionAbsolute: p };
      }
      return node;
    }));
    const payloads = Array.from(updates.entries());
    for (const [id, pos] of payloads) {
      try {
        await updateNodePosition(currentDatasetId as string, id, pos);
      } catch (e) {
        console.warn('[FlowDiagram] Failed to persist tool node position', id, e);
      }
    }
    instance.fitView({ includeHiddenNodes: true, padding: 0.2 });
  }, [reactFlowRef, currentDatasetId]);

  const adjustLayerSpacing = React.useCallback(async () => {
    const instance = reactFlowRef.current;
    if (!instance) return;
    const rendered = instance.getNodes();
    const toolIds = new Set(
      rendered
        .filter((n) => {
          const d = n.data as FlowNodeData;
          return d && (d.type === NodeType.TOOL || d.type === 'tool');
        })
        .map((n) => n.id)
    );

    const domWidth = (id: string, fallback: number) => {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`) as HTMLElement | null;
      return (el?.offsetWidth ?? fallback ?? 0);
    };

    const nonTool = rendered.filter((n) => !toolIds.has(n.id));

    const parentsMap = new Map<string, Set<string>>();
    const rfEdges = (instance as any).getEdges ? (instance as any).getEdges() : [];
    rfEdges.forEach((e: any) => {
      if (toolIds.has(e.source) || toolIds.has(e.target)) return;
      if (!parentsMap.has(e.target)) parentsMap.set(e.target, new Set());
      parentsMap.get(e.target)!.add(e.source);
      if (!parentsMap.has(e.source)) parentsMap.set(e.source, new Set());
    });

    const layerOf = new Map<string, number>();
    const calcLayer = (id: string): number => {
      if (layerOf.has(id)) return layerOf.get(id)!;
      const ps = Array.from(parentsMap.get(id) || []);
      if (ps.length === 0) {
        layerOf.set(id, 0);
        return 0;
      }
      const l = Math.max(...ps.map(calcLayer)) + 1;
      layerOf.set(id, l);
      return l;
    };
    nonTool.forEach((n) => calcLayer(n.id));

    const byLayer = new Map<number, typeof nonTool>();
    nonTool.forEach((n) => {
      const l = layerOf.get(n.id) || 0;
      if (!byLayer.has(l)) byLayer.set(l, [] as any);
      (byLayer.get(l) as any).push(n);
    });

    const sortedLayers = Array.from(byLayer.keys()).sort((a, b) => a - b);
    if (sortedLayers.length === 0) return;

    const updates = new Map<string, { x: number; y: number }>();
    // Compute right edge of each layer and reposition next layer
    // Keep layer 0 left as-is
    let prevLayerRight = Math.max(
      ...((byLayer.get(sortedLayers[0]) || []) as any).map((n: any) => n.position.x + domWidth(n.id, n.width || 0))
    );
    const layerLeft = new Map<number, number>();
    sortedLayers.forEach((l) => {
      const group = byLayer.get(l)!;
      const left = Math.min(...group.map((n) => n.position.x));
      layerLeft.set(l, left);
    });

    for (let i = 1; i < sortedLayers.length; i++) {
      const l = sortedLayers[i];
      const group = byLayer.get(l)!;
      const origLeft = layerLeft.get(l)!;
      const newLeft = prevLayerRight + LAYER_GAP;
      group.forEach((n) => {
        const shift = n.position.x - origLeft;
        updates.set(n.id, { x: newLeft + shift, y: n.position.y });
      });
      prevLayerRight = Math.max(...group.map((n) => (newLeft + (n.position.x - origLeft) + domWidth(n.id, n.width || 0))));
    }

    if (updates.size === 0) return;
    setNodes((nds) => nds.map((node) => {
      const u = updates.get(node.id);
      if (u) {
        const p = { x: u.x, y: u.y };
        return { ...node, position: p, positionAbsolute: p };
      }
      return node;
    }));
    const payloads = Array.from(updates.entries());
    for (const [id, pos] of payloads) {
      try {
        await updateNodePosition(currentDatasetId as string, id, pos);
      } catch (e) {
        console.warn('[FlowDiagram] Failed to persist layer node position', id, e);
      }
    }
    instance.fitView({ includeHiddenNodes: true, padding: 0.2 });
  }, [reactFlowRef, currentDatasetId]);
  const [apiNodes, setApiNodes] = useState<Node<FlowNodeData>[] | null>(null);
  const [apiEdges, setApiEdges] = useState<Edge[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Store debounce timeouts for node position updates (per node)
  const positionUpdateTimeoutsRef = useRef<Record<string, NodeJS.Timeout>>({});

  // Cleanup timeouts on component unmount
  useEffect(() => {
    const timeoutsRef = positionUpdateTimeoutsRef.current;
    return () => {
      Object.values(timeoutsRef).forEach(timeoutId => {
        clearTimeout(timeoutId);
      });
    };
  }, []);

  // 从 API 获取项目数据
  useEffect(() => {
    const fetchProjectData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Use currentDatasetId directly - no mapping needed as we now load projects dynamically
        // Always bypass cache to get latest project metadata
        const project = await getProject(currentDatasetId, true);
        console.log('[FlowDiagram] Loaded project:', project);
        console.log('[FlowDiagram] Nodes count:', project.nodes.length);
        console.log('[FlowDiagram] Sample node:', project.nodes[0]);

        // 转换 API 数据为 ReactFlow 格式，计算节点位置
        // 首先按类别分组节点
        const nodesByCategory = new Map<string, ProjectNode[]>();
        const categoryIndices = new Map<string, number>();

        project.nodes.forEach((node: ProjectNode) => {
          const category = getNodeCategory(node.type);
          console.log(`[FlowDiagram] Node ${node.id}: type=${node.type}, category=${category}`);
          if (!category) {
            console.warn(`[FlowDiagram] Node ${node.id} has no category!`);
            return;
          }

          if (!nodesByCategory.has(category)) {
            nodesByCategory.set(category, []);
            categoryIndices.set(category, 0);
          }
          nodesByCategory.get(category)!.push(node);
        });

        const flowNodes: Node<FlowNodeData>[] = project.nodes.map((node: ProjectNode) => {
          const category = getNodeCategory(node.type);
          if (!category) {
            return {
              id: node.id,
              type: 'default',
              position: { x: 0, y: 0 },
              data: {
                label: node.label,
                type: node.type,
                isVisible: true,
              },
              className: `flow-node-${node.type}`,
              selectable: true,
            };
          }

          // 如果节点有保存的位置，使用保存的位置；否则根据布局规则计算
          let position: { x: number; y: number };
          if (node.position && node.position.x !== undefined && node.position.y !== undefined) {
            position = node.position;
            console.log(`[FlowDiagram] Node ${node.id} using saved position:`, position);
          } else {
            const layout = CATEGORY_LAYOUTS[category];
            const categoryNodes = nodesByCategory.get(category) || [];
            const nodeIndexInCategory = categoryNodes.findIndex(n => n.id === node.id);

            // 计算位置
            let x = layout.x;
            let y = nodeIndexInCategory * layout.spacing;

            // 如果有列数限制，则使用网格布局
            if (layout.columnCount) {
              const row = Math.floor(nodeIndexInCategory / layout.columnCount);
              const col = nodeIndexInCategory % layout.columnCount;
              x = layout.x + (col * layout.spacing);
              y = row * 250;  // 行间距为250
            }

            position = { x, y };
            console.log(`[FlowDiagram] Node ${node.id} using calculated position:`, position);
          }

          return {
            id: node.id,
            type: 'default',
            position: position,
            sourcePosition: Position.Right,
            targetPosition: Position.Left,
            data: {
              label: node.label,
              type: node.type,
              executionStatus: node.execution_status || 'not_executed',
              errorMessage: node.error_message || undefined,
              isVisible: true,
            },
            className: `flow-node-${node.type}`,
            selectable: true,
          };
        });

        // Use edges from API response
        // The backend already constructs edges from node.depends_on in the get_project endpoint (lines 182-188 of app.py)
        // When a node is executed:
        // 1. Backend analyzes code and updates node['depends_on'] in project.json
        // 2. Frontend reloads project data via getProject()
        // 3. Backend reconstructs edges from the updated depends_on values
        // 4. Frontend receives the new edges and displays them dynamically
        const flowEdges = (project.edges || []).map((edge: ProjectEdge) => ({
          ...edge,
          markerEnd: { type: MarkerType.ArrowClosed },
          // Use a curved (smooth step) connection style for better left-right flow
          style: { strokeWidth: 2 }
        }));

        setApiNodes(flowNodes);
        setApiEdges(flowEdges);
        console.log('[FlowDiagram] Initialized with', flowNodes.length, 'nodes and', flowEdges.length, 'edges from API');
      } catch (err) {
        console.error('Failed to fetch project data:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch project data');
        // Show empty state on error instead of falling back to hardcoded data
        setApiNodes([]);
        setApiEdges([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjectData();
  }, [currentDatasetId]);

  // 获取当前数据集的nodes和edges - 优先使用API数据
  const datasetData = React.useMemo(() => {
    if (apiNodes !== null && apiEdges !== null) {
      console.log('[FlowDiagram] datasetData created with', apiNodes.length, 'nodes');
      return { nodes: apiNodes, edges: apiEdges };
    }
    // Don't fallback to hardcoded data - show empty state
    console.log('[FlowDiagram] datasetData fallback to empty');
    return { nodes: [], edges: [] };
  }, [currentDatasetId, apiNodes, apiEdges]);

  const currentNodes = datasetData.nodes || [];
  const currentEdges = datasetData.edges || [];
  console.log('[FlowDiagram] currentNodes length:', currentNodes.length);

  // Use local state for nodes and edges to avoid synchronization issues with useNodesState
  const [nodes, setNodes] = React.useState<Node<FlowNodeData>[]>([]);
  const [edges, setEdges] = React.useState<Edge[]>([]);
  const [localMinimapOpen, setLocalMinimapOpen] = React.useState(minimapOpen);
  const [nodeTypeFilter, setNodeTypeFilter] = React.useState<Set<NodeCategory | string>>(
    new Set(Object.values(NodeCategory))
  );
  const [nodeIdCounter, setNodeIdCounter] = React.useState(0);
  const [openCategoryDropdown, setOpenCategoryDropdown] = React.useState<string | null>(null);
  const [selectedNodeTypeForDrag, setSelectedNodeTypeForDrag] = React.useState<NodeType | null>(null);
  const [isAutoLayouting, setIsAutoLayouting] = React.useState(false);

  // Handle auto-layout
  const handleAutoLayout = React.useCallback(async () => {
    try {
      setIsAutoLayouting(true);
      const result = await autoLayoutNodes(currentDatasetId);
      console.log('[FlowDiagram] Auto-layout result:', result);

      // Update node positions based on the result
      setNodes((nds) =>
        nds.map((node) => {
          const newPosition = result.updated_nodes[node.id];
          if (newPosition) {
            return {
              ...node,
              position: newPosition,
              positionAbsolute: newPosition,
            };
          }
          return node;
        })
      );

      requestAnimationFrame(() => {
        void adjustToolRowSpacing().then(() => {
          requestAnimationFrame(() => { void adjustLayerSpacing(); });
        });
      });
    } catch (error) {
      console.error('[FlowDiagram] Auto-layout failed:', error);
      alert(`Auto-layout failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsAutoLayouting(false);
    }
  }, [currentDatasetId, adjustToolRowSpacing, adjustLayerSpacing]);

  // Handle node changes (including drag operations)
  const handleNodesChange = React.useCallback((changes: any) => {
    setNodes((nds) => {
      const updatedNodes = nds.slice();
      changes.forEach((change: any) => {
        const nodeIndex = updatedNodes.findIndex(n => n.id === change.id);
        if (nodeIndex !== -1) {
          if (change.type === 'position' && change.position) {
            // Update position for drag operations
            updatedNodes[nodeIndex] = {
              ...updatedNodes[nodeIndex],
              position: change.position,
              positionAbsolute: change.positionAbsolute,
            };

            // Send position update to backend with debounce per node
            const nodeId = change.id;
            const position = change.position;

            // Clear existing timeout for this node if any
            if (positionUpdateTimeoutsRef.current[nodeId]) {
              clearTimeout(positionUpdateTimeoutsRef.current[nodeId]);
            }

            // Set new timeout for this node
            positionUpdateTimeoutsRef.current[nodeId] = setTimeout(() => {
              console.log(`[FlowDiagram] Saving position for node ${nodeId}:`, position);
              updateNodePosition(currentDatasetId, nodeId, position)
                .then(() => {
                  console.log(`[FlowDiagram] Position saved for node ${nodeId}`);
                })
                .catch((error) => {
                  console.error(`[FlowDiagram] Failed to save position for node ${nodeId}:`, error);
                });

              // Clean up timeout reference
              delete positionUpdateTimeoutsRef.current[nodeId];
            }, 500); // Debounce 500ms to avoid too many requests while dragging
          } else if (change.type === 'select') {
            // Handle selection changes if needed
            updatedNodes[nodeIndex] = {
              ...updatedNodes[nodeIndex],
              selected: change.selected,
            };
          }
        }
      });
      return updatedNodes;
    });
  }, [currentDatasetId]);

  // Handle edge changes
  const handleEdgesChange = React.useCallback((changes: any) => {
    setEdges((eds) => {
      const updatedEdges = eds.slice();
      changes.forEach((change: any) => {
        const edgeIndex = updatedEdges.findIndex(e => e.id === change.id);
        if (edgeIndex !== -1) {
          if (change.type === 'select') {
            updatedEdges[edgeIndex] = {
              ...updatedEdges[edgeIndex],
              selected: change.selected,
            };
          }
        }
      });
      return updatedEdges;
    });
  }, []);

  // When currentNodes or currentEdges change, update the local state
  React.useEffect(() => {
    console.log('[FlowDiagram] useEffect updating nodes/edges, currentNodes length:', currentNodes.length);
    setNodes(currentNodes);
    setEdges(currentEdges);
  }, [currentDatasetId, currentNodes, currentEdges]);

  // 当 minimapOpen 属性改变时，同步到 localMinimapOpen
  React.useEffect(() => {
    setLocalMinimapOpen(minimapOpen);
  }, [minimapOpen]);

  // 获取某个节点的所有父节点（输入节点）- 支持多个直接父节点
  const getDirectParentNodes = (nodeId: string, allEdges: Edge[]): Set<string> => {
    const directParents = new Set<string>();
    // 找出所有以 nodeId 为 target 的边的 source 节点
    const incomingEdges = allEdges.filter(edge => edge.target === nodeId);
    incomingEdges.forEach(edge => {
      directParents.add(edge.source);
    });
    return directParents;
  };

  // 获取所有祖先节点（递归）
  const getAllAncestorNodes = (nodeId: string, allEdges: Edge[]): Set<string> => {
    const ancestors = new Set<string>();

    const findAncestors = (currentNodeId: string) => {
      const directParents = getDirectParentNodes(currentNodeId, allEdges);
      directParents.forEach(parentId => {
        if (!ancestors.has(parentId)) {
          ancestors.add(parentId);
          // 递归找父节点的父节点
          findAncestors(parentId);
        }
      });
    };

    findAncestors(nodeId);
    return ancestors;
  };

  const getNodeTypeById = (nodeId: string): string | null => {
    const n = nodes.find(n => n.id === nodeId);
    if (!n) return null;
    const d = n.data as FlowNodeData;
    return d.type || null;
  };

  const edgeKey = (e: Edge): string => (e.id || `${e.source}->${e.target}`);

  const visibility = React.useMemo(() => {
    if (!selectedNodeId) {
      return {
        nodeIds: new Set<string>(),
        edgeKeys: new Set<string>(),
      };
    }

    const selectedType = getNodeTypeById(selectedNodeId);
    const isToolSelected = selectedType === NodeType.TOOL || selectedType === 'tool';

    const nodeIds = new Set<string>();
    const edgeKeys = new Set<string>();
    nodeIds.add(selectedNodeId);

    if (isToolSelected) {
      edges.forEach(e => {
        if (e.source === selectedNodeId) {
          nodeIds.add(e.target);
          edgeKeys.add(edgeKey(e));
        }
      });
      return { nodeIds, edgeKeys };
    }

    const visited = new Set<string>();
    const stack: string[] = [selectedNodeId];
    visited.add(selectedNodeId);

    while (stack.length) {
      const current = stack.pop() as string;
      edges.forEach(e => {
        if (e.target === current) {
          const parentId = e.source;
          const parentType = getNodeTypeById(parentId);
          if (parentType && parentType !== NodeType.TOOL && parentType !== 'tool') {
            if (!visited.has(parentId)) {
              visited.add(parentId);
              nodeIds.add(parentId);
              stack.push(parentId);
            }
            edgeKeys.add(edgeKey(e));
          }
        }
      });
    }

    edges.forEach(e => {
      if (e.target === selectedNodeId) {
        const parentType = getNodeTypeById(e.source);
        if (parentType === NodeType.TOOL || parentType === 'tool') {
          nodeIds.add(e.source);
          edgeKeys.add(edgeKey(e));
        }
      }
    });

    return { nodeIds, edgeKeys };
  }, [selectedNodeId, nodes, edges]);

  const getNodeLevel = (nodeId: string): 'selected' | 'parent' | 'ancestor' | 'dimmed' => {
    if (!selectedNodeId) return 'dimmed';
    if (nodeId === selectedNodeId) return 'selected';
    return visibility.nodeIds.has(nodeId) ? 'parent' : 'dimmed';
  };

  const handleNodeClick = (_event: React.MouseEvent | any, node: Node) => {
    // 调用点击回调让父组件更新选择状态
    onNodeClick(node.id);
  };

  // Handle right-click context menu on nodes
  const handleNodeContextMenu = (event: React.MouseEvent<any>, nodeId: string) => {
    event.preventDefault();
    const confirmed = window.confirm(`确定删除节点 ${nodeId} 吗？`);
    if (confirmed) {
      handleDeleteNode(nodeId);
    }
  };

  // Handle visibility toggle for nodes
  const toggleNodeVisibility = (nodeId: string) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? {
              ...node,
              data: {
                ...(node.data as FlowNodeData),
                isVisible: !((node.data as FlowNodeData).isVisible ?? true)
              }
            }
          : node
      )
    );
  };

  // Handle drop on canvas to add new node
  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();

    try {
      // Get the node type from the drag data
      const dragData = event.dataTransfer.getData('application/json');
      if (!dragData) {
        console.warn('[FlowDiagram] No drag data found');
        return;
      }

      const data = JSON.parse(dragData);
      if (data.type !== 'add-node' || !data.nodeType) {
        console.warn('[FlowDiagram] Invalid drag data');
        return;
      }

      const nodeType = data.nodeType;
      const config = getNodeTypeConfig(nodeType);
      if (!config) {
        console.error('[FlowDiagram] No config found for node type:', nodeType);
        return;
      }

      // Generate unique node ID
      const nodeId = `${nodeType}-${Date.now()}-${nodeIdCounter}`;
      setNodeIdCounter((counter) => counter + 1);

      // Get canvas position from drop event
      const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      // Create new node
      const newNode: Node<FlowNodeData> = {
        id: nodeId,
        type: 'default',
        position: { x, y },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        data: {
          label: `${config.label} 节点`,
          type: nodeType,
          executionStatus: 'not_executed',
          isVisible: true,
        },
        className: `flow-node-${nodeType}`,
        selectable: true,
      };

      setNodes((nds) => [...nds, newNode]);
      console.log('[FlowDiagram] Added new node:', nodeId, 'at position', { x, y });
    } catch (error) {
      console.error('[FlowDiagram] Error handling drop:', error);
    }
  };

  // Handle node deletion
  const handleDeleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    if (selectedNodeId === nodeId) {
      onNodeClick('');
    }
    console.log('[FlowDiagram] Deleted node:', nodeId);
  };

  // Handle category type selection for drag
  const handleSelectNodeType = (nodeType: NodeType) => {
    setSelectedNodeTypeForDrag(selectedNodeTypeForDrag === nodeType ? null : nodeType);
    setOpenCategoryDropdown(null);
  };

  const toggleNodeTypeFilter = (type: 'data' | 'compute' | 'chart') => {
    const newFilter = new Set(nodeTypeFilter);
    if (newFilter.has(type)) {
      newFilter.delete(type);
    } else {
      newFilter.add(type);
    }
    setNodeTypeFilter(newFilter);
  };

  const shouldShowEdge = (edge: Edge): boolean => {
    if (!selectedNodeId) return true;
    return visibility.edgeKeys.has(edgeKey(edge));
  };

  // 动态添加边（在节点执行时调用）
  // 这是实现动态依赖系统的关键方法
  const addEdgesCallback = React.useCallback((newEdges: Edge[]) => {
    setEdges((prevEdges) => {
      // 避免重复添加边
      const existingIds = new Set(prevEdges.map(e => e.id));
      const uniqueNewEdges = newEdges.filter(e => !existingIds.has(e.id));

      if (uniqueNewEdges.length > 0) {
        console.log('[FlowDiagram] Adding', uniqueNewEdges.length, 'new edges');
        // 通知父组件有新边被添加
        onEdgesAdded?.(uniqueNewEdges);
        return [...prevEdges, ...uniqueNewEdges];
      }

      return prevEdges;
    });
  }, [onEdgesAdded]);

  return (
    <div className="h-full w-full bg-card rounded-lg border border-border overflow-hidden flex flex-col">
      {/* 顶部工具栏：右侧节点添加面板 */}
      <div className="flex items-center justify-end gap-3 p-3 border-b border-border bg-muted/50">
        {/* 右侧：节点添加和管理面板 */}
        <div className="flex gap-1 bg-background/50 rounded p-2 border border-border/30">
          {Object.values(CATEGORY_LAYOUTS).map((layout) => {
            const nodeTypesInCategory = layout.nodeTypes;
            const hasMultipleTypes = nodeTypesInCategory.length > 1;
            const isOpen = openCategoryDropdown === layout.category;
            // Check if any type in this category is selected
            const isAnyTypeSelected = selectedNodeTypeForDrag &&
              nodeTypesInCategory.includes(selectedNodeTypeForDrag as NodeType);

            return (
              <div key={layout.category} className="relative">
                {/* 节点类型按钮 - 可拖拽 */}
                <div className="flex items-center gap-1">
                  <button
                    draggable={nodeTypeFilter.has(layout.category)}
                    onDragStart={(e) => {
                      // Only allow drag if category is visible
                      if (!nodeTypeFilter.has(layout.category)) {
                        e.preventDefault();
                        return;
                      }

                      // Always use the first node type of this category for drag
                      const nodeTypeForDrag = layout.nodeTypes[0];

                      e.dataTransfer.effectAllowed = 'copy';
                      e.dataTransfer.setData('application/json', JSON.stringify({
                        type: 'add-node',
                        nodeType: nodeTypeForDrag,
                      }));
                    }}
                    onClick={() => {
                      if (hasMultipleTypes) {
                        setOpenCategoryDropdown(isOpen ? null : layout.category);
                      }
                    }}
                    className="px-2.5 py-1.5 rounded transition-all flex items-center gap-1.5 text-xs font-medium"
                    style={{
                      backgroundColor: isAnyTypeSelected ? layout.color + '80' : layout.color + '20',
                      border: `1px solid ${layout.color}`,
                      color: isAnyTypeSelected ? '#000000' : layout.color,
                      cursor: nodeTypeFilter.has(layout.category) ? 'grab' : 'not-allowed',
                      opacity: nodeTypeFilter.has(layout.category) ? 1 : 0.5,
                    }}
                    title={nodeTypeFilter.has(layout.category) ? `拖拽添加 ${layout.label} 节点${hasMultipleTypes ? '（点击选择具体类型）' : ''}` : `${layout.label} 节点已隐藏，点击眼睛显示`}
                  >
                    <span>{layout.label}</span>
                    {hasMultipleTypes && (
                      <span className="text-xs leading-none">▼</span>
                    )}
                  </button>

                  {/* 眼睛图标 - 隐显已添加的节点 */}
                  <button
                    onClick={() => toggleNodeTypeFilter(layout.category)}
                    className="px-1.5 py-1.5 rounded hover:bg-muted transition-all"
                    style={{
                      backgroundColor: nodeTypeFilter.has(layout.category) ? 'transparent' : 'rgba(0,0,0,0.05)',
                      border: `1px solid ${layout.color}40`,
                    }}
                    title={`${nodeTypeFilter.has(layout.category) ? '隐藏' : '显示'} ${layout.label} 节点`}
                  >
                    {nodeTypeFilter.has(layout.category) ? (
                      <Eye className="h-3.5 w-3.5" style={{ color: layout.color, opacity: 1 }} />
                    ) : (
                      <EyeOff className="h-3.5 w-3.5" style={{ color: layout.color, opacity: 0.7 }} />
                    )}
                  </button>
                </div>

                {/* 下拉菜单 */}
                {hasMultipleTypes && isOpen && (
                  <div className="absolute top-full left-0 mt-1 bg-card border border-border rounded shadow-lg z-50 min-w-max">
                    {nodeTypesInCategory.map((nodeType) => {
                      const config = getNodeTypeConfig(nodeType);
                      if (!config) return null;

                      return (
                        <button
                          key={nodeType}
                          draggable={true}
                          onDragStart={(e) => {
                            e.dataTransfer.effectAllowed = 'copy';
                            e.dataTransfer.setData('application/json', JSON.stringify({
                              type: 'add-node',
                              nodeType: nodeType,
                            }));
                          }}
                          onClick={() => handleSelectNodeType(nodeType)}
                          className="w-full text-left px-3 py-1.5 text-xs hover:bg-muted transition-colors flex items-center gap-2 cursor-grab"
                          style={{
                            backgroundColor: selectedNodeTypeForDrag === nodeType ? layout.color + '20' : 'transparent',
                            color: layout.color,
                          }}
                        >
                          <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: config.color }}></span>
                          <span className="truncate">{config.description}</span>
                          {selectedNodeTypeForDrag === nodeType && <span className="ml-auto">✓</span>}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Flow 区域 */}
      <div
        className="flex-1 overflow-hidden flex flex-col relative"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <style>{`
        /* 基础样式 */
        [class*="flow-node-"] {
          border: 2px solid transparent;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          width: auto;
          min-width: 140px;
          padding: 12px 20px;
        }

        /* ReactFlow node基础样式 */
        .react-flow__node {
          border: 2px solid transparent;
          border-radius: 8px;
          pointer-events: auto;
          cursor: pointer;
        }

        [class*="flow-node-"] > div {
          font-weight: 500;
          font-size: 13px;
          text-align: center;
          pointer-events: auto;
        }

        /* 数据源节点 (data_source) - 莫兰迪蓝 */
        .flow-node-data_source {
          background: #8db4cc !important;
          opacity: 1;
        }

        .flow-node-data_source > div {
          color: #2c3a48 !important;
        }

        .flow-node-data_source.selected {
          background: #8db4cc;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(141, 180, 204, 0.8);
          opacity: 1;
        }

        .flow-node-data_source.parent {
          background: #8db4cc;
          opacity: 1;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .flow-node-data_source.ancestor {
          background: #bfd5e8 !important;
          opacity: 0.7;
        }

        .flow-node-data_source.dimmed {
          background: #d6dfe8 !important;
          opacity: 0.4;
        }

        /* 计算节点 (compute) - 莫兰迪紫 */
        .flow-node-compute {
          background: #b390c8 !important;
          opacity: 1;
        }

        .flow-node-compute > div {
          color: #39283f !important;
        }

        .flow-node-compute.selected {
          background: #b390c8 !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(179, 144, 200, 0.8) !important;
          opacity: 1;
        }

        .flow-node-compute.parent {
          background: #b390c8 !important;
          opacity: 1;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        .flow-node-compute.ancestor {
          background: #d3bfe0 !important;
          opacity: 0.7;
        }

        .flow-node-compute.dimmed {
          background: #dccce4 !important;
          opacity: 0.4;
        }

        /* 图表节点 (chart & image) - 莫兰迪棕 */
        .flow-node-chart,
        .flow-node-image {
          background: #c4ad8a !important;
          opacity: 1;
        }

        .flow-node-chart > div,
        .flow-node-image > div {
          color: #42372a !important;
        }

        .flow-node-chart.selected,
        .flow-node-image.selected {
          background: #c4ad8a !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(196, 173, 138, 0.8) !important;
          opacity: 1;
        }

        .flow-node-chart.parent,
        .flow-node-image.parent {
          background: #c4ad8a !important;
          opacity: 1;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        .flow-node-chart.ancestor,
        .flow-node-image.ancestor {
          background: #ddd5c7 !important;
          opacity: 0.7;
        }

        .flow-node-chart.dimmed,
        .flow-node-image.dimmed {
          background: #e4ddd0 !important;
          opacity: 0.4;
        }

        /* 工具节点 (tool) - 莫兰迪青 */
        .flow-node-tool {
          background: #8ec0b0 !important;
          opacity: 1;
        }

        .flow-node-tool > div {
          color: #293a35 !important;
        }

        .flow-node-tool.selected {
          background: #8ec0b0 !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(142, 192, 176, 0.8) !important;
          opacity: 1;
        }

        .flow-node-tool.parent {
          background: #8ec0b0 !important;
          opacity: 1;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        .flow-node-tool.ancestor {
          background: #c4ddd5 !important;
          opacity: 0.7;
        }

        .flow-node-tool.dimmed {
          background: #d0e4dc !important;
          opacity: 0.4;
        }

        .react-flow__edge-path {
          stroke: hsl(var(--flow-connection));
          stroke-width: 2;
        }

        /* Arrow marker styling */
        marker {
          fill: hsl(var(--flow-connection));
        }

        /* Curved edge styling for smooth left-right flow */
        .react-flow__edge {
          stroke-linecap: round;
          stroke-linejoin: round;
        }

        .react-flow__edge.animated .react-flow__edge-path {
          stroke-dasharray: 5;
          animation: dashdraw 0.5s linear infinite;
        }

        @keyframes dashdraw {
          to {
            stroke-dashoffset: -10;
          }
        }
        
        .react-flow__controls {
          button {
            background: hsl(var(--background));
            border: 1px solid hsl(var(--border));
            color: hsl(var(--foreground));
          }
          button:hover {
            background: hsl(var(--muted));
          }
        }
        
        .react-flow__minimap {
          background: hsl(var(--muted));
        }

        /* Ensure nodes capture pointer events properly and uniformly */
        .react-flow__node {
          pointer-events: auto;
          cursor: pointer;
        }

        .react-flow__node > div {
          pointer-events: auto; /* Inner div also captures clicks */
        }

        /* Node content should capture clicks and let them bubble */
        [class*="flow-node-"] {
          pointer-events: auto;
        }

        [class*="flow-node-"] > div {
          pointer-events: auto; /* Inner text captures and bubbles clicks */
        }

        /* Execution status indicators - border colors */
        /* Target nodes by their status class - green for success */
        [class*="status-validated"] {
          border: 2px solid #22c55e !important;  /* Green for validated */
          box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        /* Red for failure/error */
        [class*="status-pending_validation"],
        [class*="status-validation_error"] {
          border: 2px solid #ef4444 !important;  /* Red for pending validation or validation error */
          box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        /* Gray for not executed - using attribute selector for robustness */
        [class*="status-not_executed"] {
          border: 2px solid #999999 !important;     /* Gray for not executed */
          box-shadow: 0 0 0 3px rgba(153, 153, 153, 0.1), 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        /* Status badge styling for showing indicator icon */
        .flow-node-status-badge {
          position: absolute;
          top: -8px;
          right: -8px;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          background: white;
          border: 2px solid currentColor;
        }

        .flow-node-status-badge.validated {
          color: #22c55e;
        }

        .flow-node-status-badge.pending_validation,
        .flow-node-status-badge.validation_error {
          color: #ef4444;
        }

        .flow-node-status-badge.not_executed {
          color: #999;
        }

        /* 确保节点层级高于pane_draggable，这样点击节点优先被识别 */
        .react-flow__node {
          z-index: 10 !important;
        }

        /* pane_draggable层级要低于节点，但要允许拖拽 */
        .react-flow__pane {
          z-index: 1 !important;
        }

        /* 节点删除按钮 */
        .node-delete-btn {
          position: absolute;
          top: -12px;
          left: -12px;
          width: 24px;
          height: 24px;
          background: #ef4444;
          border: 2px solid white;
          border-radius: 50%;
          color: white;
          font-size: 14px;
          cursor: pointer;
          display: none;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
          z-index: 20;
        }

        .react-flow__node.selected .node-delete-btn {
          display: flex;
        }

        .node-delete-btn:hover {
          background: #dc2626;
          transform: scale(1.1);
        }
      `}</style>
      
      <ReactFlow
        onInit={(instance) => { reactFlowRef.current = instance; }}
        key={currentDatasetId}
        nodes={(() => {
          console.log('[FlowDiagram render] nodes state length:', nodes.length);
          if (nodes.length > 0) {
            console.log('[FlowDiagram render] first node:', nodes[0].id, 'position:', nodes[0].position, 'data:', nodes[0].data);
          }
          const filtered = nodes
            .filter(node => {
              const nodeData = node.data as FlowNodeData;
              const category = getNodeCategory(nodeData.type);
              const pass = category && nodeTypeFilter.has(category);
              if (!pass) {
                console.log(`[FlowDiagram] Node ${node.id} filtered out: category=${category}, type=${nodeData.type}`);
              }
              return pass;
            })
            .map(node => {
              let classNames = node.className || '';
              const nodeLevel = getNodeLevel(node.id);
              const nodeData = node.data as FlowNodeData;
              const status = nodeData.executionStatus || 'not_executed';

              if (selectedNodeId) {
                // 根据节点等级添加相应的类名
                classNames += ` ${nodeLevel}`;
              }

              // Add status as className for CSS selector
              // This adds the status class to the inner div
              classNames += ` status-${status}`;

              // IMPORTANT: Also store status in the node itself for ReactFlow to apply to parent
              // ReactFlow will pass this through to the wrapper element via data attributes
              return {
                ...node,
                className: classNames,
                selectable: true,  // 确保节点可被选中
                // Store status for potential use in node rendering
                data: {
                  ...node.data,
                  _executionStatus: status, // for CSS/styling reference
                  onVisibilityToggle: toggleNodeVisibility, // Add visibility toggle callback
                  onNodeDelete: handleDeleteNode, // Add delete callback
                }
              };
            });
          console.log('[FlowDiagram] ReactFlow rendering with', filtered.length, 'nodes out of', nodes.length, 'total nodeTypeFilter:', Array.from(nodeTypeFilter));

          // Debug: Log node classNames
          if (filtered.length > 0) {
            console.log('[FlowDiagram] First node className:', filtered[0].className);
            console.log('[FlowDiagram] First node data:', filtered[0].data);
          }

          return filtered;
        })()}
        edges={edges.filter(edge => {
          // 过滤筛选后的节点相关的边
          const sourceNode = nodes.find(n => n.id === edge.source);
          const targetNode = nodes.find(n => n.id === edge.target);

          if (!sourceNode || !targetNode) return false;

          const sourceData = sourceNode.data as FlowNodeData;
          const targetData = targetNode.data as FlowNodeData;

          const sourceCategory = getNodeCategory(sourceData.type);
          const targetCategory = getNodeCategory(targetData.type);

          return (sourceCategory && targetCategory &&
                  nodeTypeFilter.has(sourceCategory) &&
                  nodeTypeFilter.has(targetCategory) &&
                  shouldShowEdge(edge));
        })}
        defaultEdgeOptions={{
          markerEnd: { type: MarkerType.ArrowClosed },
        }}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onNodeClick={handleNodeClick}
        connectionMode={ConnectionMode.Loose}
        fitView
        attributionPosition="bottom-left"
        selectNodesOnDrag={true}
        multiSelectionKeyCode={null}
        deleteKeyCode={null}
        zoomOnDoubleClick={false}
      >
        <Background />
        <Controls />
        {localMinimapOpen && <MiniMap />}
        <div className="absolute bottom-4 right-4 z-40 flex gap-2">
          <button
            onClick={handleAutoLayout}
            disabled={isAutoLayouting}
            className="flex items-center justify-center gap-2 px-3 py-2 rounded border border-border bg-background hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="自动排列节点"
          >
            <Layout className="h-4 w-4" />
            <span className="text-xs font-medium">{isAutoLayouting ? '排列中...' : '自动排列'}</span>
          </button>
          <button
            onClick={() => setLocalMinimapOpen(!localMinimapOpen)}
            className="flex items-center justify-center w-8 h-8 rounded border border-border bg-background hover:bg-muted transition-colors"
            title={localMinimapOpen ? '隐藏迷你地图' : '显示迷你地图'}
          >
            {localMinimapOpen ? '✕' : '◻'}
          </button>
        </div>
      </ReactFlow>

        {/* Loading state overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 pointer-events-none z-50">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-foreground"></div>
              <p className="text-muted-foreground text-sm mt-2">Loading project...</p>
            </div>
          </div>
        )}


        {/* Empty state overlay - very light, non-intrusive */}
        {!isLoading && currentNodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center bg-background/80 rounded-lg p-6 border border-border">
              <p className="text-muted-foreground text-base mb-2">No nodes in this project</p>
              <p className="text-muted-foreground text-xs">
                {error ? `Error: ${error}` : 'Start by adding nodes to build your workflow'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
