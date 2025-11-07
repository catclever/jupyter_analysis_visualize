/**
 * Conclusions Data Configuration
 * 结论数据配置：左侧面板中展示的分析结论
 */

export interface ConclusionItem {
  id: string;
  conclusion: string; // 结论内容（主要信息）
  nodeId: string;
  nodeName: string; // 节点名称（次要信息）
}

export const conclusions: ConclusionItem[] = [
  // ===== compute-1: 申请人特征分析 =====

  // ===== compute-2: 年龄-收入交叉分析 =====
  {
    id: "c2-1",
    conclusion: "年轻低收入人群风险最高，25-30岁+低收入组违约率达24%",
    nodeId: "compute-2",
    nodeName: "年龄-收入交叉分析"
  },
  {
    id: "c2-2",
    conclusion: "中年中等收入是最安全的客户群体，31-40岁+中等收入违约率仅18%，是最大客户群体",
    nodeId: "compute-2",
    nodeName: "年龄-收入交叉分析"
  },
  {
    id: "c2-3",
    conclusion: "高收入人群跨所有年龄段违约率都较低，高收入成为强保护因素",
    nodeId: "compute-2",
    nodeName: "年龄-收入交叉分析"
  },

  // ===== compute-3: 职业风险分析 =====
  {
    id: "c3-1",
    conclusion: "个体/商户违约率最高达28%，是风险最高的职业群体",
    nodeId: "compute-3",
    nodeName: "职业风险分析"
  },
  {
    id: "c3-2",
    conclusion: "医疗/教育工作者违约率最低仅9%，风险相对可控",
    nodeId: "compute-3",
    nodeName: "职业风险分析"
  },
  {
    id: "c3-3",
    conclusion: "软件/IT工程师违约率14%，销售/市场类19%，公务员10%，需要按职业差异化定价",
    nodeId: "compute-3",
    nodeName: "职业风险分析"
  },

  // ===== compute-4: 逾期率统计 =====

  // ===== compute-5: 金额与违约关系 =====
  {
    id: "c5-1",
    conclusion: "申请金额与违约率呈强正相关，金额越大违约风险越高",
    nodeId: "compute-5",
    nodeName: "金额与违约关系分析"
  },

  // ===== compute-6: 首贷vs复贷对比 =====
  {
    id: "c6-1",
    conclusion: "首贷客户违约率9%，复贷客户违约率14%，二次借贷风险明显升高",
    nodeId: "compute-6",
    nodeName: "首贷vs复贷对比"
  },

  // ===== compute-7: 特征重要性排序 =====
  {
    id: "c7-1",
    conclusion: "申请金额对违约的预测能力最强，其次是年龄、收入、职业等维度",
    nodeId: "compute-7",
    nodeName: "特征重要性排序"
  },

  // ===== chart-1: 年龄-收入散点图 =====
  {
    id: "ch1-1",
    conclusion: "年龄-收入-违约率三维关系清晰，年轻低收入群体风险突出",
    nodeId: "chart-1",
    nodeName: "年龄-收入散点图"
  },

  // ===== chart-2: 逾期率趋势图 =====
  {
    id: "ch2-1",
    conclusion: "逾期率呈现明显的月度变化趋势，季节性规律突出",
    nodeId: "chart-2",
    nodeName: "逾期率趋势图"
  },

  // ===== chart-3: 特征重要性柱状图 =====
  {
    id: "ch3-1",
    conclusion: "特征重要性排序显示金额、年龄、收入是最重要的风险预测因子",
    nodeId: "chart-3",
    nodeName: "特征重要性柱状图"
  }
];
