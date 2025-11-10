import React, { useState, useMemo, useEffect } from "react";
import { Code2, CheckCircle2, XCircle, Lightbulb, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { analysisRequests, nodeLabels, type AnalysisRequest, type StepDetail } from "@/data";
import { getDatasetById } from "@/data/datasets";


interface AnalysisSidebarProps {
  isOpen: boolean;
  onToggle: (open: boolean) => void;
  selectedNodeId?: string | null;
  onNodeSelect?: (nodeId: string) => void;
  currentDatasetId?: string;
}

export function AnalysisSidebar({
  isOpen,
  onToggle,
  selectedNodeId,
  onNodeSelect,
  currentDatasetId = "data-analysis",
}: AnalysisSidebarProps) {
  const [manualActiveTab, setManualActiveTab] = useState<"current" | "all">("all");

  // 动态获取当前数据集的数据
  const datasetData = useMemo(() => {
    try {
      return getDatasetById(currentDatasetId);
    } catch {
      return { analysisRequests: [], nodeLabels: {} };
    }
  }, [currentDatasetId]);

  const currentAnalysisRequests = datasetData.analysisRequests || [];
  const currentNodeLabels = datasetData.nodeLabels || {};

  // 根据 isOpen 和 selectedNodeId 计算实际的 activeTab
  const activeTab = useMemo(() => {
    // 如果面板关闭，始终显示"全部"
    if (!isOpen) {
      return "all";
    }
    // 如果面板打开且有选中节点，使用手动选择的tab（默认是"当前节点"）
    if (selectedNodeId) {
      return manualActiveTab;
    }
    // 如果面板打开但没有选中节点，显示"全部"
    return "all";
  }, [isOpen, selectedNodeId, manualActiveTab]);

  // 当选择节点时，自动切换到当前节点tab
  useEffect(() => {
    if (selectedNodeId && isOpen) {
      setManualActiveTab("current");
    }
  }, [selectedNodeId, isOpen]);

  // 获取与当前节点相关的分析需求（生成它的和从它导出的）
  const currentNodeRequests = useMemo(() => {
    if (!selectedNodeId) return [];

    const requests = currentAnalysisRequests.filter(
      (req) => req.outputNode === selectedNodeId || req.sourceNodes.includes(selectedNodeId)
    );

    // 按时间排序
    return requests.sort((a, b) => a.timestamp - b.timestamp);
  }, [selectedNodeId, currentAnalysisRequests]);

  const allRequests = useMemo(() => {
    return [...currentAnalysisRequests].sort((a, b) => a.timestamp - b.timestamp);
  }, [currentAnalysisRequests]);

  return (
    <div className="bg-card border-l border-border flex flex-col h-screen relative">
      {/* 收起按钮 - 在面板左上方 */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onToggle(false)}
        className="absolute -left-2 top-4 h-6 w-6 rounded-full border border-border bg-background shadow-sm hover:bg-accent z-10"
        title="隐藏分析面板"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>

      <Tabs value={activeTab} onValueChange={(value) => setManualActiveTab(value as "current" | "all")} className="flex-1 flex flex-col min-h-0">
        <div className="border-b border-border flex-shrink-0">
          {selectedNodeId && isOpen ? (
            <TabsList className="w-full justify-start rounded-none h-12 bg-transparent px-4">
              <TabsTrigger value="current" className="data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none">
                当前节点
              </TabsTrigger>
              <TabsTrigger value="all" className="data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none">
                全部
              </TabsTrigger>
            </TabsList>
          ) : (
            <TabsList className="w-full justify-start rounded-none h-12 bg-transparent px-4">
              <TabsTrigger value="all" className="data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none">
                全部
              </TabsTrigger>
            </TabsList>
          )}
        </div>

        {activeTab === "current" && selectedNodeId && isOpen ? (
          <TabsContent value="current" className="flex-1 m-0 flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto px-4 py-4 min-h-0 flex flex-col">
              <div className="space-y-4 flex-1">
                {currentNodeRequests.length > 0 ? (
                  currentNodeRequests.map((request) => (
                    <AnalysisRequestCard key={request.id} request={request} onNodeClick={onNodeSelect} selectedNodeId={selectedNodeId} />
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-8 flex items-center justify-center">
                    暂无相关分析需求
                  </div>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-border bg-card flex-shrink-0">
              <Textarea
                placeholder="请输入分析需求"
                className="min-h-[80px] resize-none"
              />
            </div>
          </TabsContent>
        ) : (
          <TabsContent value="all" className="flex-1 m-0 flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto px-4 py-4 min-h-0 flex flex-col">
              <div className="space-y-4 flex-1">
                {allRequests && allRequests.length > 0 ? (
                  allRequests.map((request) => (
                    <AnalysisRequestCard key={request.id} request={request} onNodeClick={onNodeSelect} selectedNodeId={selectedNodeId} />
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-8 flex items-center justify-center">
                    暂无分析需求
                  </div>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-border bg-card flex-shrink-0">
              <Textarea
                placeholder="请输入分析需求"
                className="min-h-[80px] resize-none"
              />
            </div>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

interface AnalysisRequestCardProps {
  request: AnalysisRequest;
  onNodeClick?: (nodeId: string) => void;
  selectedNodeId?: string | null;
}

function AnalysisRequestCard({ request, onNodeClick, selectedNodeId }: AnalysisRequestCardProps) {
  const [expandedStepId, setExpandedStepId] = React.useState<number | null>(null);
  const [isStepsExpanded, setIsStepsExpanded] = React.useState(request.steps.length <= 3);

  // 根据输出节点ID获取节点类型
  const getNodeType = (nodeId: string): 'data' | 'compute' | 'chart' => {
    if (nodeId.startsWith('data-')) return 'data';
    if (nodeId.startsWith('compute-')) return 'compute';
    if (nodeId.startsWith('chart-')) return 'chart';
    return 'data';
  };

  // 根据节点类型获取颜色
  const getNodeColor = (nodeId: string) => {
    const type = getNodeType(nodeId);
    const colorMap = {
      data: '#a8c5da',
      compute: '#c4a8d4',
      chart: '#c9a8a8',
    };
    return colorMap[type];
  };

  const getIcon = () => {
    switch (request.status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />;
      case "pending":
        return <XCircle className="h-4 w-4 text-muted-foreground flex-shrink-0" />;
      case "suggestion":
        return <Lightbulb className="h-4 w-4 text-primary flex-shrink-0" />;
    }
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const isCurrentNode = selectedNodeId === request.outputNode;
  const displaySteps = isStepsExpanded ? request.steps : request.steps.slice(-3);
  const hasMoreSteps = !isStepsExpanded && request.steps.length > 3;
  const firstDisplayIdx = isStepsExpanded ? 0 : Math.max(0, request.steps.length - 3);

  return (
    <div className="space-y-2 pb-3 border-b border-border/30 last:border-b-0 px-3 py-2 rounded">
      {/* 头部：icon + 描述 */}
      <div className="flex items-start gap-2">
        {getIcon()}
        <div className="flex-1">
          <p className="text-sm text-foreground leading-relaxed">
            {request.description}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {formatTime(request.timestamp)}
          </p>
        </div>
      </div>

      {/* 操作步骤 - 虚线圆点连接 */}
      {request.steps && request.steps.length > 0 && (
        <div className="mt-3">
          {/* 上方连接线和"还有n个步骤"或"收起" - 当不显示第一个步骤时或展开时 */}
          {(hasMoreSteps || isStepsExpanded) && request.steps.length > 3 && (
            <button
              onClick={() => {
                if (hasMoreSteps) {
                  setIsStepsExpanded(true);
                } else {
                  setIsStepsExpanded(false);
                  setExpandedStepId(null);
                }
              }}
              className="flex items-center gap-2 mb-2 text-muted-foreground hover:text-primary transition-colors group"
            >
              <div className="flex-shrink-0 w-2 h-4 flex items-center justify-center">
                <svg className="w-0.5 h-4 stroke-current group-hover:stroke-primary" viewBox="0 0 1 16" strokeDasharray="1,1" strokeWidth="0.5">
                  <line x1="0.5" y1="0" x2="0.5" y2="16" />
                </svg>
              </div>
              <span className="text-xs">
                {hasMoreSteps ? `还有 ${request.steps.length - 3} 个步骤...` : '收起'}
              </span>
            </button>
          )}

          {/* 步骤列表 */}
          <div className="space-y-2">
            {displaySteps.map((step, displayIdx) => {
              const actualIdx = request.steps.indexOf(step);
              const isExpanded = expandedStepId === actualIdx;
              const isLast = displayIdx === displaySteps.length - 1;

              return (
                <div key={actualIdx}>
                  {/* 虚线连接 + 圆点 + 标题 */}
                  <div className="flex gap-2">
                    {/* 虚线和圆点 */}
                    <div className="flex flex-col items-center flex-shrink-0">
                      {/* 上方虚线 */}
                      {displayIdx > 0 && (
                        <svg className="w-0.5 h-2 stroke-muted-foreground" viewBox="0 0 1 8" strokeDasharray="1,1" strokeWidth="0.5">
                          <line x1="0.5" y1="0" x2="0.5" y2="8" />
                        </svg>
                      )}

                      {/* 圆环按钮 - 精确对齐到文字基线 */}
                      <button
                        onClick={() => setExpandedStepId(isExpanded ? null : actualIdx)}
                        className="w-2 h-2 rounded-full border border-muted-foreground hover:border-primary hover:scale-150 transition-all flex-shrink-0 cursor-pointer mt-1"
                        title={step.title}
                      />

                      {/* 下方虚线 */}
                      {!isLast && (
                        <svg className="w-0.5 h-2 stroke-muted-foreground" viewBox="0 0 1 8" strokeDasharray="1,1" strokeWidth="0.5">
                          <line x1="0.5" y1="0" x2="0.5" y2="8" />
                        </svg>
                      )}
                    </div>

                    {/* 步骤标题 */}
                    <div className="flex-1 min-w-0">
                      <button
                        onClick={() => setExpandedStepId(isExpanded ? null : actualIdx)}
                        className="text-xs font-medium text-foreground hover:text-primary transition-colors text-left"
                      >
                        {actualIdx + 1}. {step.title}
                      </button>

                      {/* 展开的内容 */}
                      {isExpanded && (
                        <div className="text-xs text-muted-foreground mt-2 leading-relaxed">
                          {step.description}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      )}

      {/* 输出节点按钮 - 根据节点类型使用颜色反色 */}
      {request.steps && request.steps.length > 0 && (
        <div className={`mt-3 pt-2 border-t border-border/20 ${isCurrentNode ? '-mx-3 px-3 py-1.5' : ''}`}
          style={isCurrentNode ? { backgroundColor: getNodeColor(request.outputNode) + '20' } : {}}
        >
          {isCurrentNode ? (
            <div className="flex items-center gap-2 text-xs cursor-default font-medium" style={{ color: getNodeColor(request.outputNode) }}>
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getNodeColor(request.outputNode) }} />
              <span>{request.outputNodeLabel}</span>
            </div>
          ) : (
            <Button
              variant="link"
              size="sm"
              className="h-auto p-0 hover:text-primary-hover text-xs"
              style={{ color: getNodeColor(request.outputNode) }}
              onClick={() => onNodeClick?.(request.outputNode)}
            >
              <span>→ {request.outputNodeLabel}</span>
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
