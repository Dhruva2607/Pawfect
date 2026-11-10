package com.pawfect.app.ui.screens.matches

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.ui.components.CircularMatchGauge
import com.pawfect.app.ui.components.PawEmptyState
import com.pawfect.app.ui.components.PawErrorState
import com.pawfect.app.ui.components.PawLogo
import com.pawfect.app.ui.components.PawSectionHeader
import com.pawfect.app.ui.components.PawSkeleton
import com.pawfect.app.ui.components.PawTag
import com.pawfect.app.ui.components.PetImage
import com.pawfect.app.ui.theme.AccentCoral
import com.pawfect.app.ui.theme.MatchGreen
import com.pawfect.app.ui.viewmodel.MatchesViewModel

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
    val snackbarHostState = remember { SnackbarHostState() }
    LaunchedEffect(savedOnly) { viewModel.loadMatches(savedOnly) }
    LaunchedEffect(uiState.actionError) {
        uiState.actionError?.let { message ->
            snackbarHostState.showSnackbar(message)
            viewModel.clearActionError()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                            PawLogo(Modifier.padding(7.dp).size(18.dp))
                        }
                        Spacer(Modifier.width(10.dp))
                        Text(
                            if (savedOnly) "Saved pets"
                            else if (uiState.evaluationsByPetId.isNotEmpty()) "Your AI matches" else "Meet the pets",
                            style = MaterialTheme.typography.headlineSmall
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadMatches(savedOnly) }) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        when {
            uiState.isLoading -> MatchesSkeleton(Modifier.fillMaxSize().padding(paddingValues))
            uiState.error != null -> PawErrorState(
                message = uiState.error.orEmpty(),
                onRetry = { viewModel.loadMatches(savedOnly) },
                modifier = Modifier.fillMaxSize().padding(paddingValues)
            )
            else -> {
                val topPet = uiState.topMatch
                if (topPet == null) {
                    PawEmptyState(
                        title = if (savedOnly) "No saved pets yet" else "No pets to show right now",
                        message = if (savedOnly) {
                            "Tap the heart on a pet profile to save it here."
                        } else {
                            "Try refreshing or chat with our AI counselor to find a thoughtful match."
                        },
                        actionLabel = if (savedOnly) "Find a companion" else "Start a conversation",
                        onAction = onStartChat,
                        modifier = Modifier.fillMaxSize().padding(paddingValues)
                    )
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize().padding(paddingValues),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(
                            start = 16.dp, end = 16.dp, top = 4.dp, bottom = 24.dp
                        ),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        item {
                            HeroMatchCard(
                                pet = topPet,
                                matchScore = uiState.evaluationsByPetId[topPet.id]?.compatibilityScore,
                                isFavorited = topPet.id in uiState.savedPetIds,
                                onToggleFavorite = { viewModel.toggleFavorite(topPet.id) },
                                onLearnMore = { onSelectPet(topPet.id) },
                                onAdoptMe = { onApply(topPet.id) }
                            )
                        }
                        if (uiState.otherMatches.isNotEmpty()) {
                            item {
                                PawSectionHeader(
                                    title = if (savedOnly) "Your saved companions"
                                    else if (uiState.evaluationsByPetId.isNotEmpty()) "More matches for you"
                                    else "More companions"
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
                        }
                    }
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
        shape = MaterialTheme.shapes.extraLarge,
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column {
            Box {
                PetImage(
                    url = pet.photoUrl,
                    contentDescription = pet.name,
                    modifier = Modifier.fillMaxWidth().height(250.dp)
                )
                Box(
                    Modifier
                        .matchParentSize()
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(Color.Transparent, Color(0xCC0E1A14))
                            )
                        )
                )
                IconButton(
                    onClick = onToggleFavorite,
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(12.dp)
                        .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.9f), CircleShape)
                        .size(40.dp)
                ) {
                    Icon(
                        imageVector = if (isFavorited) Icons.Filled.Favorite else Icons.Filled.FavoriteBorder,
                        contentDescription = "Favorite",
                        tint = if (isFavorited) AccentCoral else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Column(Modifier.align(Alignment.BottomStart).padding(16.dp)) {
                    Text(
                        pet.name,
                        style = MaterialTheme.typography.headlineMedium,
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "${pet.breed} · ${formatAge(pet.ageMonths)} old · ${pet.gender}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.85f)
                    )
                }
                if (matchScore != null) {
                    Surface(
                        shape = CircleShape,
                        color = MaterialTheme.colorScheme.surface,
                        modifier = Modifier.align(Alignment.BottomEnd).padding(12.dp)
                    ) {
                        CircularMatchGauge(score = matchScore, size = 70.dp, strokeWidth = 6.dp)
                    }
                }
            }

            Column(Modifier.padding(16.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    PawTag("Energy ${pet.energyLevel}/5")
                    if (pet.goodWithKids) PawTag("Kid-friendly")
                    if (pet.goodWithOtherPets) PawTag("Pet-friendly")
                }
                Spacer(Modifier.height(14.dp))
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (matchScore != null) LifestyleCheckItem("AI compatibility: $matchScore%")
                    LifestyleCheckItem("Suitable for ${pet.housingRequirement.replace('_', ' ')}")
                    if (pet.goodWithKids) LifestyleCheckItem("Safe and affectionate with children")
                }
                Spacer(Modifier.height(14.dp))
                Surface(
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f),
                    shape = MaterialTheme.shapes.medium,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(Modifier.padding(14.dp)) {
                        Text(
                            "Why ${pet.name}?",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(Modifier.height(4.dp))
                        Text(
                            pet.bioText,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
                Spacer(Modifier.height(16.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedButton(
                        onClick = onLearnMore,
                        modifier = Modifier.weight(1f).height(48.dp),
                        shape = MaterialTheme.shapes.medium
                    ) { Text("Learn more") }
                    Button(
                        onClick = onAdoptMe,
                        modifier = Modifier.weight(1f).height(48.dp),
                        shape = MaterialTheme.shapes.medium
                    ) { Text("Apply to adopt") }
                }
            }
        }
    }
}

@Composable
fun LifestyleCheckItem(text: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            imageVector = Icons.Filled.CheckCircle,
            contentDescription = null,
            tint = MatchGreen,
            modifier = Modifier.size(18.dp)
        )
        Spacer(Modifier.width(8.dp))
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
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            PetImage(
                url = pet.photoUrl,
                contentDescription = pet.name,
                modifier = Modifier.size(84.dp).clip(RoundedCornerShape(14.dp))
            )
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(pet.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text(
                    "${pet.breed} · ${pet.gender}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                if (matchScore != null) {
                    Spacer(Modifier.height(2.dp))
                    Text(
                        "$matchScore% match",
                        style = MaterialTheme.typography.labelSmall,
                        color = MatchGreen,
                        fontWeight = FontWeight.Bold
                    )
                }
                Spacer(Modifier.height(6.dp))
                PawTag(pet.temperament.firstOrNull() ?: pet.species)
            }
            IconButton(onClick = onToggleFavorite) {
                Icon(
                    imageVector = if (isFavorited) Icons.Filled.Favorite else Icons.Filled.FavoriteBorder,
                    contentDescription = "Favorite",
                    tint = if (isFavorited) AccentCoral else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun MatchesSkeleton(modifier: Modifier = Modifier) {
    Column(modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        PawSkeleton(Modifier.fillMaxWidth().height(250.dp), MaterialTheme.shapes.extraLarge)
        PawSkeleton(Modifier.fillMaxWidth(0.55f).height(24.dp))
        repeat(3) {
            PawSkeleton(Modifier.fillMaxWidth().height(96.dp), MaterialTheme.shapes.large)
        }
    }
}

private fun formatAge(ageMonths: Int): String =
    if (ageMonths >= 12) {
        val years = ageMonths / 12
        val months = ageMonths % 12
        if (months == 0) "$years yr" else "$years yr $months mo"
    } else {
        "$ageMonths mo"
    }
