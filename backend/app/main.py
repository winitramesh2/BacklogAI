import asyncio
import json
import logging
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import os
from dotenv import load_dotenv
from uuid import uuid4

# Import internal modules
from app.schemas import (
    BacklogItemCreate, 
    BacklogItemResponse, 
    BacklogItemSyncResponse, 
    BacklogItemGenerateV2Request,
    BacklogItemGenerateV2Response,
    GenerationTelemetry,
    MetricItem,
    PriorityBand,
    PriorityBreakdown,
    QualityBreakdown,
    QualityWarning,
    ResearchSummary,
    RoleScores,
    JiraSyncRequestV2,
    JiraSyncRequest,
    PriorityLevel, 
    PillarScores
)
from app.services.story_engine import StoryGenerationEngine
from app.services.prioritization_engine import PrioritizationEngine
from app.services.quality_engine import QualityValidationEngine
from app.services.jira_service import JiraService
from app.services.slack_service import SlackService
from app.models import BacklogItem, BacklogItemStatus, Project, SlackSessionStatus

# Load environment variables
load_dotenv()

app = FastAPI(
    title="BackLogAI API",
    description="Intelligent Backlog Generator & Prioritization System",
    version="0.1.0"
)

logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")

# Register Tortoise ORM
register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Initialize Engines
story_engine = StoryGenerationEngine()
prioritization_engine = PrioritizationEngine()
quality_engine = QualityValidationEngine()
jira_service = JiraService()
slack_service = SlackService()

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "BackLogAI API is running! 🚀"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "db_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "sqlite"}


def _verify_slack_request(headers: dict, body: bytes) -> None:
    signature = headers.get("x-slack-signature", "")
    timestamp = headers.get("x-slack-request-timestamp", "")
    if not slack_service.verify_signature(timestamp=timestamp, signature=signature, body=body):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")


def _build_research_summary(payload: dict | None) -> ResearchSummary:
    raw = payload or {}
    return ResearchSummary(
        trends=raw.get("trends", []),
        competitor_features=raw.get("competitor_features", []),
        differentiators=raw.get("differentiators", []),
        risks=raw.get("risks", []),
        sources=raw.get("sources", []),
        citation_map=raw.get("citation_map", {}),
        source_details=raw.get("source_details", []),
        quality=raw.get("quality", {}),
    )


def _calculate_evidence_signal(research_summary: ResearchSummary) -> float:
    quality = research_summary.quality
    source_signal = min(1.0, quality.source_count / 8.0)
    domain_signal = min(1.0, quality.unique_domain_count / 6.0)
    citation_signal = max(0.0, min(1.0, quality.citation_coverage))
    freshness_signal = max(0.0, min(1.0, quality.freshness_coverage))
    return round((source_signal * 0.35) + (domain_signal * 0.2) + (citation_signal * 0.35) + (freshness_signal * 0.1), 2)


def _compute_user_demand_signal(
    objective: str,
    context: str,
    success_metrics: str | None,
    generated_metrics: list[str],
    target_user: str | None,
) -> float:
    score = 0.0
    objective_lower = objective.lower()
    demand_terms = ["increase", "reduce", "improve", "faster", "conversion", "retention", "adoption"]

    if any(term in objective_lower for term in demand_terms):
        score += 0.25
    if success_metrics:
        score += 0.25
    if len(generated_metrics) >= 2:
        score += 0.2
    if target_user:
        score += 0.15
    if len(context) > 120:
        score += 0.15
    return round(min(1.0, score), 2)


def _compute_competitor_pressure_signal(competitors: list[str], research_summary: ResearchSummary) -> float:
    score = 0.0
    if competitors:
        score += min(0.3, len(competitors) * 0.1)
    if research_summary.competitor_features:
        score += min(0.45, len(research_summary.competitor_features) * 0.1)
    if research_summary.differentiators:
        score += 0.15
    return round(min(1.0, score), 2)


def _compute_effort_penalty(
    dependencies: list[str],
    open_questions: list[str],
    constraints: str | None,
    technical_reality_score: float,
) -> float:
    score = 0.0
    score += min(0.45, len(dependencies) * 0.1)
    score += min(0.25, len(open_questions) * 0.07)
    if constraints:
        score += 0.15
    if technical_reality_score < 4.5:
        score += 0.2
    return round(min(1.0, score), 2)


def _compute_evidence_multiplier(research_summary: ResearchSummary) -> float:
    evidence = _calculate_evidence_signal(research_summary)
    return round(0.9 + (0.2 * evidence), 2)


def _normalize_metric_payload(generated_content: dict) -> tuple[list[str], list[MetricItem]]:
    metrics = generated_content.get("metrics", [])
    structured = generated_content.get("structured_metrics", [])

    normalized_metrics: list[str] = []
    structured_metrics: list[MetricItem] = []

    for entry in metrics:
        if isinstance(entry, str) and entry.strip():
            normalized_metrics.append(entry.strip())
        elif isinstance(entry, dict):
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            metric = MetricItem(
                name=name,
                baseline=str(entry.get("baseline")).strip() if entry.get("baseline") else None,
                target=str(entry.get("target")).strip() if entry.get("target") else None,
                timeframe=str(entry.get("timeframe")).strip() if entry.get("timeframe") else None,
                owner=str(entry.get("owner")).strip() if entry.get("owner") else None,
            )
            structured_metrics.append(metric)
            normalized_metrics.append(metric.name)

    for entry in structured:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip()
        if not name:
            continue
        metric = MetricItem(
            name=name,
            baseline=str(entry.get("baseline")).strip() if entry.get("baseline") else None,
            target=str(entry.get("target")).strip() if entry.get("target") else None,
            timeframe=str(entry.get("timeframe")).strip() if entry.get("timeframe") else None,
            owner=str(entry.get("owner")).strip() if entry.get("owner") else None,
        )
        structured_metrics.append(metric)
        normalized_metrics.append(metric.name)

    deduped_metrics: list[str] = []
    seen = set()
    for metric in normalized_metrics:
        key = metric.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped_metrics.append(metric)

    deduped_structured: list[MetricItem] = []
    seen_structured = set()
    for metric in structured_metrics:
        key = metric.name.lower()
        if key in seen_structured:
            continue
        seen_structured.add(key)
        deduped_structured.append(metric)

    return deduped_metrics[:8], deduped_structured[:8]


async def _generate_and_post_preview(input_payload: dict, channel_id: str, slack_user_id: str) -> None:
    try:
        generated_content = await story_engine.generate_story_v2(
            context=input_payload["context"],
            objective=input_payload["objective"],
            target_user=input_payload.get("target_user"),
            market_segment=input_payload.get("market_segment"),
            constraints=input_payload.get("constraints"),
            success_metrics=input_payload.get("success_metrics"),
            competitors=input_payload.get("competitors_optional", []),
        )

        summary = generated_content.get("summary", input_payload["objective"])
        user_story = generated_content.get("user_story", input_payload["objective"])
        acceptance_criteria = generated_content.get("acceptance_criteria", [])
        dependencies = generated_content.get("dependencies", [])
        metrics, structured_metrics = _normalize_metric_payload(generated_content)
        non_functional_reqs = generated_content.get("non_functional_reqs", [])
        open_questions = generated_content.get("open_questions", [])
        pillar_scores = _normalize_pillar_scores(generated_content.get("pillar_scores"))

        research_summary = _build_research_summary(generated_content.get("research_summary"))
        user_demand_signal = _compute_user_demand_signal(
            objective=input_payload["objective"],
            context=input_payload["context"],
            success_metrics=input_payload.get("success_metrics"),
            generated_metrics=metrics,
            target_user=input_payload.get("target_user"),
        )
        competitor_pressure_signal = _compute_competitor_pressure_signal(
            competitors=input_payload.get("competitors_optional", []),
            research_summary=research_summary,
        )
        effort_penalty = _compute_effort_penalty(
            dependencies=dependencies,
            open_questions=open_questions,
            constraints=input_payload.get("constraints"),
            technical_reality_score=pillar_scores.technical_reality,
        )
        evidence_multiplier = _compute_evidence_multiplier(research_summary)

        (
            priority_score,
            priority_level,
            priority_band,
            priority_text,
            priority_confidence,
            priority_breakdown,
        ) = prioritization_engine.calculate_priority_v2(
            pillar_scores=pillar_scores.dict(),
            user_demand_signal=user_demand_signal,
            competitor_pressure_signal=competitor_pressure_signal,
            effort_penalty=effort_penalty,
            evidence_multiplier=evidence_multiplier,
        )
        priority_value = priority_level.value if hasattr(priority_level, "value") else str(priority_level)

        quality_eval = quality_engine.evaluate_story_v2(
            summary=summary,
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies,
            metrics=metrics,
            non_functional_reqs=non_functional_reqs,
            evidence_signal=_calculate_evidence_signal(research_summary),
        )
        warnings = quality_eval["warnings_text"]
        warning_details: list[QualityWarning] = quality_eval["warnings"]
        quality_score = quality_eval["quality_score"]

        description = jira_service.build_description_template(
            context=input_payload["context"],
            objective=input_payload["objective"],
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            non_functional_reqs=non_functional_reqs,
            risks=generated_content.get("risks", []),
            metrics=metrics,
            rollout_plan=generated_content.get("rollout_plan", []),
            research_summary=research_summary,
        )

        preview_payload = {
            "summary": summary,
            "user_story": user_story,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "priority": priority_value,
            "priority_score": priority_score,
            "priority_label": int(priority_band.value),
            "priority_label_text": priority_text,
            "priority_confidence": priority_confidence,
            "priority_breakdown": priority_breakdown.model_dump(),
            "quality_score": quality_score,
            "quality_breakdown": quality_eval["quality_breakdown"].model_dump(),
            "quality_confidence": quality_eval["quality_confidence"],
            "execution_readiness_score": quality_eval["execution_readiness_score"],
            "role_scores": quality_eval["role_scores"].model_dump(),
            "warning_details": [warning.model_dump() for warning in warning_details],
            "labels": [],
            "components": [],
            "warnings": warnings,
            "structured_metrics": [metric.model_dump() for metric in structured_metrics],
        }

        session = await slack_service.create_session(
            slack_user_id=slack_user_id,
            slack_channel_id=channel_id,
            input_payload=input_payload,
            preview_payload=preview_payload,
        )

        await slack_service.post_preview(
            channel_id=channel_id,
            summary=summary,
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            quality_score=quality_score,
            moscow_priority=priority_value,
            priority_label=priority_text,
            execution_readiness_score=quality_eval["execution_readiness_score"],
            session_id=str(session.id),
        )
    except Exception as exc:
        await slack_service.post_error(channel_id=channel_id, message=str(exc))


async def _open_modal_safely(trigger_id: str, channel_id: str, user_id: str) -> None:
    try:
        await slack_service.open_input_modal(trigger_id=trigger_id, channel_id=channel_id, user_id=user_id)
    except Exception as exc:
        logger.exception(
            "Slack modal open failed for channel=%s user=%s: %s",
            channel_id,
            user_id,
            exc,
        )

@app.post("/backlog/generate", response_model=BacklogItemResponse)
async def generate_backlog_item(item: BacklogItemCreate):
    """
    Generates a structured User Story with AI, calculates priority, and validates quality.
    """
    # 1. Generate Story Content (AI)
    generated_content = await story_engine.generate_story(
        title=item.title,
        description=item.description,
        personas=item.personas,
        pillar_scores=item.pillar_scores.dict()
    )
    
    # 2. Calculate Priority
    priority_score, priority_level = prioritization_engine.calculate_priority(
        item.pillar_scores.dict()
    )
    
    # 3. Validate Quality (INVEST)
    acceptance_criteria = generated_content.get("acceptance_criteria", [])
    warnings = quality_engine.validate_invest(
        title=item.title,
        description=generated_content.get("user_story", item.description),
        acceptance_criteria=acceptance_criteria,
        pillar_scores=item.pillar_scores
    )
    
    # 4. Construct Response (Simulated DB persistence for now)
    response = BacklogItemResponse(
        id=uuid4(),
        title=item.title,
        description=generated_content.get("user_story", item.description), # Fallback if AI fails
        acceptance_criteria=generated_content.get("acceptance_criteria", []),
        sub_tasks=generated_content.get("sub_tasks", []),
        priority_score=priority_score,
        moscow_priority=priority_level,
        pillar_scores=item.pillar_scores,
        status="draft",
        validation_warnings=warnings
    )
    
    return response

def _normalize_pillar_scores(scores: dict | None) -> PillarScores:
    defaults = {
        "user_value": 5.0,
        "commercial_impact": 5.0,
        "strategic_horizon": 5.0,
        "competitive_positioning": 5.0,
        "technical_reality": 5.0,
    }
    if scores:
        for key, value in scores.items():
            if key not in defaults or value is None:
                continue
            try:
                defaults[key] = max(0.0, min(10.0, float(value)))
            except (TypeError, ValueError):
                continue
    return PillarScores(**defaults)

@app.post("/backlog/generate/v2", response_model=BacklogItemGenerateV2Response)
async def generate_backlog_item_v2(item: BacklogItemGenerateV2Request):
    run_id = str(uuid4())
    started = time.perf_counter()

    generated_content = await story_engine.generate_story_v2(
        context=item.context,
        objective=item.objective,
        target_user=item.target_user,
        market_segment=item.market_segment,
        constraints=item.constraints,
        success_metrics=item.success_metrics,
        competitors=item.competitors_optional,
    )

    def evaluate_payload(payload: dict) -> dict:
        summary = payload.get("summary", item.objective)
        user_story = payload.get("user_story", item.objective)
        acceptance_criteria = payload.get("acceptance_criteria", [])
        sub_tasks = payload.get("sub_tasks", [])
        dependencies = payload.get("dependencies", [])
        risks = payload.get("risks", [])
        metrics, structured_metrics = _normalize_metric_payload(payload)
        rollout_plan = payload.get("rollout_plan", [])
        non_functional_reqs = payload.get("non_functional_reqs", [])
        assumptions = payload.get("assumptions", [])
        open_questions = payload.get("open_questions", [])
        out_of_scope = payload.get("out_of_scope", [])
        confidence = round(max(0.0, min(1.0, float(payload.get("confidence", 0.65)))), 2)

        research_summary = _build_research_summary(payload.get("research_summary"))
        pillar_scores = _normalize_pillar_scores(payload.get("pillar_scores"))

        user_demand_signal = _compute_user_demand_signal(
            objective=item.objective,
            context=item.context,
            success_metrics=item.success_metrics,
            generated_metrics=metrics,
            target_user=item.target_user,
        )
        competitor_pressure_signal = _compute_competitor_pressure_signal(
            competitors=item.competitors_optional,
            research_summary=research_summary,
        )
        effort_penalty = _compute_effort_penalty(
            dependencies=dependencies,
            open_questions=open_questions,
            constraints=item.constraints,
            technical_reality_score=pillar_scores.technical_reality,
        )
        evidence_multiplier = _compute_evidence_multiplier(research_summary)
        (
            priority_score,
            priority_level,
            priority_band,
            priority_text,
            priority_confidence,
            priority_breakdown,
        ) = prioritization_engine.calculate_priority_v2(
            pillar_scores=pillar_scores.dict(),
            user_demand_signal=user_demand_signal,
            competitor_pressure_signal=competitor_pressure_signal,
            effort_penalty=effort_penalty,
            evidence_multiplier=evidence_multiplier,
        )

        quality_eval = quality_engine.evaluate_story_v2(
            summary=summary,
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies,
            metrics=metrics,
            non_functional_reqs=non_functional_reqs,
            evidence_signal=_calculate_evidence_signal(research_summary),
        )

        return {
            "summary": summary,
            "user_story": user_story,
            "acceptance_criteria": acceptance_criteria,
            "sub_tasks": sub_tasks,
            "dependencies": dependencies,
            "risks": risks,
            "metrics": metrics,
            "structured_metrics": structured_metrics,
            "rollout_plan": rollout_plan,
            "non_functional_reqs": non_functional_reqs,
            "assumptions": assumptions,
            "open_questions": open_questions,
            "out_of_scope": out_of_scope,
            "confidence": confidence,
            "research_summary": research_summary,
            "pillar_scores": pillar_scores,
            "priority_score": priority_score,
            "priority_level": priority_level,
            "priority_band": priority_band,
            "priority_text": priority_text,
            "priority_confidence": priority_confidence,
            "priority_breakdown": priority_breakdown,
            "quality_eval": quality_eval,
        }

    evaluation = evaluate_payload(generated_content)

    warning_messages = evaluation["quality_eval"]["warnings_text"]
    warning_details = evaluation["quality_eval"]["warnings"]
    should_revise = story_engine.client and (
        evaluation["quality_eval"]["quality_score"] < 85.0
        or any(warning.severity.value == "high" for warning in warning_details)
    )

    if should_revise:
        revised = await story_engine.revise_story_v2(generated_content, warning_messages)
        generated_content = revised
        evaluation = evaluate_payload(generated_content)
        warning_messages = evaluation["quality_eval"]["warnings_text"]
        warning_details = evaluation["quality_eval"]["warnings"]

    research_summary = evaluation["research_summary"]

    description = jira_service.build_description_template(
        context=item.context,
        objective=item.objective,
        user_story=evaluation["user_story"],
        acceptance_criteria=evaluation["acceptance_criteria"],
        non_functional_reqs=evaluation["non_functional_reqs"],
        risks=evaluation["risks"],
        metrics=evaluation["metrics"],
        rollout_plan=evaluation["rollout_plan"],
        dependencies=evaluation["dependencies"],
        assumptions=evaluation["assumptions"],
        open_questions=evaluation["open_questions"],
        out_of_scope=evaluation["out_of_scope"],
        research_summary=research_summary,
    )

    generation_meta = generated_content.get("_meta", {}) if isinstance(generated_content, dict) else {}
    latency_ms = int((time.perf_counter() - started) * 1000)
    high_severity_count = sum(1 for warning in warning_details if warning.severity.value == "high")
    telemetry = GenerationTelemetry(
        run_id=run_id,
        model_draft=str(generation_meta.get("model_draft") or story_engine.draft_model),
        model_revise=str(generation_meta.get("model_revise") or story_engine.revise_model),
        latency_ms=latency_ms,
        used_fallback=bool(generation_meta.get("used_fallback", False)),
        warnings_count=len(warning_details),
        high_severity_warnings=high_severity_count,
        research_queries=int(generation_meta.get("research_queries", 0)),
        research_snippets=int(generation_meta.get("research_snippets", 0)),
        research_sources=int(generation_meta.get("research_sources", research_summary.quality.source_count)),
        citation_coverage=research_summary.quality.citation_coverage,
    )

    logger.info(
        "story_generate_v2 run_id=%s quality_score=%.1f execution_readiness=%.1f priority_score=%.1f warnings=%d fallback=%s",
        run_id,
        evaluation["quality_eval"]["quality_score"],
        evaluation["quality_eval"]["execution_readiness_score"],
        evaluation["priority_score"],
        len(warning_details),
        telemetry.used_fallback,
    )

    response = BacklogItemGenerateV2Response(
        id=uuid4(),
        run_id=run_id,
        summary=evaluation["summary"],
        user_story=evaluation["user_story"],
        description=description,
        acceptance_criteria=evaluation["acceptance_criteria"],
        sub_tasks=evaluation["sub_tasks"],
        dependencies=evaluation["dependencies"],
        risks=evaluation["risks"],
        metrics=evaluation["metrics"],
        structured_metrics=evaluation["structured_metrics"],
        rollout_plan=evaluation["rollout_plan"],
        non_functional_reqs=evaluation["non_functional_reqs"],
        assumptions=evaluation["assumptions"],
        open_questions=evaluation["open_questions"],
        out_of_scope=evaluation["out_of_scope"],
        confidence=evaluation["confidence"],
        research_summary=research_summary,
        priority_score=evaluation["priority_score"],
        moscow_priority=evaluation["priority_level"],
        priority_label=evaluation["priority_band"],
        priority_label_text=evaluation["priority_text"],
        priority_confidence=evaluation["priority_confidence"],
        priority_breakdown=evaluation["priority_breakdown"],
        pillar_scores=evaluation["pillar_scores"],
        status="draft",
        validation_warnings=warning_messages,
        warning_details=warning_details,
        quality_score=evaluation["quality_eval"]["quality_score"],
        quality_breakdown=evaluation["quality_eval"]["quality_breakdown"],
        quality_confidence=evaluation["quality_eval"]["quality_confidence"],
        role_scores=evaluation["quality_eval"]["role_scores"],
        execution_readiness_score=evaluation["quality_eval"]["execution_readiness_score"],
        generation_telemetry=telemetry,
    )

    return response

@app.post("/backlog/sync", response_model=BacklogItemSyncResponse)
async def sync_to_jira(request: JiraSyncRequest):
    """
    Syncs a backlog item to JIRA (Create Issue).
    """
    try:
        jira_response = jira_service.create_issue(
            title=request.title,
            description=request.description,
            priority=request.priority or "Medium",
            issue_type=request.issue_type
        )
        
        return BacklogItemSyncResponse(
            id=uuid4(),
            jira_key=jira_response["key"],
            jira_url=jira_response["url"],
            status="synced"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backlog/sync/v2", response_model=BacklogItemSyncResponse)
async def sync_to_jira_v2(request: JiraSyncRequestV2):
    try:
        jira_response = jira_service.create_issue_v2(
            summary=request.summary,
            description=request.description,
            priority=request.priority or "Medium",
            issue_type=request.issue_type,
            labels=request.labels,
            components=request.components,
        )

        return BacklogItemSyncResponse(
            id=uuid4(),
            jira_key=jira_response["key"],
            jira_url=jira_response["url"],
            status="synced"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/slack/commands")
async def slack_commands(request: Request):
    if not slack_service.is_configured:
        raise HTTPException(status_code=503, detail="Slack integration is disabled")

    raw_body = await request.body()
    _verify_slack_request(request.headers, raw_body)
    form = await request.form()

    command = str(form.get("command", "")).strip()
    trigger_id = str(form.get("trigger_id", "")).strip()
    channel_id = str(form.get("channel_id", "")).strip()
    user_id = str(form.get("user_id", "")).strip()

    if command != "/backlogai":
        return JSONResponse({"response_type": "ephemeral", "text": "Unsupported command."})

    if not trigger_id or not channel_id or not user_id:
        return JSONResponse(
            {
                "response_type": "ephemeral",
                "text": "Missing Slack command metadata. Please retry /backlogai.",
            }
        )

    asyncio.create_task(_open_modal_safely(trigger_id=trigger_id, channel_id=channel_id, user_id=user_id))
    return JSONResponse({"response_type": "ephemeral", "text": "Opening BacklogAI modal..."})


@app.post("/slack/interactions")
async def slack_interactions(request: Request):
    if not slack_service.is_configured:
        raise HTTPException(status_code=503, detail="Slack integration is disabled")

    raw_body = await request.body()
    _verify_slack_request(request.headers, raw_body)
    form = await request.form()
    payload_raw = form.get("payload")
    if not payload_raw:
        raise HTTPException(status_code=400, detail="Missing payload")
    payload = json.loads(str(payload_raw))
    interaction_type = payload.get("type")

    if interaction_type == "view_submission" and payload.get("view", {}).get("callback_id") == "backlogai_modal_submit":
        metadata = json.loads(payload.get("view", {}).get("private_metadata", "{}") or "{}")
        channel_id = metadata.get("channel_id")
        user_id = metadata.get("user_id")
        input_payload = slack_service.parse_modal_submission(payload)

        if not input_payload.get("context") or not input_payload.get("objective"):
            return JSONResponse({
                "response_action": "errors",
                "errors": {
                    "context": "Context is required",
                    "objective": "Objective is required"
                }
            })

        asyncio.create_task(_generate_and_post_preview(input_payload, channel_id, user_id))
        return JSONResponse({"response_action": "clear"})

    if interaction_type == "block_actions":
        actions = payload.get("actions", [])
        if not actions:
            return JSONResponse({"text": "No action payload."})

        action = actions[0]
        if action.get("action_id") != "sync_to_jira":
            return JSONResponse({"text": "Unsupported action."})

        session_id = action.get("value")
        session = await slack_service.get_session(session_id)
        if not session:
            return JSONResponse({"text": "Session not found or expired."})

        if session.status == SlackSessionStatus.SYNCED:
            await slack_service.post_sync_success(
                channel_id=session.slack_channel_id,
                jira_key=session.jira_key or "unknown",
                jira_url=session.jira_url or "",
            )
            return JSONResponse({"text": "Already synced."})

        preview = session.preview_payload or {}
        jira_response = jira_service.create_issue_v2(
            summary=preview.get("summary", "BacklogAI Story"),
            description=preview.get("description", ""),
            priority=preview.get("priority", "Medium"),
            issue_type="Story",
            labels=preview.get("labels", []),
            components=preview.get("components", []),
        )
        await slack_service.mark_synced(session, jira_response["key"], jira_response["url"])
        await slack_service.post_sync_success(
            channel_id=session.slack_channel_id,
            jira_key=jira_response["key"],
            jira_url=jira_response["url"],
        )
        return JSONResponse({"text": "Synced to JIRA."})

    return JSONResponse({"text": "Interaction received."})


@app.post("/slack/events")
async def slack_events(request: Request):
    if not slack_service.is_configured:
        raise HTTPException(status_code=503, detail="Slack integration is disabled")

    raw_body = await request.body()
    _verify_slack_request(request.headers, raw_body)
    payload = await request.json()

    if payload.get("type") == "url_verification":
        return JSONResponse({"challenge": payload.get("challenge")})
    return JSONResponse({"ok": True})
