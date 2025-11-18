"""
Generate two sample projects with executed nodes for frontend testing

Projects:
1. User Behavior Analysis - Data analysis workflow
2. Sales Performance Report - Business intelligence workflow
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_manager import ProjectManager


def create_user_behavior_analysis():
    """Create a user behavior analysis project with executed nodes"""
    print("\n" + "=" * 70)
    print("Creating Project 1: User Behavior Analysis")
    print("=" * 70)

    projects_root = Path("../projects")  # 项目根目录
    pm = ProjectManager(str(projects_root), "test_user_behavior_analysis")  # test_ 前缀

    # Create project
    pm.create(
        name="User Behavior Analysis",
        description="Analyze user behavior patterns from activity logs",
        version="1.0.0"
    )

    print(f"✓ Project created: {pm.project_id}")

    # Load project for adding nodes
    pm.load()

    # Node 1: Load User Data
    user_data = pd.DataFrame({
        "user_id": range(1, 101),
        "age": np.random.randint(18, 80, 100),
        "signup_date": pd.date_range("2023-01-01", periods=100),
        "country": np.random.choice(["USA", "UK", "CN", "JP", "DE"], 100),
        "premium": np.random.choice([True, False], 100)
    })

    user_data_path = pm.save_node_result("user_data", user_data, result_type="parquet")

    pm.add_node(
        node_id="user_data",
        node_type="data_source",
        name="Load User Data",
        code="""import pandas as pd

# Load user data from CSV
user_data = pd.read_csv('users.csv')
print(f"Loaded {len(user_data)} users")""",
        node_description="""## User Data Source

**Description**: Contains basic user profile information

### Schema

| Column | Type | Description |
|--------|------|-------------|
| user_id | Integer | Unique user identifier (1-100) |
| age | Integer | User age (18-80 years) |
| signup_date | DateTime | Account creation date (2023-01-01 onwards) |
| country | String | User's country (USA, UK, CN, JP, DE) |
| premium | Boolean | Premium subscription status |

### Statistics

- **Total Records**: 100 users
- **Date Range**: 2023-01-01 to 2023-04-10
- **Countries**: 5 different countries
- **Premium Users**: ~50% of dataset""",
        execution_status="validated",
        result_format="parquet",
        result_path=user_data_path
    )

    print(f"  ✓ Node 1: user_data (validated)")

    # Node 2: Load Activity Data
    activity_data = pd.DataFrame({
        "user_id": np.random.randint(1, 101, 500),
        "activity_type": np.random.choice(["login", "click", "purchase", "view"], 500),
        "timestamp": pd.date_range("2024-01-01", periods=500),
        "duration_seconds": np.random.randint(1, 300, 500)
    })

    activity_path = pm.save_node_result("activity_data", activity_data, result_type="parquet")

    pm.add_node(
        node_id="activity_data",
        node_type="data_source",
        name="Load Activity Data",
        code="""import pandas as pd

# Load user activity logs
activity_data = pd.read_csv('activity.csv')
print(f"Loaded {len(activity_data)} activity records")""",
        node_description="""## Activity Data Source

**Description**: User activity event log from the platform

### Schema

| Column | Type | Description |
|--------|------|-------------|
| user_id | Integer | User identifier |
| activity_type | String | Type of activity (login, click, purchase, view) |
| timestamp | DateTime | When activity occurred |
| duration_seconds | Integer | Duration of activity (1-300 seconds) |

### Statistics

- **Total Records**: 500 events
- **Date Range**: 2024-01-01 onwards
- **Activity Types**: 4 categories
- **Avg Duration**: ~150 seconds per activity
- **Users Covered**: 100 users""",
        execution_status="validated",
        result_format="parquet",
        result_path=activity_path
    )

    print(f"  ✓ Node 2: activity_data (validated)")

    # Node 3: Merge Data
    merged_data = user_data.merge(
        activity_data,
        on="user_id",
        how="left"
    )

    merged_path = pm.save_node_result("merged_data", merged_data, result_type="parquet")

    pm.add_node(
        node_id="merged_data",
        node_type="compute",
        name="Merge Datasets",
        depends_on=["user_data", "activity_data"],
        code="""import pandas as pd

# Merge user and activity data
merged_data = user_data.merge(
    activity_data,
    on='user_id',
    how='left'
)
print(f"Merged dataset shape: {merged_data.shape}")""",
        node_description="""## Merged Dataset

**Description**: Combines user profiles with their activity logs using left join

### Operation

- **Join Type**: Left join on `user_id`
- **Left Table**: user_data (100 rows)
- **Right Table**: activity_data (500 rows)
- **Result**: All users with their associated activities

### Output Schema

Combines all columns from both sources:
- From user_data: user_id, age, signup_date, country, premium
- From activity_data: activity_type, timestamp, duration_seconds

### Statistics

- **Total Records**: 500 activity records
- **Users Represented**: 100 users
- **Columns**: 9 total columns""",
        execution_status="validated",
        result_format="parquet",
        result_path=merged_path
    )

    print(f"  ✓ Node 3: merged_data (validated)")

    # Node 4: Compute Statistics
    stats_df = pd.DataFrame({
        "metric": ["total_users", "total_activities", "avg_age", "premium_ratio"],
        "value": [
            len(user_data),
            len(activity_data),
            float(user_data['age'].mean()),
            float((user_data['premium'].sum() / len(user_data)))
        ]
    })

    stats_path = pm.save_node_result("statistics", stats_df, result_type="parquet")

    pm.add_node(
        node_id="statistics",
        node_type="compute",
        name="Compute Statistics",
        depends_on=["merged_data", "user_data"],
        code="""import pandas as pd

# Calculate statistics from merged data and user data
statistics = {
    'total_users': len(user_data),
    'total_activities': len(merged_data),
    'avg_age': merged_data['age'].mean(),
    'premium_ratio': (user_data['premium'].sum() / len(user_data))
}
print(statistics)""",
        node_description="""## Summary Statistics

**Description**: Key statistics computed from merged user and activity data

### Computed Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| total_users | 100 | Number of unique users |
| total_activities | 500 | Total activity events recorded |
| avg_age | ~45 | Average user age |
| premium_ratio | 0.5 | Proportion of premium users |

### Insights

- Average user age is approximately 45 years
- Activity data shows 500 total interactions across 100 users
- About half of the user base has premium subscriptions""",
        execution_status="validated",
        result_format="parquet",
        result_path=stats_path
    )

    print(f"  ✓ Node 4: statistics (validated)")

    # Node 5: Generate Report
    report_df = pd.DataFrame({
        "title": ["User Behavior Analysis Report"],
        "generated_at": ["2024-11-07"],
        "status": ["completed"]
    })

    report_path = pm.save_node_result(
        "report",
        report_df,
        result_type="parquet"
    )

    pm.add_node(
        node_id="report",
        node_type="compute",
        name="Generate Report",
        depends_on=[],
        code="""import pandas as pd

# Generate final report
report = {
    'title': 'User Behavior Analysis Report',
    'generated_at': '2024-11-07',
    'status': 'completed'
}
print(report)""",
        node_description="""## Analysis Report

**Description**: Final report summarizing the user behavior analysis

### Report Contents

- **Title**: User Behavior Analysis Report
- **Generated**: 2024-11-07
- **Status**: Completed

### Key Findings

This report presents the consolidated analysis of user behavior patterns derived from:
1. Basic user demographic information (100 users)
2. Activity event logs (500 recorded events)
3. Aggregated statistics from the merged dataset

### Report Structure

- Executive summary of key metrics
- User segmentation analysis
- Activity type distribution
- Premium vs standard user comparison""",
        execution_status="validated",
        result_format="parquet",
        result_path=report_path
    )

    print(f"  ✓ Node 5: report (validated)")

    print(f"\n✓ Project '{pm.metadata.name}' created successfully")
    print(f"  Path: {pm.project_path}")
    print(f"  Total nodes: 5")
    print(f"  Executed nodes: 5 (validated)")


def create_sales_performance_project():
    """Create a sales performance report project with executed nodes"""
    print("\n" + "=" * 70)
    print("Creating Project 2: Sales Performance Report")
    print("=" * 70)

    projects_root = Path("../projects")  # 项目根目录
    pm = ProjectManager(str(projects_root), "test_sales_performance_report")  # test_ 前缀

    # Create project
    pm.create(
        name="Sales Performance Report",
        description="Track and analyze sales performance metrics",
        version="1.0.0"
    )

    print(f"✓ Project created: {pm.project_id}")

    # Load project for adding nodes
    pm.load()

    # Node 1: Load Sales Data
    sales_data = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=90),
        "region": np.random.choice(["North", "South", "East", "West"], 90),
        "sales_amount": np.random.randint(10000, 100000, 90),
        "units_sold": np.random.randint(100, 1000, 90),
        "salesman": np.random.choice(["Alice", "Bob", "Charlie", "Diana"], 90)
    })

    sales_path = pm.save_node_result("sales_data", sales_data, result_type="parquet")

    pm.add_node(
        node_id="sales_data",
        node_type="data_source",
        name="Load Sales Data",
        code="""import pandas as pd

# Load sales records from database
sales_data = pd.read_csv('sales.csv')
print(f"Loaded {len(sales_data)} sales records")""",
        node_description="""## Sales Transaction Data

**Description**: Daily sales records across regions and salespeople

### Schema

| Column | Type | Description |
|--------|------|-------------|
| date | DateTime | Transaction date |
| region | String | Sales region (North, South, East, West) |
| sales_amount | Integer | Revenue in dollars (10k-100k) |
| units_sold | Integer | Number of units sold (100-1000) |
| salesman | String | Name of salesperson |

### Statistics

- **Total Records**: 90 daily sales entries
- **Date Range**: 2024-01-01 to 2024-03-31 (Q1 2024)
- **Regions**: 4 regions
- **Salespeople**: 4 salespeople (Alice, Bob, Charlie, Diana)
- **Revenue Range**: $10k - $100k per transaction""",
        execution_status="validated",
        result_format="parquet",
        result_path=sales_path
    )

    print(f"  ✓ Node 1: sales_data (validated)")

    # Node 2: Load Target Data
    targets = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "monthly_target": [250000, 300000, 280000, 320000],
        "quarterly_target": [750000, 900000, 840000, 960000]
    })

    targets_path = pm.save_node_result("targets", targets, result_type="parquet")

    pm.add_node(
        node_id="targets",
        node_type="data_source",
        name="Load Sales Targets",
        code="""import pandas as pd

# Load regional sales targets
targets = pd.read_csv('targets.csv')
print(f"Loaded targets for {len(targets)} regions")""",
        node_description="""## Sales Targets by Region

**Description**: Monthly and quarterly sales targets for each region

### Schema

| Column | Type | Description |
|--------|------|-------------|
| region | String | Region name |
| monthly_target | Integer | Monthly revenue target in dollars |
| quarterly_target | Integer | Quarterly revenue target in dollars |

### Regional Targets

| Region | Monthly | Quarterly |
|--------|---------|-----------|
| North | $250,000 | $750,000 |
| South | $300,000 | $900,000 |
| East | $280,000 | $840,000 |
| West | $320,000 | $960,000 |

### Summary

- **Total Quarterly Target**: $3,450,000
- **Total Monthly Target**: $1,150,000
- **Highest Target**: West region""",
        execution_status="validated",
        result_format="parquet",
        result_path=targets_path
    )

    print(f"  ✓ Node 2: targets (validated)")

    # Node 3: Process Sales Data
    processed_sales = sales_data.groupby('region').agg({
        'sales_amount': 'sum',
        'units_sold': 'sum'
    }).reset_index()

    processed_path = pm.save_node_result("processed_sales", processed_sales, result_type="parquet")

    pm.add_node(
        node_id="processed_sales",
        node_type="compute",
        name="Process Sales Data",
        depends_on=["sales_data"],
        code="""import pandas as pd

# Process and aggregate sales data
processed_sales = sales_data.groupby('region').agg({
    'sales_amount': 'sum',
    'units_sold': 'sum'
}).reset_index()
print(processed_sales)""",
        node_description="""## Sales Aggregated by Region

**Description**: Sales data aggregated at the regional level for quarterly analysis

### Operation

- **Grouping**: By region
- **Aggregation**: Sum of sales_amount and units_sold
- **Result**: One row per region

### Output Schema

| Column | Type | Description |
|--------|------|-------------|
| region | String | Region name |
| sales_amount | Integer | Total sales revenue |
| units_sold | Integer | Total units sold |

### Quarterly Summary

All data is aggregated from Q1 2024 (90 days of transactions)""",
        execution_status="validated",
        result_format="parquet",
        result_path=processed_path
    )

    print(f"  ✓ Node 3: processed_sales (validated)")

    # Node 4: Calculate Performance Metrics
    metrics_df = pd.DataFrame({
        "metric": ["total_sales", "total_units", "average_deal_size"],
        "value": [
            float(sales_data['sales_amount'].sum()),
            float(sales_data['units_sold'].sum()),
            float(sales_data['sales_amount'].mean())
        ]
    })

    metrics_path = pm.save_node_result("metrics", metrics_df, result_type="parquet")

    pm.add_node(
        node_id="metrics",
        node_type="compute",
        name="Calculate Performance Metrics",
        depends_on=["processed_sales", "targets"],
        code="""import pandas as pd

# Calculate KPIs and performance metrics
metrics = {
    'total_sales': processed_sales['sales_amount'].sum(),
    'avg_deal_size': processed_sales['sales_amount'].mean(),
    'by_region': processed_sales.to_dict('records')
}
print(metrics)""",
        node_description="""## Performance Metrics

**Description**: Key performance indicators comparing actual sales to targets

### Computed Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| total_sales | ~4.5M | Total sales revenue across all regions |
| total_units | ~50K | Total units sold |
| average_deal_size | ~50K | Average transaction value |

### Analysis

- Quarterly sales total computed from daily transaction data
- Regional breakdown available for target comparison
- Average deal size indicates transaction patterns

### Key Insights

- Total Q1 2024 sales revenue
- Performance baseline for comparing against quarterly targets
- Regional variation in sales patterns""",
        execution_status="validated",
        result_format="parquet",
        result_path=metrics_path
    )

    print(f"  ✓ Node 4: metrics (validated)")

    # Node 5: Visualize Results
    # 生成实际的图表图片文件
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端

    fig, ax = plt.subplots(figsize=(10, 6))
    regions = ['North', 'South', 'East', 'West']
    sales = [800000, 850000, 920000, 980000]
    targets = [750000, 900000, 840000, 960000]

    x = range(len(regions))
    width = 0.35
    ax.bar([i - width/2 for i in x], sales, width, label='Actual Sales', color='#3498db')
    ax.bar([i + width/2 for i in x], targets, width, label='Target', color='#e74c3c')

    ax.set_ylabel('Amount ($)', fontsize=12)
    ax.set_title('Sales Performance vs Target by Region', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(regions)
    ax.legend()

    # 格式化 y 轴为货币
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))

    plt.tight_layout()

    # 保存图表到 visualizations/ 目录
    viz_path = pm.visualizations_path / "visualization.png"
    plt.savefig(str(viz_path), dpi=150, bbox_inches='tight')
    plt.close(fig)

    pm.add_node(
        node_id="visualization",
        node_type="chart",
        name="Visualize Results",
        depends_on=[],
        code="""import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Create visualization
fig, ax = plt.subplots(figsize=(10, 6))
regions = ['North', 'South', 'East', 'West']
sales = [800000, 850000, 920000, 980000]
target_values = [750000, 900000, 840000, 960000]

x = range(len(regions))
width = 0.35
ax.bar([i - width/2 for i in x], sales, width, label='Actual Sales', color='#3498db')
ax.bar([i + width/2 for i in x], target_values, width, label='Target', color='#e74c3c')

ax.set_ylabel('Amount ($)', fontsize=12)
ax.set_title('Sales Performance vs Target by Region', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(regions)
ax.legend()

# 格式化 y 轴为货币
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))

plt.tight_layout()

# 保存图表为 PNG 文件
import os
os.makedirs('visualizations', exist_ok=True)
plt.savefig('visualizations/visualize_results.png', dpi=150, bbox_inches='tight')
print("✓ Chart saved to visualizations/visualize_results.png")""",
        node_description="""## Sales vs Target Comparison Chart

**Description**: Grouped bar chart comparing actual sales to quarterly targets by region

### Visualization Details

- **Chart Type**: Grouped Bar Chart
- **X-Axis**: Regions (North, South, East, West)
- **Y-Axis**: Revenue in millions of dollars
- **Blue Bars**: Actual sales achieved
- **Red Bars**: Target sales goals

### Data Representation

Each region shows two bars side-by-side:
- **Actual Sales**: Performance achieved in Q1 2024
- **Target**: The target that was set for that region

### Key Observations

- West region shows strongest performance
- All regions demonstrated solid sales relative to targets
- Chart makes it easy to spot regional over/under performance""",
        execution_status="validated",
        result_format="image",
        result_path="visualizations/visualization.png"
    )

    print(f"  ✓ Node 5: visualization (validated)")

    print(f"\n✓ Project '{pm.metadata.name}' created successfully")
    print(f"  Path: {pm.project_path}")
    print(f"  Total nodes: 5")
    print(f"  Executed nodes: 5 (validated)")


def main():
    """Create all test projects"""
    print("\n" + "=" * 70)
    print("Generating Test Projects for Frontend Development")
    print("=" * 70)

    # Create projects
    create_user_behavior_analysis()
    create_sales_performance_project()

    # List created projects
    projects_root = Path("../projects")
    print("\n" + "=" * 70)
    print("Created Projects Summary")
    print("=" * 70)

    for project_dir in sorted(projects_root.iterdir()):
        if project_dir.is_dir() and project_dir.name.startswith("test_"):
            project_id = project_dir.name
            pm = ProjectManager(str(projects_root), project_id)
            pm.load()

            print(f"\n✓ Project: {pm.metadata.name}")
            print(f"  ID: {project_id}")
            print(f"  Path: {project_dir}")
            print(f"  Nodes:")
            for node in pm.metadata.nodes.values():
                print(f"    - {node['node_id']} ({node['type']}) - Status: {node['execution_status']}")

    print("\n" + "=" * 70)
    print("✓ Test projects created successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
