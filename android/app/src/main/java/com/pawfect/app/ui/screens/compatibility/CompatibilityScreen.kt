package com.pawfect.app.ui.screens.compatibility

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.ui.components.CircularMatchGauge
import com.pawfect.app.ui.components.PawErrorState
import com.pawfect.app.ui.components.PawLogo
import com.pawfect.app.ui.components.PawSkeleton
import com.pawfect.app.ui.components.PawTag
import com.pawfect.app.ui.theme.MatchAmber
import com.pawfect.app.ui.theme.MatchGreen
import com.pawfect.app.ui.viewmodel.CompatibilityViewModel

/**
 * Screen 6: Compatibility Analysis
 * [FROM MARKDOWN: Phase 5 - Screen 6]
 * Dedicated diagnostic screen showing high-precision gauge (e.g., 92%), bulleted Key Insights list,
 * Next Steps prompt, and "Continue ->" CTA.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CompatibilityScreen(
    petId: String,
    onBack: () -> Unit,
    onContinueToAdoption: () -> Unit,
    viewModel: CompatibilityViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(petId) {
        viewModel.evaluatePet(petId)
    }

    val eval = uiState.evaluation
    val pet = uiState.pet

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                            PawLogo(Modifier.padding(7.dp).size(18.dp))
                        }
                        Spacer(Modifier.width(10.dp))
                        Text("Compatibility", style = MaterialTheme.typography.headlineSmall)
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        bottomBar = {
            Surface(
                color = MaterialTheme.colorScheme.surface,
                shadowElevation = 10.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Button(
                    onClick = onContinueToAdoption,
                    enabled = eval != null,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                        .height(52.dp),
                    shape = MaterialTheme.shapes.medium,
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                ) {
                    Text("Continue to Adoption Process")
                    Spacer(modifier = Modifier.width(8.dp))
                    Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = null, modifier = Modifier.size(18.dp))
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        if (uiState.isLoading && eval == null) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                PawSkeleton(Modifier.fillMaxWidth().height(280.dp), MaterialTheme.shapes.extraLarge)
                PawSkeleton(Modifier.fillMaxWidth().height(120.dp), MaterialTheme.shapes.large)
                PawSkeleton(Modifier.fillMaxWidth().height(120.dp), MaterialTheme.shapes.large)
            }
        } else if (eval == null) {
            PawErrorState(
                message = uiState.error ?: "Compatibility could not be calculated.",
                onRetry = { viewModel.evaluatePet(petId) },
                modifier = Modifier.fillMaxSize().padding(paddingValues)
            )
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // High-precision circular gauge (e.g. 92%) [FROM MARKDOWN: Screen 6]
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = MaterialTheme.shapes.extraLarge,
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularMatchGauge(
                            score = eval.compatibilityScore,
                            size = 130.dp,
                            strokeWidth = 12.dp
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        Text(
                            text = "${pet?.name ?: eval.petName} & You",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )

                        Spacer(modifier = Modifier.height(6.dp))

                        Text(
                            text = eval.reasoningSummary,
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(Modifier.height(14.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            PawTag("Grounded")
                            PawTag("Explainable")
                            PawTag("Shelter data")
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Bulleted Key Insights List [FROM MARKDOWN: Screen 6]
                Text(
                    text = "Key insights",
                    style = MaterialTheme.typography.headlineSmall,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Pros
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = MaterialTheme.shapes.large,
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.CheckCircle, contentDescription = null, tint = MatchGreen, modifier = Modifier.size(20.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Why this is a strong match", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        eval.pros.forEach { pro ->
                            Row(
                                modifier = Modifier.padding(vertical = 4.dp),
                                verticalAlignment = Alignment.Top
                            ) {
                                Text("• ", color = MatchGreen, fontWeight = FontWeight.Bold)
                                Text(pro, style = MaterialTheme.typography.bodyMedium)
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Caveats
                if (eval.caveats.isNotEmpty()) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = MaterialTheme.shapes.large,
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Warning, contentDescription = null, tint = MatchAmber, modifier = Modifier.size(20.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Things to keep in mind", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            eval.caveats.forEach { caveat ->
                                Row(
                                    modifier = Modifier.padding(vertical = 4.dp),
                                    verticalAlignment = Alignment.Top
                                ) {
                                    Text("• ", color = MatchAmber, fontWeight = FontWeight.Bold)
                                    Text(caveat, style = MaterialTheme.typography.bodyMedium)
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Next Steps Prompt [FROM MARKDOWN: Screen 6]
                Surface(
                    color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f),
                    shape = MaterialTheme.shapes.medium,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(
                            text = "Next Steps",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Complete your adoption application to schedule a meet-and-greet with shelter counselors.",
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}
