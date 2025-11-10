/**
 * Multi-Dataset Management
 * 多数据集管理 - 提供统一接口访问不同项目的数据
 */

import * as dataAnalysis from './projects/data-analysis/index';
import * as riskModel from './projects/riskModel/index';

export interface DatasetMetadata {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

export interface Dataset {
  nodeLabels: Record<string, string>;
  nodes: any[];
  edges: any[];
  analysisRequests: any[];
  conclusions: any[];
}

/**
 * 支持的所有数据集列表
 */
export const AVAILABLE_DATASETS: DatasetMetadata[] = [
  {
    id: 'data-analysis',
    name: 'Data Analysis Dashboard',
    description: '数据分析仪表板 - 用户、贷款、还款数据的多维度分析',
    icon: '📊',
  },
  {
    id: 'risk-model',
    name: 'Risk Model Feature Stability',
    description: '风控模型特征稳定性 - 机器学习模型特征IV监控与稳定性分析',
    icon: '⚠️',
  },
];

/**
 * 根据数据集ID获取对应的数据
 */
export function getDatasetById(datasetId: string): Dataset {
  switch (datasetId) {
    case 'data-analysis':
      return {
        nodeLabels: dataAnalysis.nodeLabels,
        nodes: dataAnalysis.nodes,
        edges: dataAnalysis.edges,
        analysisRequests: [],
        conclusions: [],
      };
    case 'risk-model':
      return {
        nodeLabels: riskModel.nodeLabels,
        nodes: riskModel.nodes,
        edges: riskModel.edges,
        analysisRequests: [],
        conclusions: [],
      };
    default:
      throw new Error(`Unknown dataset: ${datasetId}`);
  }
}

/**
 * 获取默认数据集（Data Analysis）
 */
export function getDefaultDataset(): Dataset {
  return getDatasetById('data-analysis');
}
