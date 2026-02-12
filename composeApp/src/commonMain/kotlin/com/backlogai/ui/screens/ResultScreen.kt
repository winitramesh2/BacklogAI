package com.backlogai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import cafe.adriel.voyager.core.screen.Screen
import cafe.adriel.voyager.navigator.LocalNavigator
import cafe.adriel.voyager.navigator.currentOrThrow
import com.backlogai.shared.models.BacklogItemGenerateV2Response
import com.backlogai.shared.models.JiraSyncRequestV2
import com.backlogai.shared.network.BacklogApi
import kotlinx.coroutines.launch

sealed class JiraStatus {
    object Idle : JiraStatus()
    object Syncing : JiraStatus()
    data class Success(val key: String) : JiraStatus()
    data class Error(val message: String) : JiraStatus()
}

@OptIn(ExperimentalMaterial3Api::class)
class ResultScreen(val response: BacklogItemGenerateV2Response) : Screen {

    @Composable
    override fun Content() {
        val navigator = LocalNavigator.currentOrThrow
        val scope = rememberCoroutineScope()
        var jiraStatus by remember { mutableStateOf<JiraStatus>(JiraStatus.Idle) }
        
        // Simple DI
        val api = remember { BacklogApi() }

        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Generated Backlog Item") },
                    navigationIcon = {
                        IconButton(onClick = { navigator.pop() }) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                        }
                    }
                )
            }
        ) { padding ->
            LazyColumn(
                modifier = Modifier.padding(padding).fillMaxSize().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // ... (Previous cards remain same) ...
                item {
                    PriorityCard(response.priorityScore, response.moscowPriority)
                }

                item {
                    QualityScoreCard(response.qualityScore)
                }

                if (response.validationWarnings.isNotEmpty()) {
                    item {
                        WarningCard(response.validationWarnings)
                    }
                }

                item {
                    Text("Summary", style = MaterialTheme.typography.titleLarge)
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(response.summary, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(response.userStory, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }

                if (response.researchSummary.trends.isNotEmpty() || response.researchSummary.competitorFeatures.isNotEmpty()) {
                    item {
                        Text("Research Summary", style = MaterialTheme.typography.titleLarge)
                    }

                    items(response.researchSummary.trends) { trend ->
                        BulletRow(trend)
                    }

                    items(response.researchSummary.competitorFeatures) { feature ->
                        BulletRow("Competitor: $feature")
                    }

                    items(response.researchSummary.differentiators) { diff ->
                        BulletRow("Differentiator: $diff")
                    }
                }

                item {
                    Text("Acceptance Criteria", style = MaterialTheme.typography.titleLarge)
                }
                
                items(response.acceptanceCriteria) { criteria ->
                    Row(verticalAlignment = Alignment.Top) {
                        Icon(Icons.Default.Check, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(criteria, style = MaterialTheme.typography.bodyMedium)
                    }
                }

                if (response.nonFunctionalReqs.isNotEmpty()) {
                    item {
                        Text("Non-functional Requirements", style = MaterialTheme.typography.titleLarge)
                    }
                    items(response.nonFunctionalReqs) { req ->
                        BulletRow(req)
                    }
                }

                if (response.metrics.isNotEmpty()) {
                    item {
                        Text("Success Metrics", style = MaterialTheme.typography.titleLarge)
                    }
                    items(response.metrics) { metric ->
                        BulletRow(metric)
                    }
                }

                if (response.risks.isNotEmpty()) {
                    item {
                        Text("Risks", style = MaterialTheme.typography.titleLarge)
                    }
                    items(response.risks) { risk ->
                        BulletRow(risk)
                    }
                }

                if (response.rolloutPlan.isNotEmpty()) {
                    item {
                        Text("Rollout Plan", style = MaterialTheme.typography.titleLarge)
                    }
                    items(response.rolloutPlan) { step ->
                        BulletRow(step)
                    }
                }
                
                if (response.subTasks.isNotEmpty()) {
                    item {
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.List, contentDescription = null, tint = MaterialTheme.colorScheme.secondary)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Technical Tasks (Decomposition)", style = MaterialTheme.typography.titleLarge)
                        }
                    }
                    
                    items(response.subTasks) { task ->
                        Card(
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Text(task.title, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                                Text(task.description, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
                
                item {
                    Spacer(modifier = Modifier.height(24.dp))
                    
                    val buttonColor = when (jiraStatus) {
                        is JiraStatus.Success -> Color(0xFF4CAF50) // Green
                        is JiraStatus.Error -> MaterialTheme.colorScheme.error
                        else -> MaterialTheme.colorScheme.primary
                    }
                    
                    Button(
                        onClick = {
                            if (jiraStatus !is JiraStatus.Success) {
                                scope.launch {
                                    jiraStatus = JiraStatus.Syncing
                                    try {
                                        val syncResponse = api.syncToJiraV2(
                                            JiraSyncRequestV2(
                                                summary = response.summary,
                                                description = response.description,
                                                issueType = "Story",
                                                priority = response.moscowPriority
                                            )
                                        )
                                        jiraStatus = JiraStatus.Success(syncResponse.jiraKey)
                                    } catch (e: Exception) {
                                        jiraStatus = JiraStatus.Error(e.message ?: "Unknown error")
                                    }
                                }
                            }
                        },
                        enabled = jiraStatus !is JiraStatus.Syncing && jiraStatus !is JiraStatus.Success,
                        colors = ButtonDefaults.buttonColors(containerColor = buttonColor),
                        modifier = Modifier.fillMaxWidth().height(50.dp)
                    ) {
                        when (val status = jiraStatus) {
                            is JiraStatus.Syncing -> {
                                CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Syncing...")
                            }
                            is JiraStatus.Success -> {
                                Icon(Icons.Default.Check, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Synced: ${status.key}")
                            }
                            is JiraStatus.Error -> {
                                Icon(Icons.Default.Close, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Retry Sync")
                            }
                            is JiraStatus.Idle -> {
                                Text("Sync to JIRA")
                            }
                        }
                    }
                    
                    if (jiraStatus is JiraStatus.Error) {
                        Text(
                            text = (jiraStatus as JiraStatus.Error).message,
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(top = 8.dp)
                        )
                    }
                }
            }
        }
    }
    
    @Composable
    fun PriorityCard(score: Double, moscow: String) {
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.secondaryContainer
            ),
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier.padding(16.dp).fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("Priority Score", style = MaterialTheme.typography.labelMedium)
                    Text(score.toString(), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                }
                Surface(
                    shape = MaterialTheme.shapes.small,
                    color = MaterialTheme.colorScheme.primary
                ) {
                    Text(
                        moscow,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        color = MaterialTheme.colorScheme.onPrimary,
                        style = MaterialTheme.typography.labelLarge
                    )
                }
            }
        }
    }
    
    @Composable
    fun WarningCard(warnings: List<String>) {
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.errorContainer
            ),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Quality Warnings", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.error)
                }
                Spacer(modifier = Modifier.height(8.dp))
                warnings.forEach { warning ->
                    Text("• $warning", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onErrorContainer)
                }
            }
        }
    }

    @Composable
    fun QualityScoreCard(score: Double) {
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.tertiaryContainer
            ),
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier.padding(16.dp).fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Quality Score", style = MaterialTheme.typography.labelMedium)
                Text(score.toInt().toString(), style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            }
        }
    }

    @Composable
    fun BulletRow(text: String) {
        Row(verticalAlignment = Alignment.Top) {
            Icon(Icons.Default.Check, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(18.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text(text, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
