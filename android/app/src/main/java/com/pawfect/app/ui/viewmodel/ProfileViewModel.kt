package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.local.UserSession
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.model.UserProfileUpdateDto
import com.pawfect.app.data.model.UserProfileDto
import com.pawfect.app.data.repository.PetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ProfileUiState(
    val isLoading: Boolean = false,
    val profile: UserProfileDto? = null,
    val session: UserSession? = null,
    val savedPets: List<PetDto> = emptyList(),
    val isSaving: Boolean = false,
    val message: String? = null,
    val error: String? = null
)

@HiltViewModel
class ProfileViewModel @Inject constructor(
    private val petRepository: PetRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(ProfileUiState(session = sessionManager.currentSession()))
    val uiState: StateFlow<ProfileUiState> = _uiState.asStateFlow()

    init {
        loadProfile()
    }

    fun loadProfile() {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                val userId = sessionManager.currentSession()?.userId
                    ?: throw IllegalStateException("Sign in to load your profile.")
                val user = petRepository.getUserProfile(userId)
                val saved = petRepository.getSavedPets(userId)
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        profile = user,
                        session = sessionManager.currentSession(),
                        savedPets = saved
                    )
                }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = error.localizedMessage ?: "Could not load your profile. Please retry."
                    )
                }
            }
        }
    }

    fun savePreferences(
        name: String,
        email: String,
        housingType: String,
        hasChildren: Boolean,
        hasOtherPets: Boolean,
        energyBudget: Int
    ) {
        val userId = sessionManager.currentSession()?.userId ?: return
        _uiState.update { it.copy(isSaving = true, error = null, message = null) }
        viewModelScope.launch {
            try {
                val profile = petRepository.updateUserProfile(
                    userId,
                    UserProfileUpdateDto(
                        name = name.trim(),
                        email = email.trim(),
                        housingType = housingType,
                        hasChildren = hasChildren,
                        hasOtherPets = hasOtherPets,
                        energyBudget = energyBudget
                    )
                )
                sessionManager.updateSession(
                    profile.name,
                    profile.email,
                    profile.housingType ?: housingType,
                    profile.hasChildren ?: hasChildren,
                    profile.hasOtherPets ?: hasOtherPets,
                    profile.energyBudget ?: energyBudget
                )
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        profile = profile,
                        session = sessionManager.currentSession(),
                        message = "Your profile has been updated."
                    )
                }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        error = error.localizedMessage ?: "Could not save your profile."
                    )
                }
            }
        }
    }

    fun clearMessage() {
        _uiState.update { it.copy(message = null) }
    }
}
