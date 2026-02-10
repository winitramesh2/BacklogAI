package com.backlogai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
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
import com.backlogai.shared.models.BacklogItemResponse
import com.backlogai.shared.models.JiraSyncRequest
import com.backlogai.shared.network.BacklogApi
import kotlinx.coroutines.launch

class ResultScreen(val response: BacklogItemResponse) : Screen {

    @Composable
    override fun Content() {
        val navigator = LocalNavigator.currentOrThrow
        val scope = rememberCoroutineScope()
        var syncStatus by remember { mutableStateOf<String?>(null) }
        var isSyncing by remember { mutableStateOf(false) }
        
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
                item {
                    PriorityCard(response.priorityScore, response.moscowPriority)
                }

                if (response.validationWarnings.isNotEmpty()) {
                    item {
                        WarningCard(response.validationWarnings)
                    }
                }

                item {
                    Text("User Story", style = MaterialTheme.typography.titleLarge)
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(response.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(response.description, style = MaterialTheme.typography.bodyMedium)
                        }
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
                
                item {
                    Spacer(modifier = Modifier.height(24.dp))
                    Button(
                        onClick = {
                            scope.launch {
                                isSyncing = true
                                try {
                                    val syncResponse = api.syncToJira(
                                        JiraSyncRequest(
                                            title = response.title,
                                            description = response.description,
                                            priority = response.moscowPriority,
                                            issueType = "Story"
                                        )
                                    )
                                    syncStatus = "Synced! Key: ${syncResponse.jiraKey}"
                                } catch (e: Exception) {
                                    syncStatus = "Sync Failed: ${e.message}"
                                } finally {
                                    isSyncing = false
                                }
                            }
                        },
                        enabled = !isSyncing && syncStatus == null,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (isSyncing) {
                            CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                        } else {
                            Text(if (syncStatus != null) "Synced to JIRA" else "Sync to JIRA")
                        }
                    }
                    
                    if (syncStatus != null) {
                        Text(
                            text = syncStatus!!,
                            color = if (syncStatus!!.startsWith("Synced")) Color.Green else Color.Red,
                            style = MaterialTheme.typography.bodyMedium,
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
}
