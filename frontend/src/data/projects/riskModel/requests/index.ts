/**
 * Risk Model Feature Stability - Analysis Requests
 */

export interface StepDetail {
  title: string;
  description: string;
}

export interface AnalysisRequest {
  id: string;
  description: string;
  status: 'completed' | 'pending' | 'suggestion';
  timestamp: number;
  sourceNodes: string[];
  outputNode: string;
  outputNodeLabel: string;
  steps: StepDetail[];
}

const baseTime = Date.now();

export const analysisRequests: AnalysisRequest[] = [
  // ===== 数据导入请求（5个）=====
  {
    id: 'req-data-train',
    description: '导入机器学习模型训练集，包含125,432条样本、118个特征',
    status: 'completed',
    timestamp: baseTime - 86400000 * 20,
    sourceNodes: [],
    outputNode: 'data-train',
    outputNodeLabel: '训练数据集',
    steps: [
      {
        title: '系统连接与认证',
        description: '连接到特征库数据库，验证HTTPS连接、加载API token、确认服务可用性',
      },
      {
        title: '数据查询提取',
        description: '从特征库提取训练集：125,432条样本、118个特征、目标变量，跨度2020-01至2021-12',
      },
      {
        title: '特征元数据提取',
        description: '获取118个特征的完整元数据：特征名称、类型、取值范围、缺失率、业务含义',
      },
      {
        title: '数据质量检查',
        description: '执行验证：完整性检查（缺失值0.2%）、重复值（0条）、异常值检查，通过率99.8%',
      },
      {
        title: '数据存储',
        description: '存储125,180条数据为Parquet格式，压缩率8:1，文件大小14.2MB',
      },
    ],
  },
  {
    id: 'req-data-val',
    description: '导入模型验证集，31,358条样本、相同118个特征',
    status: 'completed',
    timestamp: baseTime - 86400000 * 19,
    sourceNodes: [],
    outputNode: 'data-val',
    outputNodeLabel: '验证数据集',
    steps: [
      {
        title: '系统连接与认证',
        description: '连接特征库，验证连接和权限',
      },
      {
        title: '数据查询提取',
        description: '提取验证集：31,358条样本、118个特征、目标变量，跨度2022-01至2022-06',
      },
      {
        title: '特征一致性检查',
        description: '确保验证集118个特征与训练集完全一致，检查名称、顺序、类型',
      },
      {
        title: '数据质量检查',
        description: '完整性检查（缺失值0.3%）、重复值检查（0条），通过率99.7%',
      },
      {
        title: '数据存储',
        description: '存储31,264条数据为Parquet格式，文件大小3.8MB',
      },
    ],
  },
  {
    id: 'req-data-prod-2022',
    description: '导入2022年生产数据，342,156条样本',
    status: 'completed',
    timestamp: baseTime - 86400000 * 18,
    sourceNodes: [],
    outputNode: 'data-prod-2022',
    outputNodeLabel: '2022年生产数据',
    steps: [
      {
        title: '数据源连接',
        description: '连接到生产环境数据仓库，验证网络连接、加载生产认证token',
      },
      {
        title: '数据查询提取',
        description: '提取2022年全年数据：342,156条样本、118个特征、目标变量，代表真实业务规模',
      },
      {
        title: '时间分段与分层',
        description: '按月份分层：12个月均匀分布，每月平均28,513条样本',
      },
      {
        title: '异常值与缺失值处理',
        description: '缺失值0.8%（高于训练集），使用前向填充处理，异常值占0.5%',
      },
      {
        title: '数据存储',
        description: '存储339,046条数据为Parquet分区格式（按月分区），文件大小39.8MB',
      },
    ],
  },
  {
    id: 'req-data-prod-2023',
    description: '导入2023年生产数据，367,824条样本',
    status: 'completed',
    timestamp: baseTime - 86400000 * 17,
    sourceNodes: [],
    outputNode: 'data-prod-2023',
    outputNodeLabel: '2023年生产数据',
    steps: [
      {
        title: '数据源连接',
        description: '连接生产数据仓库，验证连接和权限',
      },
      {
        title: '数据查询提取',
        description: '提取2023年全年数据：367,824条样本，相比2022年增长7.5%',
      },
      {
        title: '特征一致性验证',
        description: '确保118个特征与2022年保持一致，检查特征工程逻辑是否有变化',
      },
      {
        title: '质量评估',
        description: '缺失值0.9%（略高于2022年），异常值占0.6%，质量下降但仍可接受',
      },
      {
        title: '数据存储',
        description: '存储364,626条数据为Parquet分区格式，文件大小42.7MB',
      },
    ],
  },
  {
    id: 'req-data-prod-2024',
    description: '导入2024年生产数据（至10月），298,561条样本',
    status: 'completed',
    timestamp: baseTime - 86400000 * 16,
    sourceNodes: [],
    outputNode: 'data-prod-2024',
    outputNodeLabel: '2024年生产数据',
    steps: [
      {
        title: '数据源连接',
        description: '连接生产环境数据仓库，验证最新数据可用性',
      },
      {
        title: '数据查询提取',
        description: '提取2024年1月至10月数据：298,561条样本、118个特征、目标变量',
      },
      {
        title: '观测期处理',
        description: '对未到达观测期的样本（约5%）使用部分观测期标记，不排除样本',
      },
      {
        title: '质量评估',
        description: '缺失值1.1%（进一步增加），异常值占0.8%，需加强数据治理',
      },
      {
        title: '数据存储',
        description: '存储295,176条数据为Parquet分区格式，文件大小34.5MB',
      },
    ],
  },

  // ===== 分析请求（5个）=====
  

  {
    id: 'req-1',
    description: '计算所有数据集上118个特征的IV值',
    status: 'completed',
    timestamp: baseTime - 86400000 * 15,
    sourceNodes: ['binning-train', 'binning-val', 'binning-prod-2022', 'binning-prod-2023', 'binning-prod-2024'],
    outputNode: 'compute-iv',
    outputNodeLabel: 'IV计算（特征稳定性评估）',
    steps: [
      {
        title: '判断所需数据源',
        description: '根据分析需求，判断需要五个数据集作为数据源。系统检查：需同时拥有全部5个源，若缺少则自动加载。验证所有源已完成，准备进行特征IV批量计算',
      },
      {
        title: 'IV计算引擎初始化',
        description: '加载Information Value计算库，配置参数：分箱方法(Jenks)、缺失值处理（单独分箱）、异常值处理（固定范围）',
      },
      {
        title: '特征分箱与分布计算',
        description: '对118个特征分箱：连续特征用Jenks算法（平均5-8箱），分类特征根据样本量聚合',
      },
      {
        title: '单个特征IV计算',
        description: '计算每个特征的IV值，基于训练集计算，验证集和生产数据使用训练集分箱边界',
      },
      {
        title: '计算结果汇总',
        description: '生成IV矩阵：行为118个特征，列为5个数据集的IV值，保存为CSV和JSON',
      },
      {
        title: '统计指标计算',
        description: '计算全局统计：平均IV(0.285)、中位数(0.272)、标准差(0.124)、高IV特征占35.6%',
      },
    ],
  },
  {
    id: 'req-3',
    description: '对比生产数据与训练集的IV差值，计算每个特征的稳定性指标',
    status: 'completed',
    timestamp: baseTime - 86400000 * 13,
    sourceNodes: ['compute-iv'],
    outputNode: 'compute-iv-diff',
    outputNodeLabel: 'IV差值计算',
    steps: [
      {
        title: '判断所需数据源',
        description: '根据需求，判断需要IV计算结果。系统检查：若已选中compute-iv则直接使用，否则自动切换。验证compute-iv已完成所有118个特征在五个数据集的IV计算',
      },
      {
        title: '差值计算框架',
        description: '以训练集IV为基准，分别计算三个生产年份的差值：diff_2022/2023/2024 = IV_year - IV_train',
      },
      {
        title: '逐特征差值计算',
        description: '对118个特征计算：绝对差值、平均差值、最大差值、变异系数',
      },
      {
        title: '稳定性分级',
        description: '根据平均差值分级：极稳定(<0.01)占68.6%、稳定(0.01-0.03)占23.7%、一般占5.1%、不稳定占1.7%、高度不稳定(>0.08)占0.9%',
      },
      {
        title: '高风险特征识别',
        description: '识别11个高度不稳定特征：申请金额衍生(0.087)、收入-债务比(0.076)、年龄分段组合(0.069)',
      },
      {
        title: '结果存储与汇总',
        description: '生成详细差值矩阵：118行(特征)×7列(训练IV、三年IV、三个差值、平均差值、稳定性等级)',
      },
    ],
  },
  {
    id: 'req-5',
    description: '对所有特征进行差异排序，识别最不稳定的特征',
    status: 'completed',
    timestamp: baseTime - 86400000 * 11,
    sourceNodes: ['compute-iv-diff'],
    outputNode: 'compute-feature-rank',
    outputNodeLabel: '特征差异排序',
    steps: [
      {
        title: '判断所需数据源',
        description: '根据需求，判断需要IV差值计算结果。系统检查并自动切换至compute-iv-diff。验证已完成所有118个特征的三年差值计算',
      },
      {
        title: '平均差值绝对值计算',
        description: '对每个特征计算：mean_abs_diff = (|diff_2022| + |diff_2023| + |diff_2024|) / 3',
      },
      {
        title: '特征排序',
        description: '按平均差值从高到低排序，生成稳定性排名表：最不稳定到最稳定',
      },
      {
        title: '排名统计',
        description: 'Top 10特征平均差值0.069，Top 50特征平均0.021，Bottom 68特征平均0.004',
      },
      {
        title: '分群分析',
        description: '将特征分为5个群组（极稳定、稳定、中等、不稳定、高度不稳定），统计每组的特征数、平均IV、变异系数',
      },
      {
        title: '特征风险标记',
        description: '绿色标记（稳定，92%）、黄色标记（监控，6%）、红色标记（高风险，2%，共11个）',
      },
      {
        title: '排名结果存储',
        description: '保存排名表为CSV和JSON，包含排名、平均差值、稳定性等级、风险标记、建议行动',
      },
    ],
  },
  {
    id: 'req-6',
    description: '从排序结果中确定最不稳定特征，提取其分箱信息',
    status: 'completed',
    timestamp: baseTime - 86400000 * 10,
    sourceNodes: ['compute-feature-rank', 'compute-iv'],
    outputNode: 'compute-max-feature',
    outputNodeLabel: '最不稳定特征识别',
    steps: [
      {
        title: '判断所需数据源',
        description: '根据需求，判断需要两个数据源：特征排序结果和IV计算结果。系统检查：若仅一个源则自动补充，若都缺则同时加载',
      },
      {
        title: '最不稳定特征确认',
        description: '从排序结果确认排名第一特征：申请金额衍生特征，平均差值绝对值0.087（最高）',
      },
      {
        title: '特征元数据提取',
        description: '获取该特征的完整元数据：名称、类型、业务含义、取值范围、模型系数',
      },
      {
        title: '分箱数据提取',
        description: '从IV计算提取该特征的分箱信息：分箱区间、样本数、好坏样本比例、WOE值、IV贡献度',
      },
      {
        title: '分箱对比与差异分析',
        description: '对比五个数据集的分箱结果：训练集6个分箱，2024年8个分箱，某些分箱样本极度不平衡',
      },
      {
        title: '漂移来源识别',
        description: '识别IV差异根本原因：分箱边界偏移(10%)、样本分布变化(65%)、好坏比例变化(25%)',
      },
      {
        title: '优化建议生成',
        description: '提出三层建议：短期采用百分比分位数、中期定期评估分箱、长期考虑WOE稳定化',
      },
    ],
  },

  // ===== 图表可视化请求（3个）=====
  {
    id: 'req-7',
    description: '生成特征IV分布散点图',
    status: 'completed',
    timestamp: baseTime - 86400000 * 14.5,
    sourceNodes: ['compute-iv'],
    outputNode: 'chart-iv-scatter',
    outputNodeLabel: 'IV分布散点图',
    steps: [
      {
        title: '判断所需数据源',
        description: '根据可视化需求，判断需要IV计算结果。系统检查自动切换至compute-iv。验证已完成118个特征在五个数据集的IV值',
      },
      {
        title: '数据提取与格式化',
        description: '提取118×5的IV矩阵，转换为绘图格式：590个数据点',
      },
      {
        title: '坐标系与颜色方案',
        description: 'X轴为特征索引(1-118)，Y轴为IV值(0-1)，五种颜色区分数据集：训练=蓝、验证=绿、2022=橙、2023=黄、2024=红',
      },
      {
        title: '离群点与高IV特征标注',
        description: '识别15个高IV特征(>0.5)，用较大的点标记，添加特征名称标注',
      },
      {
        title: '簇聚分析与可视化',
        description: '添加三个区域标记：高IV区(>0.3)、中等IV区(0.2-0.3)、低IV区(<0.2)',
      },
      {
        title: '交互功能实现',
        description: '使用Plotly实现交互：鼠标悬停显示特征名、数据集、具体IV值，支持按特征类型过滤',
      },
      {
        title: '导出与补充',
        description: '导出为SVG和PNG格式，生成Top 15高IV特征列表和统计摘要',
      },
    ],
  },
  {
    id: 'req-8',
    description: '生成IV差值散点图，展示特征稳定性分布',
    status: 'completed',
    timestamp: baseTime - 86400000 * 12,
    sourceNodes: ['compute-iv-diff'],
    outputNode: 'chart-diff-scatter',
    outputNodeLabel: 'IV差值散点图',
    steps: [
      {
        title: '判断所需数据源',
        description: '根据可视化需求，判断需要IV差值计算结果。系统检查自动切换至compute-iv-diff。验证已完成所有计算',
      },
      {
        title: '差值数据提取',
        description: '提取三个维度数据：三个年份的差值、平均差值绝对值、稳定性等级',
      },
      {
        title: '多维坐标映射',
        description: 'X轴为特征索引(1-118)，Y轴为差值绝对值(0-0.15)，颜色代表稳定性等级(绿→黄→红)',
      },
      {
        title: '风险阈值与警告区域',
        description: '添加参考线：0.01(极限)、0.03(警告)、0.05(危险)，在>0.05区域用浅红色阴影',
      },
      {
        title: '高风险特征标注',
        description: '对11个高度不稳定特征特殊标注：较大的点、加粗边界、数字标签',
      },
      {
        title: '年份趋势展示',
        description: '可选增加三个年份的差值走势线，显示稳定性是否恶化或改善',
      },
      {
        title: '交互导出与报告',
        description: '实现完整交互：悬停显示详细信息，点击可跳转到该特征分箱分析，导出为SVG/PNG/CSV',
      },
    ],
  },
  {
    id: 'req-9',
    description: '计算最不稳定特征的分箱',
    status: 'completed',
    timestamp: baseTime - 86400000 * 7,
    sourceNodes: ['compute-max-feature', 'compute-iv'],
    outputNode: 'compute-binning',
    outputNodeLabel: '申请金额分箱计算',
    steps: [
      {
        title: '判断所需数据源',
        description: '根据可视化需求，判断需要两个数据源：最不稳定特征识别和IV计算结果。系统检查自动补充缺失源',
      },
      {
        title: '目标特征分箱数据提取',
        description: '提取申请金额衍生特征五个数据集的分箱信息：区间、样本数、好坏比例、WOE、IV贡献',
      }
    ],
  },
];
