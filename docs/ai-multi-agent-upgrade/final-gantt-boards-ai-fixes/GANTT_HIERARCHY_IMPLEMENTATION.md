# QLDAPM — Gantt Hierarchy Implementation & Behavior Guide

> **Target:** `/projects/qldapm-local/gantt`  
> **Saved View:** `QLDAPM — Scrum Roadmap theo Epic` (Query ID 37)  
> **Date:** 2026-10-20  

---

## 1. Hierarchy Specification & Ordering

### 1.1. Level Hierarchy
1. **Level 0 (Root Epics):** 11 Epics (IDs 38 to 48).
   - Indentation: `25px`.
   - Classes: `wp-table--row __hierarchy-root-{id} wp-table--hierarchy-aditional-row`.
   - Action: Clicking `a.wp-table--hierarchy-indicator` toggles expansion/collapse of all children.
2. **Level 1 (Tasks):** 54 Tasks (IDs 49..102, 447).
   - Indentation: `45px`.
   - Classes: `wp-table--row __hierarchy-root-{id} __hierarchy-group-{epic_id}`.
   - Action: Expanding a Task reveals its Subtasks. Collapsing hides them.
3. **Level 2 (Subtasks):** 270 Subtasks (IDs 103..372, 441..446).
   - Indentation: `65px`.
   - Classes: `wp-table--row __hierarchy-group-{epic_id} __hierarchy-group-{task_id}`.
   - Leaf nodes: No child indicator.

---

## 2. Interaction Contract
- **Initial Load:** All 11 Root Epics are collapsed. Only 11 rows are visible.
- **Epic Expansion:** Clicking Epic 38 (`Tài khoản & Role`) expands it, revealing Tasks 49, 50, 51.
- **Task Expansion:** Clicking Task 49 (`AUTH-01`) reveals its 5 Subtasks (BA, BE, FE, QA, PM).
- **Epic Collapse:** Clicking Epic 38 indicator hides all its Tasks and Subtasks instantly.
- **Zero Loss / Zero Duplication:** Work package IDs remain unique, parent linkages strictly respected.

---

## 3. Playwright Verification Results
- **Initial Collapsed Count:** 11 visible rows (IDs 38..48).
- **After Expanding Epic 38:** 16 visible rows.
- **After Expanding Task 49:** 16 visible rows (leaf tasks and subtasks displayed).
- **After Re-collapsing Epic 38:** 11 visible rows.
- **Screenshots:**
  - `gantt_all_epics_collapsed.png`
  - `gantt_epic38_expanded.png`
  - `gantt_task49_expanded.png`
  - `gantt_epic38_recollapsed.png`
