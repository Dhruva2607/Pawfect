package com.pawfect.app.ui.screens.shelter

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
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
fun ShelterApplicationsScreen(
    onOpenApplication: (String) -> Unit,
    viewModel: ShelterApplicationsViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val filters = listOf(null to "All", "apply" to "New", "review" to "In Review", "adopt" to "Adopted", "rejected" to "Rejected")

    LaunchedEffect(Unit) { viewModel.loadApplications() }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Applications", fontWeight = FontWeight.Bold) }) }
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            LazyRow(
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(filters) { (key, label) ->
                    FilterChip(
                        selected = uiState.selectedStatus == key,
                        onClick = { viewModel.loadApplications(key) },
                        label = { Text(label) }
                    )
                }
            }

            if (uiState.isLoading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (uiState.applications.isEmpty()) {
                Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                    Text("No applications in this stage.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(uiState.applications) { app ->
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { onOpenApplication(app.id) }
                        ) {
                            Row(
                                modifier = Modifier.padding(14.dp).fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text(app.applicantName, fontWeight = FontWeight.Bold)
                                    Text(
                                        "Pet: ${app.petName ?: app.petId}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                    Text(
                                        "Stage: ${app.stageStatus.uppercase()}",
                                        style = MaterialTheme.typography.labelMedium,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                                app.compatibilityScore?.let { score ->
                                    AssistChip(onClick = { onOpenApplication(app.id) }, label = { Text("$score% match") })
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
