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
  const [currentDatasetId, setCurrentDatasetId] = useState<string>("");
  const [projectRefreshKey, setProjectRefreshKey] = useState(0); // Trigger project reload when code is saved
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);

  // Use project cache hook for efficient data loading
  const { loadProject } = useProjectCache();

  // 初始化时加载项目列表，选择之前保存的默认项目或第一个项目
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        if (data.projects && data.projects.length > 0) {
          // 尝试恢复之前保存的默认项目
          const savedProjectId = localStorage.getItem('defaultProjectId');
          const projectExists = data.projects.some(p => p.id === savedProjectId);

          if (projectExists && savedProjectId) {
            // 恢复之前保存的项目
            setCurrentDatasetId(savedProjectId);
          } else {
            // 保存的项目不存在，使用列表第一个
            setCurrentDatasetId(data.projects[0].id);
          }
        } else {
          console.warn('No projects available');
        }
      } catch (err) {
        console.error('Failed to load projects:', err);
      } finally {
        setIsLoadingProjects(false);
      }
    };

    loadProjects();
  }, []);

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
    // 仅在存在有效数据集 ID 时加载项目，避免初始空 ID 触发 404
    if (!currentDatasetId) return;
    // Load the new project (with caching)
    loadProject(currentDatasetId).catch((err) => {
      console.error('Failed to load project:', err);
    });
  }, [currentDatasetId, loadProject]);

  // 当选中节点时，自动打开分析面板
  useEffect(() => {
    if (selectedNodeId) {
      setIsAnalysisSidebarOpen(true);
    }
  }, [selectedNodeId]);

  // Handle node deletion from DataTable
  const handleNodeDelete = (nodeId: string) => {
    // This will trigger through the FlowDiagram's onNodeDelete callback
    // For now, we just need to make sure the node gets deleted
    // The actual deletion logic is in FlowDiagram
  };

  // 如果还在加载项目，显示加载状态
  if (isLoadingProjects || !currentDatasetId) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">加载项目中...</p>
        </div>
      </div>
    );
  }

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

        <ResizablePanel defaultSize={isAnalysisSidebarOpen ? 45 : 75} minSize={20}>
          <div className="h-full w-full relative">
            {selectedNodeId ? (
              <ResizablePanelGroup direction="vertical" className="h-full">
                <ResizablePanel defaultSize={isAnalysisSidebarOpen ? 33.33 : 50} minSize={20}>
                  <div className="h-full w-full overflow-hidden">
                    <FlowDiagram
                      key={projectRefreshKey}
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
                    <DataTable
                      selectedNodeId={selectedNodeId}
                      onNodeDeselect={() => setSelectedNodeId(null)}
                      currentDatasetId={currentDatasetId}
                      onProjectUpdate={() => setProjectRefreshKey(prev => prev + 1)}
                      onNodeDelete={handleNodeDelete}
                    />
                  </div>
                </ResizablePanel>
              </ResizablePanelGroup>
            ) : (
              <div className="h-full w-full overflow-hidden">
                <FlowDiagram
                  key={projectRefreshKey}
                  onNodeClick={setSelectedNodeId}
                  selectedNodeId={selectedNodeId}
                  minimapOpen={minimapOpen}
                  currentDatasetId={currentDatasetId}
                />
              </div>
            )}
          </div>
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
