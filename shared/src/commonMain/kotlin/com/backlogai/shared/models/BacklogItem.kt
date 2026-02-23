package com.backlogai.shared.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PillarScores(
    @SerialName("user_value")
    val userValue: Double = 0.0,
    
    @SerialName("commercial_impact")
    val commercialImpact: Double = 0.0,
    
    @SerialName("strategic_horizon")
    val strategicHorizon: Double = 0.0,
    
    @SerialName("competitive_positioning")
    val competitivePositioning: Double = 0.0,
    
    @SerialName("technical_reality")
    val technicalReality: Double = 0.0
)

@Serializable
data class BacklogItemCreate(
    @SerialName("project_id")
    val projectId: String, // UUID
    
    val title: String,
    val description: String,
    
    @SerialName("pillar_scores")
    val pillarScores: PillarScores,
    
    val personas: List<String> = emptyList(),
    
    @SerialName("acceptance_criteria_hint")
    val acceptanceCriteriaHint: String? = null
)

@Serializable
data class SubTask(
    val title: String,
    val description: String
)

@Serializable
data class ResearchSummary(
    val trends: List<String> = emptyList(),
    @SerialName("competitor_features")
    val competitorFeatures: List<String> = emptyList(),
    val differentiators: List<String> = emptyList(),
    val risks: List<String> = emptyList(),
    val sources: List<String> = emptyList()
)

@Serializable
data class MetricItem(
    val name: String,
    val baseline: String? = null,
    val target: String? = null,
    val timeframe: String? = null,
    val owner: String? = null
)

@Serializable
data class QualityWarning(
    val code: String,
    val type: String,
    val severity: String,
    val message: String
)

@Serializable
data class PriorityBreakdown(
    @SerialName("base_pillar_score")
    val basePillarScore: Double,
    @SerialName("user_demand_signal")
    val userDemandSignal: Double,
    @SerialName("competitor_pressure_signal")
    val competitorPressureSignal: Double,
    @SerialName("effort_penalty")
    val effortPenalty: Double,
    @SerialName("evidence_multiplier")
    val evidenceMultiplier: Double,
    @SerialName("final_score")
    val finalScore: Double
)

@Serializable
data class QualityBreakdown(
    val clarity: Double,
    val invest: Double,
    val testability: Double,
    val measurability: Double,
    val scope: Double,
    val evidence: Double,
    @SerialName("final_score")
    val finalScore: Double
)

@Serializable
data class RoleScores(
    @SerialName("pm_clarity")
    val pmClarity: Double,
    @SerialName("engineering_estimability")
    val engineeringEstimability: Double,
    @SerialName("qa_testability")
    val qaTestability: Double,
    @SerialName("architecture_nfr_readiness")
    val architectureNfrReadiness: Double
)

@Serializable
data class GenerationTelemetry(
    @SerialName("run_id")
    val runId: String,
    @SerialName("model_draft")
    val modelDraft: String,
    @SerialName("model_revise")
    val modelRevise: String? = null,
    @SerialName("latency_ms")
    val latencyMs: Int,
    @SerialName("used_fallback")
    val usedFallback: Boolean = false,
    @SerialName("warnings_count")
    val warningsCount: Int = 0,
    @SerialName("high_severity_warnings")
    val highSeverityWarnings: Int = 0,
    @SerialName("research_queries")
    val researchQueries: Int = 0,
    @SerialName("research_snippets")
    val researchSnippets: Int = 0,
    @SerialName("research_sources")
    val researchSources: Int = 0,
    @SerialName("citation_coverage")
    val citationCoverage: Double = 0.0
)

@Serializable
data class BacklogItemResponse(
    val id: String, // UUID
    val title: String,
    val description: String,
    
    @SerialName("acceptance_criteria")
    val acceptanceCriteria: List<String> = emptyList(),
    
    @SerialName("sub_tasks")
    val subTasks: List<SubTask> = emptyList(),
    
    @SerialName("priority_score")
    val priorityScore: Double,
    
    @SerialName("moscow_priority")
    val moscowPriority: String, // Enum string
    
    @SerialName("pillar_scores")
    val pillarScores: PillarScores,
    
    val status: String,
    
    @SerialName("jira_key")
    val jiraKey: String? = null,
    
    @SerialName("validation_warnings")
    val validationWarnings: List<String> = emptyList()
)

@Serializable
data class BacklogItemGenerateV2Request(
    @SerialName("project_id")
    val projectId: String? = null,
    val context: String,
    val objective: String,
    @SerialName("target_user")
    val targetUser: String? = null,
    @SerialName("market_segment")
    val marketSegment: String? = null,
    val constraints: String? = null,
    @SerialName("success_metrics")
    val successMetrics: String? = null,
    @SerialName("competitors_optional")
    val competitorsOptional: List<String> = emptyList()
)

@Serializable
data class BacklogItemGenerateV2Response(
    val id: String,
    @SerialName("run_id")
    val runId: String? = null,
    val summary: String,
    @SerialName("user_story")
    val userStory: String,
    val description: String,
    @SerialName("acceptance_criteria")
    val acceptanceCriteria: List<String> = emptyList(),
    @SerialName("sub_tasks")
    val subTasks: List<SubTask> = emptyList(),
    val dependencies: List<String> = emptyList(),
    val risks: List<String> = emptyList(),
    val metrics: List<String> = emptyList(),
    @SerialName("rollout_plan")
    val rolloutPlan: List<String> = emptyList(),
    @SerialName("non_functional_reqs")
    val nonFunctionalReqs: List<String> = emptyList(),
    @SerialName("structured_metrics")
    val structuredMetrics: List<MetricItem> = emptyList(),
    val assumptions: List<String> = emptyList(),
    @SerialName("open_questions")
    val openQuestions: List<String> = emptyList(),
    @SerialName("out_of_scope")
    val outOfScope: List<String> = emptyList(),
    val confidence: Double = 0.0,
    @SerialName("research_summary")
    val researchSummary: ResearchSummary,
    @SerialName("priority_score")
    val priorityScore: Double,
    @SerialName("moscow_priority")
    val moscowPriority: String,
    @SerialName("priority_label")
    val priorityLabel: Int? = null,
    @SerialName("priority_label_text")
    val priorityLabelText: String? = null,
    @SerialName("priority_confidence")
    val priorityConfidence: Double? = null,
    @SerialName("priority_breakdown")
    val priorityBreakdown: PriorityBreakdown? = null,
    @SerialName("pillar_scores")
    val pillarScores: PillarScores,
    val status: String,
    @SerialName("validation_warnings")
    val validationWarnings: List<String> = emptyList(),
    @SerialName("warning_details")
    val warningDetails: List<QualityWarning> = emptyList(),
    @SerialName("quality_score")
    val qualityScore: Double = 0.0,
    @SerialName("quality_breakdown")
    val qualityBreakdown: QualityBreakdown? = null,
    @SerialName("quality_confidence")
    val qualityConfidence: Double? = null,
    @SerialName("role_scores")
    val roleScores: RoleScores? = null,
    @SerialName("execution_readiness_score")
    val executionReadinessScore: Double? = null,
    @SerialName("generation_telemetry")
    val generationTelemetry: GenerationTelemetry? = null
)

@Serializable
data class JiraSyncRequest(
    val title: String,
    val description: String,
    val priority: String? = "Medium",
    @SerialName("issue_type")
    val issueType: String = "Story"
)

@Serializable
data class JiraSyncRequestV2(
    val summary: String,
    val description: String,
    @SerialName("issue_type")
    val issueType: String = "Story",
    val priority: String? = "Medium",
    val labels: List<String> = emptyList(),
    val components: List<String> = emptyList()
)

@Serializable
data class BacklogItemSyncResponse(
    val id: String,
    @SerialName("jira_key")
    val jiraKey: String,
    @SerialName("jira_url")
    val jiraUrl: String,
    val status: String
)
