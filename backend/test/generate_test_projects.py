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

    projects_root = Path("test_projects")
    pm = ProjectManager(str(projects_root), "user_behavior_analysis")

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

    user_data_path = pm.save_node_result("load_user_data", user_data, result_type="parquet")

    pm.add_node(
        node_id="load_user_data",
        node_type="data_source",
        name="Load User Data",
        code="""import pandas as pd

# Load user data from CSV
user_data = pd.read_csv('users.csv')
print(f"Loaded {len(user_data)} users")""",
        node_description="Data source node: Loads user information from the database",
        execution_status="validated",
        result_format="parquet",
        result_path=user_data_path
    )

    print(f"  ✓ Node 1: load_user_data (validated)")

    # Node 2: Load Activity Data
    activity_data = pd.DataFrame({
        "user_id": np.random.randint(1, 101, 500),
        "activity_type": np.random.choice(["login", "click", "purchase", "view"], 500),
        "timestamp": pd.date_range("2024-01-01", periods=500),
        "duration_seconds": np.random.randint(1, 300, 500)
    })

    activity_path = pm.save_node_result("load_activity_data", activity_data, result_type="parquet")

    pm.add_node(
        node_id="load_activity_data",
        node_type="data_source",
        name="Load Activity Data",
        code="""import pandas as pd

# Load user activity logs
activity_data = pd.read_csv('activity.csv')
print(f"Loaded {len(activity_data)} activity records")""",
        node_description="Data source node: Loads user activity events",
        execution_status="validated",
        result_format="parquet",
        result_path=activity_path
    )

    print(f"  ✓ Node 2: load_activity_data (validated)")

    # Node 3: Merge Data
    merged_data = user_data.merge(
        activity_data,
        on="user_id",
        how="left"
    )

    merged_path = pm.save_node_result("merge_datasets", merged_data, result_type="parquet")

    pm.add_node(
        node_id="merge_datasets",
        node_type="compute",
        name="Merge Datasets",
        depends_on=["load_user_data", "load_activity_data"],
        code="""import pandas as pd

# Merge user and activity data
merged_data = user_data.merge(
    activity_data,
    on='user_id',
    how='left'
)
print(f"Merged dataset shape: {merged_data.shape}")""",
        node_description="Compute node: Joins user and activity datasets",
        execution_status="validated",
        result_format="parquet",
        result_path=merged_path
    )

    print(f"  ✓ Node 3: merge_datasets (validated)")

    # Node 4: Compute Statistics
    stats = {
        "total_users": len(user_data),
        "total_activities": len(activity_data),
        "avg_age": float(user_data['age'].mean()),
        "premium_ratio": float((user_data['premium'].sum() / len(user_data))),
        "countries": user_data['country'].value_counts().to_dict()
    }

    stats_path = pm.save_node_result("compute_statistics", stats, result_type="json")

    pm.add_node(
        node_id="compute_statistics",
        node_type="compute",
        name="Compute Statistics",
        depends_on=["merge_datasets"],
        code="""import json

# Calculate statistics
statistics = {
    'total_users': len(merged_data['user_id'].unique()),
    'total_activities': len(merged_data),
    'avg_age': merged_data['age'].mean(),
    'premium_ratio': (user_data['premium'].sum() / len(user_data))
}
print(json.dumps(statistics, indent=2))""",
        node_description="Compute node: Calculates summary statistics",
        execution_status="validated",
        result_format="json",
        result_path=stats_path
    )

    print(f"  ✓ Node 4: compute_statistics (validated)")

    # Node 5: Generate Report
    report_path = pm.save_node_result(
        "generate_report",
        {"status": "completed", "records": 500},
        result_type="json"
    )

    pm.add_node(
        node_id="generate_report",
        node_type="compute",
        name="Generate Report",
        depends_on=["compute_statistics"],
        code="""# Generate final report
report = {
    'title': 'User Behavior Analysis Report',
    'generated_at': '2024-11-07',
    'status': 'completed'
}
print(report)""",
        node_description="Compute node: Generates final analysis report",
        execution_status="validated",
        result_format="json",
        result_path=report_path
    )

    print(f"  ✓ Node 5: generate_report (validated)")

    print(f"\n✓ Project '{pm.metadata.name}' created successfully")
    print(f"  Path: {pm.project_path}")
    print(f"  Total nodes: 5")
    print(f"  Executed nodes: 5 (validated)")


def create_sales_performance_project():
    """Create a sales performance report project with executed nodes"""
    print("\n" + "=" * 70)
    print("Creating Project 2: Sales Performance Report")
    print("=" * 70)

    projects_root = Path("test_projects")
    pm = ProjectManager(str(projects_root), "sales_performance_report")

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

    sales_path = pm.save_node_result("load_sales_data", sales_data, result_type="parquet")

    pm.add_node(
        node_id="load_sales_data",
        node_type="data_source",
        name="Load Sales Data",
        code="""import pandas as pd

# Load sales records from database
sales_data = pd.read_csv('sales.csv')
print(f"Loaded {len(sales_data)} sales records")""",
        node_description="Data source node: Loads sales transactions",
        execution_status="validated",
        result_format="parquet",
        result_path=sales_path
    )

    print(f"  ✓ Node 1: load_sales_data (validated)")

    # Node 2: Load Target Data
    targets = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "monthly_target": [250000, 300000, 280000, 320000],
        "quarterly_target": [750000, 900000, 840000, 960000]
    })

    targets_path = pm.save_node_result("load_targets", targets, result_type="parquet")

    pm.add_node(
        node_id="load_targets",
        node_type="data_source",
        name="Load Sales Targets",
        code="""import pandas as pd

# Load regional sales targets
targets = pd.read_csv('targets.csv')
print(f"Loaded targets for {len(targets)} regions")""",
        node_description="Data source node: Loads regional sales targets",
        execution_status="validated",
        result_format="parquet",
        result_path=targets_path
    )

    print(f"  ✓ Node 2: load_targets (validated)")

    # Node 3: Process Sales Data
    processed_sales = sales_data.groupby('region').agg({
        'sales_amount': 'sum',
        'units_sold': 'sum'
    }).reset_index()

    processed_path = pm.save_node_result("process_sales", processed_sales, result_type="parquet")

    pm.add_node(
        node_id="process_sales",
        node_type="compute",
        name="Process Sales Data",
        depends_on=["load_sales_data"],
        code="""import pandas as pd

# Process and aggregate sales data
processed_sales = sales_data.groupby('region').agg({
    'sales_amount': 'sum',
    'units_sold': 'sum'
}).reset_index()
print(processed_sales)""",
        node_description="Compute node: Aggregates sales by region",
        execution_status="validated",
        result_format="parquet",
        result_path=processed_path
    )

    print(f"  ✓ Node 3: process_sales (validated)")

    # Node 4: Calculate Performance Metrics
    metrics = {
        "total_sales": float(sales_data['sales_amount'].sum()),
        "total_units": float(sales_data['units_sold'].sum()),
        "average_deal_size": float(sales_data['sales_amount'].mean()),
        "regions": {
            "North": {"sales": 800000, "target": 750000, "achievement": 106.7},
            "South": {"sales": 850000, "target": 900000, "achievement": 94.4},
            "East": {"sales": 920000, "target": 840000, "achievement": 109.5},
            "West": {"sales": 980000, "target": 960000, "achievement": 102.1}
        }
    }

    metrics_path = pm.save_node_result("calculate_metrics", metrics, result_type="json")

    pm.add_node(
        node_id="calculate_metrics",
        node_type="compute",
        name="Calculate Performance Metrics",
        depends_on=["process_sales", "load_targets"],
        code="""import json

# Calculate KPIs and performance metrics
metrics = {
    'total_sales': processed_sales['sales_amount'].sum(),
    'avg_deal_size': processed_sales['sales_amount'].mean(),
    'by_region': processed_sales.to_dict('records')
}
print(json.dumps(metrics, indent=2))""",
        node_description="Compute node: Calculates performance KPIs",
        execution_status="validated",
        result_format="json",
        result_path=metrics_path
    )

    print(f"  ✓ Node 4: calculate_metrics (validated)")

    # Node 5: Visualize Results
    viz_data = {
        "chart_type": "bar",
        "title": "Sales Performance by Region",
        "regions": ["North", "South", "East", "West"],
        "sales": [800000, 850000, 920000, 980000],
        "targets": [750000, 900000, 840000, 960000]
    }

    viz_path = pm.save_node_result("visualize_results", viz_data, result_type="json", is_visualization=True)

    pm.add_node(
        node_id="visualize_results",
        node_type="chart",
        name="Visualize Results",
        depends_on=["calculate_metrics"],
        code="""import matplotlib.pyplot as plt
import json

# Create visualization
fig, ax = plt.subplots(figsize=(10, 6))
regions = ['North', 'South', 'East', 'West']
sales = [800000, 850000, 920000, 980000]
targets = [750000, 900000, 840000, 960000]

x = range(len(regions))
width = 0.35
ax.bar([i - width/2 for i in x], sales, width, label='Actual Sales')
ax.bar([i + width/2 for i in x], targets, width, label='Target')

ax.set_ylabel('Amount ($)')
ax.set_title('Sales Performance vs Target by Region')
ax.set_xticks(x)
ax.set_xticklabels(regions)
ax.legend()

plt.tight_layout()
plt.savefig('sales_chart.png')

# Save visualization config
visualization = {
    'chart_type': 'bar',
    'title': 'Sales Performance by Region',
    'regions': regions,
    'sales': sales,
    'targets': targets
}
print(json.dumps(visualization, indent=2))""",
        node_description="Chart node: Visualizes sales performance",
        execution_status="validated",
        result_format="visualization",
        result_path=viz_path
    )

    print(f"  ✓ Node 5: visualize_results (validated)")

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
    projects_root = Path("test_projects")
    print("\n" + "=" * 70)
    print("Created Projects Summary")
    print("=" * 70)

    for project_dir in projects_root.iterdir():
        if project_dir.is_dir():
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
