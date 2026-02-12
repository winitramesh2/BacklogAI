from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from uuid import UUID
from enum import Enum

# --- Enums ---
class PriorityLevel(str, Enum):
    MUST_HAVE = "Must Have"
    SHOULD_HAVE = "Should Have"
    COULD_HAVE = "Could Have"
    WONT_HAVE = "Won't Have"

# --- Pillar Models ---
class PillarScores(BaseModel):
    user_value: float = Field(..., ge=0, le=10, description="Solving genuine user pain points (0-10)")
    commercial_impact: float = Field(..., ge=0, le=10, description="Revenue generation and deal blockers (0-10)")
    strategic_horizon: float = Field(..., ge=0, le=10, description="Long-term relevance and future demand (0-10)")
    competitive_positioning: float = Field(..., ge=0, le=10, description="Market differentiation vs catch-up (0-10)")
    technical_reality: float = Field(..., ge=0, le=10, description="Feasibility and technical debt (0-10)")

# --- Input Models ---
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    # Optional custom weights for the 5 pillars
    weights: Optional[PillarScores] = None 

class BacklogItemCreate(BaseModel):
    project_id: UUID
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., description="High-level feature request or user story")
    
    # The 5 Pillars Input
    pillar_scores: PillarScores
    
    # Context for AI Generation
    personas: List[str] = Field(default=[], description="Target users e.g. ['Admin', 'Sales Rep']")
    acceptance_criteria_hint: Optional[str] = Field(None, description="Specific requirements to include")

class SubTask(BaseModel):
    title: str
    description: str

class ResearchSummary(BaseModel):
    trends: List[str] = []
    competitor_features: List[str] = []
    differentiators: List[str] = []
    risks: List[str] = []
    sources: List[str] = []

# --- Output Models ---
class BacklogItemResponse(BaseModel):
    id: UUID
    title: str
    description: str
    acceptance_criteria: List[str]
    sub_tasks: List[SubTask] = []
    priority_score: float
    moscow_priority: PriorityLevel
    pillar_scores: PillarScores
    status: str
    jira_key: Optional[str] = None
    validation_warnings: List[str] = []
    
class BacklogItemSyncResponse(BaseModel):
    id: UUID
    jira_key: str
    jira_url: str
    status: str

    class Config:
        from_attributes = True

class JiraSyncRequest(BaseModel):
    title: str
    description: str
    priority: Optional[str] = "Medium"
    issue_type: str = "Story"

class BacklogItemGenerateV2Request(BaseModel):
    project_id: Optional[UUID] = None
    context: str = Field(..., min_length=10, description="Product context and background")
    objective: str = Field(..., min_length=5, description="Desired outcome or objective")
    target_user: Optional[str] = Field(None, description="Primary user persona")
    market_segment: Optional[str] = Field(None, description="Target market or segment")
    constraints: Optional[str] = Field(None, description="Constraints and guardrails")
    success_metrics: Optional[str] = Field(None, description="How success will be measured")
    competitors_optional: List[str] = Field(default=[], description="Known competitors")

class BacklogItemGenerateV2Response(BaseModel):
    id: UUID
    summary: str
    user_story: str
    description: str
    acceptance_criteria: List[str]
    sub_tasks: List[SubTask] = []
    dependencies: List[str] = []
    risks: List[str] = []
    metrics: List[str] = []
    rollout_plan: List[str] = []
    non_functional_reqs: List[str] = []
    research_summary: ResearchSummary
    priority_score: float
    moscow_priority: PriorityLevel
    pillar_scores: PillarScores
    status: str
    validation_warnings: List[str] = []
    quality_score: float = 0.0

class JiraSyncRequestV2(BaseModel):
    summary: str
    description: str
    issue_type: str = "Story"
    priority: Optional[str] = "Medium"
    labels: List[str] = []
    components: List[str] = []
