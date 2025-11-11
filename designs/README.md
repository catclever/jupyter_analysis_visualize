# Design Documents

This directory contains design proposals and specifications for upcoming features and architectural improvements to the Jupyter Analysis Visualize project.

## Current Design Documents

### 1. NODE_INPUT_OUTPUT_MODEL.md ⭐ **ACTIVE**
**Status**: Approved design proposal
**Purpose**: Comprehensive node standardization and input/output model specification

Complete design for standardizing node types with clear input/output specifications:
- **5 node types**: Data Source, Processing, Analysis, Visualization, Tool
- **Input modeling**: Source input, dependency input, parameter input
- **Output specification**: Automatic type inference and frontend display mapping
- **Visual graph representation**: Color coding, icons, and line styles for node distinction
- **Metadata schema**: Complete JSON structure for node input/output
- **Frontend integration**: Node card design and DAG visualization

**Key sections**:
1. Node complete definition with input/output/processing
2. Input type classification (source, dependency, parameter)
3. Five detailed node types with examples
4. Visual representation on DAG (icons, colors, line styles)
5. Complete metadata schema
6. Frontend rendering design
7. Constraints summary table
8. Implementation recommendations (immediate, medium-term, long-term)

**Next steps**: Ready for implementation starting with Phase 1 (backend)

---

### 2. NODE_IMPLEMENTATION_STEPS.md ⭐ **ACTIVE**
**Status**: Implementation guide (should be updated to align with NODE_INPUT_OUTPUT_MODEL.md)
**Purpose**: Detailed step-by-step implementation plan

Provides concrete implementation details for three phases:
- **Phase 1** (2-3 days): Backend output type inference
  - Add `_infer_output_type()` method to ExecutionManager
  - Update API response structure
  - Test with existing projects

- **Phase 2** (3-4 days): Frontend rendering
  - Create `NodeResultViewer` component
  - Update API integration
  - Add node information cards

- **Phase 3** (1-2 days): Verification and optimization
  - Testing with all project types
  - Performance optimization
  - Documentation updates

**Note**: This document was created before the complete NODE_INPUT_OUTPUT_MODEL.md and should be updated to incorporate the full input/output model.

---

### 3. CACHING_STRATEGY.md
**Status**: Reference design (for future optimization)
**Purpose**: Frontend caching strategy for project data and execution state

Describes:
- Current state and relationships between backend and frontend
- Recommended caching strategy (project cache + editing draft)
- State tree structure
- Page load and editing flow
- Cache invalidation strategy

**Next steps**: Consider implementing after core node standardization is complete.

---

## Design Evolution Process

### Rule 1: Design Optimization
When optimizing designs:
1. Create new files as needed for refinement
2. Delete or modify obsolete files
3. Consolidate learnings into final documents
4. Avoid accumulation of outdated designs

### Rule 2: Design Cleanup After Implementation
Once a feature is implemented:
1. Delete the corresponding design file
2. Move relevant docs to `reports/` if needed
3. Keep only designs that are:
   - Under review
   - Planned but not implemented
   - Awaiting approval

**Example**:
- Phase: Implement node standardization
- Delete: `designs/NODE_IMPLEMENTATION_STEPS.md` after completion
- Archive: Implementation details to `reports/NODE_STANDARDIZATION_IMPLEMENTATION.md`

---

## How to Use These Documents

### For Developers
1. Start with **NODE_INPUT_OUTPUT_MODEL.md** (Section 8) for what needs to be implemented
2. Follow **NODE_IMPLEMENTATION_STEPS.md** for concrete implementation details
3. Reference **NODE_INPUT_OUTPUT_MODEL.md** (Sections 1-7) for specifications

### For Reviewers
1. Review **NODE_INPUT_OUTPUT_MODEL.md** (Sections 1-5) for architecture and design
2. Check **NODE_INPUT_OUTPUT_MODEL.md** (Section 7) for constraint compliance
3. Verify Phase 1 implementation against **NODE_IMPLEMENTATION_STEPS.md**

### For Stakeholders
1. Read **NODE_INPUT_OUTPUT_MODEL.md** (Sections 4-6) for visual and UX impact
2. Check timeline in **NODE_IMPLEMENTATION_STEPS.md** (Phase overview)
3. Review **NODE_INPUT_OUTPUT_MODEL.md** (Section 8) for rollout strategy

---

## Document History

- **2025-11-11**: Added design cleanup rules to CLAUDE.md
- **2025-11-11**: Consolidated node design iterations:
  - ✅ Deleted obsolete: NODE_OUTPUT_DESIGN.md, NODE_ARCHITECTURE_EVOLUTION.md
  - ✅ Kept active: NODE_INPUT_OUTPUT_MODEL.md (definitive design)
  - ✅ Kept active: NODE_IMPLEMENTATION_STEPS.md (implementation guide)
  - ✅ Kept for reference: CACHING_STRATEGY.md

---

## Status Legend

- ⭐ **ACTIVE**: Ready for implementation
- 🔄 **IN PROGRESS**: Currently being developed
- 📋 **PENDING REVIEW**: Awaiting approval
- 📚 **REFERENCE**: For future reference/planning
- 🗑️ **ARCHIVED**: Previous design (kept for history)
