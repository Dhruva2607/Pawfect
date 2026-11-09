package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.model.AdoptionApplyRequestDto
import com.pawfect.app.data.model.AdoptionStatusResponseDto
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.repository.AdoptionRepository
import com.pawfect.app.data.repository.PetRepository
import com.pawfect.app.ui.components.AdoptionStep
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AdoptionUiState(
    val isLoading: Boolean = false,
    val pet: PetDto? = null,
    val currentStep: AdoptionStep = AdoptionStep.REVIEW,
    val applicantName: String = "Jane Doe",
    val applicantEmail: String = "jane.doe@example.com",
    val applicantPhone: String = "555-0199",
    val housingDetails: String = "2-bedroom apartment with secure balcony",
    val notes: String = "Our family is ready to welcome our new best friend!",
    val applicationResult: AdoptionStatusResponseDto? = null,
    val isSubmitted: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AdoptionViewModel @Inject constructor(
    private val adoptionRepository: AdoptionRepository,
    private val petRepository: PetRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AdoptionUiState())
    val uiState: StateFlow<AdoptionUiState> = _uiState.asStateFlow()

    fun loadPet(petId: String) {
        viewModelScope.launch {
            try {
                val pet = petRepository.getPet(petId)
                _uiState.update { it.copy(pet = pet) }
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    fun setStep(step: AdoptionStep) {
        _uiState.update { it.copy(currentStep = step) }
    }

    fun submitApplication(petId: String) {
        val state = _uiState.value
        _uiState.update { it.copy(isLoading = true, error = null) }

        viewModelScope.launch {
            try {
                val resp = adoptionRepository.applyAdoption(
                    AdoptionApplyRequestDto(
                        userId = "user_default",
                        petId = petId,
                        applicantName = state.applicantName,
                        applicantEmail = state.applicantEmail,
                        applicantPhone = state.applicantPhone,
                        housingDetails = state.housingDetails,
                        household_members = "Family with 1 child",
                        notes = state.notes
                    )
                )
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        currentStep = AdoptionStep.APPLY,
                        applicationResult = resp,
                        isSubmitted = true
                    )
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, error = e.localizedMessage) }
            }
        }
    }
}

