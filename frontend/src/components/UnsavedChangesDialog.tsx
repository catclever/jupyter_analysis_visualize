/**
 * Unsaved Changes Dialog Component
 *
 * Reusable dialog for confirming unsaved changes
 * Used when navigating away, closing panels, or switching nodes
 */

import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { AlertCircle } from 'lucide-react';

interface UnsavedChangesDialogProps {
  open: boolean;
  isSaving?: boolean;
  onSave: () => void | Promise<void>;
  onDiscard: () => void;
  onCancel: () => void;
  title?: string;
  description?: string;
}

export function UnsavedChangesDialog({
  open,
  isSaving = false,
  onSave,
  onDiscard,
  onCancel,
  title = 'Unsaved Changes',
  description = 'You have unsaved changes. What would you like to do?',
}: UnsavedChangesDialogProps) {
  const handleSave = async (e: React.MouseEvent) => {
    e.preventDefault();
    await onSave();
  };

  return (
    <AlertDialog open={open} onOpenChange={(isOpen) => {
      if (!isOpen) {
        onCancel();
      }
    }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600" />
            <AlertDialogTitle>{title}</AlertDialogTitle>
          </div>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex gap-2 justify-end">
          <AlertDialogCancel onClick={onCancel} disabled={isSaving}>
            Cancel
          </AlertDialogCancel>
          <button
            onClick={onDiscard}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 disabled:opacity-50"
          >
            Discard
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
