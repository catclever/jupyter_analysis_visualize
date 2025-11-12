# Frontend Crash Analysis: Per-Node Panel State Management

## Summary

The per-node panel state implementation (commit f7cff53) caused crashes when clicking on certain nodes like "merge_data" and "load_user_data". The code has been rolled back to commit 69f438a which works correctly.

## Root Causes Identified

### 1. **Timing Issue with `displayedNodeId` Initialization**

**The Problem:**
```typescript
const [displayedNodeId, setDisplayedNodeId] = useState<string | null>(selectedNodeId);

const getNodePanelState = (nodeId: string | null): NodePanelState => {
  if (!nodeId) return { showMarkdown: false, viewMode: 'table' };
  return nodePanelStates[nodeId] || { showMarkdown: false, viewMode: 'table' };
};
```

When a node is first selected, `displayedNodeId` is initialized from `selectedNodeId`. However, there's no synchronization between the parent's `selectedNodeId` prop and the component's `displayedNodeId` state. This means:

1. Parent component passes a new `selectedNodeId` (e.g., "merge_data")
2. Component's `displayedNodeId` state might not update immediately
3. Code attempts to access `nodePanelStates[displayedNodeId]` where `displayedNodeId` might not match the actual selected node

### 2. **useEffect Dependencies Missing**

**The Problem:**
```typescript
useEffect(() => {
  if (isImageNode && displayedNodeId && !nodePanelStates[displayedNodeId]) {
    setNodePanelState(displayedNodeId, { showMarkdown: true });
  }
}, [isImageNode, displayedNodeId]);  // Missing: nodePanelStates
```

The useEffect is missing `nodePanelStates` in its dependency array, which can cause:
- Stale closures when accessing `nodePanelStates`
- Race conditions where the check `!nodePanelStates[displayedNodeId]` is evaluated with outdated state
- Infinite loops if state updates trigger this effect

### 3. **Calls to `setNodePanelState` During Render Phase**

**The Problem:**
```typescript
// Inside the main useEffect that loads node data
if (node.execution_status === 'not_executed') {
  isNodeNotExecuted = true;
  setNodePanelState(displayedNodeId, { viewMode: 'code' });  // ❌ State update during data loading
  setIsEditingCode(true);
}
```

Calling state setters during the render phase or in non-effect contexts can cause:
- React warnings about state updates
- Unexpected render cycles
- State synchronization issues

### 4. **No Fallback for Non-Existent Nodes in Map**

**The Problem:**
```typescript
const displayedNodePanelState = getNodePanelState(displayedNodeId);
// Later uses like:
displayedNodePanelState.viewMode  // What if nodePanelStates is empty for a node?
```

If a node hasn't had its state initialized yet (first click on a node), there's no guarantee the state exists until the next render cycle. This creates a race condition.

### 5. **CodeEditor Component Replacement Issue**

While less critical, replacing `<textarea>` with `<CodeEditor>` could have introduced:
- The CodeEditor component might have different event handling
- The `onChange` callback signature might not match exactly
- Height/sizing issues causing layout crashes

## Why Specific Nodes Crashed

Nodes like "merge_data" and "load_user_data" likely crashed because:

1. They were clicked quickly after page load (before state was fully initialized)
2. They might be non-executed nodes (triggering the `setNodePanelState` call during data loading)
3. The `displayedNodeId` state hadn't synchronized with the new selection
4. Accessing `nodePanelStates[displayedNodeId]` before the state key existed

## Safe Implementation Strategy

To implement per-node panel state management correctly, follow this approach:

### Step 1: Proper State Synchronization

```typescript
const [displayedNodeId, setDisplayedNodeId] = useState<string | null>(selectedNodeId);
const [nodePanelStates, setNodePanelStates] = useState<Record<string, NodePanelState>>({});

// Sync parent prop changes
useEffect(() => {
  if (selectedNodeId !== displayedNodeId) {
    setDisplayedNodeId(selectedNodeId);
  }
}, [selectedNodeId, displayedNodeId]);
```

### Step 2: Initialize State Before Use

```typescript
const getNodePanelState = (nodeId: string | null): NodePanelState => {
  if (!nodeId) return { showMarkdown: false, viewMode: 'table' };
  
  // Ensure state exists for this node
  if (!nodePanelStates[nodeId]) {
    setNodePanelStates(prev => ({
      ...prev,
      [nodeId]: { showMarkdown: false, viewMode: 'table' }
    }));
  }
  
  return nodePanelStates[nodeId] || { showMarkdown: false, viewMode: 'table' };
};
```

### Step 3: Defer State Updates to useEffect

```typescript
// ❌ WRONG: Setting state during render/data loading
if (node.execution_status === 'not_executed') {
  setNodePanelState(displayedNodeId, { viewMode: 'code' });
}

// ✅ CORRECT: Use useEffect for side effects
useEffect(() => {
  if (displayedNodeId && nodeData?.execution_status === 'not_executed') {
    setNodePanelState(displayedNodeId, { viewMode: 'code' });
  }
}, [displayedNodeId, nodeData?.execution_status]);
```

### Step 4: Use Derived State Carefully

```typescript
// Avoid creating derived state from state that might be stale
const displayedNodePanelState = getNodePanelState(displayedNodeId);

// Better: Use useMemo with proper dependencies
const displayedNodePanelState = useMemo(() => {
  return getNodePanelState(displayedNodeId);
}, [displayedNodeId, nodePanelStates]);
```

### Step 5: Ensure Complete Dependency Arrays

```typescript
useEffect(() => {
  if (isImageNode && displayedNodeId && !nodePanelStates[displayedNodeId]) {
    setNodePanelState(displayedNodeId, { showMarkdown: true });
  }
}, [isImageNode, displayedNodeId, nodePanelStates]);  // ✅ Include all dependencies
```

## Implementation Checklist

When re-implementing per-node state management:

- [ ] Add `useEffect` to sync `selectedNodeId` prop with `displayedNodeId` state
- [ ] Initialize node state in state getter before using it
- [ ] Move all state setters into `useEffect` hooks (never in render phase)
- [ ] Include ALL state dependencies in useEffect dependency arrays
- [ ] Test with rapid node selection to catch race conditions
- [ ] Test with all node types: data, compute, chart, image, unexecuted
- [ ] Verify CodeEditor maintains the same signature as textarea
- [ ] Use React DevTools Profiler to detect unnecessary renders

## Current Working Version

The current working version (69f438a) uses global state with `showConclusion` and `viewMode`:

```typescript
const [viewMode, setViewMode] = useState<'table' | 'code'>('table');
const [showConclusion, setShowConclusion] = useState(false);
```

**Advantages:**
- Simple, no race conditions
- Works reliably
- Easy to debug

**Disadvantages:**
- Doesn't maintain per-node state
- Users lose their view preference when switching nodes

## Next Steps

1. Keep the current 69f438a version stable
2. Implement per-node state carefully following the checklist above
3. Test extensively with the problematic nodes
4. Consider a hybrid approach: global state for immediate UX, saved to local storage for persistence
