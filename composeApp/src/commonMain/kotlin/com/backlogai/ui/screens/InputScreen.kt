package com.backlogai.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import cafe.adriel.voyager.core.model.ScreenModel
import cafe.adriel.voyager.core.model.screenModelScope
import cafe.adriel.voyager.core.screen.Screen
import cafe.adriel.voyager.navigator.LocalNavigator
import cafe.adriel.voyager.navigator.currentOrThrow
import com.backlogai.shared.models.BacklogItemCreate
import com.backlogai.shared.models.PillarScores
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

    fun generateBacklogItem(
        title: String,
        description: String,
        pillarScores: PillarScores,
        onSuccess: (com.backlogai.shared.models.BacklogItemResponse) -> Unit
    ) {
        screenModelScope.launch {
            _isLoading.value = true
            _errorMessage.value = null
            try {
                // Use a valid UUID for project_id to satisfy backend validation
                val response = api.generateBacklogItem(request = BacklogItemCreate(
                    projectId = "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
                    title = title,
                    description = description,
                    pillarScores = pillarScores
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
        
        var title by remember { mutableStateOf("") }
        var description by remember { mutableStateOf("") }
        
        // Pillars State
        var userValue by remember { mutableStateOf(5f) }
        var commercialImpact by remember { mutableStateOf(5f) }
        var strategicHorizon by remember { mutableStateOf(5f) }
        var competitivePositioning by remember { mutableStateOf(5f) }
        var technicalReality by remember { mutableStateOf(5f) }
        
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
            topBar = {
                TopAppBar(
                    title = { Text("BackLogAI") },
                    actions = {
                        Box(
                            modifier = Modifier
                                .padding(end = 8.dp)
                                .clip(MaterialTheme.shapes.small)
                                .clickable { screenModel.checkServerStatus() }
                                .padding(8.dp) // Touch target padding
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(
                                    modifier = Modifier
                                        .size(12.dp)
                                        .clip(CircleShape)
                                        .background(if (serverStatus) Color.Green else Color.Red)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    if (serverStatus) "Online" else "Offline", 
                                    style = MaterialTheme.typography.labelSmall
                                )
                            }
                        }
                    }
                )
            }
        ) { padding ->
            Box(modifier = Modifier.fillMaxSize()) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(16.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Text("Feature Context", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            OutlinedTextField(
                                value = title,
                                onValueChange = { title = it },
                                label = { Text("Feature Title") },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                                enabled = !isLoading
                            )

                            OutlinedTextField(
                                value = description,
                                onValueChange = { description = it },
                                label = { Text("Description / Context") },
                                modifier = Modifier.fillMaxWidth(),
                                minLines = 3,
                                enabled = !isLoading
                            )
                        }
                    }
                    
                    Text("Strategic Pillars (0-10)", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 8.dp))
                    
                    PillarSlider("User Value", userValue, Icons.Default.Star) { userValue = it }
                    PillarSlider("Commercial Impact", commercialImpact, Icons.Default.Info) { commercialImpact = it }
                    PillarSlider("Strategic Horizon", strategicHorizon, Icons.Default.Info) { strategicHorizon = it }
                    PillarSlider("Competitive Positioning", competitivePositioning, Icons.Default.Info) { competitivePositioning = it }
                    PillarSlider("Technical Reality", technicalReality, Icons.Default.Info) { technicalReality = it }
                    
                    Spacer(modifier = Modifier.height(32.dp))
                }
                
                // Floating Action Button Style for Generation
                Button(
                    onClick = {
                        screenModel.generateBacklogItem(
                            title, 
                            description,
                            PillarScores(
                                userValue.toDouble(),
                                commercialImpact.toDouble(),
                                strategicHorizon.toDouble(),
                                competitivePositioning.toDouble(),
                                technicalReality.toDouble()
                            ),
                            onSuccess = { response ->
                                navigator.push(ResultScreen(response))
                            }
                        )
                    },
                    enabled = !isLoading && title.isNotBlank() && description.isNotBlank(),
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
    }
    
    @Composable
    fun PillarSlider(label: String, value: Float, icon: ImageVector, onValueChange: (Float) -> Unit) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp), tint = MaterialTheme.colorScheme.primary)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(label, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
                    }
                    Text(
                        value.toInt().toString(), 
                        style = MaterialTheme.typography.bodyLarge, 
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
                Slider(
                    value = value,
                    onValueChange = onValueChange,
                    valueRange = 0f..10f,
                    steps = 9,
                    modifier = Modifier.height(24.dp)
                )
            }
        }
    }
}
