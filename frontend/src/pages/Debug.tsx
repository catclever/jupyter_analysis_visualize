import React, { useEffect, useState } from 'react';
import { getProject, type ProjectNode, type ProjectEdge } from '@/services/api';
import { getNodeCategory, CATEGORY_LAYOUTS } from '@/config';

export function Debug() {
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error' | 'success'>('idle');

  useEffect(() => {
    const runDiagnostics = async () => {
      const debugLogs: string[] = [];

      debugLogs.push('=== 开始前端诊断 ===');
      debugLogs.push('');

      try {
        setStatus('loading');
        debugLogs.push('1. 正在加载 ecommerce_analytics 项目...');

        const project = await getProject('ecommerce_analytics');

        debugLogs.push(`✓ 项目加载成功`);
        debugLogs.push(`  - 项目 ID: ${project.id}`);
        debugLogs.push(`  - 项目名: ${project.name}`);
        debugLogs.push(`  - 节点数: ${project.nodes.length}`);
        debugLogs.push(`  - 边数: ${project.edges.length}`);
        debugLogs.push('');

        // 分析节点类型
        debugLogs.push('2. 分析节点类型分布...');
        const nodeTypeCount: Record<string, number> = {};
        project.nodes.forEach(node => {
          nodeTypeCount[node.type] = (nodeTypeCount[node.type] || 0) + 1;
        });

        Object.entries(nodeTypeCount).forEach(([type, count]) => {
          debugLogs.push(`  - ${type}: ${count} 个`);
        });
        debugLogs.push('');

        // 分析节点分类
        debugLogs.push('3. 检查节点分类映射...');
        const nodesByCategory = new Map<string, ProjectNode[]>();
        const missingCategory: ProjectNode[] = [];

        project.nodes.forEach((node: ProjectNode) => {
          const category = getNodeCategory(node.type);
          if (!category) {
            missingCategory.push(node);
            debugLogs.push(`  ✗ 节点 ${node.id} (类型: ${node.type}): 无分类`);
          } else {
            if (!nodesByCategory.has(category)) {
              nodesByCategory.set(category, []);
            }
            nodesByCategory.get(category)!.push(node);
          }
        });

        if (missingCategory.length === 0) {
          debugLogs.push(`  ✓ 所有节点都有正确的分类`);
        }

        debugLogs.push('  分类统计:');
        nodesByCategory.forEach((nodes, category) => {
          debugLogs.push(`    - ${category}: ${nodes.length} 个`);
        });
        debugLogs.push('');

        // 分析节点位置计算
        debugLogs.push('4. 模拟节点位置计算...');
        const positionMap = new Map<string, string[]>();

        const flowNodes: any[] = project.nodes.map((node: ProjectNode) => {
          const category = getNodeCategory(node.type);
          if (!category) {
            return { id: node.id, position: { x: 0, y: 0 }, type: node.type, category: 'UNKNOWN' };
          }

          const layout = CATEGORY_LAYOUTS[category];
          const categoryNodes = nodesByCategory.get(category) || [];
          const nodeIndexInCategory = categoryNodes.findIndex(n => n.id === node.id);

          let x = layout.x;
          let y = nodeIndexInCategory * layout.spacing;

          if (layout.columnCount) {
            const row = Math.floor(nodeIndexInCategory / layout.columnCount);
            const col = nodeIndexInCategory % layout.columnCount;
            x = layout.x + (col * layout.spacing);
            y = row * 250;
          }

          const posKey = `${x},${y}`;
          if (!positionMap.has(posKey)) {
            positionMap.set(posKey, []);
          }
          positionMap.get(posKey)!.push(node.id);

          return { id: node.id, position: { x, y }, type: node.type, category };
        });

        debugLogs.push(`  ✓ 计算了 ${flowNodes.length} 个节点的位置`);

        const overlappingPositions = Array.from(positionMap.entries())
          .filter(([_, nodeIds]) => nodeIds.length > 1);

        if (overlappingPositions.length > 0) {
          debugLogs.push(`  ⚠ 警告: ${overlappingPositions.length} 个位置有节点重叠`);
          overlappingPositions.slice(0, 3).forEach(([pos, nodeIds]) => {
            debugLogs.push(`    - 位置 ${pos}: ${nodeIds.join(', ')}`);
          });
        } else {
          debugLogs.push(`  ✓ 没有节点位置重叠`);
        }
        debugLogs.push('');

        // 分析边
        debugLogs.push('5. 分析边的连接...');
        const sourceNodes = new Set<string>();
        const targetNodes = new Set<string>();
        const nodeIds = new Set(project.nodes.map(n => n.id));
        let invalidEdges = 0;

        project.edges.forEach(edge => {
          sourceNodes.add(edge.source);
          targetNodes.add(edge.target);

          if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
            invalidEdges++;
            debugLogs.push(`  ✗ 边 ${edge.id}: 源或目标节点不存在`);
          }
        });

        if (invalidEdges === 0) {
          debugLogs.push(`  ✓ 所有边都有效`);
        } else {
          debugLogs.push(`  ✗ 发现 ${invalidEdges} 条无效的边`);
        }
        debugLogs.push('');

        // 总结
        debugLogs.push('=== 诊断总结 ===');
        debugLogs.push(`节点总数: ${project.nodes.length}`);
        debugLogs.push(`可渲染节点: ${flowNodes.length}`);
        debugLogs.push(`缺失分类: ${missingCategory.length}`);
        debugLogs.push(`边总数: ${project.edges.length}`);
        debugLogs.push(`无效的边: ${invalidEdges}`);
        debugLogs.push('');

        if (missingCategory.length === 0 && invalidEdges === 0) {
          debugLogs.push('✓ 后端数据结构完全正确，问题应该在前端渲染逻辑');
        } else {
          debugLogs.push('✗ 发现后端数据问题');
        }

        setStatus('success');
      } catch (err) {
        debugLogs.push(`✗ 错误: ${err instanceof Error ? err.message : String(err)}`);
        setStatus('error');
      }

      setLogs(debugLogs);
    };

    runDiagnostics();
  }, []);

  return (
    <div className="p-8 bg-background text-foreground">
      <h1 className="text-2xl font-bold mb-4">前端诊断工具</h1>

      <div className="mb-4">
        <span className={`px-3 py-1 rounded text-sm font-medium ${
          status === 'idle' ? 'bg-gray-200' :
          status === 'loading' ? 'bg-blue-200' :
          status === 'success' ? 'bg-green-200' :
          'bg-red-200'
        }`}>
          {status === 'idle' ? '等待中' :
           status === 'loading' ? '诊断中...' :
           status === 'success' ? '成功' :
           '错误'}
        </span>
      </div>

      <div className="bg-card border border-border rounded-lg p-6 font-mono text-sm">
        <div className="whitespace-pre-wrap break-words">
          {logs.map((log, i) => (
            <div key={i} className={
              log.startsWith('✓') ? 'text-green-600' :
              log.startsWith('✗') ? 'text-red-600' :
              log.startsWith('⚠') ? 'text-yellow-600' :
              'text-foreground'
            }>
              {log}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Debug;
