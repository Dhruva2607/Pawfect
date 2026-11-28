package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.model.*
import com.pawfect.app.data.repository.ShelterRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

// ── Auth ──────────────────────────────────────────────────────────────

data class ShelterAuthUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val isSuccess: Boolean = false
)

@HiltViewModel
class ShelterAuthViewModel @Inject constructor(
    private val repo: ShelterRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(ShelterAuthUiState())
    val uiState: StateFlow<ShelterAuthUiState> = _uiState.asStateFlow()

    fun login(email: String, password: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            repo.login(email.trim(), password)
                .onSuccess { _uiState.update { it.copy(isLoading = false, isSuccess = true) } }
                .onFailure { e -> _uiState.update { it.copy(isLoading = false, error = e.message ?: "Login failed") } }
        }
    }

    fun signUp(request: ShelterSignupRequestDto) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            repo.signUp(request)
                .onSuccess { _uiState.update { it.copy(isLoading = false, isSuccess = true) } }
                .onFailure { e -> _uiState.update { it.copy(isLoading = false, error = e.message ?: "Signup failed") } }
        }
    }
}

// ── Dashboard ─────────────────────────────────────────────────────────

data class ShelterDashboardUiState(
    val isLoading: Boolean = true,
    val stats: ShelterStatsDto = ShelterStatsDto(),
    val recentApplications: List<ShelterApplicationDto> = emptyList(),
    val recentNotifications: List<NotificationDto> = emptyList(),
    val error: String? = null
)

@HiltViewModel
class ShelterDashboardViewModel @Inject constructor(
    private val repo: ShelterRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(ShelterDashboardUiState())
    val uiState: StateFlow<ShelterDashboardUiState> = _uiState.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            val stats = repo.getStats().getOrNull() ?: ShelterStatsDto()
            val apps = repo.getApplications().getOrNull().orEmpty().take(5)
            val notifs = repo.getNotifications(unreadOnly = true).getOrNull().orEmpty().take(5)
            _uiState.update {
                it.copy(
                    isLoading = false,
                    stats = stats,
                    recentApplications = apps,
                    recentNotifications = notifs
                )
            }
        }
    }
}

// ── My Pets ───────────────────────────────────────────────────────────

data class ShelterPetsUiState(
    val isLoading: Boolean = true,
    val pets: List<PetDto> = emptyList(),
    val selectedStatus: String? = null,
    val error: String? = null
)

@HiltViewModel
class ShelterPetsViewModel @Inject constructor(
    private val repo: ShelterRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(ShelterPetsUiState())
    val uiState: StateFlow<ShelterPetsUiState> = _uiState.asStateFlow()

    init { loadPets(null) }

    fun loadPets(statusFilter: String? = _uiState.value.selectedStatus) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, selectedStatus = statusFilter, error = null) }
            repo.getMyPets(statusFilter)
                .onSuccess { list -> _uiState.update { it.copy(isLoading = false, pets = list) } }
                .onFailure { e -> _uiState.update { it.copy(isLoading = false, error = e.message) } }
        }
    }

    fun toggleVisibility(pet: PetDto) {
        val nextStatus = if (pet.status == "available") "hidden" else "available"
        viewModelScope.launch {
            repo.updatePetStatus(pet.id, nextStatus)
                .onSuccess { loadPets() }
                .onFailure { e -> _uiState.update { it.copy(error = e.message) } }
        }
    }

    fun softDelete(petId: String) {
        viewModelScope.launch {
            repo.deletePet(petId)
                .onSuccess { loadPets() }
                .onFailure { e -> _uiState.update { it.copy(error = e.message) } }
        }
    }
}

// ── Pet Form (driven by GET /meta/pet-options) ────────────────────────

data class ShelterPetFormUiState(
    val isLoading: Boolean = true,
    val isSaving: Boolean = false,
    val options: PetOptionsResponseDto? = null,
    val existingPet: PetDto? = null,
    val savedPetId: String? = null,
    val error: String? = null
)

@HiltViewModel
class ShelterPetFormViewModel @Inject constructor(
    private val repo: ShelterRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(ShelterPetFormUiState())
    val uiState: StateFlow<ShelterPetFormUiState> = _uiState.asStateFlow()

    fun initForm(petId: String?) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null, savedPetId = null) }
            val optionsRes = repo.getPetOptions()
            val petRes = if (!petId.isNullOrBlank()) repo.getMyPet(petId) else null
            _uiState.update {
                it.copy(
                    isLoading = false,
                    options = optionsRes.getOrNull(),
                    existingPet = petRes?.getOrNull(),
                    error = optionsRes.exceptionOrNull()?.message ?: petRes?.exceptionOrNull()?.message
                )
            }
        }
    }

    fun savePet(
        petId: String?,
        request: ShelterPetCreateRequestDto,
        photoBytes: ByteArray? = null,
        photoMimeType: String = "image/jpeg",
        photoFileName: String = "pet.jpg"
    ) {
        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true, error = null) }
            val result = if (petId.isNullOrBlank()) {
                repo.createPet(request)
            } else {
                repo.updatePet(petId, request)
            }
            result.onSuccess { saved ->
                if (photoBytes != null) {
                    repo.uploadPetPhoto(saved.id, photoBytes, photoMimeType, photoFileName)
                }
                _uiState.update { it.copy(isSaving = false, savedPetId = saved.id) }
            }.onFailure { e ->
                _uiState.update { it.copy(isSaving = false, error = e.message ?: "Failed to save pet") }
            }
        }
    }
}

// ── Applications Inbox & Detail ───────────────────────────────────────

data class ShelterApplicationsUiState(
    val isLoading: Boolean = true,
    val applications: List<ShelterApplicationDto> = emptyList(),
    val selectedApplication: ShelterApplicationDto? = null,
    val selectedStatus: String? = null,
    val isUpdating: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class ShelterApplicationsViewModel @Inject constructor(
    private val repo: ShelterRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(ShelterApplicationsUiState())
    val uiState: StateFlow<ShelterApplicationsUiState> = _uiState.asStateFlow()

    init { loadApplications(null) }

    fun loadApplications(statusFilter: String? = _uiState.value.selectedStatus) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, selectedStatus = statusFilter, error = null) }
            repo.getApplications(status = statusFilter)
                .onSuccess { list -> _uiState.update { it.copy(isLoading = false, applications = list) } }
                .onFailure { e -> _uiState.update { it.copy(isLoading = false, error = e.message) } }
        }
    }

    fun loadDetail(appId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            repo.getApplication(appId)
                .onSuccess { app -> _uiState.update { it.copy(isLoading = false, selectedApplication = app) } }
                .onFailure { e -> _uiState.update { it.copy(isLoading = false, error = e.message) } }
        }
    }

    fun updateStage(appId: String, stageStatus: String, note: String?) {
        viewModelScope.launch {
            _uiState.update { it.copy(isUpdating = true, error = null) }
            repo.updateApplicationStage(appId, stageStatus, note?.takeIf { it.isNotBlank() })
                .onSuccess { updated ->
                    _uiState.update { it.copy(isUpdating = false, selectedApplication = updated) }
                    loadApplications()
                }
                .onFailure { e ->
                    _uiState.update { it.copy(isUpdating = false, error = e.message ?: "Update failed") }
                }
        }
    }
}

// ── Notifications ─────────────────────────────────────────────────────

data class ShelterNotificationsUiState(
    val isLoading: Boolean = true,
    val notifications: List<NotificationDto> = emptyList(),
    val error: String? = null
)

@HiltViewModel
class ShelterNotificationsViewModel @Inject constructor(
    private val repo: ShelterRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(ShelterNotificationsUiState())
    val uiState: StateFlow<ShelterNotificationsUiState> = _uiState.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            repo.getNotifications()
                .onSuccess { list -> _uiState.update { it.copy(isLoading = false, notifications = list) } }
                .onFailure { e -> _uiState.update { it.copy(isLoading = false, error = e.message) } }
        }
    }

    fun markRead(notifId: String) {
        viewModelScope.launch {
            repo.markNotificationRead(notifId).onSuccess { refresh() }
        }
    }

    fun markAllRead() {
        viewModelScope.launch {
            repo.markAllNotificationsRead().onSuccess { refresh() }
        }
    }
}

// ── Shelter Profile ───────────────────────────────────────────────────

data class ShelterProfileUiState(
    val isLoading: Boolean = true,
    val isSaving: Boolean = false,
    val shelter: ShelterDto? = null,
    val savedBanner: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class ShelterProfileViewModel @Inject constructor(
    private val repo: ShelterRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(ShelterProfileUiState())
    val uiState: StateFlow<ShelterProfileUiState> = _uiState.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            repo.getMyShelter()
                .onSuccess { s -> _uiState.update { it.copy(isLoading = false, shelter = s) } }
                .onFailure { e -> _uiState.update { it.copy(isLoading = false, error = e.message) } }
        }
    }

    fun save(update: ShelterUpdateRequestDto) {
        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true, savedBanner = false, error = null) }
            repo.updateMyShelter(update)
                .onSuccess { s -> _uiState.update { it.copy(isSaving = false, shelter = s, savedBanner = true) } }
                .onFailure { e -> _uiState.update { it.copy(isSaving = false, error = e.message) } }
        }
    }
}
