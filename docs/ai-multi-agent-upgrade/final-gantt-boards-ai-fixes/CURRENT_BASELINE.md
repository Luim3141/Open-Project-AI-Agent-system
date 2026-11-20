# QLDAPM — Current Baseline Verification Report

> **Project:** QLDAPM Local Community (`qldapm-local`, ID 3)  
> **Environment:** Staging (`http://localhost:18091` / Cloudflare Quick Tunnel)  
> **Date:** 2026-10-20  
> **Commit HEAD:** `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`  
> **Containers Verified:**
> - Core: `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` (Healthy)
> - Gateway: `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` (Healthy)
> - Database: `sha256:2d2b8998d3101c5147be15e19f9bb49ec6060c5ea2bf79185a5bf965c4ec2ce0` (Healthy)

---

## 1. Work Package Inventory
- **Total Work Packages in DB:** 372
- **Work Packages in Project 3 (`qldapm-local`):** 335
  - **Epics:** 11 (IDs 38 to 48)
  - **Tasks:** 54 (IDs 49..102, 447)
  - **Subtasks:** 270 (IDs 103..372, 441..446)
- **Hierarchy Structure:** Strictly 3 levels: Root Epic -> Task -> Subtask.

---

## 2. User & 2FA State
- **User 5 (`stage-owner`):** Administrator, Active, TOTP Device 31 **ACTIVE & ENROLLED** (Device preserved, not reset). Member of Project 3 with role `QLDAPM PM`.
- **User 7 (`pm`):** Active, TOTP Device 24 **ACTIVE** (Preserved). Member of Project 3 with role `QLDAPM PM`.
- **User 8 (`be`):** Active, TOTP Device 23 **ACTIVE** (Preserved). Member of Project 3 with role `QLDAPM BE`.
- **User 6 (`ba-pm`), User 9 (`fe`), User 10 (`qa`):** Active, 0 devices (`RESET_READY_FOR_USER_ENROLLMENT`).

---

## 3. Project Configuration & Modules
- **Project Name:** QLDAPM — Local Community
- **Identifier:** `qldapm-local`
- **Enabled Modules:** `work_package_tracking`, `gantt`, `boards`, `wiki`, `activity`, `members`.
- **Global Settings:**
  - `gantt` module globally enabled.
  - `Setting.per_page_options`: `"20, 100, 500"`.
