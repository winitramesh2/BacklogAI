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

## 5) SLACK Integration

### Architectural Position
Slack is introduced as an additional client channel, equivalent to Android/iOS/macOS clients, routed through backend adapter endpoints.

### Design Goals
- Preserve existing mobile/desktop flows without modification.
- Reuse existing v2 story generation and Jira sync services.
- Keep local Jira and local backend runtime unchanged.
- Enable secure remote Slack access through outbound tunnel only.

### Components Added
- Slack Adapter Endpoints:
  - `POST /slack/commands`
  - `POST /slack/interactions`
  - `POST /slack/events` (optional for later expansion)
- Slack Service Layer:
  - Signature validation
  - Modal parsing/mapping to v2 request model
  - Preview message and action block rendering
  - Slack Web API message posting
  - Block Kit composition for Story Preview and action buttons
- Slack Session State Store:
  - Tracks generated preview state and sync status
  - Prevents duplicate Jira ticket creation on repeated sync actions
- Secure Connectivity:
  - Cloudflare Tunnel for HTTPS callback routing to local services

### Sequence Flow

```mermaid
sequenceDiagram
  participant User as Slack User
  participant Slack as Slack Cloud
  participant API as BacklogAI Backend
  participant Gen as Story Generation v2
  participant Jira as Local Jira

  User->>Slack: /backlogai
  Slack->>API: POST /slack/commands
  API-->>Slack: Open input modal

  User->>Slack: Submit key/value inputs
  Slack->>API: POST /slack/interactions (modal_submit)
  API->>Gen: generate_story_v2(...)
  Gen-->>API: Story Preview payload
  API-->>Slack: Post Story Preview + "Sync to JIRA" action

  User->>Slack: Click "Sync to JIRA"
  Slack->>API: POST /slack/interactions (button_click)
  API->>Jira: create_issue_v2(...)
  Jira-->>API: Jira key + URL
  API-->>Slack: Post Jira key + ticket URL
```

### Security Model
- Slack signature verification on all Slack callbacks.
- Request timestamp validation for replay prevention.
- Tunnel exposure limited to required callback hostnames only.
- Optional Zero Trust access policies for Jira public hostname, with Slack-specific bypass where needed.

### Non-Impact Statement
No changes are required to existing client APIs for Android, iOS, and macOS desktop.
Slack integration is implemented as an additive client adapter layer.

---

## 6) Technology Stack

### Backend
- Python 3.11+ with FastAPI
- OpenAI API for story generation
- SerpAPI for market research
- Jira REST API for issue creation
- Slack Web API + interaction webhooks for Slack client flow

### Frontend (Kotlin Multiplatform)
- Compose Multiplatform UI
- Ktor Client for networking
- Android + iOS + Desktop host apps

### Tooling
- Gradle for builds
- Docker Compose for local services
- Cloudflare Tunnel (`cloudflared`) for secure local-to-cloud webhook routing
- Slack Block Kit for rich interactive Slack UX
