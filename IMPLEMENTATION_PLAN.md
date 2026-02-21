# 🗓️ Implementation Plan: BackLogAI

> **Phased Roadmap, Key Milestones & Estimated Timelines**

This document tracks the development progress of the **BackLogAI** project.

**Current Phase:** Phase 7 (Slack Integration) 🚧

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
**Status:** ![Status](https://img.shields.io/badge/Completed-green?style=flat-square)

- [x] **JIRA Connector**
    - [x] Implement Atlassian Python API wrapper.
    - [x] Map internal Story models to JIRA Issue types.
    - [x] Push Logic: Create/Update issues, link Epics to Stories.
    - [x] Pull Logic: Sync status updates.
- [x] **API Polish**
    - [x] Finalize REST API documentation (Swagger/OpenAPI).
    - [x] Ensure all endpoints are async.

---

## 🔄 Phase 4: Kotlin Multiplatform (KMP) Shared Logic
**Goal:** Write business logic once, run everywhere.
**Status:** ![Status](https://img.shields.io/badge/Completed-green?style=flat-square)

- [x] **Shared Module Setup**
    - [x] Configure KMP for Android, iOS, JVM (Desktop), and Wasm (Web).
- [x] **Networking & Data**
    - [x] **Ktor Client:** Implement API client.
    - [x] **Serialization:** `kotlinx.serialization` (JSON).
    - [x] **Repositories:** Auth, Backlog, Settings.
- [x] **View Models**
    - [x] Implement shared ViewModels (MVVM).

---

## 📱 Phase 5: Compose Multiplatform UI
**Goal:** Build a beautiful, responsive interface for all targets.
**Status:** ![Status](https://img.shields.io/badge/Completed-green?style=flat-square)

- [x] **Design System**
    - [x] Implement Material 3 theme.
    - [x] Components: `PillarInputCard`, `StoryCard`, `PriorityBadge`, `KanbanBoard`.
- [x] **Screens Implementation**
    - [ ] **Login Screen:** SSO handling.
    - [ ] **Dashboard:** High-level metrics.
    - [x] **Wizard/Input:** Multi-step form for 5 Pillars.
    - [x] **Backlog View:** List/Kanban, Edit Mode.
    - [x] **JIRA Sync:** Status dashboard.
- [ ] **Platform Specifics**
    - [ ] **Desktop:** Window management.
    - [ ] **Mobile:** Touch interactions.
    - [ ] **Web:** Responsive layout.

---

## ✅ Phase 6: Testing & Quality Assurance
**Goal:** Ensure reliability and correctness.
**Status:** ![Status](https://img.shields.io/badge/Completed-green?style=flat-square)

- [x] **Backend Testing**
    - [x] Unit tests (`pytest`).
    - [x] Integration tests.
- [ ] **Frontend Testing**
    - [ ] UI tests (Compose).
    - [ ] Unit tests (Shared KMP).
- [x] **Performance**
    - [x] Verify "under 60 seconds" generation requirement.

---

## 💬 Phase 7: Slack Client Integration
**Goal:** Add Slack as a new client channel for story generation and Jira sync without impacting Android/iOS/macOS behavior.
**Status:** ![Status](https://img.shields.io/badge/Planned-blue?style=flat-square)

- [ ] **Slack App & Connectivity**
    - [ ] Create Slack app with scopes (`chat:write`, `commands`, interactivity).
    - [ ] Configure command and interaction callback URLs.
    - [ ] Setup secure tunnel (Cloudflare Tunnel) to local backend endpoint.
    - [ ] Validate Slack request signature verification and timestamp replay checks.

- [ ] **Backend Slack Adapter Layer**
    - [ ] Implement `POST /slack/commands` (launch input modal).
    - [ ] Implement `POST /slack/interactions` (modal submit + action buttons).
    - [ ] Add modal key/value parser mapped to `BacklogItemGenerateV2Request`.
    - [ ] Build Slack Block Kit responses for Story Preview and actions.

- [ ] **Story Preview & Jira Sync Flow**
    - [ ] Generate Story Preview using existing v2 generation pipeline.
    - [ ] Post preview message back to Slack channel.
    - [ ] Implement "Sync to JIRA" action path reusing existing Jira sync service.
    - [ ] Post Jira ticket key and URL back to Slack after successful sync.

- [ ] **State, Idempotency & Reliability**
    - [ ] Persist Slack session state (input payload, preview payload, sync status).
    - [ ] Prevent duplicate Jira tickets on repeated sync actions.
    - [ ] Return existing Jira key/URL for repeated sync clicks.

- [ ] **Validation & Regression**
    - [ ] Validate end-to-end Slack flow: input -> preview -> sync -> Jira response.
    - [ ] Add tests for signature validation, payload mapping, and idempotency.
    - [ ] Re-verify Android/iOS/macOS flows remain unchanged.

- [ ] **Scope Note**
    - [ ] Existing clients remain active: Android, iOS, macOS Desktop.
    - [ ] Windows client support remains upcoming and unaffected by Slack rollout.
