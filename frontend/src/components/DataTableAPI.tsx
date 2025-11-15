/**
 * Enhanced Data Table Component with API Integration
 *
 * Fetches node data from backend API instead of using hardcoded data.
 * Supports:
 * - Parquet data (tables with pagination)
 * - JSON data (statistics/metrics)
 * - Image/Visualization display
 */

import React, { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, AlertCircle, Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getNodeData, getProject, type ProjectNode } from "@/services/api";

interface DataTableAPIProps {
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

interface JsonData {
  [key: string]: unknown;
}

export function DataTableAPI({
  selectedNodeId,
  onNodeDeselect = () => {},
  currentDatasetId = "ecommerce_analytics",
}: DataTableAPIProps) {
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [jsonData, setJsonData] = useState<JsonData | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [nodeInfo, setNodeInfo] = useState<ProjectNode | null>(null);

  // Use currentDatasetId directly - no mapping needed as we now load projects dynamically
  const projectId = currentDatasetId;

  // 获取节点数据
  useEffect(() => {
    if (!selectedNodeId) {
      setTableData(null);
      setJsonData(null);
      setImageUrl(null);
      setNodeInfo(null);
      return;
    }

    const fetchNodeData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        setCurrentPage(1);

        // First, get project info to find node details
        const project = await getProject(projectId);
        const node = project.nodes.find((n) => n.id === selectedNodeId);

        if (!node) {
          setError(`Node ${selectedNodeId} not found in project`);
          return;
        }

        setNodeInfo(node);

        // Handle different result formats
        if (node.result_format === "parquet" || node.result_format === "json") {
          // Fetch table/JSON data
          const data = await getNodeData(projectId, selectedNodeId, 1, pageSize);

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
          } else if (data.format === "json") {
            setJsonData(
              Array.isArray(data.data)
                ? data.data[0] || data.data
                : (data.data as JsonData)
            );
            setTableData(null);
            setImageUrl(null);
          }
        } else if (node.result_format === "image" || node.result_format === "visualization") {
          // Handle image/visualization
          const imageData = await getNodeData(projectId, selectedNodeId, 1, pageSize);
          if (imageData.url) {
            setImageUrl(imageData.url);
            setTableData(null);
            setJsonData(null);
          }
        }
      } catch (err) {
        console.error("Failed to fetch node data:", err);
        setError(
          err instanceof Error ? err.message : "Failed to fetch node data"
        );
        setTableData(null);
        setJsonData(null);
        setImageUrl(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchNodeData();
  }, [selectedNodeId, projectId, pageSize]);

  // 处理分页
  const handlePrevPage = async () => {
    if (!selectedNodeId || currentPage <= 1) return;

    try {
      setIsLoading(true);
      const newPage = currentPage - 1;
      const data = await getNodeData(
        projectId,
        selectedNodeId,
        newPage,
        pageSize
      );

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
      }
      setCurrentPage(newPage);
    } catch (err) {
      console.error("Failed to fetch previous page:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNextPage = async () => {
    if (!selectedNodeId || !tableData || currentPage >= tableData.totalPages)
      return;

    try {
      setIsLoading(true);
      const newPage = currentPage + 1;
      const data = await getNodeData(
        projectId,
        selectedNodeId,
        newPage,
        pageSize
      );

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
      }
      setCurrentPage(newPage);
    } catch (err) {
      console.error("Failed to fetch next page:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedNodeId) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <p>Select a node to view its data</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-background rounded-lg border border-border">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">{nodeInfo?.label || selectedNodeId}</h2>
            <p className="text-sm text-muted-foreground">
              {nodeInfo?.result_format && `Format: ${nodeInfo.result_format}`}
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
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium">Error loading data</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {tableData && !isLoading && (
          <ScrollArea className="h-full">
            <div className="p-4">
              <Table className="border">
                <TableHeader>
                  <TableRow>
                    {tableData.columns.map((col) => (
                      <TableHead key={col} className="min-w-[100px]">
                        {col}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tableData.rows.map((row, idx) => (
                    <TableRow key={idx}>
                      {tableData.columns.map((col) => (
                        <TableCell key={col} className="text-sm">
                          {String(row[col] ?? "-")}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </ScrollArea>
        )}

        {jsonData && !isLoading && (
          <div className="p-4">
            <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-sm">
              {JSON.stringify(jsonData, null, 2)}
            </pre>
          </div>
        )}

        {imageUrl && !isLoading && (
          <div className="p-4 flex items-center justify-center">
            <img
              src={imageUrl}
              alt={`Visualization for ${selectedNodeId}`}
              className="max-w-full max-h-96 rounded-lg border border-border"
              onError={(e) => {
                console.error("Failed to load image:", e);
                setError("Failed to load image");
              }}
            />
          </div>
        )}
      </div>

      {/* Pagination Footer (only for table data) */}
      {tableData && !isLoading && (
        <div className="border-t border-border p-4 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Page {tableData.currentPage} of {tableData.totalPages} • Total:{" "}
            {tableData.totalRecords} records
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrevPage}
              disabled={tableData.currentPage <= 1 || isLoading}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNextPage}
              disabled={
                tableData.currentPage >= tableData.totalPages || isLoading
              }
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
