# 🏗️ Architecture: BackLogAI

> **Detailed System Design, Core Modules & Technology Stack**

## 1. System Overview

BackLogAI is designed as a modular, containerized application with three core layers:

1.  **Frontend (UI/CLI)**: The user interaction layer.
2.  **Backend (API/Logic)**: The processing and coordination layer.
3.  **Data & Integration**: Persistence and external service connections.

```mermaid
graph TD
    subgraph Frontend
    A[Mobile/Web/Desktop UI]
    end

    subgraph Backend
    B[FastAPI Gateway] --> C[Input Validation]
    C --> D[Story Generation Engine]
    D --> E[Prioritization Engine]
    E --> F[Quality Validation Engine]
    F --> G[(Database)]
    end

    subgraph External Services
    G --> H[JIRA API]
    D -.-> I[OpenAI / Claude API]
    end

    style Frontend fill:#f9f,stroke:#333
    style Backend fill:#bbf,stroke:#333
    style External Services fill:#e1f5fe,stroke:#333
```

---

## 2. Core Modules

| Module | Purpose | Key Responsibilities |
| :--- | :--- | :--- |
| **A. Input Module** | 📥 Data Intake | Accepts structured data for the **Five Key Pillars** (User Value, Commercial Impact, etc.). Validates schemas and sanitizes inputs. |
| **B. Story Generation Engine** | 🤖 AI Processing | Uses LLMs to draft standard user stories (`As a... I want... So that...`) with `Given/When/Then` acceptance criteria. Decomposes Epics → Stories → Tasks. |
| **C. Prioritization Engine** | ⚖️ Scoring Logic | Calculates definitive priority scores using **RICE**, **WSJF**, and **MoSCoW** algorithms based on pillar weights. |
| **D. Quality Validation Engine** | ✅ Quality Control | Checks stories against **INVEST** criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable). Returns warnings for vague stories. |
| **E. JIRA Integration Module** | 🔄 Sync & Action | Syncs the generated backlog to JIRA. Creates/updates issues, links parent/child items, and pulls status updates. |

---

## 3. Technology Stack

### Backend Stack

| Component | Technology | Why? |
| :--- | :--- | :--- |
| **Language** | ![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python&logoColor=white) | Fast, modern syntax, excellent async support. |
| **Framework** | ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi&logoColor=white) | High-performance async API, native OpenAPI/Swagger. |
| **Database** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql&logoColor=white) | Reliable data integrity, JSONB support for dynamic inputs. |
| **ORM** | **Tortoise-ORM** / **SQLAlchemy** | Async database operations for non-blocking I/O. |
| **Auth** | **OAuth2** (Google/GitHub) | Standard secure authentication via `authlib` or `fastapi-sso`. |
| **AI** | **OpenAI** / **Anthropic** | Best-in-class LLMs for creative text generation. |

### Frontend Stack (Kotlin Multiplatform)

| Component | Technology | Why? |
| :--- | :--- | :--- |
| **Framework** | ![Kotlin](https://img.shields.io/badge/Kotlin-Multiplatform-7F52FF?style=flat-square&logo=kotlin&logoColor=white) | Write business logic once, run everywhere. |
| **UI Toolkit** | **Compose Multiplatform** | Declarative UI for Android, iOS, Desktop, and Web. |
| **Targets** | 📱 Android, iOS <br> 💻 macOS, Windows, Linux <br> 🌐 Web (Wasm) | Native performance on all major platforms. |
| **Networking** | **Ktor Client** | Async, multiplatform HTTP client. |
| **State** | **Voyager** / **MVI** | Robust state management and navigation. |

### DevOps & Tooling

*   **Version Control:** Git (Monorepo structure)
*   **CI/CD:** GitHub Actions (Build, Test, Lint, Deploy)
*   **Code Quality:** `ruff` (Python), `ktlint` (Kotlin)
*   **Containerization:** Docker & Docker Compose

---

## 4. Data Schema (Conceptual ER Diagram)

```mermaid
erDiagram
    PROJECT ||--o{ BACKLOG_ITEM : contains
    PROJECT {
        uuid id PK
        string name
        json pillars_config "Weights for the 5 pillars"
        timestamp created_at
    }
    BACKLOG_ITEM ||--o{ JIRA_SYNC : tracks
    BACKLOG_ITEM {
        uuid id PK
        uuid project_id FK
        enum type "Epic, Story, Task"
        string title
        text description
        float priority_score
        json pillar_scores
        enum status "Draft, Approved, Synced"
    }
    USER ||--o{ PROJECT : owns
    USER {
        uuid id PK
        string email
        string oauth_provider
        string oauth_id
    }
```
