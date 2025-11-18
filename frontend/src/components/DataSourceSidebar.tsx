import React, { useState, useMemo, useRef, useEffect } from "react";
import { Search, X, MoreVertical, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { conclusions, type ConclusionItem } from "@/data";
import { getDatasetById } from "@/data/datasets";
import { listProjects, type Project } from "@/services/api";

// Use imported conclusions data instead of local constant
const conclusionsData: ConclusionItem[] = [];

interface DataSourceSidebarProps {
  selectedNodeId: string | null;
  onNodeSelect: (nodeId: string) => void;
  currentDatasetId?: string;
  onDatasetChange?: (datasetId: string) => void;
}

export function DataSourceSidebar({
  selectedNodeId,
  onNodeSelect,
  currentDatasetId = "ecommerce_analytics",
  onDatasetChange = () => {},
}: DataSourceSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedConclusionId, setSelectedConclusionId] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const conclusionRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // 从API加载项目列表
  useEffect(() => {
    const loadProjects = async () => {
      try {
        setIsLoadingProjects(true);
        const projectList = await listProjects();
        setProjects(projectList);

        // 当项目列表加载完成后，检查当前项目是否存在
        if (projectList.length > 0) {
          const currentProjectExists = projectList.some(p => p.id === currentDatasetId);
          if (!currentProjectExists) {
            // 当前项目不存在列表中，尝试使用保存的默认项目
            const savedProjectId = localStorage.getItem('defaultProjectId');
            const savedProjectExists = projectList.some(p => p.id === savedProjectId);

            if (savedProjectExists && savedProjectId) {
              // 保存的项目仍然存在，使用它
              onDatasetChange(savedProjectId);
            } else {
              // 保存的项目也不存在，使用列表第一个项目
              onDatasetChange(projectList[0].id);
            }
          }
        }
      } catch (error) {
        console.error("Failed to load projects:", error);
        // Fallback to hardcoded projects
        setProjects([]);
      } finally {
        setIsLoadingProjects(false);
      }
    };

    loadProjects();
  }, [currentDatasetId, onDatasetChange]);

  // 动态获取当前数据集的conclusions
  const currentDatasetConclusions = useMemo(() => {
    try {
      const dataset = getDatasetById(currentDatasetId);
      return dataset.conclusions || conclusionsData;
    } catch {
      return conclusionsData;
    }
  }, [currentDatasetId]);

  const filteredConclusions = useMemo(() => {
    if (!searchQuery.trim()) {
      return currentDatasetConclusions;
    }

    const query = searchQuery.toLowerCase();
    return currentDatasetConclusions.filter(
      (item) =>
        item.conclusion.toLowerCase().includes(query) ||
        item.nodeName.toLowerCase().includes(query)
    );
  }, [searchQuery, currentDatasetConclusions]);

  // 当选中节点时，自动定位到该节点的第一个结论
  // 只在节点变化时清除selectedConclusionId，除非selectedConclusionId已经属于这个节点
  useEffect(() => {
    if (selectedNodeId) {
      const firstConclusionOfNode = filteredConclusions.find(item => item.nodeId === selectedNodeId);
      if (firstConclusionOfNode) {
        // 只有当当前高亮的结论不属于选中的节点时，才清除它
        const shouldClearSelection = selectedConclusionId === null ||
          !filteredConclusions.find(c => c.id === selectedConclusionId && c.nodeId === selectedNodeId);

        if (shouldClearSelection) {
          setSelectedConclusionId(null);
        }

        // 使用 requestAnimationFrame 确保 DOM 已更新
        setTimeout(() => {
          const element = conclusionRefs.current[firstConclusionOfNode.id];
          if (element && scrollAreaRef.current) {
            element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        }, 0);
      }
    }
  }, [selectedNodeId, filteredConclusions, selectedConclusionId]);

  // 获取结论的状态
  const getConclusionState = (conclusionId: string, nodeId: string): 'normal' | 'highlighted' | 'dimmed' => {
    // 如果这个结论被选中，显示高亮
    if (conclusionId === selectedConclusionId) {
      return 'highlighted';
    }

    // 如果选中了节点
    if (selectedNodeId) {
      // 同一节点的结论是普通状态
      if (nodeId === selectedNodeId) {
        return 'normal';
      } else {
        // 其他节点的结论是置灰状态
        return 'dimmed';
      }
    }

    // 没有选中任何节点或结论，所有结论都是普通状态
    return 'normal';
  };

  return (
    <div className="bg-sidebar border-r border-sidebar-border flex flex-col h-screen">
      <div className="p-4 border-b border-sidebar-border space-y-3">
        <div className="space-y-2">
          <label className="text-xs font-semibold text-muted-foreground">Project / Dataset</label>
          <div className="flex gap-2">
            <div className="flex-1">
              <select
                value={currentDatasetId}
                onChange={(e) => {
                  const newProjectId = e.target.value;
                  // 保存当前项目为默认项目
                  localStorage.setItem('defaultProjectId', newProjectId);
                  onDatasetChange(newProjectId);
                }}
                disabled={isLoadingProjects || projects.length === 0}
                className="w-full px-2 py-1.5 text-xs bg-background border border-input rounded-md text-foreground disabled:opacity-50"
              >
                {projects.length === 0 ? (
                  <option value="">
                    {isLoadingProjects ? "加载中..." : "暂无项目"}
                  </option>
                ) : (
                  projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))
                )}
              </select>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>重命名项目</DropdownMenuItem>
                <DropdownMenuItem>增加结论</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <div className="px-4 py-3 border-b border-sidebar-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索结论..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-8 bg-background border-input text-xs"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-sidebar-foreground"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      <ScrollArea ref={scrollAreaRef} className="flex-1">
        <div className="p-2 space-y-2">
          {filteredConclusions.length > 0 ? (
            filteredConclusions.map((item) => {
              const state = getConclusionState(item.id, item.nodeId);
              return (
                <ContextMenu key={item.id}>
                  <ContextMenuTrigger asChild>
                    <button
                      ref={(el) => {
                        if (el) conclusionRefs.current[item.id] = el;
                      }}
                      onClick={() => {
                        // 点击结论：选中对应节点，同时高亮这个结论
                        // DEBUG: For dict_result_test, show node selection
                        if (currentDatasetId === "dict_result_test") {
                          alert(`[DEBUG] Selecting node: ${item.nodeId}`);
                        }
                        onNodeSelect(item.nodeId);
                        setSelectedConclusionId(item.id);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                        state === 'highlighted'
                          ? 'bg-primary text-primary-foreground'
                          : state === 'normal'
                          ? 'hover:bg-sidebar-accent/30'
                          : 'hover:bg-sidebar-accent/10'
                      }`}
                    >
                      {/* 结论内容 - 高层级 */}
                      <div className={`text-sm font-medium line-clamp-3 mb-1 ${
                        state === 'highlighted'
                          ? 'text-primary-foreground'
                          : state === 'normal'
                          ? 'text-sidebar-foreground/85'
                          : 'text-sidebar-foreground/40'
                      }`}>
                        {item.conclusion}
                      </div>
                      {/* 节点名称 - 低层级 */}
                      <div className={`text-xs ${
                        state === 'highlighted'
                          ? 'text-primary-foreground/80'
                          : state === 'normal'
                          ? 'text-muted-foreground/70'
                          : 'text-muted-foreground/30'
                      }`}>
                        {item.nodeName}
                      </div>
                    </button>
                  </ContextMenuTrigger>
                  <ContextMenuContent>
                    <ContextMenuItem>编辑</ContextMenuItem>
                    <ContextMenuItem>删除</ContextMenuItem>
                  </ContextMenuContent>
                </ContextMenu>
              );
            })
          ) : (
            <div className="text-center py-8 text-xs text-muted-foreground">
              未找到匹配的结论
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
