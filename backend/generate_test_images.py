#!/usr/bin/env python3
"""
Generate test images for image nodes in test projects
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Get project directories
base_dir = Path(__file__).parent.parent / "projects"

# Test 1: Generate behavior_chart.png for test_user_behavior_analysis
test1_parquets = base_dir / "test_user_behavior_analysis" / "parquets"
test1_parquets.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(12, 6))
engagement_levels = ['Low\n(0-33)', 'Medium\n(34-66)', 'High\n(67-100)']
user_counts = [20, 50, 30]
colors = ['#e74c3c', '#f39c12', '#27ae60']

bars = ax.bar(engagement_levels, user_counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=12, fontweight='bold')

ax.set_ylabel('Number of Users', fontsize=12)
ax.set_title('User Engagement Distribution', fontsize=14, fontweight='bold')
ax.set_ylim(0, max(user_counts) * 1.1)

plt.tight_layout()
chart_path = test1_parquets / "behavior_chart.png"
plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
plt.close()
print(f"✓ Generated: {chart_path}")

# Test 2: Generate visualization.png for test_sales_performance_report
test2_parquets = base_dir / "test_sales_performance_report" / "parquets"
test2_parquets.mkdir(parents=True, exist_ok=True)

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

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))

plt.tight_layout()
viz_path = test2_parquets / "visualization.png"
plt.savefig(str(viz_path), dpi=150, bbox_inches='tight')
plt.close()
print(f"✓ Generated: {viz_path}")

print("\n✅ All test images generated successfully!")
