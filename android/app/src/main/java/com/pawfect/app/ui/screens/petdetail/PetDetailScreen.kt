package com.pawfect.app.ui.screens.petdetail

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import com.pawfect.app.ui.theme.AccentCoral
import com.pawfect.app.ui.theme.BackgroundWarm
import com.pawfect.app.ui.theme.SurfaceWarm
import com.pawfect.app.ui.viewmodel.PetDetailViewModel

/**
 * Screen 5: Pet Detail Screen
 * [FROM MARKDOWN: Phase 5 - Screen 5]
 * Full-bleed pet photo, age/breed/gender header, descriptive bio, temperament chips, and "Start Adoption Chat" button.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun PetDetailScreen(
    petId: String,
    onBack: () -> Unit,
    onStartAdoptionChat: () -> Unit,
    onViewCompatibility: () -> Unit,
    onApply: () -> Unit,
    viewModel: PetDetailViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(petId) {
        viewModel.loadPet(petId)
    }

    val pet = uiState.pet

    Scaffold(
        bottomBar = {
            if (pet != null) {
                Surface(
                    color = SurfaceWarm,
                    tonalElevation = 8.dp,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        OutlinedButton(
                            onClick = onViewCompatibility,
                            modifier = Modifier
                                .weight(1f)
                                .height(52.dp)
                        ) {
                            Text("My fit")
                        }

                        Button(
                            onClick = onApply,
                            modifier = Modifier
                                .weight(1.3f)
                                .height(52.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                        ) {
                            Text("Apply to adopt")
                        }
                    }
                }
            }
        },
        containerColor = BackgroundWarm
    ) { paddingValues ->
        if (uiState.isLoading && pet == null) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (pet == null) {
            Column(
                Modifier.fillMaxSize().padding(paddingValues).padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(uiState.error ?: "This pet could not be loaded.")
                Spacer(Modifier.height(12.dp))
                Button(onClick = { viewModel.loadPet(petId) }) { Text("Try again") }
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
            ) {
                // Full-bleed Pet Photo with Top Action Bar [FROM MARKDOWN: Screen 5]
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(320.dp)
                ) {
                    AsyncImage(
                        model = pet.photoUrl,
                        contentDescription = pet.name,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize()
                    )

                    // Back button
                    IconButton(
                        onClick = onBack,
                        modifier = Modifier
                            .align(Alignment.TopStart)
                            .padding(16.dp)
                            .background(Color.White.copy(alpha = 0.85f), CircleShape)
                    ) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }

                    // Favorite toggle
                    IconButton(
                        onClick = { viewModel.toggleFavorite() },
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(16.dp)
                            .background(Color.White.copy(alpha = 0.85f), CircleShape)
                    ) {
                        Icon(
                            imageVector = if (uiState.isFavorited) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                            contentDescription = "Favorite",
                            tint = if (uiState.isFavorited) AccentCoral else Color.Gray
                        )
                    }
                }

                Column(modifier = Modifier.padding(20.dp)) {
                    // Age/Breed/Gender Header [FROM MARKDOWN: Screen 5]
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = pet.name,
                                style = MaterialTheme.typography.headlineLarge,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "${pet.breed} • ${pet.gender}",
                                style = MaterialTheme.typography.titleMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = MaterialTheme.colorScheme.primaryContainer
                        ) {
                            Text(
                                text = if (pet.ageMonths >= 12) {
                                    "${pet.ageMonths / 12} yr ${pet.ageMonths % 12} mo"
                                } else {
                                    "${pet.ageMonths} months"
                                },
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                style = MaterialTheme.typography.labelMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Temperament Chips ("Active", "Family Friendly", "Good with Kids") [FROM MARKDOWN: Screen 5]
                    Text("Temperament", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        pet.temperament.forEach { tag ->
                            Surface(
                                shape = RoundedCornerShape(16.dp),
                                color = MaterialTheme.colorScheme.surfaceVariant
                            ) {
                                Text(
                                    text = tag,
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                    style = MaterialTheme.typography.labelSmall
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    // Descriptive Bio [FROM MARKDOWN: Screen 5]
                    Text("About ${pet.name}", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = pet.bioText,
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurface
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    // Exercise Needs & Habits
                    if (!pet.exerciseNeeds.isNullOrBlank()) {
                        Text("Exercise Routine", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = pet.exerciseNeeds,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                    }

                    // Quirks & Triggers
                    if (pet.quirks.isNotEmpty()) {
                        Text("Fun Quirks", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(6.dp))
                        pet.quirks.forEach { quirk ->
                            Text("• $quirk", style = MaterialTheme.typography.bodyMedium)
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                    }

                    if (pet.triggers.isNotEmpty()) {
                        Text("Known Triggers / Sensitivities", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(6.dp))
                        pet.triggers.forEach { trigger ->
                            Text("• $trigger", style = MaterialTheme.typography.bodyMedium, color = Color(0xFFDC2626))
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                    OutlinedButton(
                        onClick = onStartAdoptionChat,
                        modifier = Modifier.fillMaxWidth().height(50.dp),
                        shape = RoundedCornerShape(24.dp)
                    ) {
                        Text("Ask the AI matchmaker about ${pet.name}")
                    }

                    Spacer(modifier = Modifier.height(24.dp))
                }
            }
        }
    }
}
