import React from 'react';
import { AVAILABLE_DATASETS } from '@/data/datasets';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card } from '@/components/ui/card';

interface DatasetSelectorProps {
  currentDatasetId: string;
  onDatasetChange: (datasetId: string) => void;
}

export function DatasetSelector({ currentDatasetId, onDatasetChange }: DatasetSelectorProps) {
  const currentDataset = AVAILABLE_DATASETS.find(d => d.id === currentDatasetId);

  return (
    <div className="space-y-3 p-4 border-b">
      <div className="space-y-2">
        <label className="text-sm font-semibold text-muted-foreground">Project / Dataset</label>
        <Select value={currentDatasetId} onValueChange={onDatasetChange}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {AVAILABLE_DATASETS.map((dataset) => (
              <SelectItem key={dataset.id} value={dataset.id}>
                <div className="flex items-center gap-2">
                  <span>{dataset.icon}</span>
                  <span>{dataset.name}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {currentDataset && (
        <Card className="p-3 bg-muted/50 border-0">
          <p className="text-xs text-muted-foreground leading-relaxed">
            {currentDataset.description}
          </p>
        </Card>
      )}
    </div>
  );
}
