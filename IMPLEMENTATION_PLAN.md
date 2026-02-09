# Implementation Plan: BackLogAI

## Phase 1: Project Initialization & Architecture Setup
**Goal:** Establish the monorepo structure, development environment, and core backend infrastructure.

1.  **Repository Setup (Monorepo)**
    *   Initialize Git repository.
    *   Structure:
        *   `/backend` (Python FastAPI)
        *   `/shared` (Kotlin Multiplatform logic)
        *   `/composeApp` (Compose Multiplatform UI)
        *   `/infra` (Docker, CI/CD)
2.  **Backend Infrastructure (Dockerized)**
    *   **Database:** Setup PostgreSQL container.
    *   **Backend:** Setup Python 3.11+ container with FastAPI and Uvicorn.
    *   **ORM:** Configure Tortoise-ORM or SQLAlchemy (Async) for database interactions.
    *   **Migrations:** Initialize Aerich or Alembic for schema management.
3.  **Authentication (SSO/OAuth)**
    *   Implement OAuth2 flow (Google/GitHub) using `authlib` or `fastapi-sso`.
    *   Create `User` model to link SSO identities.
    *   Secure API endpoints with JWT tokens.

## Phase 2: Core Backend Logic (The "Brain")
**Goal:** Implement the pillars, story generation, and prioritization engines.

1.  **Input Module & Data Models**
    *   Define Pydantic models for the **5 Key Pillars** (User Value, Commercial Impact, Strategic Horizon, Competitive Positioning, Technical Reality).
    *   Create API endpoints to accept and validate project context, personas, and feature requests.
2.  **Story Generation Engine (AI-Powered)**
    *   **Integration:** Connect to OpenAI API (GPT-4o) or Anthropic (Claude 3.5).
    *   **Prompt Engineering:** Design system prompts that enforce the "Golden Rule" (Why now? Why this? Why us?).
    *   **Logic:** Implement logic to decompose features into Epics → Stories → Tasks with Given/When/Then acceptance criteria.
3.  **Prioritization Engine**
    *   Implement algorithms for:
        *   **RICE:** (Reach × Impact × Confidence) / Effort.
        *   **WSJF:** Cost of Delay / Job Duration.
        *   **MoSCoW:** Must/Should/Could/Won't (categorical sorting).
    *   Create an endpoint to recalculate scores based on adjusted input parameters.
4.  **Quality Validation Engine**
    *   Implement heuristic checks for INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable).
    *   Return warnings if stories are too large or vague.

## Phase 3: JIRA Integration & API
**Goal:** Connect the generated backlog to the real world.

1.  **JIRA Connector**
    *   Implement Atlassian Python API wrapper.
    *   Features:
        *   Auth: JIRA API Token / OAuth.
        *   Map internal Story models to JIRA Issue types.
        *   Push Logic: Create/Update issues, link Epics to Stories.
        *   Pull Logic: Sync status updates back to BackLogAI.
2.  **API Polish**
    *   Finalize REST API documentation (Swagger/OpenAPI).
    *   Ensure all endpoints are async and performance-optimized.

## Phase 4: Kotlin Multiplatform (KMP) Shared Logic
**Goal:** Write business logic once, run everywhere.

1.  **Shared Module Setup**
    *   Configure KMP for Android, iOS, JVM (Desktop), and Wasm (Web).
2.  **Networking & Data**
    *   **Ktor Client:** Implement API client to communicate with the Python backend.
    *   **Serialization:** Use `kotlinx.serialization` for JSON parsing.
    *   **Repository Pattern:** specific repositories for Auth, Backlog, and Settings.
3.  **View Models**
    *   Implement shared ViewModels (using libraries like `voyager` or `lifecycle-viewmodel-compose`) to manage UI state across all platforms.

## Phase 5: Compose Multiplatform UI
**Goal:** Build a beautiful, responsive interface for all targets.

1.  **Design System**
    *   Implement a Material 3 theme.
    *   Create reusable components: `PillarInputCard`, `StoryCard`, `PriorityBadge`, `KanbanBoard`.
2.  **Screens Implementation**
    *   **Login Screen:** SSO handling.
    *   **Dashboard:** High-level metrics and "Create New Backlog" entry point.
    *   **Wizard/Input:** Multi-step form for entering the 5 Pillars data.
    *   **Backlog View:**
        *   List/Kanban view of generated stories.
        *   Edit mode for tweaking AI output.
    *   **JIRA Sync:** Status dashboard showing push progress and links.
3.  **Platform Specifics**
    *   **Desktop:** Window management, keyboard shortcuts.
    *   **Mobile:** Touch interactions, bottom navigation.
    *   **Web:** Responsive layout adjustments.

## Phase 6: Testing & Quality Assurance
**Goal:** Ensure reliability and correctness.

1.  **Backend Testing**
    *   Unit tests with `pytest` for algorithms.
    *   Integration tests for API endpoints (mocking external AI/JIRA services).
2.  **Frontend Testing**
    *   UI tests for Compose components.
    *   Unit tests for Shared KMP logic.
3.  **Performance**
    *   Verify "under 60 seconds" generation requirement.
