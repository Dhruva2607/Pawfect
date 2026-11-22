package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.model.DirectEvalRequestDto
import com.pawfect.app.data.model.DirectEvalResponseDto
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.model.PetEvaluationDto
import com.pawfect.app.data.model.StoredMatchResults
import com.pawfect.app.data.repository.PetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
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

    private val json = Json { ignoreUnknownKeys = true }
    private val _uiState = MutableStateFlow(CompatibilityUiState())
    val uiState: StateFlow<CompatibilityUiState> = _uiState.asStateFlow()

    fun evaluatePet(petId: String) {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                // 1. Check if this pet already has a grounded evaluation from matchmaker/matches screen
                val storedMatches = runCatching {
                    sessionManager.matchResultsJson()?.let {
                        json.decodeFromString<StoredMatchResults>(it)
                    }
                }.getOrNull()

                val existingEval = storedMatches?.evaluations?.firstOrNull { it.petId == petId }
                val storedPet = storedMatches?.candidateMatches?.firstOrNull { it.id == petId }

                if (existingEval != null) {
                    val pet = storedPet ?: runCatching { petRepository.getPet(petId) }.getOrNull()
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            pet = pet,
                            evaluation = DirectEvalResponseDto(
                                petId = existingEval.petId,
                                petName = existingEval.petName,
                                compatibilityScore = existingEval.compatibilityScore,
                                pros = existingEval.pros,
                                caveats = existingEval.caveats,
                                reasoningSummary = existingEval.reasoningSummary,
                                comparisonToHero = existingEval.comparisonToHero
                            )
                        )
                    }
                    return@launch
                }

                // 2. Perform live direct evaluation if not already evaluated
                val pet = storedPet ?: petRepository.getPet(petId)
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

                // 3. Persist into stored matches so matches and more matches screens stay consistent
                try {
                    val currentStored = storedMatches ?: StoredMatchResults()
                    val newEval = PetEvaluationDto(
                        petId = eval.petId,
                        petName = eval.petName,
                        compatibilityScore = eval.compatibilityScore,
                        pros = eval.pros,
                        caveats = eval.caveats,
                        reasoningSummary = eval.reasoningSummary,
                        comparisonToHero = eval.comparisonToHero
                    )
                    val updatedEvals = currentStored.evaluations.filter { it.petId != petId } + newEval
                    val updatedCandidates = if (currentStored.candidateMatches.none { it.id == pet.id }) {
                        currentStored.candidateMatches + pet
                    } else currentStored.candidateMatches

                    sessionManager.saveMatchResultsJson(
                        json.encodeToString(
                            StoredMatchResults(
                                candidateMatches = updatedCandidates,
                                evaluations = updatedEvals
                            )
                        )
                    )
                } catch (_: Exception) {}

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
