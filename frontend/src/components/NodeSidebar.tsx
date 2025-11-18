import React from "react";
import { GripVertical } from "lucide-react";
import { NodeType, NODE_TYPE_CONFIG, CATEGORY_LAYOUTS, NodeCategory } from "@/config";

interface NodeSidebarProps {
  onNodeDragStart?: (event: React.DragEvent<HTMLDivElement>, nodeType: NodeType) => void;
}

export function NodeSidebar({ onNodeDragStart }: NodeSidebarProps) {
  const nodeTypes = Object.values(NodeType);

  const handleDragStart = (event: React.DragEvent<HTMLDivElement>, nodeType: NodeType) => {
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData("application/json", JSON.stringify({
      type: "add-node",
      nodeType: nodeType,
      timestamp: Date.now()
    }));
    onNodeDragStart?.(event, nodeType);
  };

  return (
    <div className="bg-card border-l border-border flex flex-col h-screen p-4 w-32">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-foreground mb-3">节点类型</h3>
        <div className="space-y-2">
          {nodeTypes.map((nodeType) => {
            const config = NODE_TYPE_CONFIG[nodeType];
            if (!config) return null;

            return (
              <div
                key={nodeType}
                draggable
                onDragStart={(e) => handleDragStart(e, nodeType)}
                className="p-2.5 rounded-lg border border-border cursor-move hover:border-primary transition-colors group bg-muted/50 hover:bg-muted"
                style={{
                  borderColor: `${config.color}80`,
                }}
              >
                <div className="flex items-center gap-2">
                  <GripVertical className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">
                      {config.label}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {nodeType.replace(/_/g, " ")}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-auto pt-4 border-t border-border">
        <p className="text-xs text-muted-foreground text-center">
          拖动节点到画布添加
        </p>
      </div>
    </div>
  );
}
