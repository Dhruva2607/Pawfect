package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.model.DirectEvalRequestDto
import com.pawfect.app.data.model.DirectEvalResponseDto
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.repository.PetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CompatibilityUiState(
    val isLoading: Boolean = false,
    val pet: PetDto? = null,
    val evaluation: DirectEvalResponseDto? = null,
    val error: String? = null
)

@HiltViewModel
class CompatibilityViewModel @Inject constructor(
    private val petRepository: PetRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(CompatibilityUiState())
    val uiState: StateFlow<CompatibilityUiState> = _uiState.asStateFlow()

    fun evaluatePet(petId: String) {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                val pet = petRepository.getPet(petId)
                val session = sessionManager.currentSession()
                val eval = petRepository.directEval(
                    DirectEvalRequestDto(
                        sessionId = sessionManager.chatSessionId(),
                        petId = petId,
                        housingType = session?.housingType,
                        hasChildren = session?.hasChildren,
                        hasOtherPets = session?.hasOtherPets,
                        energyBudget = session?.energyBudget,
                        notes = null
                    )
                )
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        pet = pet,
                        evaluation = eval
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "Could not evaluate compatibility. Please try again."
                    )
                }
            }
        }
    }
}
