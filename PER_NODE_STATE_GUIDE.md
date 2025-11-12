# Safe Per-Node Panel State Implementation Guide

## Overview

This guide provides a safe, tested approach to implementing per-node panel state management in DataTable.tsx without causing crashes.

## Key Principles

1. **Prop Sync First** - Always sync parent props to local state in a useEffect
2. **Deferred State Updates** - Move all state mutations to useEffect, not render phase
3. **Complete Dependencies** - Every state variable in a closure must be in useEffect dependencies
4. **Defensive Fallbacks** - Always have sensible defaults when accessing nested state
5. **Immutable Updates** - Use functional setState with proper spreading

## Safe Implementation Pattern

### Phase 1: State Declaration and Synchronization

```typescript
export function DataTable({ selectedNodeId, ...props }: DataTableProps) {
  // IMPORTANT: This MUST be the primary state source
  const [displayedNodeId, setDisplayedNodeId] = useState<string | null>(null);
  
  // Per-node state storage
  const [nodePanelStates, setNodePanelStates] = useState<Record<string, NodePanelState>>({});

  // STEP 1: Sync parent prop to local state on changes
  // This prevents stale state issues
  useEffect(() => {
    setDisplayedNodeId(selectedNodeId);
  }, [selectedNodeId]);

  // STEP 2: Helper to get node state (with safe fallback)
  const getNodeState = useCallback((nodeId: string | null): NodePanelState => {
    if (!nodeId) {
      return { showMarkdown: false, viewMode: 'table' };
    }
    
    // Always return a value, even if not in map (prevents crashes)
    return nodePanelStates[nodeId] ?? { showMarkdown: false, viewMode: 'table' };
  }, [nodePanelStates]);

  // STEP 3: Helper to update node state (immutable)
  const updateNodeState = useCallback((nodeId: string | null, updates: Partial<NodePanelState>) => {
    if (!nodeId) return;
    
    setNodePanelStates(prev => {
      const current = prev[nodeId] ?? { showMarkdown: false, viewMode: 'table' };
      return {
        ...prev,
        [nodeId]: { ...current, ...updates }
      };
    });
  }, []);

  // STEP 4: Create derived state (memoized to prevent unnecessary renders)
  const displayedNodeState = useMemo(() => {
    return getNodeState(displayedNodeId);
  }, [displayedNodeId, getNodeState]);

  return (
    // render...
  );
}
```

### Phase 2: Node Data Loading

```typescript
// Extract the node data loading logic into its own effect
useEffect(() => {
  if (!displayedNodeId) {
    setApiData(null);
    setApiCode('');
    setApiMarkdown('');
    return;
  }

  const loadNodeData = async () => {
    try {
      // Load from API or fallback to hardcoded
      let nodeData = nodeDataMap[displayedNodeId];
      
      if (nodeData) {
        // Determine execution status, format, etc.
        const executionStatus = getExecutionStatus(displayedNodeId);
        const resultFormat = cachedResultFormat?.[displayedNodeId] ?? 'parquet';

        // STEP: Initialize state for this node if needed
        if (!nodePanelStates[displayedNodeId]) {
          updateNodeState(displayedNodeId, { 
            viewMode: 'table', 
            showMarkdown: false 
          });
        }

        // STEP: Handle special node types (deferred, not in render phase)
        if (executionStatus === 'not_executed') {
          // Queue a state update for the next effect
          scheduleNodeStateUpdate(displayedNodeId, { viewMode: 'code' });
        } else if (resultFormat === 'image') {
          scheduleNodeStateUpdate(displayedNodeId, { 
            showMarkdown: true, 
            viewMode: 'table' 
          });
        }
      }
    } catch (error) {
      console.error('Error loading node:', error);
    }
  };

  loadNodeData();
}, [displayedNodeId]); // Only depends on displayedNodeId, not other state
```

### Phase 3: Special Node Type Handling

```typescript
// Separate effect for handling special node types
// This prevents coupling the data loading with state updates
useEffect(() => {
  if (!displayedNodeId) return;

  const nodeData = nodeDataMap[displayedNodeId];
  if (!nodeData) return;

  const resultFormat = cachedResultFormat?.[displayedNodeId] ?? 'parquet';
  const executionStatus = getExecutionStatus(displayedNodeId);

  // Handle unexecuted nodes
  if (executionStatus === 'not_executed') {
    updateNodeState(displayedNodeId, { viewMode: 'code' });
    setIsEditingCode(true);
  }
  // Handle image nodes
  else if (resultFormat === 'image' || resultFormat === 'visualization') {
    updateNodeState(displayedNodeId, { showMarkdown: true, viewMode: 'table' });
  }
}, [displayedNodeId, cachedResultFormat, getExecutionStatus]);
```

### Phase 4: Button Event Handlers

```typescript
// Code view toggle
const handleToggleCodeView = () => {
  if (effectiveNodeExecutionStatus === 'not_executed') {
    toast({ description: 'Please execute the code first' });
    return;
  }

  updateNodeState(displayedNodeId, {
    viewMode: displayedNodeState.viewMode === 'code' ? 'table' : 'code'
  });
};

// Markdown panel toggle
const handleToggleMarkdown = () => {
  if (effectiveNodeExecutionStatus === 'not_executed') {
    toast({ description: 'Please execute the code first' });
    return;
  }

  if (displayedNodeState.showMarkdown) {
    checkAndCloseMarkdownPanel();
  } else {
    updateNodeState(displayedNodeId, { showMarkdown: true });
  }
};
```

## Critical Fixes

### Problem 1: State Sync

BEFORE (❌ Crashes):
```typescript
const [displayedNodeId, setDisplayedNodeId] = useState<string | null>(selectedNodeId);
// No sync effect - selectedNodeId changes aren't reflected
```

AFTER (✅ Safe):
```typescript
const [displayedNodeId, setDisplayedNodeId] = useState<string | null>(null);

useEffect(() => {
  setDisplayedNodeId(selectedNodeId);
}, [selectedNodeId]);
```

### Problem 2: State Access Race Condition

BEFORE (❌ Crashes):
```typescript
const displayedNodePanelState = getNodePanelState(displayedNodeId);
// If nodePanelStates[displayedNodeId] doesn't exist yet, undefined error
```

AFTER (✅ Safe):
```typescript
const displayedNodePanelState = useMemo(() => {
  return getNodeState(displayedNodeId); // Always returns valid state
}, [displayedNodeId, getNodeState]);
```

### Problem 3: State Updates During Render

BEFORE (❌ Crashes):
```typescript
useEffect(() => {
  // Direct state update in main data loading effect
  if (node.execution_status === 'not_executed') {
    setNodePanelState(displayedNodeId, { viewMode: 'code' });
  }
}, [displayedNodeId, nodeData]); // Too many dependencies
```

AFTER (✅ Safe):
```typescript
// Separate effect just for state-based logic
useEffect(() => {
  if (!displayedNodeId) return;
  
  const executionStatus = getExecutionStatus(displayedNodeId);
  if (executionStatus === 'not_executed') {
    updateNodeState(displayedNodeId, { viewMode: 'code' });
  }
}, [displayedNodeId, getExecutionStatus]);
```

### Problem 4: Missing Dependencies

BEFORE (❌ Crashes):
```typescript
useEffect(() => {
  if (isImageNode && displayedNodeId && !nodePanelStates[displayedNodeId]) {
    setNodePanelState(displayedNodeId, { showMarkdown: true });
  }
}, [isImageNode, displayedNodeId]); // Missing: nodePanelStates
```

AFTER (✅ Safe):
```typescript
useEffect(() => {
  if (!displayedNodeId) return;
  
  // Get fresh state
  const state = nodePanelStates[displayedNodeId];
  const resultFormat = cachedResultFormat?.[displayedNodeId];
  
  if ((resultFormat === 'image' || resultFormat === 'visualization') && !state) {
    updateNodeState(displayedNodeId, { showMarkdown: true });
  }
}, [displayedNodeId, nodePanelStates, cachedResultFormat]);
```

## Testing Checklist

Before deploying per-node state, test:

1. **Rapid Node Switching**
   - Click different nodes quickly (within 100ms)
   - Verify no crashes, state is consistent

2. **Unexecuted Nodes**
   - Click on "merge_data", "load_user_data" (known problem nodes)
   - Verify code view opens, no crashes
   - Verify edit mode works

3. **Image Nodes**
   - Click on image/visualization nodes
   - Verify markdown panel opens automatically
   - Switch back to other nodes, verify state independent

4. **First Click Sensitivity**
   - Refresh page, immediately click various nodes
   - Verify no initialization issues

5. **State Persistence**
   - Open node A, set to code view
   - Open node B, set to markdown view
   - Return to node A - verify code view is still set
   - Return to node B - verify markdown view is still set

6. **Integration with Unsaved Changes Dialog**
   - Edit markdown in one node
   - Switch to another node - unsaved dialog should appear
   - Cancel - should stay on original node
   - Confirm - should navigate and clear unsaved state

## Common Pitfalls to Avoid

1. **Accessing state directly in render**
   - ❌ `if (nodePanelStates[selectedNodeId]?.viewMode === 'code')`
   - ✅ Use memoized derived state instead

2. **Missing dependencies in effects**
   - ❌ Using `nodePanelStates[nodeId]` without `nodePanelStates` in deps
   - ✅ Use exhaustive-deps eslint rule

3. **Direct state object mutations**
   - ❌ `state.viewMode = 'code'`
   - ✅ Use functional setState: `setState(prev => ({ ...prev, viewMode: 'code' }))`

4. **State updates in promises/callbacks without cleanup**
   - ❌ Updating state in `.then()` without checking if component mounted
   - ✅ Wrap in useEffect, use AbortController for cleanup

5. **Circular dependencies**
   - ❌ `getNodeState` uses `nodePanelStates`, useCallback includes `getNodeState`
   - ✅ Keep helpers independent or use useCallback properly

## Performance Considerations

- Use `useCallback` for helper functions to prevent unnecessary effect reruns
- Use `useMemo` for derived state to prevent cascading renders
- Don't store too many nodes in state (archive old nodes if app has many)
- Consider LocalStorage for persistence: `localStorage.setItem('nodePanelStates', JSON.stringify(nodePanelStates))`

## Example: Complete Safe Implementation

See the reference implementation pattern above in Phase 1-4 sections. The key is:
1. Sync parent props in dedicated effect
2. Use memoized helpers
3. Keep effects focused on single concerns
4. Always include complete dependencies
5. Provide safe fallbacks for all state access
