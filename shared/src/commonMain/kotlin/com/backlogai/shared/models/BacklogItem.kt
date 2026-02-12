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
    @SerialName("research_summary")
    val researchSummary: ResearchSummary,
    @SerialName("priority_score")
    val priorityScore: Double,
    @SerialName("moscow_priority")
    val moscowPriority: String,
    @SerialName("pillar_scores")
    val pillarScores: PillarScores,
    val status: String,
    @SerialName("validation_warnings")
    val validationWarnings: List<String> = emptyList(),
    @SerialName("quality_score")
    val qualityScore: Double = 0.0
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
