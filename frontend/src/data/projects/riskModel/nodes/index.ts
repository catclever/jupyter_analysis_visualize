/**
 * Risk Model Feature Stability - Flow Nodes Data
 * 风控模型特征稳定性分析 - 流程图节点数据
 */

import { Node, Edge } from '@xyflow/react';

export interface FlowNodeData {
  label: string;
  type?: 'data' | 'compute' | 'chart';
}

/**
 * 节点标签映射
 */
export const nodeLabels: Record<string, string> = {
  'data-train': '训练数据集',
  'data-val': '验证数据集',
  'data-prod-2022': '2022年生产数据',
  'data-prod-2023': '2023年生产数据',
  'data-prod-2024': '2024年生产数据',

  'binning-train': '训练集分箱计算',
  'binning-val': '验证集分箱计算',
  'binning-prod-2022': '2022年分箱计算',
  'binning-prod-2023': '2023年分箱计算',
  'binning-prod-2024': '2024年分箱计算',

  'compute-iv': 'IV计算（特征稳定性评估）',
  'compute-iv-diff': 'IV差值计算',
  'compute-feature-rank': '特征差异排序',
  'compute-max-feature': '最不稳定特征识别',

  'compute-binning': '申请金额分箱计算',

  'chart-iv-scatter': 'IV分布散点图',
  'chart-diff-scatter': 'IV差值散点图',
};

/**
 * 流程图节点定义
 */
export const nodes: Node<FlowNodeData & Record<string, unknown>>[] = [
  // ===== 数据源节点 =====
  {
    id: 'data-train',
    type: 'default',
    position: { x: 0, y: 0 },
    data: { label: '训练数据集', type: 'data' },
    className: 'flow-node-data',
  },
  {
    id: 'data-val',
    type: 'default',
    position: { x: 200, y: 0 },
    data: { label: '验证数据集', type: 'data' },
    className: 'flow-node-data',
  },
  {
    id: 'data-prod-2022',
    type: 'default',
    position: { x: 400, y: 0 },
    data: { label: '2022年生产数据', type: 'data' },
    className: 'flow-node-data',
  },
  {
    id: 'data-prod-2023',
    type: 'default',
    position: { x: 600, y: 0 },
    data: { label: '2023年生产数据', type: 'data' },
    className: 'flow-node-data',
  },
  {
    id: 'data-prod-2024',
    type: 'default',
    position: { x: 800, y: 0 },
    data: { label: '2024年生产数据', type: 'data' },
    className: 'flow-node-data',
  },

  // ===== 分箱计算节点（中间层） =====
  {
    id: 'binning-train',
    type: 'default',
    position: { x: 0, y: 150 },
    data: { label: '训练集分箱', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'binning-val',
    type: 'default',
    position: { x: 200, y: 150 },
    data: { label: '验证集分箱', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'binning-prod-2022',
    type: 'default',
    position: { x: 400, y: 150 },
    data: { label: '2022分箱', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'binning-prod-2023',
    type: 'default',
    position: { x: 600, y: 150 },
    data: { label: '2023分箱', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'binning-prod-2024',
    type: 'default',
    position: { x: 800, y: 150 },
    data: { label: '2024分箱', type: 'compute' },
    className: 'flow-node-compute',
  },

  // ===== IV计算节点 =====
  {
    id: 'compute-iv',
    type: 'default',
    position: { x: 200, y: 300 },
    data: { label: 'IV计算', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-iv-diff',
    type: 'default',
    position: { x: 600, y: 300 },
    data: { label: 'IV差值计算', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-feature-rank',
    type: 'default',
    position: { x: 200, y: 450 },
    data: { label: '特征差异排序', type: 'compute' },
    className: 'flow-node-compute',
  },
  {
    id: 'compute-max-feature',
    type: 'default',
    position: { x: 600, y: 450 },
    data: { label: '最不稳定特征', type: 'compute' },
    className: 'flow-node-compute',
  },

  // ===== 计算节点（分箱统计） =====
  {
    id: 'compute-binning',
    type: 'default',
    position: { x: 400, y: 300 },
    data: { label: '申请金额分箱计算', type: 'compute' },
    className: 'flow-node-compute',
  },

  // ===== 可视化节点 =====
  {
    id: 'chart-iv-scatter',
    type: 'default',
    position: { x: 200, y: 600 },
    data: { label: 'IV分布散点图', type: 'chart' },
    className: 'flow-node-chart',
  },
  {
    id: 'chart-diff-scatter',
    type: 'default',
    position: { x: 600, y: 600 },
    data: { label: 'IV差值散点图', type: 'chart' },
    className: 'flow-node-chart',
  },
];

/**
 * 流程图边定义
 */
export const edges: Edge[] = [
  // 数据 -> 分箱
  { id: 'e1', source: 'data-train', target: 'binning-train', animated: true },
  { id: 'e2', source: 'data-val', target: 'binning-val', animated: true },
  { id: 'e3', source: 'data-prod-2022', target: 'binning-prod-2022', animated: true },
  { id: 'e4', source: 'data-prod-2023', target: 'binning-prod-2023', animated: true },
  { id: 'e5', source: 'data-prod-2024', target: 'binning-prod-2024', animated: true },

  // 分箱 -> IV计算
  { id: 'e6', source: 'binning-train', target: 'compute-iv', animated: true },
  { id: 'e7', source: 'binning-val', target: 'compute-iv', animated: true },
  { id: 'e8', source: 'binning-prod-2022', target: 'compute-iv', animated: true },
  { id: 'e9', source: 'binning-prod-2023', target: 'compute-iv', animated: true },
  { id: 'e10', source: 'binning-prod-2024', target: 'compute-iv', animated: true },

  // IV计算 -> 差值
  { id: 'e11', source: 'compute-iv', target: 'compute-iv-diff', animated: true },

  // IV计算 -> 可视化
  { id: 'e12', source: 'compute-iv', target: 'chart-iv-scatter', animated: true },
  { id: 'e13', source: 'compute-iv-diff', target: 'chart-diff-scatter', animated: true },

  // 分箱 -> 分箱分析图（所有分箱节点）
  { id: 'e14', source: 'binning-train', target: 'compute-binning', animated: true },
  { id: 'e14b', source: 'binning-val', target: 'compute-binning', animated: true },
  { id: 'e14c', source: 'binning-prod-2022', target: 'compute-binning', animated: true },
  { id: 'e14d', source: 'binning-prod-2023', target: 'compute-binning', animated: true },
  { id: 'e14e', source: 'binning-prod-2024', target: 'compute-binning', animated: true },

  // 差值 -> 排序分析
  { id: 'e15', source: 'compute-iv-diff', target: 'compute-feature-rank', animated: true },
  { id: 'e16', source: 'compute-feature-rank', target: 'compute-max-feature', animated: true },
];
