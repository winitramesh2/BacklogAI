# 🗓️ Implementation Plan: BackLogAI

> **Phased Roadmap, Key Milestones & Estimated Timelines**

This document tracks the development progress of the **BackLogAI** project.

**Current Phase:** Project Complete 🚀

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

## SLACK Integration

### Objective
Introduce Slack as an additional client channel to collect backlog inputs, generate Story Preview, and trigger Jira sync, while preserving all existing Android/iOS/macOS behavior.

### Scope
- Add Slack adapter endpoints and service layer.
- Add Slack modal input handling (key/value mapping to v2 request).
- Post Story Preview back to Slack.
- Add "Sync to JIRA" action handling.
- Return Jira key + URL to Slack.
- Add signature verification, idempotency, and session state tracking.

### Out of Scope
- Replacing existing mobile/desktop clients.
- Changing existing local service ports/URLs.
- Migrating core generation/sync logic away from current v2 pipeline.

### Implementation Phases

#### Phase S1: Slack App + Connectivity
- Configure Slack app (scopes, command, interactivity).
- Configure secure tunnel to current local backend endpoint.
- Validate Slack callback reachability and signature verification.

#### Phase S2: Backend Slack Adapter
- Implement `POST /slack/commands`.
- Implement `POST /slack/interactions`.
- Implement modal field parser and mapper to `BacklogItemGenerateV2Request`.

#### Phase S3: Preview + Sync
- Generate Story Preview via existing v2 generation services.
- Post preview blocks/messages to Slack.
- Implement "Sync to JIRA" action to call existing Jira sync path.
- Post Jira key + URL response to Slack.

#### Phase S4: State + Idempotency
- Persist Slack session state (input, preview, sync status).
- Ensure repeated "Sync to JIRA" does not create duplicates.
- Return existing Jira key/URL on repeated sync action.

#### Phase S5: Validation & Regression
- Verify Android/iOS/macOS flows unchanged.
- Verify Slack end-to-end flow from command to Jira sync.
- Add unit/integration tests for signature validation, mapping, and idempotency.

### Acceptance Criteria
- Slack user can submit required inputs via modal.
- Story Preview is posted back to Slack.
- "Sync to JIRA" creates exactly one Jira ticket.
- Jira key + URL is posted back to Slack.
- Existing Android/iOS/macOS flows remain fully functional.

### Operational Notes
- Keep current local Jira and backend runtime unchanged.
- Use tunnel and Slack app configuration to enable remote Slack access.
- Use existing environment values and service endpoints as currently configured.
