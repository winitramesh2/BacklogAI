# BacklogAI AI Content Improvement Plan

## Objective
Improve AI-generated backlog content so users only provide context and objective. The system will perform market research, competitive analysis, refine the need, generate INVEST-compliant JIRA stories aligned to strategic goals, and sync to JIRA.

## Scope
- New v2 generation flow: context + objective input
- Market research via SerpAPI
- Multi-stage AI pipeline (understand -> research -> generate -> quality revise)
- Expanded story output schema suitable for JIRA sync
- UI updates for new flow
- Tests for quality and research fallbacks

## Implementation Plan

### 1) API Contract: Context + Objective
- Add new v2 request model with:
  - context
  - objective
  - target_user
  - market_segment
  - constraints
  - success_metrics
  - competitors_optional
- Keep v1 models for backward compatibility

### 2) Market Research Service (SerpAPI)
- New service module to query SerpAPI using objective + market segment + competitors
- Summarize findings:
  - trends
  - competitor_features
  - differentiators
  - risks
  - sources
- Cache by request hash to reduce repeated calls
- Env var: SERPAPI_API_KEY

### 3) Multi-Stage Generation Pipeline
- Stage A: Need understanding (scope, non-goals, assumptions, user pain, business value)
- Stage B: Inject research brief
- Stage C: Draft story + AC + sub-tasks + NFRs + metrics + rollout + dependencies
- Stage D: Quality gate; revise if warnings exceed threshold

### 4) Expanded Output Schema (JIRA-ready)
- summary
- description
- acceptance_criteria
- sub_tasks
- dependencies
- risks
- metrics
- rollout_plan
- non_functional_reqs
- validation_warnings
- pillar_scores, priority_score, moscow_priority

### 5) JIRA Sync Mapping
- Build a description template:
  - Background
  - Objective
  - Research Summary
  - User Story
  - Acceptance Criteria
  - Non-functional Requirements
  - Risks
  - Metrics
  - Rollout Plan
- Leave Epic Link, Components, Labels blank unless provided

### 6) UI Updates
- Replace input form with context/objective fields
- Show research summary + story preview + warnings
- Add edit-before-sync step

### 7) Tests and Evaluation
- Tests for:
  - SerpAPI fallback behavior
  - v2 schema validation
  - INVEST quality thresholds
- Small evaluation set (10-20 cases)

## Files to Change
- backend/app/schemas.py
- backend/app/services/market_research_service.py (new)
- backend/app/services/story_engine.py
- backend/app/services/quality_engine.py
- backend/app/main.py
- backend/app/services/jira_service.py
- composeApp/src/commonMain/kotlin/com/backlogai/ui/screens/InputScreen.kt
- composeApp/src/commonMain/kotlin/com/backlogai/ui/screens/ResultScreen.kt
- shared/src/commonMain/kotlin/com/backlogai/shared/network/BacklogApi.kt

## Notes
- Use existing model configuration (no model changes)
- SerpAPI is the recommended web search API
