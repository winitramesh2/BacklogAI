# 🗓️ Implementation Plan: BackLogAI

> **Phased Roadmap, Key Milestones & Estimated Timelines**

This document tracks the development progress of the **BackLogAI** project.

**Current Phase:** [Phase 3: JIRA Integration & API](#phase-3-jira-integration--api) 🔌

---

## 🏗️ Phase 1: Project Initialization & Architecture Setup
**Goal:** Establish the monorepo structure, development environment, and core backend infrastructure.
**Status:** ![Status](https://img.shields.io/badge/Completed-green?style=flat-square)

- [x] **Repository Setup (Monorepo)**
    - [x] Initialize Git repository.
    - [x] Structure: `/backend`, `/shared`, `/composeApp`, `/infra`.
- [x] **Backend Infrastructure (Dockerized)**
    - [x] **Database:** Setup PostgreSQL container.
    - [x] **Backend:** Setup Python 3.11+ container with FastAPI and Uvicorn.
    - [x] **ORM:** Configure Tortoise-ORM/SQLAlchemy (Async).
    - [x] **Migrations:** Initialize Aerich or Alembic.
- [ ] **Authentication (SSO/OAuth)**
    - [ ] Implement OAuth2 flow (Google/GitHub) with `authlib`.
    - [ ] Create `User` model.
    - [ ] Secure API endpoints (JWT).

---

## 🧠 Phase 2: Core Backend Logic (The "Brain")
**Goal:** Implement the pillars, story generation, and prioritization engines.
**Status:** ![Status](https://img.shields.io/badge/Completed-green?style=flat-square)

- [x] **Input Module & Data Models**
    - [x] Define Pydantic models for the **5 Key Pillars**.
    - [x] Create API endpoints to validate project context.
- [x] **Story Generation Engine (AI-Powered)**
    - [x] **Integration:** Connect to OpenAI API / Claude 3.5.
    - [x] **Prompt Engineering:** Enforce "Why now? Why this? Why us?".
    - [x] **Logic:** Implement Epics → Stories → Tasks decomposition.
- [x] **Prioritization Engine**
    - [x] Implement **RICE** algorithm.
    - [x] Implement **WSJF** algorithm.
    - [x] Implement **MoSCoW** logic.
- [x] **Quality Validation Engine**
    - [x] Implement **INVEST** criteria checks.
    - [x] Return warnings for vague stories.

---

## 🔌 Phase 3: JIRA Integration & API
**Goal:** Connect the generated backlog to the real world.
**Status:** ![Status](https://img.shields.io/badge/Pending-lightgrey?style=flat-square)

- [ ] **JIRA Connector**
    - [ ] Implement Atlassian Python API wrapper.
    - [ ] Map internal Story models to JIRA Issue types.
    - [ ] Push Logic: Create/Update issues, link Epics to Stories.
    - [ ] Pull Logic: Sync status updates.
- [ ] **API Polish**
    - [ ] Finalize REST API documentation (Swagger/OpenAPI).
    - [ ] Ensure all endpoints are async.

---

## 🔄 Phase 4: Kotlin Multiplatform (KMP) Shared Logic
**Goal:** Write business logic once, run everywhere.
**Status:** ![Status](https://img.shields.io/badge/Pending-lightgrey?style=flat-square)

- [ ] **Shared Module Setup**
    - [ ] Configure KMP for Android, iOS, JVM (Desktop), and Wasm (Web).
- [ ] **Networking & Data**
    - [ ] **Ktor Client:** Implement API client.
    - [ ] **Serialization:** `kotlinx.serialization` (JSON).
    - [ ] **Repositories:** Auth, Backlog, Settings.
- [ ] **View Models**
    - [ ] Implement shared ViewModels (MVVM).

---

## 📱 Phase 5: Compose Multiplatform UI
**Goal:** Build a beautiful, responsive interface for all targets.
**Status:** ![Status](https://img.shields.io/badge/Pending-lightgrey?style=flat-square)

- [ ] **Design System**
    - [ ] Implement Material 3 theme.
    - [ ] Components: `PillarInputCard`, `StoryCard`, `PriorityBadge`, `KanbanBoard`.
- [ ] **Screens Implementation**
    - [ ] **Login Screen:** SSO handling.
    - [ ] **Dashboard:** High-level metrics.
    - [ ] **Wizard/Input:** Multi-step form for 5 Pillars.
    - [ ] **Backlog View:** List/Kanban, Edit Mode.
    - [ ] **JIRA Sync:** Status dashboard.
- [ ] **Platform Specifics**
    - [ ] **Desktop:** Window management.
    - [ ] **Mobile:** Touch interactions.
    - [ ] **Web:** Responsive layout.

---

## ✅ Phase 6: Testing & Quality Assurance
**Goal:** Ensure reliability and correctness.
**Status:** ![Status](https://img.shields.io/badge/Pending-lightgrey?style=flat-square)

- [ ] **Backend Testing**
    - [ ] Unit tests (`pytest`).
    - [ ] Integration tests.
- [ ] **Frontend Testing**
    - [ ] UI tests (Compose).
    - [ ] Unit tests (Shared KMP).
- [ ] **Performance**
    - [ ] Verify "under 60 seconds" generation requirement.
