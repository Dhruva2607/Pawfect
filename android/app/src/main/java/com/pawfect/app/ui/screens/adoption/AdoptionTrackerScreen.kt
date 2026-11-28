package com.pawfect.app.ui.screens.adoption

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Pets
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.data.model.AdoptionStatusResponseDto
import com.pawfect.app.ui.components.PawEmptyState
import com.pawfect.app.ui.components.PawErrorState
import com.pawfect.app.ui.components.PawSkeleton
import com.pawfect.app.ui.components.PawTag
import com.pawfect.app.ui.viewmodel.AdoptionTrackerViewModel

/**
 * Adopter-side adoption tracker.
 *
 * Lists every application the signed-in adopter has submitted, newest first,
 * with its current stage. Previously an application could only be revisited by
 * id, so it effectively vanished after a restart.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdoptionTrackerScreen(
    onBack: () -> Unit,
    onBrowsePets: () -> Unit,
    viewModel: AdoptionTrackerViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(Unit) { viewModel.load() }

    LaunchedEffect(uiState.error) {
        uiState.error?.let { snackbarHostState.showSnackbar(it) }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My applications", style = MaterialTheme.typography.titleLarge) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { paddingValues ->
        when {
            uiState.isLoading -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                        .padding(horizontal = 20.dp, vertical = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    repeat(3) { PawSkeleton(Modifier.fillMaxWidth().height(104.dp)) }
                }
            }

            uiState.isEmpty -> {
                Box(Modifier.fillMaxSize().padding(paddingValues)) {
                    PawEmptyState(
                        title = "No applications yet",
                        message = "When you apply to adopt a companion, you can follow its progress here.",
                        icon = Icons.Filled.Pets,
                        actionLabel = "Find a companion",
                        onAction = onBrowsePets,
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
            }

            uiState.applications.isEmpty() && uiState.error != null -> {
                Box(Modifier.fillMaxSize().padding(paddingValues)) {
                    PawErrorState(
                        message = uiState.error ?: "Could not load your applications.",
                        onRetry = {
                            viewModel.clearError()
                            viewModel.load()
                        },
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
            }

            else -> {
                LazyColumn(
                    modifier = Modifier.fillMaxSize().padding(paddingValues),
                    contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(uiState.applications, key = { it.applicationId }) { application ->
                        ApplicationCard(application)
                    }
                }
            }
        }
    }
}

@Composable
private fun ApplicationCard(application: AdoptionStatusResponseDto) {
    Card(
        shape = MaterialTheme.shapes.large,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(
                    shape = CircleShape,
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Icon(
                        imageVector = Icons.Filled.Pets,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(9.dp).size(18.dp)
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(
                        application.petName ?: "Companion",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Applied ${formatAppliedDate(application.submittedAt)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                StageBadge(application.stageStatus)
            }

            Spacer(Modifier.height(12.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                val score = application.compatibilityScore
                if (score != null) {
                    PawTag("$score% match")
                }
                if (!application.shelterNote.isNullOrBlank()) {
                    PawTag("Note from shelter")
                }
            }

            if (!application.shelterNote.isNullOrBlank()) {
                Spacer(Modifier.height(10.dp))
                Surface(
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f),
                    shape = MaterialTheme.shapes.medium,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = application.shelterNote!!,
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun StageBadge(stage: String) {
    val (label, container) = when (stage.lowercase()) {
        "apply" -> "Submitted" to MaterialTheme.colorScheme.secondaryContainer
        "review" -> "In review" to MaterialTheme.colorScheme.tertiaryContainer
        "adopt" -> "Adopted" to MaterialTheme.colorScheme.primaryContainer
        "rejected" -> "Not selected" to MaterialTheme.colorScheme.errorContainer
        else -> stage.replaceFirstChar { it.uppercase() } to MaterialTheme.colorScheme.surfaceVariant
    }

    Surface(shape = MaterialTheme.shapes.small, color = container) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
        )
    }
}

/** Renders an ISO-8601 timestamp as a short, locale-safe date. */
private fun formatAppliedDate(raw: String): String {
    val datePart = raw.substringBefore('T')
    if (datePart.length == 10) return datePart
    return raw.take(10)
}
