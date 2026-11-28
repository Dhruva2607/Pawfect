package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.model.AdoptionStatusResponseDto
import com.pawfect.app.data.repository.AdoptionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AdoptionTrackerUiState(
    val isLoading: Boolean = true,
    val applications: List<AdoptionStatusResponseDto> = emptyList(),
    val error: String? = null
) {
    val isEmpty: Boolean
        get() = !isLoading && error == null && applications.isEmpty()
}

/**
 * Backs the adopter-side "My applications" screen.
 *
 * Before this existed an adopter could only look up an application if they had
 * kept its id, so reloading the app lost their entire adoption history.
 */
@HiltViewModel
class AdoptionTrackerViewModel @Inject constructor(
    private val adoptionRepository: AdoptionRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(AdoptionTrackerUiState())
    val uiState: StateFlow<AdoptionTrackerUiState> = _uiState.asStateFlow()

    private var loadJob: Job? = null

    fun load() {
        // Cancel any in-flight refresh so a stale response cannot overwrite a
        // newer one when the user pulls to refresh repeatedly.
        loadJob?.cancel()
        loadJob = viewModelScope.launch {
            val userId = sessionManager.currentSession()?.userId
            if (userId.isNullOrBlank()) {
                _uiState.update {
                    it.copy(isLoading = false, error = "Please sign in to view your applications.")
                }
                return@launch
            }

            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                val applications = adoptionRepository.getMyApplications()
                _uiState.update {
                    it.copy(isLoading = false, applications = applications, error = null)
                }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = error.localizedMessage
                            ?: "Could not load your applications. Please try again."
                    )
                }
            }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
}
