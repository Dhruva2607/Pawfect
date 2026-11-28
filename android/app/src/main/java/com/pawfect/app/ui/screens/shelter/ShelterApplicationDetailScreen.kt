package com.pawfect.app.ui.screens.shelter

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.ui.viewmodel.ShelterApplicationsViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShelterApplicationDetailScreen(
    appId: String,
    onBack: () -> Unit,
    viewModel: ShelterApplicationsViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var noteText by remember { mutableStateOf("") }

    LaunchedEffect(appId) { viewModel.loadDetail(appId) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Application Review", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        val app = uiState.selectedApplication
        if (uiState.isLoading || app == null) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
            return@Scaffold
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(app.applicantName, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text("Applying for: ${app.petName ?: app.petId}", style = MaterialTheme.typography.titleSmall)
                    Text("Current Stage: ${app.stageStatus.uppercase()}", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
                    app.compatibilityScore?.let { score ->
                        Text("Compatibility Score: $score%", fontWeight = FontWeight.SemiBold)
                    }
                    app.compatibilityReasoning?.let { reason ->
                        Text(reason, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }

            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Applicant Details", fontWeight = FontWeight.SemiBold)
                    Text("Email: ${app.applicantEmail}")
                    app.applicantPhone?.let { Text("Phone: $it") }
                    app.housingDetails?.let { Text("Housing: $it") }
                    app.householdMembers?.let { Text("Household: $it") }
                    app.notes?.let { Text("Applicant Notes: $it") }
                }
            }

            if (app.stageHistory.isNotEmpty()) {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("Stage History", fontWeight = FontWeight.SemiBold)
                        app.stageHistory.forEach { entry ->
                            Text(
                                "• ${entry.stage.uppercase()}${entry.note?.let { " — $it" } ?: ""}",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }
            }

            if (app.stageStatus == "apply" || app.stageStatus == "review") {
                OutlinedTextField(
                    value = noteText,
                    onValueChange = { noteText = it },
                    label = { Text("Note to applicant (optional)") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2
                )

                if (!uiState.error.isNullOrBlank()) {
                    Text(uiState.error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }

                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedButton(
                        onClick = { viewModel.updateStage(app.id, "rejected", noteText) },
                        enabled = !uiState.isUpdating,
                        modifier = Modifier.weight(1f).height(48.dp)
                    ) {
                        Text("Reject")
                    }
                    if (app.stageStatus == "apply") {
                        Button(
                            onClick = { viewModel.updateStage(app.id, "review", noteText) },
                            enabled = !uiState.isUpdating,
                            modifier = Modifier.weight(1f).height(48.dp)
                        ) {
                            Text("Move to Review")
                        }
                    } else if (app.stageStatus == "review") {
                        Button(
                            onClick = { viewModel.updateStage(app.id, "adopt", noteText) },
                            enabled = !uiState.isUpdating,
                            modifier = Modifier.weight(1f).height(48.dp)
                        ) {
                            Text("Approve Adoption")
                        }
                    }
                }
            }
        }
    }
}
