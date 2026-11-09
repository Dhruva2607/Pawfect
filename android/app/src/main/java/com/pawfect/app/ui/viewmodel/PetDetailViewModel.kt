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

data class PetDetailUiState(
    val isLoading: Boolean = false,
    val pet: PetDto? = null,
    val isFavorited: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class PetDetailViewModel @Inject constructor(
    private val petRepository: PetRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(PetDetailUiState())
    val uiState: StateFlow<PetDetailUiState> = _uiState.asStateFlow()

    fun loadPet(petId: String) {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                val pet = petRepository.getPet(petId)
                val savedPets = petRepository.getSavedPets("user_default").map { it.id }.toSet()
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        pet = pet,
                        isFavorited = pet.id in savedPets
                    )
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, error = e.localizedMessage) }
            }
        }
    }

    fun toggleFavorite() {
        val currentPet = _uiState.value.pet ?: return
        viewModelScope.launch {
            try {
                val resp = petRepository.toggleFavorite("user_default", currentPet.id)
                _uiState.update { it.copy(isFavorited = resp.isFavorited) }
            } catch (e: Exception) {
                // Ignore
            }
        }
    }
}

