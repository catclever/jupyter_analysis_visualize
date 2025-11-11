/**
 * Empty Display Component
 *
 * Displays a message when there's no result to show (e.g., function outputs)
 */

import React from "react";

interface EmptyDisplayProps {
  message?: string;
  details?: string;
}

export function EmptyDisplay({
  message = "No result to display",
  details = "This node type does not produce a displayable result.",
}: EmptyDisplayProps) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <p className="text-muted-foreground mb-2">{message}</p>
        {details && <p className="text-xs text-muted-foreground">{details}</p>}
      </div>
    </div>
  );
}
