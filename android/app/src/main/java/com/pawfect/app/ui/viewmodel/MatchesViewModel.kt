package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.repository.PetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class MatchesUiState(
    val isLoading: Boolean = false,
    val topMatch: PetDto? = null,
    val otherMatches: List<PetDto> = emptyList(),
    val savedPetIds: Set<String> = emptySet(),
    val error: String? = null
)

@HiltViewModel
class MatchesViewModel @Inject constructor(
    private val petRepository: PetRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(MatchesUiState())
    val uiState: StateFlow<MatchesUiState> = _uiState.asStateFlow()

    init {
        loadMatches()
    }

    fun loadMatches() {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                val pets = petRepository.listPets()
                val top = pets.firstOrNull()
                val others = if (pets.size > 1) pets.subList(1, pets.size.coerceAtMost(6)) else emptyList()
                val saved = petRepository.getSavedPets("user_default").map { it.id }.toSet()

                _uiState.update {
                    it.copy(
                        isLoading = false,
                        topMatch = top,
                        otherMatches = others,
                        savedPetIds = saved
                    )
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, error = e.localizedMessage) }
            }
        }
    }

    fun toggleFavorite(petId: String) {
        viewModelScope.launch {
            try {
                val resp = petRepository.toggleFavorite("user_default", petId)
                _uiState.update { state ->
                    val updatedSaved = if (resp.isFavorited) {
                        state.savedPetIds + petId
                    } else {
                        state.savedPetIds - petId
                    }
                    state.copy(savedPetIds = updatedSaved)
                }
            } catch (e: Exception) {
                // Ignore or log
            }
        }
    }
}

