package com.pawfect.app.ui.screens.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.ui.components.PawEmptyState
import com.pawfect.app.ui.components.PawErrorState
import com.pawfect.app.ui.components.PawLogo
import com.pawfect.app.ui.components.PawSectionHeader
import com.pawfect.app.ui.components.PawSkeleton
import com.pawfect.app.ui.components.PawTag
import com.pawfect.app.ui.components.PetImage
import com.pawfect.app.ui.viewmodel.HomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onViewPet: (String) -> Unit,
    onStartChat: () -> Unit,
    onViewMatches: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                            PawLogo(Modifier.padding(8.dp).size(20.dp))
                        }
                        Spacer(Modifier.width(10.dp))
                        Column {
                            Text("PawFect", style = MaterialTheme.typography.headlineSmall)
                            Text(
                                "A better way to find your best friend",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::loadPets) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh pets")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { insets ->
        when {
            state.isLoading -> HomeSkeleton(Modifier.fillMaxSize().padding(insets))
            state.error != null -> PawErrorState(
                message = state.error.orEmpty(),
                onRetry = viewModel::loadPets,
                modifier = Modifier.fillMaxSize().padding(insets)
            )
            state.pets.isEmpty() -> PawEmptyState(
                title = "No companions yet",
                message = "The shelter catalog is empty right now. Refresh in a moment.",
                actionLabel = "Refresh",
                onAction = viewModel::loadPets,
                modifier = Modifier.fillMaxSize().padding(insets)
            )
            else -> {
                val featured = state.pets.first()
                val rest = state.pets.drop(1)
                LazyColumn(
                    modifier = Modifier.fillMaxSize().padding(insets),
                    contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 4.dp, bottom = 24.dp),
                    verticalArrangement = Arrangement.spacedBy(20.dp)
                ) {
                    item { AiMatchmakerCard(onStartChat) }
                    item {
                        PawSectionHeader(
                            title = "Meet the pets",
                            subtitle = "Real companions waiting for a home",
                            actionLabel = "See all",
                            onAction = onViewMatches
                        )
                    }
                    item { FeaturedPetCard(featured, onViewPet) }
                    if (rest.isNotEmpty()) {
                        item {
                            LazyRow(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                                items(rest.take(8), key = { it.id }) { pet ->
                                    PetMiniCard(pet, onViewPet)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AiMatchmakerCard(onStartChat: () -> Unit) {
    Card(
        shape = MaterialTheme.shapes.extraLarge,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Box {
            PawLogo(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(18.dp)
                    .size(110.dp),
                tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)
            )
            Column(Modifier.padding(22.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Surface(
                        shape = CircleShape,
                        color = MaterialTheme.colorScheme.surface.copy(alpha = 0.75f)
                    ) {
                        PawLogo(Modifier.padding(7.dp).size(18.dp))
                    }
                    Spacer(Modifier.width(8.dp))
                    Text(
                        "Your AI matchmaker",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
                Spacer(Modifier.height(12.dp))
                Text("A companion who fits your life.", style = MaterialTheme.typography.headlineMedium)
                Spacer(Modifier.height(6.dp))
                Text(
                    "Tell us about your home, routine and the kind of friend you hope to meet.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(18.dp))
                Button(onClick = onStartChat, shape = MaterialTheme.shapes.medium) {
                    Text("Start a conversation")
                    Spacer(Modifier.width(8.dp))
                    Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = null, modifier = Modifier.size(18.dp))
                }
            }
        }
    }
}

@Composable
private fun FeaturedPetCard(pet: PetDto, onViewPet: (String) -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable { onViewPet(pet.id) },
        shape = MaterialTheme.shapes.extraLarge,
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Box {
            PetImage(
                url = pet.photoUrl,
                contentDescription = pet.name,
                modifier = Modifier.fillMaxWidth().height(240.dp)
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
            Column(Modifier.align(Alignment.BottomStart).padding(18.dp)) {
                Text(
                    pet.name,
                    style = MaterialTheme.typography.headlineMedium,
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "${pet.breed} · ${pet.gender}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.85f)
                )
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    pet.temperament.take(3).forEach { tag ->
                        Surface(shape = CircleShape, color = Color.White.copy(alpha = 0.18f)) {
                            Text(
                                tag,
                                style = MaterialTheme.typography.labelSmall,
                                color = Color.White,
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun PetMiniCard(pet: PetDto, onViewPet: (String) -> Unit) {
    Card(
        modifier = Modifier.width(210.dp).clickable { onViewPet(pet.id) },
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column {
            PetImage(
                url = pet.photoUrl,
                contentDescription = pet.name,
                modifier = Modifier.fillMaxWidth().height(130.dp)
            )
            Column(Modifier.padding(14.dp)) {
                Text(pet.name, style = MaterialTheme.typography.titleMedium)
                Text(
                    "${pet.breed} · ${pet.gender}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(8.dp))
                PawTag(pet.temperament.firstOrNull() ?: pet.species)
            }
        }
    }
}

@Composable
private fun HomeSkeleton(modifier: Modifier = Modifier) {
    Column(modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        PawSkeleton(Modifier.fillMaxWidth().height(190.dp), MaterialTheme.shapes.extraLarge)
        PawSkeleton(Modifier.fillMaxWidth(0.5f).height(26.dp))
        PawSkeleton(Modifier.fillMaxWidth().height(240.dp), MaterialTheme.shapes.extraLarge)
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            repeat(2) {
                PawSkeleton(Modifier.width(180.dp).height(200.dp), MaterialTheme.shapes.large)
            }
        }
    }
}
