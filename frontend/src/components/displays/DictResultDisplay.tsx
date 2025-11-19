/**
 * Dict Result Display Component
 *
 * Displays dict of DataFrames with tabs for each key
 * Supports pagination for large DataFrames
 */

import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TableDisplay } from "@/components/displays/TableDisplay";
import { AlertCircle } from "lucide-react";

export interface TablePageInfo {
  data: Array<Record<string, unknown>>;
  total_rows: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface DictResultDisplayProps {
  keys: string[];
  tables: Record<string, TablePageInfo | Array<Record<string, unknown>>>;
  onPageChange?: (key: string, newPage: number) => void;
  onTablePageChange?: (key: string, newPage: number) => Promise<void>;
}

export function DictResultDisplay({
  keys,
  tables,
  onTablePageChange,
}: DictResultDisplayProps) {
  const defaultTab = keys[0] || "";
  const [activeTab, setActiveTab] = useState<string>(defaultTab);
  const [tablePages, setTablePages] = useState<Record<string, number>>({})

  if (!keys || keys.length === 0) {
    return (
      <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        <span className="text-sm">No data available in dict result</span>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col p-4 bg-background">
      {/* Tab List */}
      <div className="mb-4 border-b border-border">
        <div className="flex gap-2 flex-wrap">
          {keys.map((key) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === key
                  ? "border-blue-500 text-blue-600 bg-blue-50"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {key}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto min-h-0">
        {keys.map((key) => {
          const tableData = tables[key];
          const isPagedData = tableData && typeof tableData === 'object' && !Array.isArray(tableData) && 'data' in tableData;
          const pageInfo = isPagedData ? (tableData as TablePageInfo) : null;
          const rows = isPagedData ? pageInfo.data : Array.isArray(tableData) ? tableData : [];
          const currentPage = isPagedData ? pageInfo.page : 1;
          const totalPages = isPagedData ? pageInfo.total_pages : 1;
          const totalRecords = isPagedData ? pageInfo.total_rows : (Array.isArray(tableData) ? tableData.length : 0);
          const pageSize = isPagedData ? pageInfo.page_size : rows.length;

          const handlePageChange = async (newPage: number) => {
            setTablePages(prev => ({ ...prev, [key]: newPage }));
            if (onTablePageChange) {
              try {
                await onTablePageChange(key, newPage);
              } catch (err) {
                console.error(`Failed to load page ${newPage} for table ${key}:`, err);
              }
            }
          };

          return (
            <div key={key} className={activeTab === key ? "block" : "hidden"}>
              {rows && rows.length > 0 ? (
                <div className="flex flex-col h-full">
                  <div className="flex-1 overflow-auto min-h-0">
                    <TableDisplay
                      columns={Object.keys(rows[0] || {})}
                      rows={rows}
                      totalRecords={totalRecords}
                      totalPages={totalPages}
                      currentPage={currentPage}
                      onPageChange={handlePageChange}
                    />
                  </div>
                  {isPagedData && totalPages > 1 && (
                    <div className="border-t border-border p-2 text-xs text-muted-foreground text-center">
                      Page {currentPage} of {totalPages} | {totalRecords} total rows | {pageSize} rows per page
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <p className="text-sm">No data in this table</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
