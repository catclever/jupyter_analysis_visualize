/**
 * Dict Result Display Component
 *
 * Displays dict of DataFrames with tabs for each key
 */

import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TableDisplay } from "@/components/displays/TableDisplay";
import { AlertCircle } from "lucide-react";

interface DictResultDisplayProps {
  keys: string[];
  tables: Record<string, Array<Record<string, unknown>>>;
  onPageChange?: (key: string, newPage: number) => void;
}

export function DictResultDisplay({
  keys,
  tables,
}: DictResultDisplayProps) {
  const defaultTab = keys[0] || "";
  const [activeTab, setActiveTab] = useState<string>(defaultTab);

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
        {keys.map((key) => (
          <div key={key} className={activeTab === key ? "block" : "hidden"}>
            {tables[key] && Array.isArray(tables[key]) && tables[key].length > 0 ? (
              <TableDisplay
                columns={Object.keys(tables[key][0] || {})}
                rows={tables[key]}
                totalRecords={tables[key].length}
                totalPages={1}
                currentPage={1}
                onPageChange={() => {}}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <p className="text-sm">No data in this table</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
