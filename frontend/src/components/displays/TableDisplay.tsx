/**
 * Table Display Component
 *
 * Displays DataFrame/tabular data with pagination and sorting
 */

import React, { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TableDisplayProps {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  totalRecords: number;
  totalPages: number;
  currentPage: number;
  rowsPerPage?: number;
  onPageChange?: (page: number) => void;
  isLoading?: boolean;
  error?: string | null;
}

export function TableDisplay({
  columns,
  rows,
  totalRecords,
  totalPages,
  currentPage,
  rowsPerPage = 10,
  onPageChange = () => {},
  isLoading = false,
  error = null,
}: TableDisplayProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) {
      return "-";
    }

    // Convert all values to string
    const strValue = String(value);

    // Check if it looks like JSON format and try to prettify it
    if (
      (strValue.startsWith("{") && strValue.endsWith("}")) ||
      (strValue.startsWith("[") && strValue.endsWith("]"))
    ) {
      try {
        // Try to parse and re-stringify with indentation
        const parsed = JSON.parse(strValue);
        const prettified = JSON.stringify(parsed, null, 2);

        // Display with limit, add ellipsis if too long
        if (prettified.length > 200) {
          return prettified.substring(0, 200) + "\n...";
        }
        return prettified;
      } catch {
        // If JSON parsing fails, just return as is
        return strValue.substring(0, 100);
      }
    }

    // For non-JSON strings, show first 100 chars
    return strValue.substring(0, 100);
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded">
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">No data to display</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Table */}
      <ScrollArea className="flex-1">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {columns.map((col) => (
                <TableHead
                  key={col}
                  onClick={() => handleSort(col)}
                  className="cursor-pointer hover:bg-muted text-nowrap"
                >
                  <div className="flex items-center gap-2">
                    {col}
                    {sortColumn === col && (
                      <span className="text-xs">
                        {sortDirection === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, idx) => (
              <TableRow key={idx}>
                {columns.map((col) => (
                  <TableCell key={`${idx}-${col}`} className="text-nowrap">
                    {formatValue(row[col])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </ScrollArea>

      {/* Pagination */}
      <div className="border-t border-border p-4 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Page {currentPage} of {totalPages} ({totalRecords} total records)
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNextPage}
            disabled={currentPage >= totalPages}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
