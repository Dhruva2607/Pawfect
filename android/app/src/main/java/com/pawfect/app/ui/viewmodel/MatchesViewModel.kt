package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.model.PetEvaluationDto
import com.pawfect.app.data.model.StoredMatchResults
import com.pawfect.app.data.repository.PetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class MatchesUiState(
    val isLoading: Boolean = false,
    val isSavedOnly: Boolean = false,
    val topMatch: PetDto? = null,
    val otherMatches: List<PetDto> = emptyList(),
    val evaluationsByPetId: Map<String, PetEvaluationDto> = emptyMap(),
    val savedPetIds: Set<String> = emptySet(),
    val error: String? = null
)

@HiltViewModel
class MatchesViewModel @Inject constructor(
    private val petRepository: PetRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val json = Json { ignoreUnknownKeys = true }
    private val userId get() = sessionManager.currentSession()?.userId.orEmpty()
    private val _uiState = MutableStateFlow(MatchesUiState())
    val uiState: StateFlow<MatchesUiState> = _uiState.asStateFlow()

    fun loadMatches(savedOnly: Boolean = false) {
        _uiState.update { it.copy(isLoading = true, isSavedOnly = savedOnly, error = null) }
        viewModelScope.launch {
            try {
                val storedMatches = runCatching {
                    sessionManager.matchResultsJson()?.let {
                        json.decodeFromString<StoredMatchResults>(it)
                    } ?: StoredMatchResults()
                }.getOrElse { StoredMatchResults() }
                val savedPets = petRepository.getSavedPets(userId)
                val catalog = if (savedOnly) emptyList() else petRepository.listPets()
                val scores = storedMatches.evaluations.associateBy { it.petId }
                val pets = if (savedOnly) {
                    savedPets
                } else {
                    storedMatches.candidateMatches
                        .ifEmpty { catalog }
                        .sortedByDescending { scores[it.id]?.compatibilityScore ?: -1 }
                }
                val top = pets.firstOrNull()
                val others = if (pets.size > 1) pets.subList(1, pets.size.coerceAtMost(6)) else emptyList()
                val saved = savedPets.map { it.id }.toSet()

                _uiState.update {
                    it.copy(
                        isLoading = false,
                        topMatch = top,
                        otherMatches = others,
                        evaluationsByPetId = scores,
                        savedPetIds = saved
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "Could not load pets. Check your connection and try again."
                    )
                }
            }
        }
    }

    fun toggleFavorite(petId: String) {
        viewModelScope.launch {
            try {
                val resp = petRepository.toggleFavorite(userId, petId)
                _uiState.update { state ->
                    val updatedSaved = if (resp.isFavorited) {
                        state.savedPetIds + petId
                    } else {
                        state.savedPetIds - petId
                    }
                    val visiblePets = listOfNotNull(state.topMatch) + state.otherMatches
                    val updatedPets = if (state.isSavedOnly && !resp.isFavorited) {
                        visiblePets.filterNot { it.id == petId }
                    } else {
                        visiblePets
                    }
                    state.copy(
                        savedPetIds = updatedSaved,
                        topMatch = updatedPets.firstOrNull(),
                        otherMatches = updatedPets.drop(1)
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(error = e.localizedMessage ?: "Could not update saved pets. Please try again.")
                }
            }
        }
    }
}
