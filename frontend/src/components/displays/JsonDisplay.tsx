/**
 * JSON Display Component
 *
 * Displays JSON data with syntax highlighting and collapsible structure
 */

import React, { useState } from "react";
import { ChevronDown, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface JsonDisplayProps {
  data: Record<string, unknown> | unknown[];
  isLoading?: boolean;
  error?: string | null;
}

interface JsonNodeProps {
  data: unknown;
  level: number;
  name?: string;
}

function JsonNode({ data, level, name }: JsonNodeProps) {
  const [expanded, setExpanded] = useState(level < 2);
  const indent = level * 2;

  if (data === null) {
    return (
      <div style={{ marginLeft: `${indent * 8}px` }} className="text-amber-600">
        {name && <span className="text-foreground font-mono">{name}: </span>}
        <span className="font-mono">null</span>
      </div>
    );
  }

  if (typeof data === "boolean") {
    return (
      <div style={{ marginLeft: `${indent * 8}px` }} className="text-amber-600">
        {name && <span className="text-foreground font-mono">{name}: </span>}
        <span className="font-mono">{String(data)}</span>
      </div>
    );
  }

  if (typeof data === "number") {
    return (
      <div style={{ marginLeft: `${indent * 8}px` }} className="text-amber-600">
        {name && <span className="text-foreground font-mono">{name}: </span>}
        <span className="font-mono">{data}</span>
      </div>
    );
  }

  if (typeof data === "string") {
    return (
      <div style={{ marginLeft: `${indent * 8}px` }} className="text-green-600">
        {name && <span className="text-foreground font-mono">{name}: </span>}
        <span className="font-mono">"{data}"</span>
      </div>
    );
  }

  if (Array.isArray(data)) {
    return (
      <div style={{ marginLeft: `${indent * 8}px` }}>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-0 hover:bg-muted rounded"
          >
            <ChevronDown
              className={`w-4 h-4 transition-transform ${
                expanded ? "" : "-rotate-90"
              }`}
            />
          </button>
          {name && <span className="text-foreground font-mono">{name}: </span>}
          <span className="text-blue-600 font-mono">
            [{expanded ? "" : "..."}]
          </span>
        </div>
        {expanded && (
          <div>
            {data.map((item, idx) => (
              <JsonNode key={idx} data={item} level={level + 1} name={`[${idx}]`} />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (typeof data === "object") {
    const entries = Object.entries(data);
    return (
      <div style={{ marginLeft: `${indent * 8}px` }}>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-0 hover:bg-muted rounded"
          >
            <ChevronDown
              className={`w-4 h-4 transition-transform ${
                expanded ? "" : "-rotate-90"
              }`}
            />
          </button>
          {name && <span className="text-foreground font-mono">{name}: </span>}
          <span className="text-blue-600 font-mono">
            {"{"}
            {expanded ? "" : "..."}
            {"}"}
          </span>
        </div>
        {expanded && (
          <div>
            {entries.map(([key, value]) => (
              <JsonNode
                key={key}
                data={value}
                level={level + 1}
                name={key}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return <div className="text-muted-foreground font-mono">[unknown type]</div>;
}

export function JsonDisplay({
  data,
  isLoading = false,
  error = null,
}: JsonDisplayProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
        <div className="text-muted-foreground">Loading JSON...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="border-b border-border p-2 flex items-center justify-end gap-2 bg-background">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="gap-1"
        >
          {copied ? (
            <>
              <Check className="w-4 h-4" />
              Copied
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-4 font-mono text-sm">
          <JsonNode data={data} level={0} />
        </div>
      </ScrollArea>
    </div>
  );
}
