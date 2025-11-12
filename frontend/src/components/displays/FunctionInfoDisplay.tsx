/**
 * Function Info Display Component
 *
 * Displays information about a function/tool result.
 * Tool nodes produce callable functions that are stored as pickle files.
 * This component shows metadata about the function rather than the function itself.
 */

import React from "react";
import { Code2, Info } from "lucide-react";

interface FunctionInfoDisplayProps {
  functionName?: string;
  description?: string;
  nodeId?: string;
  resultPath?: string;
}

export function FunctionInfoDisplay({
  functionName = "Callable Function",
  description = "This node produces a callable function that can be invoked by other nodes",
  nodeId,
  resultPath,
}: FunctionInfoDisplayProps) {
  return (
    <div className="h-full flex flex-col p-6 bg-background">
      {/* Header */}
      <div className="flex items-start gap-3 mb-6 pb-4 border-b border-border">
        <Code2 className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold mb-1">{functionName}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>

      {/* Info Panel */}
      <div className="space-y-4">
        <div className="bg-muted/50 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-medium mb-1">Function Output</p>
              <p>
                This node produces a Python callable (function) that is serialized using pickle format.
              </p>
            </div>
          </div>
        </div>

        {/* Metadata */}
        <div className="space-y-3">
          {nodeId && (
            <div>
              <label className="text-xs font-medium text-muted-foreground">Node ID</label>
              <p className="text-sm font-mono bg-muted rounded px-3 py-2 mt-1 break-all">
                {nodeId}
              </p>
            </div>
          )}

          {resultPath && (
            <div>
              <label className="text-xs font-medium text-muted-foreground">Storage Path</label>
              <p className="text-sm font-mono bg-muted rounded px-3 py-2 mt-1 break-all">
                {resultPath}
              </p>
            </div>
          )}
        </div>

        {/* Usage Note */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mt-6">
          <p className="text-xs text-blue-700 dark:text-blue-400">
            <strong>Usage:</strong> This function can be used as input to other compute or chart nodes.
            Pass the function as a parameter to use its functionality.
          </p>
        </div>
      </div>
    </div>
  );
}
