from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import os
from dotenv import load_dotenv
from uuid import uuid4

# Import internal modules
from app.schemas import BacklogItemCreate, BacklogItemResponse, PriorityLevel, PillarScores
from app.services.story_engine import StoryGenerationEngine
from app.services.prioritization_engine import PrioritizationEngine
from app.services.quality_engine import QualityValidationEngine
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
        acceptance_criteria=acceptance_criteria,
        priority_score=priority_score,
        moscow_priority=priority_level,
        pillar_scores=item.pillar_scores,
        status="draft",
        validation_warnings=warnings
    )
    
    return response
