# E-Commerce Analytics Platform

## 项目概览

一个全面的电商数据分析平台，包含 **4 条分析路径**、**24 个分析节点**（包括4个工具节点）。

### 项目信息
- **项目ID**: ecommerce_analytics
- **版本**: 1.0.0
- **总节点数**: 24
- **节点类型分布**:
  - 数据源节点: 4 个
  - 计算节点: 12 个
  - 可视化节点: 4 个
  - 工具节点: 4 个 ✨ (包含复用逻辑)

### 初始状态
- ✅ 所有节点状态: `not_executed`
- ✅ 所有依赖关系: 已定义但未形成（即无循环、合法的DAG结构）
- ✅ 所有配置: 已就绪，可直接执行

---

## 📊 4 条分析路径

### 1. **销售趋势分析** (5 个节点)
分析日销售、周销售和品类销售分布

**节点流程**:
```
load_orders_data
  ├── p1_daily_sales (日销售统计)
  ├── p1_category_sales (品类销售分布)
  ├── p1_weekly_trend (周销售趋势)
  └── p1_sales_chart (品类销售图表)
```

**关键输出**:
- 日销售趋势数据
- 各品类销售占比
- 周度销售波动

---

### 2. **客户行为分析** (6 个节点)
理解客户购买模式、忠诚度等级和区域行为

**节点流程**:
```
load_orders_data + load_customers_data
  ├── p2_customer_purchase (客户购买统计)
  │   ├── p2_loyalty_analysis (忠诚度等级分析)
  │   └── p2_regional_behavior (区域行为分析)
  └── p2_customer_chart (忠诚度分布图)
```

**关键输出**:
- 客户购买历史汇总
- 按忠诚度等级的统计
- 地区销售分布

---

### 3. **品类竞争分析** (6 个节点)
比较品类性能和识别畅销产品

**节点流程**:
```
load_orders_data + load_products_data
  ├── p3_category_comparison (品类性能对比)
  │   ├── p3_category_market_share (市场份额)
  │   └── p3_top_products (畅销产品TOP10)
  └── p3_category_chart (市场份额分布图)
```

**关键输出**:
- 品类利润率和销售额
- 市场占有率百分比
- 畅销产品排名

---

### 4. **营销效果评估** (5 个节点)
评估促销活动的影响和支付方式偏好

**节点流程**:
```
load_orders_data
  ├── p4_promo_effectiveness (促销效果)
  ├── p4_category_promo_impact (品类促销影响)
  ├── p4_payment_method_analysis (支付方式分析)
  └── p4_promo_chart (促销效果对比图)
```

**关键输出**:
- 促销 vs 非促销订单对比
- 各品类的促销影响
- 支付方式使用统计

---

## 🛠️ 工具节点 (可复用组件)

项目包含 **4 个工具节点**，演示工具节点的复用价值:

### 1. **tool_time_aggregation**
时间序列聚合函数库
- 支持日、周、月多粒度聚合
- 用于销售趋势分析路径

### 2. **tool_cohort_analysis**
队列分析工具
- 客户群组分析和对比
- 用于客户行为分析路径

### 3. **tool_category_metrics**
品类指标计算
- 自动计算品类的利润率、毛利等
- 用于品类竞争分析路径

### 4. **tool_promo_impact**
促销影响分析
- 促销订单 vs 非促销订单对比
- 用于营销效果评估路径

---

## 📁 数据文件

### CSV 数据源
- **orders.csv** (50条订单记录)
  - 字段: order_id, customer_id, product_id, category, order_date, quantity, unit_price, total_amount, payment_method, is_promoted, promotion_discount
  
- **customers.csv** (23个客户)
  - 字段: customer_id, customer_name, register_date, city, region, age_group, loyalty_level, total_orders, lifetime_value

- **products.csv** (30个产品)
  - 字段: product_id, product_name, category, supplier_id, cost, retail_price, stock_quantity, reorder_level, rating, review_count

- **promotions.csv** (10个促销活动)
  - 字段: promotion_id, campaign_name, start_date, end_date, category, discount_rate, budget_usd, impression_count, click_count, conversion_count

---

## 📓 Notebook 结构

### 项目notebook: `project.ipynb`

**单元组织** (24 个单元格):

1. **第1-4单元**: 数据源节点
   - 加载4个CSV文件
   - 数据类型转换和初步清理

2. **第5-8单元**: 工具节点
   - 定义4个可复用的分析函数
   - 不存储结果，为其他节点提供功能

3. **第9-12单元**: 路径1 - 销售趋势分析
   - 日销售、品类销售、周销售聚合
   - 生成销售品类对比图

4. **第13-16单元**: 路径2 - 客户行为分析
   - 客户购买统计、忠诚度分析、区域分析
   - 生成忠诚度分布图

5. **第17-20单元**: 路径3 - 品类竞争分析
   - 品类性能对比、市场份额计算、产品排名
   - 生成市场份额分布图

6. **第21-24单元**: 路径4 - 营销效果评估
   - 促销效果、品类促销影响、支付方式分析
   - 生成促销效果对比图

---

## 🔗 依赖关系 DAG

### 节点依赖概览

```
数据源层:
  load_orders_data ──┐
  load_customers_data├─── (多条路径使用)
  load_products_data ├─┘
  load_promotions_data

工具层:
  tool_time_aggregation (独立)
  tool_cohort_analysis (独立)
  tool_category_metrics (独立)
  tool_promo_impact (独立)

分析层:
  路径1: load_orders_data → [p1_daily_sales, p1_category_sales, p1_weekly_trend] → p1_sales_chart
  
  路径2: load_orders_data + load_customers_data → p2_customer_purchase → [p2_loyalty_analysis, p2_regional_behavior] → p2_customer_chart
  
  路径3: load_orders_data + load_products_data → p3_category_comparison → [p3_category_market_share, p3_top_products] → p3_category_chart
  
  路径4: load_orders_data → [p4_promo_effectiveness, p4_category_promo_impact, p4_payment_method_analysis] → p4_promo_chart
```

---

## ✅ 初始化验证

**元数据验证** ✅
- [x] 所有节点已定义
- [x] 所有节点执行状态为 `not_executed`
- [x] 所有依赖关系已配置
- [x] DAG无循环（合法的拓扑结构）
- [x] 4个分析路径已定义

**数据文件验证** ✅
- [x] 4个CSV数据源已生成
- [x] 数据文件格式正确
- [x] 包含足量的示例数据

**Notebook验证** ✅
- [x] 24个单元格已创建
- [x] 所有单元格的元数据完整
- [x] 代码已准备好执行
- [x] 无语法错误

---

## 🚀 后续步骤

1. **执行项目**: 
   ```bash
   # 前端访问 http://localhost:5173
   # 选择项目 "ecommerce_analytics"
   # 可视化整个分析DAG
   ```

2. **执行单条路径**:
   ```bash
   # 执行销售趋势分析路径
   # 系统会按依赖顺序执行相关节点
   ```

3. **修改和迭代**:
   - 更新节点代码
   - 添加新的分析节点
   - 创建新的分析路径

---

## 📋 项目元数据

文件: `project.json`

包含:
- 项目基本信息 (ID, 名称, 版本等)
- 所有24个节点的定义和依赖
- 4条分析路径的详细说明
- DAG元数据 (总节点数、类型分布、深度等)

---

## 🎯 项目亮点

1. ✨ **完整的4条分析路径**: 覆盖销售、客户、品类和营销多个维度
2. ✨ **工具节点复用**: 展示了工具节点的价值，可被多条路径使用
3. ✨ **现实数据模型**: 基于真实电商场景的数据结构
4. ✨ **初始化就绪**: 所有节点都是未执行状态，可从零开始探索
5. ✨ **教学价值**: 很好地演示了复杂的多路径分析项目结构

---

**创建时间**: 2024-11-15
**项目版本**: 1.0.0
**状态**: ✅ 就绪
