# Architecture: BacklogAI

> Detailed system design, core modules, and runtime flows.

## 1) System Overview

BacklogAI is a Kotlin Multiplatform client connected to a FastAPI backend that orchestrates research, story generation, quality validation, and JIRA sync.

```mermaid
graph TD
  subgraph Clients
    A1[Android App]
    A2[iOS App]
    A3[macOS Desktop App]
    A4[Windows Desktop App]
    A5[Slack Client]
  end

  subgraph Backend
    B1[FastAPI API]
    B2[Story Generation Engine v2]
    B3[Market Research Service]
    B4[Quality Validation Engine]
    B5[Prioritization Engine]
    B6[JIRA Service]
    B7[Slack Adapter Endpoints]
  end

  subgraph Connectivity and Security
    S1[Cloudflare Tunnel]
    S2[Cloudflare Zero Trust]
  end

  subgraph External Services
    C1[OpenAI API]
    C2[SerpAPI]
    C3[JIRA Cloud/Server]
    C4[Slack Cloud]
  end

  A1 --> B1
  A2 --> B1
  A3 --> B1
  A4 --> B1
  A5 --> C4
  C4 --> S1
  S1 --> B7
  S2 --> C3

  B1 --> B2
  B2 --> B3
  B3 --> C2
  B2 --> C1
  B2 --> B4
  B4 --> B2
  B2 --> B5
  B1 --> B6
  B7 --> B2
  B7 --> B6
  B7 --> C4
  B6 --> C3
```

Key notes:
- The v2 flow starts with context + objective, then runs research, generation, and quality checks.
- SerpAPI is rate-limited and cached to respect the free tier and reduce costs.
- If OpenAI is unavailable, a deterministic fallback uses SerpAPI summaries to populate research fields.
- Slack command handling uses an ack-first pattern to respond quickly and open modal work asynchronously.
- Jira URL normalization handles local runtime differences when `host.docker.internal` is not resolvable.
- Compose Desktop `desktopMain` powers both macOS and Windows clients from a shared code path.

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
  G --> H[User reviews on client app]
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
Slack is introduced as an additional client channel, equivalent to Android/iOS/macOS/Windows clients, routed through backend adapter endpoints.

### Design Goals
- Preserve existing Android/iOS/macOS flows while introducing Windows desktop support.
- Reuse existing v2 story generation and Jira sync services.
- Keep local Jira and local backend runtime unchanged.
- Enable secure remote Slack access through outbound tunnel only.

### Components Added
- Slack Adapter Endpoints:
  - `POST /slack/commands`
  - `POST /slack/interactions`
  - `POST /slack/events` (optional for later expansion)
  - Command endpoint returns immediate ACK to satisfy Slack timeout constraints.
- Slack Service Layer:
  - Signature validation
  - Modal parsing/mapping to v2 request model
  - Preview message and action block rendering
  - Slack Web API message posting
  - Block Kit composition for Story Preview and action buttons
- Slack Session State Store:
  - Tracks generated preview state and sync status
  - Prevents duplicate Jira ticket creation on repeated sync actions
- Jira Connectivity Reliability:
  - Normalizes Docker host aliases to `localhost` when backend runs directly on host runtime
  - Preserves Docker alias URL when hostname resolves in containerized runtime
- Secure Connectivity:
  - Cloudflare Tunnel for HTTPS callback routing to local services (`localhost` ingress)
  - Service mode support for roaming environments (Wi-Fi/hotspot switches)

### Secure Connectivity Flow

```mermaid
flowchart LR
  S[Slack Cloud] --> T[Cloudflare Tunnel Hostname]
  T --> A[/slack/commands or /slack/interactions/]
  A --> B[BacklogAI Local Backend]
  B --> J[Jira Local Server]

  Z[Zero Trust App] --> J
  P[Slack Bypass Policy] --> J
```

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
- Cloudflare Access policy for Jira hostname (team email allow-list).
- Slack bypass policy for Jira path `/rest/slack/latest/*` with approved Slack IP ranges.
- Bypass policy priority above the main allow policy.

### Non-Impact Statement
No changes are required to existing client APIs for Android, iOS, and macOS desktop.
Windows desktop rollout and Slack integration are additive channels over the same backend API contracts.

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
- Android + iOS + Desktop host apps (macOS + Windows)

### Tooling
- Gradle for builds
- Docker Compose for local services
- Cloudflare Tunnel (`cloudflared`) for secure local-to-cloud webhook routing
- Slack Block Kit for rich interactive Slack UX
