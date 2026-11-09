package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.UserSession
import com.pawfect.app.data.model.AuthRequestDto
import com.pawfect.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AuthUiState(
    val isLoading: Boolean = false,
    val session: UserSession? = null,
    val error: String? = null
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val repository: AuthRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    fun authenticate(
        isSignUp: Boolean,
        name: String,
        email: String,
        password: String,
        housingType: String,
        hasChildren: Boolean,
        hasOtherPets: Boolean,
        energyBudget: Int
    ) {
        val normalizedEmail = email.trim().lowercase()
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(normalizedEmail).matches()) {
            _uiState.value = AuthUiState(error = "Enter a valid email address.")
            return
        }
        if (password.length < 6) {
            _uiState.value = AuthUiState(error = "Use a password with at least 6 characters.")
            return
        }
        if (isSignUp && name.isBlank()) {
            _uiState.value = AuthUiState(error = "Enter your name to create an account.")
            return
        }

        _uiState.value = AuthUiState(isLoading = true)
        viewModelScope.launch {
            try {
                val request = AuthRequestDto(
                    email = normalizedEmail,
                    password = password,
                    name = name.trim().takeIf { isSignUp },
                    housingType = housingType,
                    hasChildren = hasChildren,
                    hasOtherPets = hasOtherPets,
                    energyBudget = energyBudget
                )
                if (isSignUp) repository.signup(request) else repository.login(request)
                _uiState.value = AuthUiState(session = repository.currentSession())
            } catch (error: Exception) {
                _uiState.value = AuthUiState(
                    error = error.localizedMessage ?: "Unable to connect. Check your connection and try again."
                )
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
