package com.backlogai.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import cafe.adriel.voyager.core.model.ScreenModel
import cafe.adriel.voyager.core.model.screenModelScope
import cafe.adriel.voyager.core.screen.Screen
import cafe.adriel.voyager.navigator.LocalNavigator
import cafe.adriel.voyager.navigator.currentOrThrow
import com.backlogai.shared.models.BacklogItemGenerateV2Request
import com.backlogai.shared.models.BacklogItemGenerateV2Response
import com.backlogai.shared.network.BacklogApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class InputScreenModel : ScreenModel {
    private val api = BacklogApi()

    private val _isLoading = MutableStateFlow(false)
    val isLoading = _isLoading.asStateFlow()
    
    private val _serverStatus = MutableStateFlow(false)
    val serverStatus = _serverStatus.asStateFlow()
    
    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage = _errorMessage.asStateFlow()

    init {
        checkServerStatus()
    }

    fun checkServerStatus() {
        screenModelScope.launch {
            _serverStatus.value = api.healthCheck()
        }
    }
    
    fun clearError() {
        _errorMessage.value = null
    }

    fun generateBacklogItemV2(
        context: String,
        objective: String,
        targetUser: String,
        marketSegment: String,
        constraints: String,
        successMetrics: String,
        competitors: List<String>,
        onSuccess: (BacklogItemGenerateV2Response) -> Unit
    ) {
        screenModelScope.launch {
            _isLoading.value = true
            _errorMessage.value = null
            try {
                val response = api.generateBacklogItemV2(request = BacklogItemGenerateV2Request(
                    projectId = "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    context = context,
                    objective = objective,
                    targetUser = targetUser.ifBlank { null },
                    marketSegment = marketSegment.ifBlank { null },
                    constraints = constraints.ifBlank { null },
                    successMetrics = successMetrics.ifBlank { null },
                    competitorsOptional = competitors
                ))
                onSuccess(response)
            } catch (e: Exception) {
                _errorMessage.value = "Failed to generate: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }
}

class InputScreen : Screen {
    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    override fun Content() {
        val navigator = LocalNavigator.currentOrThrow
        val screenModel = remember { InputScreenModel() }
        val snackbarHostState = remember { SnackbarHostState() }
        var infoDialogTitle by remember { mutableStateOf("") }
        var infoDialogBody by remember { mutableStateOf("") }
        var showInfoDialog by remember { mutableStateOf(false) }
        
        var context by remember { mutableStateOf("") }
        var objective by remember { mutableStateOf("") }
        var targetUser by remember { mutableStateOf("") }
        var marketSegment by remember { mutableStateOf("") }
        var constraints by remember { mutableStateOf("") }
        var successMetrics by remember { mutableStateOf("") }
        var competitors by remember { mutableStateOf("") }
        
        val isLoading by screenModel.isLoading.collectAsState()
        val serverStatus by screenModel.serverStatus.collectAsState()
        val errorMessage by screenModel.errorMessage.collectAsState()
        
        // Handle Error Side Effect
        LaunchedEffect(errorMessage) {
            errorMessage?.let {
                snackbarHostState.showSnackbar(it)
                screenModel.clearError()
            }
        }

        Scaffold(
            snackbarHost = { SnackbarHost(snackbarHostState) },
            topBar = {}
        ) { padding ->
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        Brush.verticalGradient(
                            colors = listOf(
                                MaterialTheme.colorScheme.primary.copy(alpha = 0.12f),
                                MaterialTheme.colorScheme.background
                            )
                        )
                    )
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(16.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    HeaderBlock(
                        serverStatus = serverStatus,
                        onRefresh = { screenModel.checkServerStatus() }
                    )

                    SectionCard(
                        title = "Define the product need",
                        subtitle = "Give context and objective. The AI fills the rest.",
                        onInfoClick = {
                            infoDialogTitle = "Define the product need"
                            infoDialogBody = "Share the background and the outcome you want.\n\nExample context: We help PMs convert raw customer feedback into prioritized JIRA stories for B2B SaaS teams.\nExample objective: Increase story clarity so PMs spend 40% less time editing before JIRA sync."
                            showInfoDialog = true
                        }
                    ) {
                        OutlinedTextField(
                            value = context,
                            onValueChange = { context = it },
                            label = { Text("Context") },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 4,
                            enabled = !isLoading
                        )

                        OutlinedTextField(
                            value = objective,
                            onValueChange = { objective = it },
                            label = { Text("Objective") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            enabled = !isLoading
                        )
                    }

                    SectionCard(
                        title = "Add optional signals",
                        subtitle = "Helps the AI choose better benchmarks and metrics.",
                        onInfoClick = {
                            infoDialogTitle = "Add optional signals"
                            infoDialogBody = "These inputs improve research and prioritization.\n\nExample target user: Product Manager.\nExample segment: B2B SaaS.\nExample constraints: Must work with existing JIRA sync.\nExample success metrics: Reduce edits before sync by 40%.\nExample competitors: Linear, Productboard."
                            showInfoDialog = true
                        }
                    ) {
                        OutlinedTextField(
                            value = targetUser,
                            onValueChange = { targetUser = it },
                            label = { Text("Target User") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            enabled = !isLoading
                        )

                        OutlinedTextField(
                            value = marketSegment,
                            onValueChange = { marketSegment = it },
                            label = { Text("Market Segment") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            enabled = !isLoading
                        )

                        OutlinedTextField(
                            value = constraints,
                            onValueChange = { constraints = it },
                            label = { Text("Constraints") },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 2,
                            enabled = !isLoading
                        )

                        OutlinedTextField(
                            value = successMetrics,
                            onValueChange = { successMetrics = it },
                            label = { Text("Success Metrics") },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 2,
                            enabled = !isLoading
                        )

                        OutlinedTextField(
                            value = competitors,
                            onValueChange = { competitors = it },
                            label = { Text("Competitors (comma-separated)") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            enabled = !isLoading
                        )
                    }

                    Spacer(modifier = Modifier.height(80.dp))
                }
                
                // Floating Action Button Style for Generation
                Button(
                    onClick = {
                        val competitorList = competitors
                            .split(",")
                            .map { it.trim() }
                            .filter { it.isNotBlank() }
                        screenModel.generateBacklogItemV2(
                            context,
                            objective,
                            targetUser,
                            marketSegment,
                            constraints,
                            successMetrics,
                            competitorList,
                            onSuccess = { response ->
                                navigator.push(ResultScreen(response))
                            }
                        )
                    },
                    enabled = !isLoading && context.isNotBlank() && objective.isNotBlank(),
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(16.dp)
                        .fillMaxWidth()
                        .height(56.dp)
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                    } else {
                        Text("Generate Backlog Item", style = MaterialTheme.typography.titleMedium)
                    }
                }
                
                // Full Screen Loading Overlay
                if (isLoading) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color.Black.copy(alpha = 0.3f))
                            .clickable(enabled = false) {}, // Block interaction
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator()
                    }
                }
            }
        }

        if (showInfoDialog) {
            AlertDialog(
                onDismissRequest = { showInfoDialog = false },
                title = { Text(infoDialogTitle) },
                text = { Text(infoDialogBody) },
                confirmButton = {
                    TextButton(onClick = { showInfoDialog = false }) {
                        Text("Close")
                    }
                }
            )
        }
    }

    @Composable
    private fun HeaderBlock(serverStatus: Boolean, onRefresh: () -> Unit) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(MaterialTheme.shapes.large)
                .background(
                    Brush.horizontalGradient(
                        colors = listOf(
                            MaterialTheme.colorScheme.primary,
                            MaterialTheme.colorScheme.tertiary
                        )
                    )
                )
                .padding(20.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column {
                    Text("BacklogAI", style = MaterialTheme.typography.displayLarge, color = MaterialTheme.colorScheme.onPrimary)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Turn product context into JIRA-ready stories",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.9f)
                    )
                }
                Box(
                    modifier = Modifier
                        .clip(MaterialTheme.shapes.small)
                        .background(MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.12f))
                        .clickable { onRefresh() }
                        .padding(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .background(if (serverStatus) Color(0xFFB8F7D4) else Color(0xFFFFB4A6), shape = MaterialTheme.shapes.small)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            if (serverStatus) "Online" else "Offline",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                    }
                }
            }
        }
    }

    @Composable
    private fun SectionCard(
        title: String,
        subtitle: String,
        onInfoClick: (() -> Unit)? = null,
        content: @Composable ColumnScope.() -> Unit
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(title, style = MaterialTheme.typography.titleLarge)
                    if (onInfoClick != null) {
                        IconButton(
                            onClick = onInfoClick,
                            modifier = Modifier.size(28.dp)
                        ) {
                            Icon(
                                Icons.Default.Info,
                                contentDescription = "$title info",
                                tint = MaterialTheme.colorScheme.secondary,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
                Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                content()
            }
        }
    }
}
