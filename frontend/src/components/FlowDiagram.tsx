import React, { useEffect, useState } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  ConnectionMode,
  NodeProps,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Eye, EyeOff } from 'lucide-react';
import { getProject, type ProjectNode, type ProjectEdge } from '@/services/api';
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

// Custom node component with eye icon and delete button
function NodeWithEyeIcon({ id, data }: NodeProps<FlowNodeData>) {
  const handleVisibilityToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    data.onVisibilityToggle?.(id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    const confirmed = window.confirm(`确定删除节点 ${id} 吗?`);
    if (confirmed && (data as any).onNodeDelete) {
      (data as any).onNodeDelete(id);
    }
  };

  const isVisible = data.isVisible ?? true;

  return (
    <div className="relative w-full h-full">
      <Handle position={Position.Top} type="target" />
      <div className="relative px-4 py-3">
        <p className="text-sm font-medium text-center whitespace-nowrap">{data.label}</p>

        {/* Bottom left: Eye icon, Bottom right: Empty (for potential delete button) */}
        <div className="absolute bottom-1 left-1">
          <button
            onClick={handleVisibilityToggle}
            className="p-1.5 rounded hover:bg-black/10 transition-colors"
            title={isVisible ? '隐藏节点' : '显示节点'}
            style={{
              background: isVisible ? 'transparent' : 'rgba(0,0,0,0.05)',
            }}
          >
            {isVisible ? (
              <Eye className="h-3.5 w-3.5 text-foreground/70" />
            ) : (
              <EyeOff className="h-3.5 w-3.5 text-foreground/40" />
            )}
          </button>
        </div>

        {/* Delete button - always visible but subtle */}
        <button
          onClick={handleDelete}
          className="absolute bottom-1 right-1 p-1 rounded hover:bg-red-100 transition-all"
          title="删除此节点"
          style={{
            background: 'transparent',
            color: '#ef4444',
            opacity: 0.6,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = '1';
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = '0.6';
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <span className="text-sm font-bold leading-none">×</span>
        </button>
      </div>
      <Handle position={Position.Bottom} type="source" />
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
  const [apiNodes, setApiNodes] = useState<Node<FlowNodeData>[] | null>(null);
  const [apiEdges, setApiEdges] = useState<Edge[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


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

          return {
            id: node.id,
            type: 'default',
            position: { x, y },
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
        const flowEdges = project.edges || [];

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
  const [selectedNodeTypeForDrag, setSelectedNodeTypeForDrag] = React.useState<NodeType | null>(null);
  const [openCategoryDropdown, setOpenCategoryDropdown] = React.useState<string | null>(null);

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
  }, []);

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
      // 如果有选择的节点类型，用它来创建节点
      if (selectedNodeTypeForDrag) {
        const nodeType = selectedNodeTypeForDrag;
        const config = getNodeTypeConfig(nodeType);
        if (!config) return;

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
      }
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
      {/* 顶部工具栏：左侧过滤条 + 右侧节点添加面板 */}
      <div className="flex items-center justify-between gap-3 p-3 border-b border-border bg-muted/50">
        {/* 左侧：过滤条 */}
        <div className="flex gap-2">
          {Object.values(CATEGORY_LAYOUTS).map((layout) => (
            <button
              key={`filter-${layout.category}`}
              onClick={() => toggleNodeTypeFilter(layout.category)}
              className="px-3 py-1 rounded transition-all text-xs font-medium"
              style={{
                backgroundColor: nodeTypeFilter.has(layout.category) ? layout.color + '80' : layout.color + '08',
                border: `1px solid ${layout.color}`,
                color: nodeTypeFilter.has(layout.category) ? '#000000' : layout.color,
                opacity: nodeTypeFilter.has(layout.category) ? 0.9 : 0.35,
              }}
              title={`${nodeTypeFilter.has(layout.category) ? '隐藏' : '显示'} ${layout.label}`}
            >
              {layout.label}
            </button>
          ))}
        </div>

        {/* 右侧：节点添加和管理面板 */}
        <div className="flex gap-1 bg-background/50 rounded p-2 border border-border/30">
          {Object.values(CATEGORY_LAYOUTS).map((layout) => {
            const nodeTypesInCategory = layout.nodeTypes;
            const hasMultipleTypes = nodeTypesInCategory.length > 1;
            const isOpen = openCategoryDropdown === layout.category;
            const isSelected = selectedNodeTypeForDrag &&
              nodeTypesInCategory.includes(selectedNodeTypeForDrag as NodeType);

            return (
              <div key={layout.category} className="relative">
                {/* 节点类型按钮 - 可拖拽 */}
                <div className="flex items-center gap-1">
                  <button
                    draggable={selectedNodeTypeForDrag !== null}
                    onDragStart={(e) => {
                      if (selectedNodeTypeForDrag) {
                        e.dataTransfer.effectAllowed = 'copy';
                        e.dataTransfer.setData('application/json', JSON.stringify({
                          type: 'add-node',
                          nodeType: selectedNodeTypeForDrag,
                        }));
                      }
                    }}
                    onClick={() => {
                      if (hasMultipleTypes) {
                        setOpenCategoryDropdown(isOpen ? null : layout.category);
                      } else {
                        handleSelectNodeType(nodeTypesInCategory[0]);
                      }
                    }}
                    className="px-2.5 py-1.5 rounded transition-all flex items-center gap-1.5 text-xs font-medium"
                    style={{
                      backgroundColor: isSelected ? layout.color + '80' : layout.color + '20',
                      border: `1px solid ${layout.color}`,
                      color: isSelected ? '#000000' : layout.color,
                      cursor: selectedNodeTypeForDrag ? 'grab' : 'pointer',
                    }}
                    title={isSelected ? `拖拽添加 ${layout.label} 节点` : `点击选择 ${layout.label} 类型`}
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
                      <Eye className="h-3.5 w-3.5" style={{ color: layout.color }} />
                    ) : (
                      <EyeOff className="h-3.5 w-3.5" style={{ color: layout.color, opacity: 0.5 }} />
                    )}
                  </button>
                </div>

                {/* 下拉菜单 */}
                {hasMultipleTypes && isOpen && (
                  <div className="absolute top-full left-0 mt-1 bg-card border border-border rounded shadow-lg z-50 min-w-max">
                    {nodeTypesInCategory.map((nodeType) => {
                      const config = getNodeTypeConfig(nodeType);
                      if (!config) return null;
                      const isThisTypeSelected = selectedNodeTypeForDrag === nodeType;

                      return (
                        <button
                          key={nodeType}
                          onClick={() => handleSelectNodeType(nodeType)}
                          className="w-full text-left px-3 py-1.5 text-xs hover:bg-muted transition-colors flex items-center gap-2"
                          style={{
                            backgroundColor: isThisTypeSelected ? layout.color + '20' : 'transparent',
                            color: layout.color,
                          }}
                        >
                          <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: config.color }}></span>
                          <span className="truncate">{config.description}</span>
                          {isThisTypeSelected && <span className="ml-auto">✓</span>}
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
          background: #a8c5da !important;
        }

        .flow-node-data_source > div {
          color: #3d4a5a !important;
        }

        .flow-node-data_source.selected {
          background: #a8c5da;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(168, 197, 218, 0.8);
        }

        .flow-node-data_source.parent {
          background: #a8c5da;
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
          background: #c4a8d4 !important;
        }

        .flow-node-compute > div {
          color: #4a3d53 !important;
        }

        .flow-node-compute.selected {
          background: #c4a8d4 !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(196, 168, 212, 0.8) !important;
        }

        .flow-node-compute.parent {
          background: #c4a8d4 !important;
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
          background: #d4c4a8 !important;
        }

        .flow-node-chart > div,
        .flow-node-image > div {
          color: #524a3a !important;
        }

        .flow-node-chart.selected,
        .flow-node-image.selected {
          background: #d4c4a8 !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(212, 196, 168, 0.8) !important;
        }

        .flow-node-chart.parent,
        .flow-node-image.parent {
          background: #d4c4a8 !important;
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
          background: #a8d4c4 !important;
        }

        .flow-node-tool > div {
          color: #3a524a !important;
        }

        .flow-node-tool.selected {
          background: #a8d4c4 !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(168, 212, 196, 0.8) !important;
        }

        .flow-node-tool.parent {
          background: #a8d4c4 !important;
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
        <div className="absolute bottom-4 right-4 z-40">
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