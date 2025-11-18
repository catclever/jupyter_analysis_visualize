#!/usr/bin/env python3
"""
Create a test project with a single compute node that outputs dict of DataFrames.

This project is used to test the new dict-of-DataFrames support in result saving/loading.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_manager import ProjectManager
from notebook_manager import NotebookManager


def create_dict_result_test_project():
    """Create a test project with dict of DataFrames result"""

    project_id = "dict_result_test"
    project_name = "Dict of DataFrames Test"
    projects_dir = Path(__file__).parent.parent.parent / "projects"
    project_path = projects_dir / project_id

    print("=" * 80)
    print("Creating Dict Result Test Project")
    print("=" * 80)

    # Create project directory
    project_path.mkdir(parents=True, exist_ok=True)
    parquets_dir = project_path / "parquets"
    parquets_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n✓ Created project directory: {project_path}")

    # Create project.json with one compute node
    project_data = {
        "project_id": project_id,
        "name": project_name,
        "description": "Test project for dict of DataFrames result format",
        "version": "1.0.0",
        "created_date": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "notebook_path": "project.ipynb",
        "nodes": {
            "create_summaries": {
                "node_id": "create_summaries",
                "node_type": "compute",
                "name": "Create Multiple Summaries",
                "depends_on": [],
                "execution_status": "not_executed",
                "result_format": "parquet",
                "result_path": None,
            }
        },
        "dag_metadata": {
            "total_nodes": 1,
            "node_types": {"compute": 1},
            "max_depth": 0,
            "has_cycles": False,
        },
    }

    with open(project_path / "project.json", "w") as f:
        json.dump(project_data, f, indent=2)

    print("✓ Created project.json")

    # Create sample data CSV
    sample_csv = """date,value,category
2025-01-01,100,A
2025-01-02,150,B
2025-01-03,200,A
2025-01-04,120,C
2025-01-05,180,B
2025-01-06,220,A
2025-01-07,140,C
"""

    with open(project_path / "sample_data.csv", "w") as f:
        f.write(sample_csv)

    print("✓ Created sample_data.csv")

    # Create notebook with compute node
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "node_id": "create_summaries",
                    "node_type": "compute",
                    "execution_status": "not_executed",
                },
                "outputs": [],
                "source": [
                    "# ===== System-managed metadata (auto-generated, understand to edit) =====\n",
                    "# @node_type: compute\n",
                    "# @node_id: create_summaries\n",
                    "# @execution_status: not_executed\n",
                    "# @depends_on: []\n",
                    "# @name: Create Multiple Summaries\n",
                    "# ===== End of system-managed metadata =====\n",
                    "\n",
                    "import pandas as pd\n",
                    "import os\n",
                    "\n",
                    "# Load sample data\n",
                    "csv_path = os.path.join(os.getcwd(), 'sample_data.csv')\n",
                    "df = pd.read_csv(csv_path)\n",
                    "\n",
                    "# Create multiple summaries as dict\n",
                    "create_summaries = {\n",
                    "    'daily_summary': df.groupby('date').agg({'value': 'sum'}).reset_index(),\n",
                    "    'category_summary': df.groupby('category').agg({'value': ['sum', 'mean']}).reset_index(),\n",
                    "    'all_records': df,\n",
                    "}\n",
                    "\n",
                    "# Print info about each summary\n",
                    "for key, summary_df in create_summaries.items():\n",
                    "    print(f'Summary {key}:')\n",
                    "    print(f'  Shape: {summary_df.shape}')\n",
                    "    print(f'  Columns: {list(summary_df.columns)}')\n",
                    "    print()\n",
                ],
            }
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {
                "name": "python",
                "version": "3.10.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    with open(project_path / "project.ipynb", "w") as f:
        json.dump(notebook, f, indent=2)

    print("✓ Created project.ipynb with compute node")
    print("\nProject Structure:")
    print(f"  {project_path}/")
    print(f"    project.json")
    print(f"    project.ipynb")
    print(f"    sample_data.csv")
    print(f"    parquets/")

    print("\n" + "=" * 80)
    print("✓ Test project created successfully!")
    print("=" * 80)

    print("\nNode Details:")
    print("  node_id: create_summaries")
    print("  type: compute")
    print("  input: reads sample_data.csv")
    print("  output: dict of DataFrames with keys:")
    print("    - daily_summary: sum of values by date")
    print("    - category_summary: sum/mean of values by category")
    print("    - all_records: original data")
    print("  result_format: parquet (will save each df separately)")

    print("\nNext Steps:")
    print("1. Execute the create_summaries node via the API")
    print("2. Check parquets/create_summaries/ directory for:")
    print("   - _metadata.json (dict structure)")
    print("   - daily_summary.parquet")
    print("   - category_summary.parquet")
    print("   - all_records.parquet")
    print("3. Verify loading works by executing a dependent node")

    return project_path


if __name__ == "__main__":
    project_path = create_dict_result_test_project()
    print(f"\n✓ Project ready at: {project_path}")
