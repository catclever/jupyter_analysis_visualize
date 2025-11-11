/**
 * Image Display Component
 *
 * Displays image results (PNG, JPG, GIF, etc.)
 */

import React, { useState } from "react";
import { AlertCircle, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ImageDisplayProps {
  imageUrl: string;
  alt?: string;
  isLoading?: boolean;
  error?: string | null;
}

export function ImageDisplay({
  imageUrl,
  alt = "Result image",
  isLoading = false,
  error = null,
}: ImageDisplayProps) {
  const [scale, setScale] = useState(1);
  const [imageError, setImageError] = useState(false);

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  const handleReset = () => {
    setScale(1);
  };

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading image...</div>
      </div>
    );
  }

  if (imageError) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted rounded">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 text-destructive mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">Failed to load image</p>
          <p className="text-xs text-muted-foreground mt-1">{imageUrl}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-muted rounded">
      {/* Controls */}
      <div className="border-b border-border p-2 flex items-center gap-2 bg-background">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          title="Zoom in"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          title="Zoom out"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        <div className="text-xs text-muted-foreground ml-2">
          {Math.round(scale * 100)}%
        </div>
        {scale !== 1 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="ml-auto"
            title="Reset zoom"
          >
            Reset
          </Button>
        )}
      </div>

      {/* Image Container */}
      <div className="flex-1 overflow-auto flex items-center justify-center p-4">
        <div
          style={{
            transform: `scale(${scale})`,
            transformOrigin: "center",
            transition: "transform 0.2s ease-out",
          }}
        >
          <img
            src={imageUrl}
            alt={alt}
            onError={() => setImageError(true)}
            className="max-w-full h-auto shadow-lg rounded"
            style={{
              maxHeight: `${100 / scale}%`,
              maxWidth: `${100 / scale}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
