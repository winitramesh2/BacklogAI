# 🗓️ Implementation Plan: BackLogAI

> **Phased Roadmap, Key Milestones & Estimated Timelines**

This document tracks the development progress of the **BackLogAI** project.

**Current Phase:** Phase 8 (Windows Client) 🚧 In Progress

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
**Status:** ![Status](https://img.shields.io/badge/Completed-green?style=flat-square)

- [x] **Slack App & Connectivity**
    - [x] Create Slack app with scopes (`chat:write`, `commands`, interactivity).
    - [x] Configure command and interaction callback URLs.
    - [x] Setup secure tunnel (Cloudflare Tunnel) to local backend endpoint.
    - [x] Validate Slack request signature verification and timestamp replay checks.

- [x] **Secure Connectivity (Quick Tunnel for Live Local Demo)**
    - [x] Install `cloudflared` on host machine.
    - [x] Start quick tunnel for BacklogAI callback host.
    - [x] Start quick tunnel for Jira host access.
    - [x] Validate callback behavior (`405` on GET, `401` on unsigned POST).
    - [x] Document URL rotation procedure in `SLACK_QUICK_TUNNEL_CHECKLIST.md`.

- [ ] **Production Hardening (Deferred)**
    - [ ] Migrate from quick tunnels to named tunnel + stable DNS.
    - [ ] Create Cloudflare Access self-hosted app for Jira public hostname.
    - [ ] Add primary allow policy (team email domain allow-list).
    - [ ] Confirm authenticated users can access Jira through protected URL.

- [ ] **Slack Bypass Policy for Jira Endpoints (Deferred)**
    - [ ] Add bypass policy for Jira Slack integration path: `/rest/slack/latest/*`.
    - [ ] Add Slack source IP ranges:
        - [ ] `3.23.0.0/14`
        - [ ] `3.120.0.0/14`
        - [ ] `35.154.0.0/15`
        - [ ] `44.192.0.0/11`
        - [ ] `52.64.0.0/13`
        - [ ] `54.64.0.0/13`
    - [ ] Ensure bypass policy priority is above team access allow policy.

- [x] **Jira + Slack Finalization (Local Runtime)**
    - [x] Keep Jira on local runtime and validate issue creation through Slack flow.
    - [x] Add Jira URL host fallback for local non-Docker backend runtime.
    - [x] Confirm repeated Slack sync clicks do not create duplicate Jira issues.

- [x] **Backend Slack Adapter Layer**
    - [x] Implement `POST /slack/commands` (launch input modal).
    - [x] Implement `POST /slack/interactions` (modal submit + action buttons).
    - [x] Add modal key/value parser mapped to `BacklogItemGenerateV2Request`.
    - [x] Build Slack Block Kit responses for Story Preview and actions.
    - [x] Add non-blocking command ACK path to avoid Slack `dispatch_unknown_error`.

- [x] **Story Preview & Jira Sync Flow**
    - [x] Generate Story Preview using existing v2 generation pipeline.
    - [x] Post preview message back to Slack channel.
    - [x] Implement "Sync to JIRA" action path reusing existing Jira sync service.
    - [x] Post Jira ticket key and URL back to Slack after successful sync.

- [x] **State, Idempotency & Reliability**
    - [x] Persist Slack session state (input payload, preview payload, sync status).
    - [x] Prevent duplicate Jira tickets on repeated sync actions.
    - [x] Return existing Jira key/URL for repeated sync clicks.

- [x] **Validation & Regression**
    - [x] Validate end-to-end Slack flow: input -> preview -> sync -> Jira response.
    - [x] Add tests for signature validation, payload mapping, and idempotency.
    - [x] Re-verify Android/iOS/macOS flows remain unchanged.

- [x] **Scope Note**
    - [x] Existing clients remain active: Android, iOS, macOS Desktop.
    - [x] Windows client rollout is tracked separately in Phase 8.

- [x] **Documentation & Demos**
    - [x] Publish Slack live setup guide and quick tunnel checklist.
    - [x] Update implementation and architecture docs for Slack runtime behavior.
    - [x] Add v3 demo assets for Slack and client app flows under `demo/`.

---

## 🪟 Phase 8: Windows Client (Compose Desktop)
**Goal:** Deliver a modern Windows desktop client with end-to-end story generation and Jira sync using Kotlin Multiplatform + Compose.
**Status:** ![Status](https://img.shields.io/badge/In%20Progress-orange?style=flat-square)

- [x] **Planning & Scope Baseline**
    - [x] Confirm architecture path: reuse `desktopMain` Compose codebase.
    - [x] Define distribution strategy: MSI installer + portable ZIP.
    - [x] Document Phase 8 plan in project roadmap.

- [ ] **Windows Runtime UX Modernization**
    - [ ] Improve desktop window defaults (initial size, minimum size, usability baseline).
    - [ ] Refine desktop-friendly spacing and readability in Input/Result screens.
    - [ ] Add clear desktop interaction feedback for generate/sync states.

- [ ] **Windows Packaging & Distribution**
    - [ ] Build Windows installer artifact (`.msi`) using Compose Desktop distribution tasks.
    - [ ] Build portable Windows ZIP package for no-installation usage.
    - [ ] Publish Windows binaries under `demo/binaries-v3/windows/`.

- [ ] **Windows End-to-End Validation**
    - [ ] Validate flow on Windows runtime: health -> generate v2 -> sync v2.
    - [ ] Verify error handling UX (API unavailable, sync failures, retry behavior).
    - [ ] Capture Windows demo assets under `demo/windows-e2e-v3/`.

- [ ] **Cross-Platform Regression**
    - [ ] Re-verify Android, iOS, and macOS behaviors remain unchanged.
    - [ ] Re-verify Slack client flow remains stable after desktop updates.

- [x] **Documentation Track (Initial)**
    - [x] Update README support matrix to reflect Windows in-progress status.
    - [x] Add Windows setup and release checklist docs.
    - [x] Add architecture notes for shared desktop path (macOS + Windows).

- [ ] **Documentation Track (Completion)**
    - [ ] Mark Windows client as live after successful E2E validation.
    - [ ] Link final Windows demos and binaries in README.
