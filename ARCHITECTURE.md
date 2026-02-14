# Architecture: BacklogAI

> Detailed system design, core modules, and runtime flows.

## 1) System Overview

BacklogAI is a Kotlin Multiplatform client connected to a FastAPI backend that orchestrates research, story generation, quality validation, and JIRA sync.

```mermaid
graph TD
  subgraph Clients
    A1[Android App]
    A2[iOS App]
    A3[Desktop App]
  end

  subgraph Backend
    B1[FastAPI API]
    B2[Story Generation Engine v2]
    B3[Market Research Service]
    B4[Quality Validation Engine]
    B5[Prioritization Engine]
    B6[JIRA Service]
  end

  subgraph External Services
    C1[OpenAI API]
    C2[SerpAPI]
    C3[JIRA Cloud/Server]
  end

  A1 --> B1
  A2 --> B1
  A3 --> B1

  B1 --> B2
  B2 --> B3
  B3 --> C2
  B2 --> C1
  B2 --> B4
  B4 --> B2
  B2 --> B5
  B1 --> B6
  B6 --> C3
```

Key notes:
- The v2 flow starts with context + objective, then runs research, generation, and quality checks.
- SerpAPI is rate-limited and cached to respect the free tier and reduce costs.
- If OpenAI is unavailable, a deterministic fallback uses SerpAPI summaries to populate research fields.

---

## 2) Core Modules

| Module | Purpose | Key Responsibilities |
| --- | --- | --- |
| Input V2 | Context intake | Accepts context, objective, and optional signals (persona, segment, constraints, metrics, competitors). |
| Market Research | External signal discovery | Queries SerpAPI, summarizes trends/competitors, caches results, enforces rate limits. |
| Story Generation v2 | AI drafting | Produces INVEST-ready story, Gherkin AC, tasks, NFRs, metrics, risks, and rollout plan. |
| Quality Validation | INVEST checks | Scores and warns; triggers revision pass when quality is low. |
| Prioritization | Scoring | Computes priority score and MoSCoW classification. |
| JIRA Integration | Sync | Maps summary/description to JIRA fields and creates issues. |
| KMM UI | Cross-platform app | Guides input, previews research and story, syncs to JIRA. |

---

## 3) Runtime Flow (v2)

```mermaid
flowchart TD
  A[User enters context + objective] --> B[API: /backlog/generate/v2]
  B --> C[Market research via SerpAPI]
  C --> D[Story generation v2]
  D --> E[INVEST quality validation]
  E -->|Warnings| F[Revise pass]
  F --> D
  E -->|OK| G[Prioritization + response]
  G --> H[User reviews on mobile]
  H --> I[Sync to JIRA: /backlog/sync/v2]
```

---

## 4) Sequence Diagram (Generate + Sync)

```mermaid
sequenceDiagram
  participant U as User (Mobile App)
  participant API as FastAPI
  participant RS as Research Service
  participant SAPI as SerpAPI
  participant AI as OpenAI
  participant Q as Quality Engine
  participant J as JIRA Service
  participant JIRA as JIRA API

  U->>API: POST /backlog/generate/v2
  API->>RS: fetch_research_inputs()
  RS->>SAPI: search queries
  SAPI-->>RS: snippets + sources
  API->>AI: generate story JSON (with research)
  AI-->>API: draft story
  API->>Q: validate_invest_v2
  Q-->>API: warnings + score
  alt warnings
    API->>AI: revise_story_v2
    AI-->>API: revised story
    API->>Q: validate_invest_v2
    Q-->>API: warnings + score
  end
  API-->>U: response (summary, story, research, quality)

  U->>API: POST /backlog/sync/v2
  API->>J: create_issue_v2
  J->>JIRA: Create Story
  JIRA-->>J: issue key
  J-->>API: issue key + URL
  API-->>U: sync response
```

---

## 5) Technology Stack

### Backend
- Python 3.11+ with FastAPI
- OpenAI API for story generation
- SerpAPI for market research
- Jira REST API for issue creation

### Frontend (Kotlin Multiplatform)
- Compose Multiplatform UI
- Ktor Client for networking
- Android + iOS host apps

### Tooling
- Gradle for builds
- Docker Compose for local services
