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
data class JiraSyncRequest(
    val title: String,
    val description: String,
    val priority: String? = "Medium",
    @SerialName("issue_type")
    val issueType: String = "Story"
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
