/**
 * Risk Model Feature Stability - Conclusions Data
 */

export interface ConclusionItem {
  id: string;
  conclusion: string;
  nodeId: string;
  nodeName: string;
}

export const conclusions: ConclusionItem[] = [
  
  {
    id: 'c1-2',
    conclusion: '验证集特征IV平均0.278，与训练集相差仅0.007，显示良好的泛化能力',
    nodeId: 'compute-iv',
    nodeName: 'IV计算',
  },
  {
    id: 'c1-3',
    conclusion: '三年生产数据平均IV为0.267，呈现小幅波动但整体稳定趋势',
    nodeId: 'compute-iv',
    nodeName: 'IV计算',
  },
  {
    id: 'c2-1',
    conclusion: '对比生产数据与训练集：2022年平均差值0.019，2023年0.014，2024年0.021，三年均值0.018',
    nodeId: 'compute-iv-diff',
    nodeName: 'IV差值计算',
  },
  {
    id: 'c3-1',
    conclusion: '12个特征的三年平均差值>0.05（高风险），64个特征在0.01-0.03之间（低风险），其余特征<0.01（极低风险）',
    nodeId: 'compute-iv-diff',
    nodeName: 'IV差值计算',
  },
  {
    id: 'c5-1',
    conclusion: '高风险特征排序：申请金额衍生（0.087）、收入-债务比（0.076）、年龄分段组合（0.069）',
    nodeId: 'compute-feature-rank',
    nodeName: '特征差异排序',
  },
  {
    id: 'c6-1',
    conclusion: '最不稳定特征：申请金额衍生（2022: 0.412 → 2024: 0.499），平均差值绝对值0.087',
    nodeId: 'compute-max-feature',
    nodeName: '最不稳定特征识别',
  },
  {
    id: 'ch3-1',
    conclusion: '申请金额分箱分析：箱体中存在0值，可能导致模型预测错误',
    nodeId: 'compute-binning',
    nodeName: '申请金额分箱计算',
  },
];
