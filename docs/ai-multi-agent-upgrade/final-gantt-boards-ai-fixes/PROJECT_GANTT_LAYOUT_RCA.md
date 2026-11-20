# QLDAPM — Root Cause Analysis: Project Gantt Squished Vertical Layout

> **Target:** `/projects/qldapm-local/gantt`  
> **Topic:** Squished Rows & Large White Space Issue  
> **Date:** 2026-10-20  

---

## 1. Symptom
In `/projects/qldapm-local/gantt`, users reported:
- The Gantt table and timeline appeared "squished" with only ~2 rows showing at the very top.
- A huge blank white space occupied the lower ~80% of the screen.
- The pagination footer showed `(1 - 20/335)`.

---

## 2. DOM & CSS Diagnostics (Empirical Measurement)
From `gantt_layout_metrics.json`:
- **Table Container (`.work-package-table--container`):**
  - `offsetHeight`: 867px
  - `clientHeight`: 867px
  - `computedHeight`: 867px
  - `overflow`: `scroll hidden`
  - `flex`: `1 1 0%`
- **Main Content Container (`#content`):**
  - `offsetHeight`: 1025px
  - `clientHeight`: 1025px
- **Visible Row Heights:**
  - Row 38 height: 40px
  - Row 39 height: 40px
  - Total rendered row height on Page 1 (when collapsed): `2 * 40px = 80px`.
  - Available viewport height: `867px`.
  - Unfilled empty white space: `867px - 80px = 787px`.

---

## 3. Root Cause
The squished appearance was NOT caused by a CSS bug or broken flexbox rule.
The flexbox container was correctly allocated 867px height.
The root cause was **Paging Fragmentation**:
1. OpenProject was querying with `pageSize=20`.
2. Out of 335 total items, Page 1 only received 20 items.
3. These 20 items belonged to only 2 root Epics (38 and 39) plus an unparented task.
4. When those 2 Epics were collapsed, the children were hidden from DOM, leaving only 2 rows (80px total) in a container sized for 867px.
5. The remaining 9 Epics were trapped on subsequent pagination pages (Pages 2 through 17).

---

## 4. Fix & Verification
1. **Paging Setting:** Updated `Setting.per_page_options` in Rails to `"20, 100, 500"`.
2. **Page Size Query Parameter:** Added `pp=500` to the Gantt query / saved view, fetching all 335 items onto Page 1.
3. **Result:**
   - All 11 Epics appear on Page 1 (11 * 40px = 440px).
   - When expanded, the table and timeline seamlessly populate the full 867px+ container with smooth native vertical scrolling.
   - Pager shows `(1 - 335/335)`.
   - No CSS hacks or container height overrides required.
