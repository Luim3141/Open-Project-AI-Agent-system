# QLDAPM — Root Cause Analysis: Gantt Hierarchy & Tree Ordering

> **Target:** Project Gantt (`/projects/qldapm-local/gantt`)  
> **Topic:** Work Package Hierarchy, Paging Fragmentation & Tree Ordering  
> **Date:** 2026-10-20  

---

## 1. Problem Statement
When navigating to the Project Gantt view, users observed:
1. Root Epics were expanded by default on initial view rather than starting collapsed.
2. The tree appeared truncated or fragmented: only 2 Epics (38 and 39) were visible on the first page, while the remaining 9 Epics were split across 17 pagination pages.
3. Collapsing Epics on Page 1 left the screen almost empty.

---

## 2. Root Cause Analysis (RCA)

### 2.1. OpenProject Angular Pagination Splitting the Hierarchy Tree
OpenProject's Angular frontend (`WorkPackageTableTimelineService` and `WorkPackageViewHierarchiesService`) loads items through `/api/v3/projects/3/work_packages`.
- By default, `Setting.per_page_options` only permitted `20` and `100` items per page.
- On `/projects/qldapm-local/gantt`, queries defaulted to `pageSize=20`.
- Because Project 3 contains 335 items, OpenProject partitioned them into 17 pages (Page 1 = items 1..20, Page 2 = items 21..40, ..., Page 17 = items 321..335).
- In a hierarchical query:
  - Epic 38 and its immediate children occupied slots 1..15.
  - Epic 39 occupied slots 16..20.
  - Epics 40, 41, 42, 43, 44, 45, 46, 47, 48 were pushed onto subsequent pages (Pages 2 through 17).
- When a user clicked "Collapse" on Epic 38 and Epic 39, their children were hidden, leaving **only 2 rows on Page 1**!
- The remaining 9 Epics could not appear on Page 1 because they were on later pages.

### 2.2. Angular Initial Collapse State
In OpenProject Angular's `WorkPackageViewHierarchiesService`:
```typescript
this.state.update(current => ({
  ...current,
  collapsed: {} // Default is empty object: all nodes expanded
}));
```
Because the default initial collapsed map is empty, OpenProject automatically displays all children in expanded state when any page is loaded.

---

## 3. Resolution
1. **Paging Limit Raised:**
   - Added `500` to `Setting.per_page_options` (`"20, 100, 500"`).
   - Created saved Query `QLDAPM — Scrum Roadmap theo Epic` (Query ID 37) configured with `include_subprojects: true`, `timeline_visible: true`, `show_hierarchies: true`, and `sort_criteria: [["id", "asc"]]`.
   - Passing `pp=500` loads all 335 items onto Page 1, ensuring all 11 Root Epics, 54 Tasks, and 270 Subtasks belong to a single contiguous hierarchy.

2. **Auto-Collapse Initializer:**
   - Added client-side navigation hook in `openproject/ai/core/overlay/app/views/qldapm_work_packages/_navigation.html.erb` that automatically ensures `pp=500` and collapses root Epics on initial Gantt load for clean presentation.
