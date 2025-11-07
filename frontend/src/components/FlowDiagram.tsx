import React from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { nodes as initialNodes, edges as initialEdges } from '@/data';
import { getDatasetById } from '@/data/datasets';

interface FlowNodeData extends Record<string, unknown> {
  label: string;
  type: 'data' | 'compute' | 'chart';
  phase?: string;
}

interface FlowDiagramProps {
  onNodeClick: (nodeId: string) => void;
  selectedNodeId: string | null;
  minimapOpen?: boolean;
  currentDatasetId?: string;
}

export function FlowDiagram({ onNodeClick, selectedNodeId, minimapOpen = true, currentDatasetId = "data-analysis" }: FlowDiagramProps) {
  // 获取当前数据集的nodes和edges
  const datasetData = React.useMemo(() => {
    try {
      return getDatasetById(currentDatasetId);
    } catch {
      return { nodes: initialNodes, edges: initialEdges };
    }
  }, [currentDatasetId]);

  const currentNodes = datasetData.nodes || initialNodes;
  const currentEdges = datasetData.edges || initialEdges;

  const [nodes, setNodes, onNodesChange] = useNodesState(currentNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(currentEdges);
  const [localMinimapOpen, setLocalMinimapOpen] = React.useState(minimapOpen);
  const [nodeTypeFilter, setNodeTypeFilter] = React.useState<Set<'data' | 'compute' | 'chart'>>(
    new Set(['data', 'compute', 'chart'])
  );

  // 当数据集改变时，更新 nodes 和 edges
  React.useEffect(() => {
    setNodes(currentNodes);
    setEdges(currentEdges);
  }, [currentDatasetId, currentNodes, currentEdges, setNodes, setEdges]);

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

  // 获取节点的显示等级：selected(当前) > parent(直接父节点) > ancestor(祖先) > dimmed(其他)
  const getNodeLevel = (nodeId: string): 'selected' | 'parent' | 'ancestor' | 'dimmed' => {
    if (!selectedNodeId) return 'dimmed'; // 没有选中时都是普通状态
    if (nodeId === selectedNodeId) return 'selected';

    const directParents = getDirectParentNodes(selectedNodeId, edges);
    if (directParents.has(nodeId)) return 'parent';

    const ancestors = getAllAncestorNodes(selectedNodeId, edges);
    if (ancestors.has(nodeId)) return 'ancestor';

    return 'dimmed';
  };

  const handleNodeClick = (_event: React.MouseEvent, node: Node) => {
    onNodeClick(node.id);
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

  // 判断边是否应该显示（只有当两个端点都不是置灰状态时，才显示）
  const shouldShowEdge = (edge: Edge): boolean => {
    if (!selectedNodeId) return true; // 没有选中时，所有边都显示

    const sourceLevel = getNodeLevel(edge.source);
    const targetLevel = getNodeLevel(edge.target);

    // 只要任一端点是置灰的，就隐藏这条边
    return sourceLevel !== 'dimmed' && targetLevel !== 'dimmed';
  };

  return (
    <div className="h-full bg-card rounded-lg border border-border overflow-hidden flex flex-col">
      {/* 筛选条 */}
      <div className="flex items-center justify-end gap-3 p-3 border-b border-border bg-muted/50">
        <div className="flex gap-3">
          {(['data', 'compute', 'chart'] as const).map((type) => {
            const colorMap = {
              data: '#a8c5da',
              compute: '#c4a8d4',
              chart: '#c9a8a8',
            };
            const labelMap = {
              data: '数据',
              compute: '计算',
              chart: '图表',
            };
            const bgColor = colorMap[type];
            return (
              <button
                key={type}
                onClick={() => toggleNodeTypeFilter(type)}
                className="px-3 py-1 rounded transition-all"
                style={{
                  backgroundColor: nodeTypeFilter.has(type) ? bgColor + '80' : bgColor + '08',
                  border: `1px solid ${bgColor}`,
                  color: nodeTypeFilter.has(type) ? '#000000' : bgColor,
                  opacity: nodeTypeFilter.has(type) ? 0.9 : 0.35,
                }}
                title={labelMap[type]}
              >
                <span className="text-xs font-medium">
                  {labelMap[type]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Flow 区域 */}
      <div className="flex-1 overflow-hidden">
      <style>{`
        /* 数据源节点 - 莫兰迪蓝 */
        .flow-node-data {
          background: #a8c5da !important;
          border: none !important;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
          width: auto !important;
          min-width: 140px;
          padding: 12px 20px;
        }

        .flow-node-data > div {
          color: #3d4a5a !important;
          font-weight: 500;
          font-size: 13px;
          text-align: center;
          cursor: pointer;
        }

        .flow-node-data.selected {
          background: #a8c5da !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(168, 197, 218, 0.8) !important;
        }

        .flow-node-data.parent {
          background: #a8c5da !important;
          opacity: 1;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        .flow-node-data.ancestor {
          background: #bfd5e8 !important;
          opacity: 0.7;
        }

        .flow-node-data.dimmed {
          background: #d6dfe8 !important;
          opacity: 0.4;
        }

        /* 计算/分析节点 - 莫兰迪紫 */
        .flow-node-compute {
          background: #c4a8d4 !important;
          border: none !important;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
          width: auto !important;
          min-width: 140px;
          padding: 12px 20px;
        }

        .flow-node-compute > div {
          color: #4a3d53 !important;
          font-weight: 500;
          font-size: 13px;
          text-align: center;
          cursor: pointer;
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

        /* 图表节点 - 莫兰迪红 */
        .flow-node-chart {
          background: #c9a8a8 !important;
          border: none !important;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
          width: auto !important;
          min-width: 140px;
          padding: 12px 20px;
        }

        .flow-node-chart > div {
          color: #52363a !important;
          font-weight: 500;
          font-size: 13px;
          text-align: center;
          cursor: pointer;
        }

        .flow-node-chart.selected {
          background: #c9a8a8 !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 0 0 3px rgba(201, 168, 168, 0.8) !important;
        }

        .flow-node-chart.parent {
          background: #c9a8a8 !important;
          opacity: 1;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        .flow-node-chart.ancestor {
          background: #d6bfbe !important;
          opacity: 0.7;
        }

        .flow-node-chart.dimmed {
          background: #dccccb !important;
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
      `}</style>
      
      <ReactFlow
        key={currentDatasetId}
        nodes={nodes
          .filter(node => {
            const nodeData = node.data as FlowNodeData;
            return nodeTypeFilter.has(nodeData.type);
          })
          .map(node => {
            let classNames = node.className || '';
            const nodeLevel = getNodeLevel(node.id);

            if (selectedNodeId) {
              // 根据节点等级添加相应的类名
              classNames += ` ${nodeLevel}`;
            }

            return {
              ...node,
              className: classNames,
            };
          })}
        edges={edges.filter(edge => {
          // 过滤筛选后的节点相关的边
          const sourceNode = nodes.find(n => n.id === edge.source);
          const targetNode = nodes.find(n => n.id === edge.target);

          if (!sourceNode || !targetNode) return false;

          const sourceData = sourceNode.data as FlowNodeData;
          const targetData = targetNode.data as FlowNodeData;

          return nodeTypeFilter.has(sourceData.type) &&
                 nodeTypeFilter.has(targetData.type) &&
                 shouldShowEdge(edge);
        })}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        connectionMode={ConnectionMode.Loose}
        fitView
        attributionPosition="bottom-left"
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
      </div>
    </div>
  );
}