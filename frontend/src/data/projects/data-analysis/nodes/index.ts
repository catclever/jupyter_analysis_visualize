/**
 * Flow Diagram Nodes Configuration
 * 流程图节点配置：包含数据源节点、计算分析节点、图表可视化节点
 */

import { Node } from '@xyflow/react';

interface FlowNodeData extends Record<string, unknown> {
  label: string;
  type: 'data' | 'compute' | 'chart';
}

// 节点标签映射 - 用于分析请求中引用
export const nodeLabels: Record<string, string> = {
  // 数据源节点
  "data-1": "用户基本信息",
  "data-2": "贷款申请数据",
  "data-3": "还款历史数据",

  // 计算分析节点
  "compute-1": "申请人特征分析",
  "compute-2": "年龄-收入交叉分析",
  "compute-3": "职业风险分析",
  "compute-4": "逾期率统计",
  "compute-5": "金额与违约关系",
  "compute-6": "首贷vs复贷对比",
  "compute-7": "特征重要性排序",

  // 图表节点
  "chart-1": "年龄-收入散点图",
  "chart-2": "逾期率趋势图",
  "chart-3": "特征重要性柱状图",
};

// 节点定义
export const nodes: Node<FlowNodeData>[] = [
  // ===== 数据源节点（蓝色） =====
  {
    id: 'data-1',
    type: 'default',
    position: { x: 0, y: 0 },
    data: { label: '用户基本信息', type: 'data' },
    className: 'flow-node-data',
  },
  {
    id: 'data-2',
    type: 'default',
    position: { x: 0, y: 100 },
    data: { label: '贷款申请数据', type: 'data' },
    className: 'flow-node-data',
  },
  {
    id: 'data-3',
    type: 'default',
    position: { x: 0, y: 200 },
    data: { label: '还款历史数据', type: 'data' },
    className: 'flow-node-data',
  },

  // ===== 计算/分析节点（紫色） =====
  {
    id: 'compute-1',
    type: 'default',
    position: { x: 280, y: 30 },
    data: { label: '申请人特征分析', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-2',
    type: 'default',
    position: { x: 280, y: 130 },
    data: { label: '年龄-收入交叉分析', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-3',
    type: 'default',
    position: { x: 280, y: 230 },
    data: { label: '职业风险分析', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-4',
    type: 'default',
    position: { x: 560, y: 30 },
    data: { label: '逾期率统计', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-5',
    type: 'default',
    position: { x: 560, y: 130 },
    data: { label: '金额与违约关系', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-6',
    type: 'default',
    position: { x: 560, y: 230 },
    data: { label: '首贷vs复贷对比', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-7',
    type: 'default',
    position: { x: 840, y: 80 },
    data: { label: '特征重要性排序', type: 'compute' },
    className: 'flow-node-compute',
  },

  // ===== 图表/可视化节点（红色） =====
  {
    id: 'chart-1',
    type: 'default',
    position: { x: 280, y: 340 },
    data: { label: '年龄-收入散点图', type: 'chart' },
    className: 'flow-node-chart',
  },
  {
    id: 'chart-2',
    type: 'default',
    position: { x: 560, y: 340 },
    data: { label: '逾期率趋势图', type: 'chart' },
    className: 'flow-node-chart',
  },
  {
    id: 'chart-3',
    type: 'default',
    position: { x: 840, y: 280 },
    data: { label: '特征重要性柱状图', type: 'chart' },
    className: 'flow-node-chart',
  },
];

// 边定义（连接线）
export const edges = [
  // 数据源 -> 计算节点
  { id: 'e1', source: 'data-1', target: 'compute-1', animated: true },
  { id: 'e2', source: 'data-2', target: 'compute-1', animated: true },
  { id: 'e3', source: 'data-2', target: 'compute-2', animated: true },
  { id: 'e4', source: 'data-2', target: 'compute-3', animated: true },

  { id: 'e5', source: 'data-2', target: 'compute-4', animated: true },
  { id: 'e6', source: 'data-3', target: 'compute-4', animated: true },
  { id: 'e7', source: 'data-2', target: 'compute-5', animated: true },
  { id: 'e8', source: 'data-3', target: 'compute-5', animated: true },

  { id: 'e9', source: 'data-1', target: 'compute-6', animated: true },
  { id: 'e10', source: 'data-3', target: 'compute-6', animated: true },

  // 计算节点 -> 图表节点
  { id: 'e11', source: 'compute-1', target: 'chart-1', animated: true },
  { id: 'e12', source: 'compute-2', target: 'chart-1', animated: true },

  { id: 'e13', source: 'compute-4', target: 'chart-2', animated: true },

  // 计算节点汇聚
  { id: 'e14', source: 'compute-1', target: 'compute-7', animated: true },
  { id: 'e15', source: 'compute-2', target: 'compute-7', animated: true },
  { id: 'e16', source: 'compute-3', target: 'compute-7', animated: true },
  { id: 'e17', source: 'compute-4', target: 'compute-7', animated: true },
  { id: 'e18', source: 'compute-5', target: 'compute-7', animated: true },
  { id: 'e19', source: 'compute-6', target: 'compute-7', animated: true },

  // 特征重要性 -> 图表
  { id: 'e20', source: 'compute-7', target: 'chart-3', animated: true },
];
