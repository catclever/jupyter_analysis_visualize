import React, { useState, useEffect } from "react";
import { DataSourceSidebar } from "@/components/DataSourceSidebar";
import { FlowDiagram } from "@/components/FlowDiagram";
import { DataTable } from "@/components/DataTable";
import { AnalysisSidebar } from "@/components/AnalysisSidebar";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useProjectCache } from "@/hooks/useProjectCache";

const Index = () => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isAnalysisSidebarOpen, setIsAnalysisSidebarOpen] = useState(true);
  const [minimapOpen, setMinimapOpen] = useState(false); // 默认关闭 minimap
  const [shouldCloseMinimap, setShouldCloseMinimap] = useState(false); // 用于追踪数据面板打开状态变化
  const [currentDatasetId, setCurrentDatasetId] = useState<string>("data-analysis");

  // Use project cache hook for efficient data loading
  const { loadProject } = useProjectCache();

  // 当打开数据面板时，关闭 minimap；当关闭时，打开 minimap
  useEffect(() => {
    if (isAnalysisSidebarOpen) {
      setMinimapOpen(false);
      setShouldCloseMinimap(true);
    } else {
      setMinimapOpen(true);
      setShouldCloseMinimap(false);
    }
  }, [isAnalysisSidebarOpen]);

  // 当数据集改变时，加载新项目并重置选中的节点
  useEffect(() => {
    setSelectedNodeId(null);
    // Load the new project (with caching)
    loadProject(currentDatasetId).catch((err) => {
      console.error('Failed to load project:', err);
    });
  }, [currentDatasetId, loadProject]);

  return (
    <div className="h-screen w-full relative">
      <ResizablePanelGroup direction="horizontal" className="h-full w-full">
        <ResizablePanel defaultSize={15} minSize={15} maxSize={40}>
          <DataSourceSidebar
            selectedNodeId={selectedNodeId}
            onNodeSelect={setSelectedNodeId}
            currentDatasetId={currentDatasetId}
            onDatasetChange={setCurrentDatasetId}
          />
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel defaultSize={isAnalysisSidebarOpen ? 40 : 60} minSize={20}>
          {selectedNodeId ? (
            <ResizablePanelGroup direction="vertical" className="h-full">
              <ResizablePanel defaultSize={isAnalysisSidebarOpen ? 33.33 : 50} minSize={20}>
                <div className="h-full overflow-auto p-6">
                  <FlowDiagram
                    onNodeClick={setSelectedNodeId}
                    selectedNodeId={selectedNodeId}
                    minimapOpen={minimapOpen}
                    currentDatasetId={currentDatasetId}
                  />
                </div>
              </ResizablePanel>

              <ResizableHandle withHandle />

              <ResizablePanel defaultSize={isAnalysisSidebarOpen ? 66.67 : 50} minSize={20}>
                <div className="h-full overflow-auto p-6">
                  <DataTable selectedNodeId={selectedNodeId} onNodeDeselect={() => setSelectedNodeId(null)} currentDatasetId={currentDatasetId} />
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          ) : (
            <div className="h-full overflow-auto p-6">
              <FlowDiagram
                onNodeClick={setSelectedNodeId}
                selectedNodeId={selectedNodeId}
                minimapOpen={minimapOpen}
                currentDatasetId={currentDatasetId}
              />
            </div>
          )}
        </ResizablePanel>

        {isAnalysisSidebarOpen && (
          <>
            <ResizableHandle withHandle />

            <ResizablePanel defaultSize={20} minSize={15} maxSize={40}>
              <AnalysisSidebar
                isOpen={isAnalysisSidebarOpen}
                onToggle={setIsAnalysisSidebarOpen}
                selectedNodeId={selectedNodeId}
                onNodeSelect={setSelectedNodeId}
                currentDatasetId={currentDatasetId}
              />
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* 展开按钮 - 只在右侧面板隐藏时显示 */}
      {!isAnalysisSidebarOpen && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsAnalysisSidebarOpen(true)}
          className="fixed right-0 top-4 h-6 w-6 rounded-full border border-border bg-background shadow-sm hover:bg-accent z-50"
          title="展开分析面板"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
};

export default Index;
