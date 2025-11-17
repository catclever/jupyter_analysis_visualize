/**
 * Result Panel Component
 *
 * Intelligently displays node results based on display_type and result_format
 * Automatically selects the appropriate display component
 */

import React, { useState, useEffect } from "react";
import {
  DisplayType,
  DisplayComponentType,
  getDisplayComponentType,
  getDisplayRule,
  inferDisplayType,
} from "@/config";
import {
  TableDisplay,
  ImageDisplay,
  JsonDisplay,
  EmptyDisplay,
  DictResultDisplay,
} from "@/components/displays";
import { getNodeData, getDictResult, getProject, type ProjectNode, type DictResult } from "@/services/api";
import { AlertCircle, Loader2 } from "lucide-react";

interface ResultPanelProps {
  selectedNodeId: string | null;
  onNodeDeselect?: () => void;
  currentDatasetId?: string;
}

interface TableData {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  totalRecords: number;
  currentPage: number;
  totalPages: number;
}

export function ResultPanel({
  selectedNodeId,
  onNodeDeselect = () => {},
  currentDatasetId = "ecommerce_analytics",
}: ResultPanelProps) {
  const [nodeInfo, setNodeInfo] = useState<ProjectNode | null>(null);
  const [displayType, setDisplayType] = useState<DisplayType>(DisplayType.NONE);
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [jsonData, setJsonData] = useState<unknown>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [dictResult, setDictResult] = useState<DictResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  // Use currentDatasetId directly - no mapping needed as we now load projects dynamically
  const projectId = currentDatasetId;

  // DEBUG: For dict_result_test project, show alert immediately
  useEffect(() => {
    if (projectId === "dict_result_test") {
      const fetchDebugInfo = async () => {
        try {
          const project = await getProject(projectId);
          const debugInfo = project.nodes.map((n: any) =>
            `${n.id}: result_is_dict=${n.result_is_dict}, path=${n.result_path}`
          ).join("\n");
          alert("[DEBUG dict_result_test]\n" + debugInfo);
        } catch (e) {
          alert("Error loading debug info: " + String(e));
        }
      };
      fetchDebugInfo();
    }
  }, [projectId]);

  // Fetch node data
  useEffect(() => {
    if (!selectedNodeId) {
      setNodeInfo(null);
      setDisplayType(DisplayType.NONE);
      setTableData(null);
      setJsonData(null);
      setImageUrl(null);
      setDictResult(null);
      return;
    }

    const fetchNodeData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        setCurrentPage(1);

        // Get project info to find node details
        const project = await getProject(projectId);
        console.log("[DEBUG] Full project loaded:", project);

        const node = project.nodes.find((n) => n.id === selectedNodeId);
        console.log("[DEBUG] Selected node:", node);

        if (!node) {
          setError(`Node ${selectedNodeId} not found in project`);
          return;
        }

        // DEBUG: Show alert with node info
        const debugMsg = `Node: ${node.id}\nresult_is_dict: ${node.result_is_dict}\nresult_path: ${node.result_path}\nexecution_status: ${node.execution_status}`;
        alert("[DEBUG]\n" + debugMsg);

        setNodeInfo(node);

        // DEBUG: Log node info
        console.log("[ResultPanel] Node loaded:", {
          id: node.id,
          result_is_dict: node.result_is_dict,
          result_path: node.result_path,
          execution_status: node.execution_status
        });

        // Determine display type from node output configuration
        let inferredDisplayType: DisplayType = DisplayType.NONE;

        // Try to use display_type from node output if available
        if (node.output?.display_type) {
          inferredDisplayType = node.output.display_type as DisplayType;
        }
        // Otherwise infer from output_type
        else if (node.output?.output_type) {
          inferredDisplayType = inferDisplayType(
            node.output.output_type as any
          );
        }

        setDisplayType(inferredDisplayType);

        // Check if this is a dict result
        console.log("[ResultPanel] Checking if dict result:", node.result_is_dict);
        if (node.result_is_dict) {
          try {
            const dictData = await getDictResult(projectId, selectedNodeId);
            setDictResult(dictData);
            setTableData(null);
            setJsonData(null);
            setImageUrl(null);
          } catch (err) {
            console.error("Failed to fetch dict result:", err);
            setError(err instanceof Error ? err.message : "Failed to fetch dict result");
            setDictResult(null);
          }
        } else {
          // Fetch result data based on result_format
          const data = await getNodeData(projectId, selectedNodeId, 1, pageSize);

          // Load data based on format
          if (data.format === "parquet") {
            setTableData({
              columns: data.columns || [],
              rows: (Array.isArray(data.data) ? data.data : [data.data]) as Array<
                Record<string, unknown>
              >,
              totalRecords: data.total_records,
              currentPage: data.page,
              totalPages: data.total_pages,
            });
            setJsonData(null);
            setImageUrl(null);
            setDictResult(null);
          } else if (data.format === "json") {
            setJsonData(
              Array.isArray(data.data) ? data.data[0] || data.data : data.data
            );
            setTableData(null);
            setImageUrl(null);
            setDictResult(null);
          } else if (data.format === "image") {
            if (data.url) {
              setImageUrl(data.url);
            }
            setTableData(null);
            setJsonData(null);
            setDictResult(null);
          } else {
            // Unknown format - try to display as JSON
            setJsonData(data);
            setTableData(null);
            setImageUrl(null);
            setDictResult(null);
          }
        }
      } catch (err) {
        console.error("Failed to fetch node data:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch node data");
        setTableData(null);
        setJsonData(null);
        setImageUrl(null);
        setDictResult(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchNodeData();
  }, [selectedNodeId, projectId, pageSize]);

  // Handle page changes
  const handlePageChange = async (newPage: number) => {
    if (!selectedNodeId) return;

    try {
      setIsLoading(true);
      const data = await getNodeData(projectId, selectedNodeId, newPage, pageSize);

      if (data.format === "parquet" && tableData) {
        setTableData({
          ...tableData,
          columns: data.columns || [],
          rows: (Array.isArray(data.data) ? data.data : [data.data]) as Array<
            Record<string, unknown>
          >,
          currentPage: data.page,
          totalPages: data.total_pages,
        });
      }
      setCurrentPage(newPage);
    } catch (err) {
      console.error("Failed to fetch page:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Render nothing if no node selected
  if (!selectedNodeId) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <p>Select a node to view its data</p>
      </div>
    );
  }

  // Render component
  return (
    <div className="h-full flex flex-col bg-background rounded-lg border border-border">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">
              {nodeInfo?.label || selectedNodeId}
            </h2>
            <p className="text-sm text-muted-foreground">
              {nodeInfo?.output?.description && `${nodeInfo.output.description}`}
            </p>
          </div>
          <button
            onClick={onNodeDeselect}
            className="text-muted-foreground hover:text-foreground"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Loading data...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* DEBUG: Show what we're rendering */}
        {!isLoading && !error && (
          <div className="text-xs text-muted-foreground p-2 bg-muted/50">
            [DEBUG] result_is_dict={nodeInfo?.result_is_dict ? "true" : "false"},
            dictResult={dictResult ? "loaded" : "null"},
            tableData={tableData ? "loaded" : "null"}
          </div>
        )}

        {!isLoading && !error && (
          <>
            {dictResult && (
              <DictResultDisplay
                keys={dictResult.keys}
                tables={dictResult.tables}
              />
            )}

            {displayType === DisplayType.TABLE && tableData && (
              <TableDisplay
                columns={tableData.columns}
                rows={tableData.rows}
                totalRecords={tableData.totalRecords}
                totalPages={tableData.totalPages}
                currentPage={tableData.currentPage}
                onPageChange={handlePageChange}
              />
            )}

            {displayType === DisplayType.JSON_VIEWER && jsonData && (
              <JsonDisplay data={jsonData as Record<string, unknown>} />
            )}

            {displayType === DisplayType.IMAGE_VIEWER && imageUrl && (
              <ImageDisplay imageUrl={imageUrl} />
            )}

            {displayType === DisplayType.PLOTLY_CHART && jsonData && (
              <div className="p-4 text-muted-foreground">
                <p className="text-sm">
                  Plotly chart support coming soon. Raw data:
                </p>
                <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-h-64">
                  {JSON.stringify(jsonData, null, 2)}
                </pre>
              </div>
            )}

            {displayType === DisplayType.ECHARTS_CHART && jsonData && (
              <div className="p-4 text-muted-foreground">
                <p className="text-sm">
                  ECharts support coming soon. Raw data:
                </p>
                <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-h-64">
                  {JSON.stringify(jsonData, null, 2)}
                </pre>
              </div>
            )}

            {displayType === DisplayType.NONE && !dictResult && (
              <EmptyDisplay
                message="No result to display"
                details="This node type does not produce a displayable result."
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
