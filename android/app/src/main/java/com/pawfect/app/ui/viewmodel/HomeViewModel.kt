package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.repository.PetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeUiState(
    val isLoading: Boolean = true,
    val pets: List<PetDto> = emptyList(),
    val error: String? = null
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val petRepository: PetRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    init {
        loadPets()
    }

    fun loadPets() {
        _uiState.value = HomeUiState(isLoading = true)
        viewModelScope.launch {
            try {
                _uiState.value = HomeUiState(isLoading = false, pets = petRepository.listPets())
            } catch (error: Exception) {
                _uiState.value = HomeUiState(
                    isLoading = false,
                    error = error.localizedMessage ?: "Could not load pets. Check your connection and retry."
                )
            }
        }
    }
}
