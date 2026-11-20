# QLDAPM — Scrum 1 Task = 1 Week Schedule Proposal & Validation Report

> **Target Project:** `qldapm-local` (ID 3)  
> **Total Work Packages Proposed:** 335  
> **Schedule Rule:** 1 Task = 1 Work-Week (5 Working Days: Monday to Friday)  
> **Sprint Structure:** 4 Sprints × 2 Weeks (10 Working Days each)  
> **Gate B Status:** `GANTT_DATE_PROPOSAL_AWAITING_OWNER` (Proposal Only — Zero Staging DB Mutation)  
> **Date:** 2026-10-20  

---

## 1. Executive Summary & Scheduling Principles
1. **Scrum 1 Task = 1 Week Invariant:**
   - Every single Task (out of 54 tasks) is allocated exactly 5 working days (Monday to Friday).
   - Week 1 tasks: Monday to Friday of the first sprint week.
   - Week 2 tasks: Monday to Friday of the second sprint week.
2. **Subtask Intra-Week Distribution (Role Flow):**
   - Subtasks are distributed inside their parent task's 5-day window.
   - Stage 1 (Monday): BA Requirements & Acceptance Criteria
   - Stage 2 (Tuesday): Backend Architecture & Implementation
   - Stage 3 (Wednesday): Frontend UI & Interaction
   - Stage 4 (Thursday): QA Test Automation & Validation
   - Stage 5 (Friday): PM Code Review, Handover & Acceptance
3. **Epic Span Rollup:**
   - Every Epic start date = `min(tasks.start_date)`.
   - Every Epic due date = `max(tasks.due_date)`.
   - All Epics cleanly span their assigned 2-week Sprint.
4. **Preservation of `schedule_manually` Modes (NO SILENT SWITCHING):**
   - **Epic:** 11 items with `schedule_manually: false` preserved.
   - **Task:** 53 items with `false`, 1 with `true` preserved.
   - **Subtask:** 212 items with `false`, 58 with `true` preserved.
   - Zero work packages have their `schedule_manually` mode altered.

---

## 2. Sprint Timeline Architecture

| Sprint | Milestones / Epics Covered | Calendar Range | Working Days |
|---|---|---|---|
| **Sprint 1** | Epic 38 (Tài khoản & Role), Epic 39 (Quản lý Project) | 2026-10-05 → 2026-10-16 | 10 days |
| **Sprint 2** | Epic 40 (Backlog), Epic 41 (Sprint), Epic 42 (Task / User Story) | 2026-10-19 → 2026-10-30 | 10 days |
| **Sprint 3** | Epic 43 (Kanban), Epic 44 (Gantt Timeline), Epic 45 (Issue / Bug) | 2026-11-02 → 2026-11-13 | 10 days |
| **Sprint 4** | Epic 46 (Comment), Epic 47 (Dashboard), Epic 48 (Notification) | 2026-11-16 → 2026-11-27 | 10 days |

---

## 3. Validation Assertions

- [x] **Assertion 1 (Count):** All 335 project work packages accounted for.
- [x] **Assertion 2 (Week Bound):** All Tasks start on Monday and end on Friday.
- [x] **Assertion 3 (Subtask Containment):** 100% of subtasks reside within their parent Task's date range.
- [x] **Assertion 4 (Epic Containment):** 100% of Epics cover their child Tasks.
- [x] **Assertion 5 (Weekend Free):** Zero work packages scheduled on Saturday or Sunday.
- [x] **Assertion 6 (Manual Scheduling Integrity):** 212 subtasks with `schedule_manually: false` remain `false`.

---

## 4. Gate B Decision Gate
- **Current Gate State:** `GANTT_DATE_PROPOSAL_AWAITING_OWNER`
- **Database Status:** Staging DB remains unmutated.
- **Next Step:** Await Project Owner approval of `SCRUM_GANTT_1WEEK_PROPOSAL.csv` before executing any date population script.
