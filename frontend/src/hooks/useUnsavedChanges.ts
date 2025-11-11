/**
 * Hook for managing unsaved changes with confirmation dialog
 *
 * Handles the logic for:
 * - Detecting unsaved changes
 * - Showing confirmation dialog when needed
 * - Allowing user to save, discard, or cancel navigation
 */

import { useState, useCallback } from 'react';

export interface UnsavedChangesState {
  hasChanges: boolean;
  showDialog: boolean;
  pendingAction: (() => void) | null;
}

export interface UseUnsavedChangesReturn {
  hasChanges: boolean;
  showDialog: boolean;
  checkAndNavigate: (action: () => void) => void;
  confirmSave: (saveCallback: () => Promise<void>) => Promise<void>;
  confirmDiscard: () => void;
  confirmCancel: () => void;
  markAsChanged: () => void;
  markAsSaved: () => void;
  reset: () => void;
}

export function useUnsavedChanges(): UseUnsavedChangesReturn {
  const [hasChanges, setHasChanges] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [pendingAction, setPendingAction] = useState<(() => void) | null>(null);

  const checkAndNavigate = useCallback((action: () => void) => {
    if (hasChanges) {
      setPendingAction(() => action);
      setShowDialog(true);
    } else {
      action();
    }
  }, [hasChanges]);

  const confirmSave = useCallback(async (saveCallback: () => Promise<void>) => {
    try {
      await saveCallback();
      setHasChanges(false);
      setShowDialog(false);
      pendingAction?.();
    } catch (err) {
      console.error('Failed to save:', err);
      throw err;
    }
  }, [pendingAction]);

  const confirmDiscard = useCallback(() => {
    setHasChanges(false);
    setShowDialog(false);
    pendingAction?.();
  }, [pendingAction]);

  const confirmCancel = useCallback(() => {
    setShowDialog(false);
    setPendingAction(null);
  }, []);

  const markAsChanged = useCallback(() => {
    setHasChanges(true);
  }, []);

  const markAsSaved = useCallback(() => {
    setHasChanges(false);
  }, []);

  const reset = useCallback(() => {
    setHasChanges(false);
    setShowDialog(false);
    setPendingAction(null);
  }, []);

  return {
    hasChanges,
    showDialog,
    checkAndNavigate,
    confirmSave,
    confirmDiscard,
    confirmCancel,
    markAsChanged,
    markAsSaved,
    reset,
  };
}
