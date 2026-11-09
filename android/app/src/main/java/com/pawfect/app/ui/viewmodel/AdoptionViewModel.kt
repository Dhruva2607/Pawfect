package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
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
    val applicantName: String = "",
    val applicantEmail: String = "",
    val applicantPhone: String = "",
    val housingDetails: String = "",
    val householdMembers: String = "",
    val notes: String = "",
    val applicationResult: AdoptionStatusResponseDto? = null,
    val isRefreshingStatus: Boolean = false,
    val isSubmitted: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AdoptionViewModel @Inject constructor(
    private val adoptionRepository: AdoptionRepository,
    private val petRepository: PetRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(AdoptionUiState())
    val uiState: StateFlow<AdoptionUiState> = _uiState.asStateFlow()

    fun loadPet(petId: String) {
        viewModelScope.launch {
            try {
                val pet = petRepository.getPet(petId)
                val session = sessionManager.currentSession()
                _uiState.update {
                    it.copy(
                        pet = pet,
                        applicantName = session?.name.orEmpty(),
                        applicantEmail = session?.email.orEmpty()
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(error = e.localizedMessage ?: "Could not load this pet.")
                }
            }
        }
    }

    fun setStep(step: AdoptionStep) {
        _uiState.update { it.copy(currentStep = step) }
    }

    fun refreshApplicationStatus() {
        val applicationId = _uiState.value.applicationResult?.applicationId ?: return
        _uiState.update { it.copy(isRefreshingStatus = true, error = null) }
        viewModelScope.launch {
            try {
                val response = adoptionRepository.getAdoptionStatus(applicationId)
                _uiState.update {
                    it.copy(
                        applicationResult = response,
                        isRefreshingStatus = false,
                        error = null
                    )
                }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isRefreshingStatus = false,
                        error = error.localizedMessage ?: "Could not refresh application status."
                    )
                }
            }
        }
    }

    fun submitApplication(
        petId: String,
        applicantName: String,
        applicantEmail: String,
        applicantPhone: String,
        housingDetails: String,
        householdMembers: String,
        notes: String
    ) {
        val session = sessionManager.currentSession()
        if (applicantName.isBlank() || applicantEmail.isBlank()) {
            _uiState.update { it.copy(error = "Name and email are required to apply.") }
            return
        }
        if (session == null) {
            _uiState.update { it.copy(error = "Sign in before submitting an adoption application.") }
            return
        }
        _uiState.update { it.copy(isLoading = true, error = null) }

        viewModelScope.launch {
            try {
                val resp = adoptionRepository.applyAdoption(
                    AdoptionApplyRequestDto(
                        userId = session.userId,
                        petId = petId,
                        applicantName = applicantName.trim(),
                        applicantEmail = applicantEmail.trim(),
                        applicantPhone = applicantPhone.trim().takeIf { it.isNotEmpty() },
                        housingDetails = housingDetails.trim(),
                        householdMembers = householdMembers.trim(),
                        notes = notes.trim()
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
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "Could not submit the application. Please try again."
                    )
                }
            }
        }
    }
}
