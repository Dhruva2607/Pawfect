package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.UserSession
import com.pawfect.app.data.model.AuthRequestDto
import com.pawfect.app.data.model.GeneratedProfileResponseDto
import com.pawfect.app.data.model.UserProfileUpdateDto
import com.pawfect.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AuthUiState(
    val isLoading: Boolean = false,
    val session: UserSession? = null,
    val signUpStep: Int = 0,
    val generatedProfile: GeneratedProfileResponseDto? = null,
    val error: String? = null
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val repository: AuthRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    fun login(email: String, password: String) {
        val normalizedEmail = email.trim().lowercase()
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(normalizedEmail).matches()) {
            _uiState.update { it.copy(error = "Enter a valid email address.") }
            return
        }
        if (password.length < 6) {
            _uiState.update { it.copy(error = "Use a password with at least 6 characters.") }
            return
        }

        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                repository.login(AuthRequestDto(email = normalizedEmail, password = password))
                _uiState.update { it.copy(isLoading = false, session = repository.currentSession()) }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = error.localizedMessage ?: "Unable to connect. Check your connection and try again."
                    )
                }
            }
        }
    }

    fun startSignUpAccount(name: String, email: String, password: String) {
        val normalizedEmail = email.trim().lowercase()
        if (name.isBlank()) {
            _uiState.update { it.copy(error = "Enter your name to create an account.") }
            return
        }
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(normalizedEmail).matches()) {
            _uiState.update { it.copy(error = "Enter a valid email address.") }
            return
        }
        if (password.length < 6) {
            _uiState.update { it.copy(error = "Use a password with at least 6 characters.") }
            return
        }

        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                repository.signup(
                    AuthRequestDto(
                        email = normalizedEmail,
                        password = password,
                        name = name.trim()
                    )
                )
                _uiState.update { it.copy(isLoading = false, signUpStep = 1) }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = error.localizedMessage ?: "Unable to connect. Check your connection and try again."
                    )
                }
            }
        }
    }

    fun submitHousingAnswer(housingType: String) {
        saveAnswerAndAdvance(UserProfileUpdateDto(housingType = housingType), nextStep = 2)
    }

    fun submitChildrenAnswer(hasChildren: Boolean) {
        saveAnswerAndAdvance(UserProfileUpdateDto(hasChildren = hasChildren), nextStep = 3)
    }

    fun submitOtherPetsAnswer(hasOtherPets: Boolean) {
        saveAnswerAndAdvance(UserProfileUpdateDto(hasOtherPets = hasOtherPets), nextStep = 4)
    }

    fun submitEnergyAndGenerateProfile(energyBudget: Int) {
        val userId = repository.currentSession()?.userId
        if (userId == null) {
            _uiState.update { it.copy(error = "Please create your account first.", signUpStep = 0) }
            return
        }
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                repository.updateProfileAnswer(userId, UserProfileUpdateDto(energyBudget = energyBudget))
                val generated = repository.generateAndSaveProfile(userId)
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        generatedProfile = generated,
                        signUpStep = 5
                    )
                }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = error.localizedMessage ?: "Could not save your profile. Please try again."
                    )
                }
            }
        }
    }

    fun completeSignUp() {
        _uiState.update { it.copy(session = repository.currentSession()) }
    }

    fun previousSignUpStep() {
        _uiState.update { state ->
            if (state.signUpStep in 1..4) state.copy(signUpStep = state.signUpStep - 1, error = null)
            else state
        }
    }

    fun resetSignUpFlow() {
        _uiState.update { it.copy(signUpStep = 0, generatedProfile = null, error = null) }
    }

    private fun saveAnswerAndAdvance(update: UserProfileUpdateDto, nextStep: Int) {
        val userId = repository.currentSession()?.userId
        if (userId == null) {
            _uiState.update { it.copy(error = "Please create your account first.", signUpStep = 0) }
            return
        }
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                repository.updateProfileAnswer(userId, update)
                _uiState.update { it.copy(isLoading = false, signUpStep = nextStep) }
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = error.localizedMessage ?: "Could not save your answer. Please try again."
                    )
                }
            }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
}
