package com.pawfect.app.ui.screens.shelter

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.ui.components.PetImage
import com.pawfect.app.ui.viewmodel.ShelterPetsViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShelterPetsScreen(
    onAddPet: () -> Unit,
    onEditPet: (String) -> Unit,
    viewModel: ShelterPetsViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val filters = listOf(null to "All", "available" to "Available", "draft" to "Drafts", "adopted" to "Adopted", "hidden" to "Hidden")

    LaunchedEffect(Unit) { viewModel.loadPets() }

    Scaffold(
        topBar = { TopAppBar(title = { Text("My Pets", fontWeight = FontWeight.Bold) }) },
        floatingActionButton = {
            FloatingActionButton(onClick = onAddPet) {
                Icon(Icons.Default.Add, contentDescription = "Add Pet")
            }
        }
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            LazyRow(
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(filters) { (key, label) ->
                    FilterChip(
                        selected = uiState.selectedStatus == key,
                        onClick = { viewModel.loadPets(key) },
                        label = { Text(label) }
                    )
                }
            }

            if (uiState.isLoading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (uiState.pets.isEmpty()) {
                Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                    Text("No pets in this category yet. Tap + to list a pet.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(uiState.pets) { pet ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    PetImage(
                                        url = pet.photoUrl,
                                        contentDescription = pet.name,
                                        modifier = Modifier
                                            .size(68.dp)
                                            .clip(RoundedCornerShape(12.dp))
                                    )
                                    Column(Modifier.weight(1f)) {
                                        Text("${pet.name} · ${pet.breed}", fontWeight = FontWeight.Bold)
                                        Text(
                                            "${pet.species.replaceFirstChar { it.uppercase() }} · ${pet.ageMonths} mo · ${pet.size}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                    AssistChip(
                                        onClick = {},
                                        label = { Text((pet.status ?: "available").uppercase()) }
                                    )
                                }
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    OutlinedButton(onClick = { onEditPet(pet.id) }) {
                                        Icon(Icons.Default.Edit, contentDescription = null, modifier = Modifier.size(16.dp))
                                        Spacer(Modifier.width(4.dp))
                                        Text("Edit")
                                    }
                                    if (pet.status != "adopted") {
                                        TextButton(onClick = { viewModel.toggleVisibility(pet) }) {
                                            Text(if (pet.status == "available") "Hide" else "Publish")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
