# Quick Fix Reference: Per-Node State Crashes

## One-Minute Problem Summary

The per-node state implementation crashed when clicking certain nodes because:
1. Parent props weren't synced to local state
2. State was accessed before being initialized
3. State was updated during render (not in effects)
4. useEffect dependencies were incomplete

## The Five Critical Fixes

### Fix 1: Add State Sync Effect

```typescript
// At top of component, FIRST effect
useEffect(() => {
  setDisplayedNodeId(selectedNodeId);
}, [selectedNodeId]);
```

**Why:** Ensures local state always matches parent's selectedNodeId

---

### Fix 2: Safe State Access

```typescript
// Helper function
const getNodeState = useCallback((nodeId: string | null): NodePanelState => {
  if (!nodeId) return { showMarkdown: false, viewMode: 'table' };
  return nodePanelStates[nodeId] ?? { showMarkdown: false, viewMode: 'table' };
}, [nodePanelStates]);

// In render
const displayedNodeState = useMemo(() => {
  return getNodeState(displayedNodeId);
}, [displayedNodeId, getNodeState]);
```

**Why:** Always returns valid state, prevents crashes from undefined access

---

### Fix 3: Move State Updates to Effects

```typescript
// ❌ WRONG - in main effect
useEffect(() => {
  if (node.execution_status === 'not_executed') {
    setNodePanelState(displayedNodeId, { viewMode: 'code' });
  }
}, [displayedNodeId, node]);

// ✅ CORRECT - separate effect
useEffect(() => {
  if (executionStatus === 'not_executed') {
    updateNodeState(displayedNodeId, { viewMode: 'code' });
  }
}, [displayedNodeId, executionStatus]);
```

**Why:** Prevents state updates during render phase, ensures clean effect logic

---

### Fix 4: Complete Dependencies

```typescript
// ❌ WRONG
useEffect(() => {
  if (isImageNode && !nodePanelStates[displayedNodeId]) {
    setNodePanelState(displayedNodeId, { showMarkdown: true });
  }
}, [isImageNode, displayedNodeId]); // Missing: nodePanelStates!

// ✅ CORRECT
useEffect(() => {
  const state = nodePanelStates[displayedNodeId];
  if (isImageNode && !state) {
    updateNodeState(displayedNodeId, { showMarkdown: true });
  }
}, [isImageNode, displayedNodeId, nodePanelStates]);
```

**Why:** Prevents stale closures, ensures effect runs when dependencies change

---

### Fix 5: Immutable State Updates

```typescript
// ❌ WRONG - direct mutation
const setNodePanelState = (nodeId: string, state: Partial<NodePanelState>) => {
  nodePanelStates[nodeId] = state;  // Wrong!
};

// ✅ CORRECT - functional setState
const updateNodeState = useCallback((nodeId: string | null, updates: Partial<NodePanelState>) => {
  if (!nodeId) return;
  setNodePanelStates(prev => ({
    ...prev,
    [nodeId]: { ...getNodeState(nodeId), ...updates }
  }));
}, [getNodeState]);
```

**Why:** React requires immutable updates to detect state changes

---

## Testing the Fixes

```bash
# Test 1: Rapid node clicking
- Click "merge_data" fast
- Click "load_user_data" fast
- No crashes = success

# Test 2: Unexecuted nodes
- Click unexecuted node
- Should see code view
- No crashes = success

# Test 3: State persistence
- Click node A, set code view
- Click node B, set markdown view
- Return to A: should have code view
- Return to B: should have markdown view
```

## Key Variables

```typescript
interface NodePanelState {
  showMarkdown: boolean;  // Is markdown panel visible?
  viewMode: 'table' | 'code';  // Showing table or code?
}

// Usage:
displayedNodeState.viewMode     // Current view mode
displayedNodeState.showMarkdown // Markdown panel open?
```

## Common Error Patterns to AVOID

1. **Accessing state that may not exist**
   ```typescript
   // ❌ CRASHES if nodeId not in map
   nodePanelStates[nodeId].viewMode
   
   // ✅ Safe
   getNodeState(nodeId).viewMode
   ```

2. **Missing dependency in effect**
   ```typescript
   // ❌ Stale closure
   useEffect(() => {
     setNodePanelState(displayedNodeId, { viewMode: determineViewMode(nodePanelStates) });
   }, [displayedNodeId]); // Missing nodePanelStates!
   
   // ✅ All deps included
   useEffect(() => {
     // ...
   }, [displayedNodeId, nodePanelStates, /* other deps */]);
   ```

3. **State update in render phase**
   ```typescript
   // ❌ Direct call
   if (isImageNode) {
     setNodePanelState(displayedNodeId, { showMarkdown: true });
   }
   
   // ✅ In effect
   useEffect(() => {
     if (isImageNode) {
       updateNodeState(displayedNodeId, { showMarkdown: true });
     }
   }, [isImageNode, displayedNodeId]);
   ```

## Success Criteria

Your implementation is safe when:
- [ ] No crashes when rapidly switching nodes
- [ ] No crashes on first click of any node
- [ ] Node state persists when switching away and returning
- [ ] Unexecuted nodes show code view
- [ ] Image nodes show markdown view
- [ ] ESLint shows no warnings for deps
- [ ] React DevTools Profiler shows no unexpected renders

## If Still Crashing

1. Check console for errors - read the full message
2. Check if nodePanelStates[nodeId] is accessed without getNodeState()
3. Check all useEffect dependencies with eslint-plugin-react-hooks
4. Add console.log() in getNodeState() to debug access patterns
5. Check if selectedNodeId is being passed correctly from parent
