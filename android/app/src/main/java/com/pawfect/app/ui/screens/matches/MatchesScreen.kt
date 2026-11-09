package com.pawfect.app.ui.screens.matches

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.ui.components.CircularMatchGauge
import com.pawfect.app.ui.theme.AccentCoral
import com.pawfect.app.ui.theme.BackgroundWarm
import com.pawfect.app.ui.theme.MatchGreen
import com.pawfect.app.ui.theme.SurfaceWarm
import com.pawfect.app.ui.viewmodel.MatchesViewModel

/**
 * Screen 4: Your Perfect Match!
 * [FROM MARKDOWN: Phase 5 - Screen 4]
 * Circular match score gauge (e.g., 96%), lifestyle checkmarks, pet hero photo, favorite heart toggle,
 * "Why Buddy?" explanation summary, and direct "Adopt Me" / "Learn More" CTAs.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MatchesScreen(
    onSelectPet: (String) -> Unit,
    onApply: (String) -> Unit,
    onStartChat: () -> Unit,
    savedOnly: Boolean = false,
    viewModel: MatchesViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    LaunchedEffect(savedOnly) { viewModel.loadMatches(savedOnly) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        if (savedOnly) "Saved pets"
                        else if (uiState.evaluationsByPetId.isNotEmpty()) "Your AI matches" else "Meet the pets",
                        fontWeight = FontWeight.Bold
                    )
                },
                actions = {
                    IconButton(onClick = { viewModel.loadMatches(savedOnly) }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = SurfaceWarm)
            )
        },
        containerColor = BackgroundWarm
    ) { paddingValues ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (uiState.error != null) {
            Column(
                Modifier.fillMaxSize().padding(paddingValues).padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(uiState.error ?: "Something went wrong", textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                Spacer(Modifier.height(12.dp))
                Button(onClick = { viewModel.loadMatches(savedOnly) }) { Text("Try again") }
            }
        } else {
            val topPet = uiState.topMatch

            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (topPet != null) {
                    item {
                        Spacer(modifier = Modifier.height(4.dp))
                        HeroMatchCard(
                            pet = topPet,
                            matchScore = uiState.evaluationsByPetId[topPet.id]?.compatibilityScore,
                            isFavorited = topPet.id in uiState.savedPetIds,
                            onToggleFavorite = { viewModel.toggleFavorite(topPet.id) },
                            onLearnMore = { onSelectPet(topPet.id) },
                            onAdoptMe = { onApply(topPet.id) }
                        )
                    }

                    item {
                        Text(
                            text = if (savedOnly) "Your saved companions"
                            else if (uiState.evaluationsByPetId.isNotEmpty()) "More matches for you"
                            else "More companions",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(top = 8.dp, bottom = 4.dp)
                        )
                    }

                    items(uiState.otherMatches) { pet ->
                        CompactPetCard(
                            pet = pet,
                            matchScore = uiState.evaluationsByPetId[pet.id]?.compatibilityScore,
                            isFavorited = pet.id in uiState.savedPetIds,
                            onToggleFavorite = { viewModel.toggleFavorite(pet.id) },
                            onClick = { onSelectPet(pet.id) }
                        )
                    }
                } else {
                    item {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 48.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(
                                    if (savedOnly) "No saved pets yet" else "No pets to show right now",
                                    style = MaterialTheme.typography.titleMedium
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    if (savedOnly) "Tap the heart on a pet profile to save it here."
                                    else "Try refreshing or chat with our AI counselor to find a thoughtful match."
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Button(onClick = onStartChat) {
                                    Text(if (savedOnly) "Find a companion" else "Start a conversation")
                                }
                            }
                        }
                    }
                }

                item {
                    Spacer(modifier = Modifier.height(16.dp))
                }
            }
        }
    }
}

@Composable
fun HeroMatchCard(
    pet: PetDto,
    matchScore: Int?,
    isFavorited: Boolean,
    onToggleFavorite: () -> Unit,
    onLearnMore: () -> Unit,
    onAdoptMe: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = SurfaceWarm),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp)
    ) {
        Column {
            // Pet Hero Photo + Heart Toggle + Match Gauge overlay
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(240.dp)
            ) {
                AsyncImage(
                    model = pet.photoUrl,
                    contentDescription = pet.name,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )

                // Favorite heart toggle
                IconButton(
                    onClick = onToggleFavorite,
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(12.dp)
                        .background(Color.White.copy(alpha = 0.85f), shape = CircleShape)
                        .size(40.dp)
                ) {
                    Icon(
                        imageVector = if (isFavorited) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                        contentDescription = "Favorite",
                        tint = if (isFavorited) AccentCoral else Color.Gray
                    )
                }

                // Circular Match Score Gauge [FROM MARKDOWN: Screen 4 - e.g. 96%]
                if (matchScore != null) {
                    Surface(
                        shape = CircleShape,
                        color = Color.White.copy(alpha = 0.95f),
                        modifier = Modifier.align(Alignment.BottomStart).padding(12.dp)
                    ) {
                        CircularMatchGauge(
                            score = matchScore,
                            size = 72.dp,
                            strokeWidth = 6.dp
                        )
                    }
                }
            }

            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = pet.name,
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "${pet.breed} • ${pet.ageMonths / 12} yrs old • ${pet.gender}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Lifestyle Checkmarks [FROM MARKDOWN: Screen 4]
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (matchScore != null) LifestyleCheckItem(text = "AI compatibility: $matchScore%")
                    LifestyleCheckItem(text = "Energy level: ${pet.energyLevel}/5")
                    if (pet.goodWithKids) LifestyleCheckItem(text = "Safe & affectionate with children")
                    if (pet.goodWithOtherPets) LifestyleCheckItem(text = "Socialized with other pets")
                    LifestyleCheckItem(text = "Suitable for ${pet.housingRequirement.replace('_', ' ')}")
                }

                Spacer(modifier = Modifier.height(14.dp))

                // "Why Buddy?" Explanation Summary [FROM MARKDOWN: Screen 4]
                Surface(
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "Why ${pet.name}?",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = pet.bioText,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Direct "Adopt Me" / "Learn More" CTAs [FROM MARKDOWN: Screen 4]
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedButton(
                        onClick = onLearnMore,
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp)
                    ) {
                        Text("Learn More")
                    }

                    Button(
                        onClick = onAdoptMe,
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Text("Adopt Me 🐾")
                    }
                }
            }
        }
    }
}

@Composable
fun LifestyleCheckItem(text: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = null,
            tint = MatchGreen,
            modifier = Modifier.size(18.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(text = text, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun CompactPetCard(
    pet: PetDto,
    matchScore: Int? = null,
    isFavorited: Boolean,
    onToggleFavorite: () -> Unit,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = SurfaceWarm)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            AsyncImage(
                model = pet.photoUrl,
                contentDescription = pet.name,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .size(80.dp)
                    .clip(RoundedCornerShape(12.dp))
            )

            Spacer(modifier = Modifier.width(14.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(pet.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text("${pet.breed} • ${pet.gender}", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                if (matchScore != null) {
                    Text(
                        "$matchScore% match",
                        style = MaterialTheme.typography.labelSmall,
                        color = MatchGreen,
                        fontWeight = FontWeight.Bold
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = pet.temperament.take(2).joinToString(" • "),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary
                )
            }

            IconButton(onClick = onToggleFavorite) {
                Icon(
                    imageVector = if (isFavorited) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                    contentDescription = "Favorite",
                    tint = if (isFavorited) AccentCoral else Color.Gray
                )
            }
        }
    }
}
