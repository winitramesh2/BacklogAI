package com.backlogai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import cafe.adriel.voyager.core.model.ScreenModel
import cafe.adriel.voyager.core.model.coroutineScope
import cafe.adriel.voyager.core.screen.Screen
import cafe.adriel.voyager.koin.getScreenModel
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

    fun generateBacklogItem(
        title: String,
        description: String,
        pillarScores: PillarScores,
        onSuccess: (com.backlogai.shared.models.BacklogItemResponse) -> Unit,
        onError: (String) -> Unit
    ) {
        coroutineScope.launch {
            _isLoading.value = true
            try {
                val request = BacklogItemCreate(
                    projectId = "default-project-id", // TODO: Real Project ID
                    title = title,
                    description = description,
                    pillarScores = pillarScores
                )
                val response = api.generateBacklogItem(request)
                onSuccess(response)
            } catch (e: Exception) {
                onError(e.message ?: "Unknown error")
            } finally {
                _isLoading.value = false
            }
        }
    }
}

class InputScreen : Screen {
    @Composable
    override fun Content() {
        val navigator = LocalNavigator.currentOrThrow
        // In real app use Koin for DI, here simple instantiation or remember
        val screenModel = remember { InputScreenModel() }
        
        var title by remember { mutableStateOf("") }
        var description by remember { mutableStateOf("") }
        
        // Pillars State
        var userValue by remember { mutableStateOf(5f) }
        var commercialImpact by remember { mutableStateOf(5f) }
        var strategicHorizon by remember { mutableStateOf(5f) }
        var competitivePositioning by remember { mutableStateOf(5f) }
        var technicalReality by remember { mutableStateOf(5f) }
        
        val isLoading by screenModel.isLoading.collectAsState()
        val scrollState = rememberScrollState()

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text("Create Backlog Item", style = MaterialTheme.typography.headlineMedium)

            OutlinedTextField(
                value = title,
                onValueChange = { title = it },
                label = { Text("Feature Title") },
                modifier = Modifier.fillMaxWidth()
            )

            OutlinedTextField(
                value = description,
                onValueChange = { description = it },
                label = { Text("Description / Context") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3
            )
            
            HorizontalDivider()
            Text("Strategic Pillars (0-10)", style = MaterialTheme.typography.titleMedium)
            
            PillarSlider("User Value", userValue) { userValue = it }
            PillarSlider("Commercial Impact", commercialImpact) { commercialImpact = it }
            PillarSlider("Strategic Horizon", strategicHorizon) { strategicHorizon = it }
            PillarSlider("Competitive Positioning", competitivePositioning) { competitivePositioning = it }
            PillarSlider("Technical Reality", technicalReality) { technicalReality = it }
            
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
                        },
                        onError = { error ->
                            println("Error: $error") // Handle UI error properly in real app
                        }
                    )
                },
                enabled = !isLoading && title.isNotBlank() && description.isNotBlank(),
                modifier = Modifier.fillMaxWidth().height(50.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                } else {
                    Text("Generate Backlog Item")
                }
            }
        }
    }
    
    @Composable
    fun PillarSlider(label: String, value: Float, onValueChange: (Float) -> Unit) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(label, style = MaterialTheme.typography.bodyMedium)
                Text(value.toInt().toString(), fontWeight = FontWeight.Bold)
            }
            Slider(
                value = value,
                onValueChange = onValueChange,
                valueRange = 0f..10f,
                steps = 9
            )
        }
    }
}
