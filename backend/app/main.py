from fastapi import FastAPI, HTTPException
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
from app.models import BacklogItem, BacklogItemStatus, Project

# Load environment variables
load_dotenv()

app = FastAPI(
    title="BackLogAI API",
    description="Intelligent Backlog Generator & Prioritization System",
    version="0.1.0"
)

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

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "BackLogAI API is running! 🚀"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "db_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "sqlite"}

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
