# Code Snippets - Copy and Paste Templates

Ready-to-use code patterns for implementing per-node panel state safely.

## Pattern 1: State Declaration Block

```typescript
// Place at the top of DataTable component after props
// ============================================

interface NodePanelState {
  showMarkdown: boolean;
  viewMode: 'table' | 'code';
}

export function DataTable({ selectedNodeId, ...otherProps }: DataTableProps) {
  // Initialize displayed node ID as null first
  const [displayedNodeId, setDisplayedNodeId] = useState<string | null>(null);
  
  // Per-node state storage
  const [nodePanelStates, setNodePanelStates] = useState<Record<string, NodePanelState>>({});

  // === HELPERS (memoized) ===
  
  const getNodeState = useCallback((nodeId: string | null): NodePanelState => {
    if (!nodeId) {
      return { showMarkdown: false, viewMode: 'table' };
    }
    // Always return valid state, even if node not visited
    return nodePanelStates[nodeId] ?? { showMarkdown: false, viewMode: 'table' };
  }, [nodePanelStates]);

  const updateNodeState = useCallback(
    (nodeId: string | null, updates: Partial<NodePanelState>) => {
      if (!nodeId) return;
      
      setNodePanelStates(prev => {
        const current = getNodeState(nodeId);
        return {
          ...prev,
          [nodeId]: { ...current, ...updates }
        };
      });
    },
    [getNodeState]
  );

  // Derived state (memoized to prevent unnecessary renders)
  const displayedNodeState = useMemo(() => {
    return getNodeState(displayedNodeId);
  }, [displayedNodeId, getNodeState]);

  // ============================================
  // Rest of component continues below...
}
```

## Pattern 2: State Synchronization Effect

```typescript
// Add this FIRST effect to sync parent prop changes
// ==================================================

useEffect(() => {
  setDisplayedNodeId(selectedNodeId);
}, [selectedNodeId]);

// This ensures local state always matches parent's selectedNodeId
```

## Pattern 3: Node Data Loading Effect

```typescript
// Load node data when displayed node changes
// =========================================

useEffect(() => {
  if (!displayedNodeId) {
    setApiData(null);
    setApiCode('');
    setApiMarkdown('');
    setNodeResultFormat('parquet');
    return;
  }

  const loadNodeData = async () => {
    try {
      // Get node data (from API or fallback to hardcoded)
      const nodeData = nodeDataMap[displayedNodeId];
      
      if (nodeData) {
        setApiData({
          headers: nodeData.headers,
          data: nodeData.data,
          totalRecords: nodeData.totalRecords,
          currentPage: 1,
        });
        
        setApiCode(nodeData.code || '');
        setApiMarkdown(nodeData.conclusion || '');
        setNodeResultFormat(nodeData.result_format || 'parquet');
        
        // Initialize state for this node if it doesn't exist
        if (!nodePanelStates[displayedNodeId]) {
          updateNodeState(displayedNodeId, {
            viewMode: 'table',
            showMarkdown: false
          });
        }
      }
    } catch (error) {
      console.error('Failed to load node data:', error);
    }
  };

  loadNodeData();
}, [displayedNodeId]); // Only depends on displayedNodeId
```

## Pattern 4: Special Node Type Handling Effect

```typescript
// Separate effect for special node type logic
// ==========================================

useEffect(() => {
  if (!displayedNodeId) return;

  const nodeData = nodeDataMap[displayedNodeId];
  if (!nodeData) return;

  const resultFormat = nodeData.result_format || 'parquet';
  const executionStatus = getExecutionStatus(displayedNodeId);

  // Handle unexecuted nodes
  if (executionStatus === 'not_executed') {
    updateNodeState(displayedNodeId, { viewMode: 'code' });
    setIsEditingCode(true);
  }
  // Handle image/visualization nodes
  else if (resultFormat === 'image' || resultFormat === 'visualization') {
    updateNodeState(displayedNodeId, {
      showMarkdown: true,
      viewMode: 'table'
    });
  }
}, [displayedNodeId]); // Only depends on displayedNodeId
```

## Pattern 5: Button Click Handlers

```typescript
// Code view toggle button handler
// ==============================

const handleToggleCodeView = () => {
  if (nodeExecutionStatus === 'not_executed') {
    toast({ description: 'Please execute the code first' });
    return;
  }

  updateNodeState(displayedNodeId, {
    viewMode: displayedNodeState.viewMode === 'code' ? 'table' : 'code'
  });
};

// Markdown panel toggle button handler
// ===================================

const handleToggleMarkdown = () => {
  if (nodeExecutionStatus === 'not_executed') {
    toast({ description: 'Please execute the code first' });
    return;
  }

  if (displayedNodeState.showMarkdown) {
    // Close markdown panel - check for unsaved changes
    checkAndCloseMarkdownPanel();
  } else {
    // Open markdown panel
    updateNodeState(displayedNodeId, { showMarkdown: true });
  }
};
```

## Pattern 6: Conditional Rendering

```typescript
// Use displayedNodeState for all conditional rendering
// ==================================================

return (
  <>
    {/* Button styling based on state */}
    <Button
      variant={displayedNodeState.viewMode === 'code' ? 'default' : 'ghost'}
      onClick={handleToggleCodeView}
    >
      <Code className="h-4 w-4" />
    </Button>

    <Button
      variant={displayedNodeState.showMarkdown ? 'default' : 'ghost'}
      onClick={handleToggleMarkdown}
    >
      <FileText className="h-4 w-4" />
    </Button>

    {/* Conditional panel display */}
    {displayedNodeState.showMarkdown ? (
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel defaultSize={60}>
          {displayedNodeState.viewMode === 'table' ? (
            <DataTableView data={currentData.data} />
          ) : (
            <CodeEditor
              value={apiCode}
              onChange={handleCodeChange}
            />
          )}
        </ResizablePanel>
        <ResizablePanel defaultSize={40}>
          <MarkdownPanel
            content={apiMarkdown}
            onEdit={handleMarkdownEdit}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    ) : displayedNodeState.viewMode === 'table' ? (
      <DataTableView data={currentData.data} />
    ) : (
      <CodeEditor value={apiCode} onChange={handleCodeChange} />
    )}
  </>
);
```

## Pattern 7: Testing Setup

```typescript
// Test file: DataTable.test.tsx
// ============================

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DataTable } from './DataTable';

describe('DataTable Per-Node State', () => {
  it('should sync selectedNodeId prop to displayed node', async () => {
    const { rerender } = render(
      <DataTable selectedNodeId="data-1" />
    );
    
    await waitFor(() => {
      expect(screen.getByText('用户基本信息数据')).toBeInTheDocument();
    });

    // Switch nodes
    rerender(<DataTable selectedNodeId="data-2" />);
    
    await waitFor(() => {
      expect(screen.getByText('贷款申请数据')).toBeInTheDocument();
    });
  });

  it('should persist state when returning to a node', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <DataTable selectedNodeId="data-1" />
    );

    // Set to code view
    await user.click(screen.getByRole('button', { name: /code/i }));

    // Switch nodes
    rerender(<DataTable selectedNodeId="data-2" />);
    await waitFor(() => {
      expect(screen.getByText('贷款申请数据')).toBeInTheDocument();
    });

    // Return to first node
    rerender(<DataTable selectedNodeId="data-1" />);
    
    // Should still be in code view
    expect(screen.getByText('python')).toBeInTheDocument();
  });

  it('should handle rapid node switching', async () => {
    const { rerender } = render(
      <DataTable selectedNodeId="data-1" />
    );

    // Rapid switches
    rerender(<DataTable selectedNodeId="data-2" />);
    rerender(<DataTable selectedNodeId="data-3" />);
    rerender(<DataTable selectedNodeId="data-1" />);

    // Should not crash and show correct node
    await waitFor(() => {
      expect(screen.getByText('用户基本信息数据')).toBeInTheDocument();
    });
  });
});
```

## Pattern 8: LocalStorage Persistence (Simpler Alternative)

```typescript
// If you want simpler per-node state without complex effects
// Use localStorage to persist view preferences
// ==========================================================

const getStoredViewMode = (nodeId: string): 'table' | 'code' => {
  try {
    const stored = localStorage.getItem(`view-${nodeId}`);
    return (stored === 'code' ? 'code' : 'table') as 'table' | 'code';
  } catch {
    return 'table';
  }
};

const setStoredViewMode = (nodeId: string, mode: 'table' | 'code') => {
  try {
    localStorage.setItem(`view-${nodeId}`, mode);
  } catch {
    // Fail silently if localStorage not available
  }
};

// In component:
const [viewMode, setViewMode] = useState<'table' | 'code'>('table');

useEffect(() => {
  if (selectedNodeId) {
    setViewMode(getStoredViewMode(selectedNodeId));
  }
}, [selectedNodeId]);

const handleViewModeChange = (mode: 'table' | 'code') => {
  setViewMode(mode);
  if (selectedNodeId) {
    setStoredViewMode(selectedNodeId, mode);
  }
};
```

## Checklist Before Using These Patterns

Before copying and pasting:

- [ ] You've read PER_NODE_STATE_GUIDE.md
- [ ] You understand the five critical bugs
- [ ] Your component has the necessary imports (useState, useEffect, useCallback, useMemo)
- [ ] You've set up proper TypeScript types
- [ ] You have a testing plan
- [ ] You have React DevTools installed for debugging
- [ ] You understand the difference between effect timing and render phase

## Common Copy-Paste Mistakes to Avoid

1. **Forgetting dependencies**
   - ❌ Copy code but forgot to include all [dependencies]
   - Use: `eslint-plugin-react-hooks` to catch these

2. **Wrong closure variables**
   - ❌ Copied effect but used wrong variable names
   - Check: All variable names match your component

3. **Missing error handling**
   - ❌ Forgot try-catch in async functions
   - Add: Error handling for API calls

4. **Not initializing state**
   - ❌ Forgot to initialize nodePanelStates
   - Remember: Must initialize ALL state hooks

5. **Mixing patterns**
   - ❌ Mixing localStorage pattern with full state pattern
   - Choose: One approach, stick with it

---

**Ready to use**: Copy these patterns as-is and adapt variable names to your component
**Need clarification?**: See PER_NODE_STATE_GUIDE.md for detailed explanations
**Still have issues?**: Check CRASH_ANALYSIS.md for what goes wrong
