package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.repository.PetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class PetDetailUiState(
    val isLoading: Boolean = false,
    val pet: PetDto? = null,
    val isFavorited: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class PetDetailViewModel @Inject constructor(
    private val petRepository: PetRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(PetDetailUiState())
    val uiState: StateFlow<PetDetailUiState> = _uiState.asStateFlow()

    fun loadPet(petId: String) {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                val pet = petRepository.getPet(petId)
                val userId = sessionManager.currentSession()?.userId
                val savedPets = if (userId != null) {
                    petRepository.getSavedPets(userId).map { it.id }.toSet()
                } else {
                    emptySet()
                }
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        pet = pet,
                        isFavorited = pet.id in savedPets
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "Could not load this pet. Check your connection and try again."
                    )
                }
            }
        }
    }

    fun toggleFavorite() {
        val currentPet = _uiState.value.pet ?: return
        val userId = sessionManager.currentSession()?.userId
        if (userId == null) {
            _uiState.update { it.copy(error = "Sign in to save pets.") }
            return
        }
        viewModelScope.launch {
            try {
                val resp = petRepository.toggleFavorite(userId, currentPet.id)
                _uiState.update { it.copy(isFavorited = resp.isFavorited) }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(error = e.localizedMessage ?: "Could not update saved pets. Please try again.")
                }
            }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
}
