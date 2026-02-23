from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from uuid import UUID
from enum import Enum

# --- Enums ---
class PriorityLevel(str, Enum):
    MUST_HAVE = "Must Have"
    SHOULD_HAVE = "Should Have"
    COULD_HAVE = "Could Have"
    WONT_HAVE = "Won't Have"


class PriorityBand(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


class WarningSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WarningType(str, Enum):
    CLARITY = "clarity"
    INVEST = "invest"
    TESTABILITY = "testability"
    MEASURABILITY = "measurability"
    SCOPE = "scope"
    RESEARCH = "research"
    NFR = "nfr"

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


class MetricItem(BaseModel):
    name: str
    baseline: Optional[str] = None
    target: Optional[str] = None
    timeframe: Optional[str] = None
    owner: Optional[str] = None


class ResearchSource(BaseModel):
    id: int
    url: str
    domain: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    freshness_days: Optional[int] = None


class ResearchQuality(BaseModel):
    source_count: int = 0
    unique_domain_count: int = 0
    citation_coverage: float = 0.0
    freshness_coverage: float = 0.0


class QualityWarning(BaseModel):
    code: str
    type: WarningType
    severity: WarningSeverity
    message: str


class PriorityBreakdown(BaseModel):
    base_pillar_score: float
    user_demand_signal: float
    competitor_pressure_signal: float
    effort_penalty: float
    evidence_multiplier: float
    final_score: float


class QualityBreakdown(BaseModel):
    clarity: float
    invest: float
    testability: float
    measurability: float
    scope: float
    evidence: float
    final_score: float


class RoleScores(BaseModel):
    pm_clarity: float
    engineering_estimability: float
    qa_testability: float
    architecture_nfr_readiness: float


class GenerationTelemetry(BaseModel):
    run_id: str
    model_draft: str
    model_revise: Optional[str] = None
    latency_ms: int
    used_fallback: bool = False
    warnings_count: int = 0
    high_severity_warnings: int = 0
    research_queries: int = 0
    research_snippets: int = 0
    research_sources: int = 0
    citation_coverage: float = 0.0

class ResearchSummary(BaseModel):
    trends: List[str] = Field(default_factory=list)
    competitor_features: List[str] = Field(default_factory=list)
    differentiators: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    citation_map: Dict[str, List[int]] = Field(default_factory=dict)
    source_details: List[ResearchSource] = Field(default_factory=list)
    quality: ResearchQuality = Field(default_factory=ResearchQuality)

# --- Output Models ---
class BacklogItemResponse(BaseModel):
    id: UUID
    title: str
    description: str
    acceptance_criteria: List[str]
    sub_tasks: List[SubTask] = Field(default_factory=list)
    priority_score: float
    moscow_priority: PriorityLevel
    pillar_scores: PillarScores
    status: str
    jira_key: Optional[str] = None
    validation_warnings: List[str] = Field(default_factory=list)
    
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
    competitors_optional: List[str] = Field(default_factory=list, description="Known competitors")

class BacklogItemGenerateV2Response(BaseModel):
    id: UUID
    run_id: Optional[str] = None
    summary: str
    user_story: str
    description: str
    acceptance_criteria: List[str]
    sub_tasks: List[SubTask] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    structured_metrics: List[MetricItem] = Field(default_factory=list)
    rollout_plan: List[str] = Field(default_factory=list)
    non_functional_reqs: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    research_summary: ResearchSummary
    priority_score: float
    moscow_priority: PriorityLevel
    priority_label: PriorityBand = PriorityBand.MEDIUM
    priority_label_text: str = "Medium"
    priority_confidence: float = 0.0
    priority_breakdown: PriorityBreakdown
    pillar_scores: PillarScores
    status: str
    validation_warnings: List[str] = Field(default_factory=list)
    warning_details: List[QualityWarning] = Field(default_factory=list)
    quality_score: float = 0.0
    quality_breakdown: QualityBreakdown
    quality_confidence: float = 0.0
    role_scores: RoleScores
    execution_readiness_score: float = 0.0
    generation_telemetry: GenerationTelemetry

class JiraSyncRequestV2(BaseModel):
    summary: str
    description: str
    issue_type: str = "Story"
    priority: Optional[str] = "Medium"
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
