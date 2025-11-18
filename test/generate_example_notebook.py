"""
生成一个完整的示例 notebook，展示优化后的所有功能

结构说明:
1. Code Cell (执行节点) - 包含 @execution_status 元数据
2. Markdown Cell (描述) - 描述数据/结果, 通过 linked_node_id 链接到代码节点
3. Result Cell (结果展示) - 从 parquet/json 加载并展示结果
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from notebook_manager import NotebookManager, ExecutionStatus


def create_example_notebook():
    """创建示例 notebook"""

    output_path = Path(__file__).parent / "example_optimized.ipynb"
    manager = NotebookManager(str(output_path))

    # ===== 项目头 =====
    manager.append_markdown_cell(
        "# 用户行为分析项目\n\n"
        "本项目分析用户在平台上的行为数据，包括数据加载、清理、特征工程和可视化。\n"
        "Project Status: 进行中"
    )

    # ===== 第一阶段: 数据加载 =====
    # 1. 代码节点 (数据加载)
    manager.append_code_cell(
        code="""import pandas as pd
import numpy as np
import os

# 加载用户数据
# 在实际场景中，这会从真实 CSV 文件读取
users_data = pd.DataFrame({
    'user_id': range(1, 1001),
    'age': np.random.randint(18, 80, 1000),
    'income': np.random.randint(20000, 200000, 1000),
    'country': np.random.choice(['US', 'UK', 'CN', 'JP'], 1000)
})

# 将结果赋值给与节点ID相同的变量名
load_raw_data = users_data
print(f"已加载 {len(load_raw_data)} 条用户记录")
print(f"字段: {list(load_raw_data.columns)}")

# 保存结果到文件
os.makedirs('parquets', exist_ok=True)
load_raw_data.to_parquet('parquets/load_raw_data.parquet')
print("✓ 数据已保存到 parquets/load_raw_data.parquet")""",
        node_type="data_source",
        node_id="load_raw_data",
        name="加载原始数据",
        execution_status=ExecutionStatus.VALIDATED.value
    )

    # 2. Markdown描述 (说明数据的含义)
    manager.append_markdown_cell(
        "### 原始用户数据\n\n"
        "从 CSV 文件加载的原始用户数据，包含以下字段:\n\n"
        "- **user_id**: 用户唯一标识\n"
        "- **age**: 用户年龄 (18-80 岁)\n"
        "- **income**: 用户年收入\n"
        "- **country**: 用户所在国家\n\n"
        "**数据规模**: 1000 条用户记录\n\n"
        "该数据将作为后续数据清理和特征工程的基础数据源。",
        linked_node_id="load_raw_data"
    )

    # 3. 结果展示 (从parquet加载并显示)
    manager.append_result_cell(
        node_id="load_raw_data",
        parquet_path="parquets/load_raw_data.parquet",
        description="原始用户数据展示"
    )

    # ===== 第二阶段: 数据清理 =====
    # 1. 代码节点 (数据清理)
    manager.append_code_cell(
        code="""import os

# 数据清理: 处理缺失值和异常值
cleaned_data = load_raw_data.copy()

# 移除缺失值
cleaned_data = cleaned_data.dropna()

# 移除异常值 (年龄范围: 18-100)
cleaned_data = cleaned_data[
    (cleaned_data['age'] >= 18) &
    (cleaned_data['age'] <= 100)
]

# 将清理后的数据赋值给clean_data变量
clean_data = cleaned_data
print(f"清理后的数据: {len(clean_data)} 条记录")
print(f"数据质量: {(len(clean_data)/len(load_raw_data)*100):.1f}%")
print(f"移除记录数: {len(load_raw_data) - len(clean_data)}")

# 保存结果到文件
os.makedirs('parquets', exist_ok=True)
clean_data.to_parquet('parquets/clean_data.parquet')
print("✓ 数据已保存到 parquets/clean_data.parquet")""",
        node_type="compute",
        node_id="clean_data",
        depends_on=["load_raw_data"],
        name="数据清理",
        execution_status=ExecutionStatus.VALIDATED.value
    )

    # 2. Markdown描述 (说明清理过程)
    manager.append_markdown_cell(
        "### 清理后的用户数据\n\n"
        "对原始数据进行数据质量检查和清理:\n\n"
        "**处理步骤**:\n"
        "1. 删除缺失值行\n"
        "2. 移除异常值 (年龄不在 18-100 范围内)\n"
        "3. 数据类型验证和转换\n\n"
        "**清理结果**:\n"
        "- 保留记录: ~990 条 (移除异常数据)\n"
        "- 数据质量: >99%\n\n"
        "清理后的数据已准备好用于特征工程和分析。",
        linked_node_id="clean_data"
    )

    # 3. 结果展示
    manager.append_result_cell(
        node_id="clean_data",
        parquet_path="parquets/clean_data.parquet",
        description="清理后的用户数据"
    )

    # ===== 第三阶段: 特征工程 =====
    # 1. 代码节点 (特征工程)
    manager.append_code_cell(
        code="""import os

# 特征工程: 创建新的分析特征
featured_data = clean_data.copy()

# 创建年龄分组
featured_data['age_group'] = pd.cut(
    featured_data['age'],
    bins=[18, 30, 45, 60, 100],
    labels=['18-30', '30-45', '45-60', '60+']
)

# 创建收入等级
featured_data['income_level'] = pd.cut(
    featured_data['income'],
    bins=[0, 50000, 100000, 150000, 300000],
    labels=['Low', 'Medium', 'High', 'Very High']
)

# 创建交叉特征
featured_data['age_income_ratio'] = featured_data['income'] / featured_data['age']

# 将结果赋值给feature_engineering变量
feature_engineering = featured_data
print(f"特征工程完成，新增特征数: 3")
print(f"总特征数: {len(featured_data.columns)}")
print(f"新增特征: age_group, income_level, age_income_ratio")

# 保存结果到文件
os.makedirs('parquets', exist_ok=True)
feature_engineering.to_parquet('parquets/feature_engineering.parquet')
print("✓ 数据已保存到 parquets/feature_engineering.parquet")""",
        node_type="compute",
        node_id="feature_engineering",
        depends_on=["clean_data"],
        name="特征工程",
        execution_status=ExecutionStatus.VALIDATED.value
    )

    # 2. Markdown描述 (说明新特征)
    manager.append_markdown_cell(
        "### 特征工程后的数据\n\n"
        "通过组合和转换原始特征，创建了三个新的分析特征:\n\n"
        "**新增特征**:\n"
        "- **age_group**: 年龄分组 (18-30, 30-45, 45-60, 60+)\n"
        "- **income_level**: 收入等级分组 (Low, Medium, High, Very High)\n"
        "- **age_income_ratio**: 年龄与收入的比率\n\n"
        "**特征用途**:\n"
        "- 用于群组分析\n"
        "- 用于风险评估\n"
        "- 用于模型输入\n\n"
        "这些特征将用于后续的统计分析和可视化。",
        linked_node_id="feature_engineering"
    )

    # 3. 结果展示
    manager.append_result_cell(
        node_id="feature_engineering",
        parquet_path="parquets/feature_engineering.parquet",
        description="特征工程后的数据"
    )

    # ===== 第四阶段: 统计分析 =====
    # 1. 代码节点 (统计分析)
    manager.append_code_cell(
        code="""import json
import os

# 统计分析: 生成汇总统计
stats_by_age = feature_engineering.groupby('age_group').agg({
    'income': ['mean', 'median', 'std'],
    'user_id': 'count'
}).round(2)

stats_by_country = feature_engineering.groupby('country').agg({
    'user_id': 'count',
    'income': 'mean'
}).round(2)

stats_by_income_level = feature_engineering.groupby('income_level').agg({
    'user_id': 'count',
    'age': 'mean',
    'age_income_ratio': 'mean'
}).round(2)

# 汇总所有统计结果
statistics = {
    'stats_by_age': stats_by_age.to_dict(),
    'stats_by_country': stats_by_country.to_dict(),
    'stats_by_income_level': stats_by_income_level.to_dict()
}

print("统计分析完成")
print("\\n按年龄分组的收入统计:")
print(stats_by_age)
print("\\n按国家的用户分布:")
print(stats_by_country)

# 保存统计结果到JSON文件
os.makedirs('parquets', exist_ok=True)
with open('parquets/statistics.json', 'w') as f:
    json.dump(statistics, f, indent=2)
print("✓ 统计结果已保存到 parquets/statistics.json")""",
        node_type="compute",
        node_id="statistics",
        depends_on=["feature_engineering"],
        name="统计分析",
        execution_status=ExecutionStatus.PENDING_VALIDATION.value
    )

    # 2. Markdown描述 (说明统计结果)
    manager.append_markdown_cell(
        "### 统计分析结果\n\n"
        "按多个维度对特征工程后的数据进行统计分析:\n\n"
        "**分析维度**:\n"
        "1. **按年龄分组**: 计算不同年龄组的平均收入、中位数和标准差\n"
        "2. **按国家**: 统计不同国家的用户数量和平均收入\n"
        "3. **按收入等级**: 统计不同收入等级的用户数和平均年龄\n\n"
        "**关键指标**:\n"
        "- 平均值、中位数、标准差\n"
        "- 用户数量分布\n"
        "- 收入等级分布\n\n"
        "这些统计结果可用于业务决策和风险评估。",
        linked_node_id="statistics"
    )

    # 3. 结果展示 (JSON格式)
    manager.append_result_cell(
        node_id="statistics",
        parquet_path="parquets/statistics.json",
        result_format="json",
        description="统计分析结果 (JSON格式)"
    )

    # ===== 第五阶段: 可视化 =====
    # 1. 代码节点 (可视化)
    manager.append_code_cell(
        code="""import matplotlib.pyplot as plt
import json
import os

# 可视化: 创建图表展示数据分布
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. 年龄分布直方图
axes[0, 0].hist(feature_engineering['age'], bins=20, color='skyblue', edgecolor='black')
axes[0, 0].set_title('Age Distribution')
axes[0, 0].set_xlabel('Age')
axes[0, 0].set_ylabel('Count')

# 2. 收入分布直方图
axes[0, 1].hist(feature_engineering['income'], bins=20, color='lightgreen', edgecolor='black')
axes[0, 1].set_title('Income Distribution')
axes[0, 1].set_xlabel('Income')
axes[0, 1].set_ylabel('Count')

# 3. 按国家的用户数分布
country_counts = feature_engineering['country'].value_counts()
axes[1, 0].bar(country_counts.index, country_counts.values, color='coral', edgecolor='black')
axes[1, 0].set_title('Users by Country')
axes[1, 0].set_xlabel('Country')
axes[1, 0].set_ylabel('Count')

# 4. 收入等级分布
income_level_counts = feature_engineering['income_level'].value_counts()
axes[1, 1].bar(income_level_counts.index, income_level_counts.values, color='plum', edgecolor='black')
axes[1, 1].set_title('Users by Income Level')
axes[1, 1].set_xlabel('Income Level')
axes[1, 1].set_ylabel('Count')

plt.tight_layout()
plt.show()

# 保存图表配置和图片文件
os.makedirs('visualizations', exist_ok=True)
visualization = {'charts': ['age_dist', 'income_dist', 'country_dist', 'income_level_dist']}

# 保存为JSON配置文件
with open('visualizations/visualization.json', 'w') as f:
    json.dump(visualization, f, indent=2)
print("✓ 图表配置已保存到 visualizations/visualization.json")

# 保存图表为PNG文件
fig.savefig('visualizations/visualization.png', dpi=100, bbox_inches='tight')
print("✓ 图表已保存到 visualizations/visualization.png")

print("可视化完成，生成 4 个图表")""",
        node_type="chart",
        node_id="visualization",
        depends_on=["feature_engineering"],
        name="数据可视化",
        execution_status=ExecutionStatus.NOT_EXECUTED.value
    )

    # 2. Markdown描述 (说明图表)
    manager.append_markdown_cell(
        "### 数据可视化\n\n"
        "通过多个图表直观展示用户数据的分布特征:\n\n"
        "**图表类型**:\n"
        "1. **年龄分布直方图**: 显示用户年龄的分布规律\n"
        "2. **收入分布直方图**: 显示用户收入的分布规律\n"
        "3. **按国家分布**: 显示不同国家的用户数量\n"
        "4. **收入等级分布**: 显示用户在不同收入等级中的分布\n\n"
        "**观察要点**:\n"
        "- 用户年龄主要集中在 30-60 岁\n"
        "- 收入分布呈现多峰分布\n"
        "- 来自不同国家的用户分布相对均衡\n\n"
        "这些图表可用于业务演示和决策支持。",
        linked_node_id="visualization"
    )

    # 3. 结果展示 (加载图表配置和图片)
    manager.append_result_cell(
        node_id="visualization",
        parquet_path="visualizations/visualization.json",
        result_format="visualization",
        description="数据可视化展示"
    )

    # Save the notebook
    manager.save()
    print(f"✓ Notebook 已保存到: {manager.notebook_path}")
    print(f"✓ 总 cell 数: {manager.get_cell_count()}")
    print(f"✓ 节点 cell 数: {len(manager.list_node_cells())}")

    # Print cell structure for verification
    print("\n=== Cell 结构验证 ===")
    cells = manager.get_cells()
    for i, cell in enumerate(cells):
        cell_type = cell['cell_type']
        node_type = cell['metadata'].get('node_type', '-')
        node_id = cell['metadata'].get('node_id', '-')
        result_cell = cell['metadata'].get('result_cell', False)
        linked_node_id = cell['metadata'].get('linked_node_id', '-')
        execution_status = cell['metadata'].get('execution_status', '-')

        if cell_type == 'markdown':
            if linked_node_id != '-':
                print(f"[{i:2d}] MARKDOWN -> 链接到节点: {linked_node_id}")
            else:
                print(f"[{i:2d}] MARKDOWN -> 通用描述")
        elif cell_type == 'code':
            if result_cell:
                print(f"[{i:2d}] RESULT   <- 节点: {node_id}")
            elif node_type != '-':
                print(f"[{i:2d}] CODE     | 节点: {node_id}, 类型: {node_type}, 状态: {execution_status}")
            else:
                print(f"[{i:2d}] CODE     | 普通代码")


if __name__ == "__main__":
    create_example_notebook()
