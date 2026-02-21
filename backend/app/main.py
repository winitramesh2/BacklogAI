import asyncio
import json
import logging
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
    ResearchSummary,
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
        metrics = generated_content.get("metrics", [])
        non_functional_reqs = generated_content.get("non_functional_reqs", [])
        pillar_scores = _normalize_pillar_scores(generated_content.get("pillar_scores"))
        _, priority_level = prioritization_engine.calculate_priority(pillar_scores.dict())
        priority_value = priority_level.value if hasattr(priority_level, "value") else str(priority_level)
        warnings, quality_score = quality_engine.validate_invest_v2(
            summary=summary,
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies,
            metrics=metrics,
            non_functional_reqs=non_functional_reqs,
        )

        research_summary_payload = generated_content.get("research_summary") or {}
        research_summary = ResearchSummary(
            trends=research_summary_payload.get("trends", []),
            competitor_features=research_summary_payload.get("competitor_features", []),
            differentiators=research_summary_payload.get("differentiators", []),
            risks=research_summary_payload.get("risks", []),
            sources=research_summary_payload.get("sources", []),
        )

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
            "quality_score": quality_score,
            "labels": [],
            "components": [],
            "warnings": warnings,
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
        defaults.update({k: v for k, v in scores.items() if v is not None})
    return PillarScores(**defaults)

@app.post("/backlog/generate/v2", response_model=BacklogItemGenerateV2Response)
async def generate_backlog_item_v2(item: BacklogItemGenerateV2Request):
    generated_content = await story_engine.generate_story_v2(
        context=item.context,
        objective=item.objective,
        target_user=item.target_user,
        market_segment=item.market_segment,
        constraints=item.constraints,
        success_metrics=item.success_metrics,
        competitors=item.competitors_optional,
    )

    summary = generated_content.get("summary", item.objective)
    user_story = generated_content.get("user_story", item.objective)
    acceptance_criteria = generated_content.get("acceptance_criteria", [])
    sub_tasks = generated_content.get("sub_tasks", [])
    dependencies = generated_content.get("dependencies", [])
    risks = generated_content.get("risks", [])
    metrics = generated_content.get("metrics", [])
    rollout_plan = generated_content.get("rollout_plan", [])
    non_functional_reqs = generated_content.get("non_functional_reqs", [])

    pillar_scores = _normalize_pillar_scores(generated_content.get("pillar_scores"))
    priority_score, priority_level = prioritization_engine.calculate_priority(
        pillar_scores.dict()
    )

    warnings, quality_score = quality_engine.validate_invest_v2(
        summary=summary,
        user_story=user_story,
        acceptance_criteria=acceptance_criteria,
        dependencies=dependencies,
        metrics=metrics,
        non_functional_reqs=non_functional_reqs,
    )

    if warnings and story_engine.client:
        revised = await story_engine.revise_story_v2(generated_content, warnings)
        summary = revised.get("summary", summary)
        user_story = revised.get("user_story", user_story)
        acceptance_criteria = revised.get("acceptance_criteria", acceptance_criteria)
        sub_tasks = revised.get("sub_tasks", sub_tasks)
        dependencies = revised.get("dependencies", dependencies)
        risks = revised.get("risks", risks)
        metrics = revised.get("metrics", metrics)
        rollout_plan = revised.get("rollout_plan", rollout_plan)
        non_functional_reqs = revised.get("non_functional_reqs", non_functional_reqs)
        pillar_scores = _normalize_pillar_scores(revised.get("pillar_scores"))
        priority_score, priority_level = prioritization_engine.calculate_priority(
            pillar_scores.dict()
        )
        warnings, quality_score = quality_engine.validate_invest_v2(
            summary=summary,
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies,
            metrics=metrics,
            non_functional_reqs=non_functional_reqs,
        )

        generated_content = revised

    research_summary_payload = generated_content.get("research_summary") or {}
    research_summary = ResearchSummary(
        trends=research_summary_payload.get("trends", []),
        competitor_features=research_summary_payload.get("competitor_features", []),
        differentiators=research_summary_payload.get("differentiators", []),
        risks=research_summary_payload.get("risks", []),
        sources=research_summary_payload.get("sources", []),
    )

    description = jira_service.build_description_template(
        context=item.context,
        objective=item.objective,
        user_story=user_story,
        acceptance_criteria=acceptance_criteria,
        non_functional_reqs=non_functional_reqs,
        risks=risks,
        metrics=metrics,
        rollout_plan=rollout_plan,
        research_summary=research_summary,
    )

    response = BacklogItemGenerateV2Response(
        id=uuid4(),
        summary=summary,
        user_story=user_story,
        description=description,
        acceptance_criteria=acceptance_criteria,
        sub_tasks=sub_tasks,
        dependencies=dependencies,
        risks=risks,
        metrics=metrics,
        rollout_plan=rollout_plan,
        non_functional_reqs=non_functional_reqs,
        research_summary=research_summary,
        priority_score=priority_score,
        moscow_priority=priority_level,
        pillar_scores=pillar_scores,
        status="draft",
        validation_warnings=warnings,
        quality_score=quality_score,
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
