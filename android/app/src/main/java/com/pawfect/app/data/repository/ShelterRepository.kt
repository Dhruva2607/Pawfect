package com.pawfect.app.data.repository

import com.pawfect.app.data.local.ShelterSessionManager
import com.pawfect.app.data.model.*
import com.pawfect.app.data.remote.PawFectApiService
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ShelterRepository @Inject constructor(
    private val api: PawFectApiService,
    private val shelterSessionManager: ShelterSessionManager
) {
    suspend fun getPetOptions(): Result<PetOptionsResponseDto> = runCatching {
        api.getPetOptions()
    }

    suspend fun signUp(request: ShelterSignupRequestDto): Result<ShelterAuthResponseDto> = runCatching {
        val response = api.shelterSignUp(request)
        shelterSessionManager.saveSession(response)
        response
    }

    suspend fun login(email: String, password: String): Result<ShelterAuthResponseDto> = runCatching {
        val response = api.shelterLogin(ShelterLoginRequestDto(email = email, password = password))
        shelterSessionManager.saveSession(response)
        response
    }

    suspend fun getMyShelter(): Result<ShelterDto> = runCatching {
        api.getMyShelter().also { shelterSessionManager.updateProfile(it) }
    }

    suspend fun updateMyShelter(request: ShelterUpdateRequestDto): Result<ShelterDto> = runCatching {
        api.updateMyShelter(request).also { shelterSessionManager.updateProfile(it) }
    }

    suspend fun getMyPets(status: String? = null): Result<List<PetDto>> = runCatching {
        api.getMyShelterPets(status = status)
    }

    suspend fun getMyPet(petId: String): Result<PetDto> = runCatching {
        api.getMyShelterPet(petId)
    }

    suspend fun createPet(request: ShelterPetCreateRequestDto): Result<PetDto> = runCatching {
        api.createMyShelterPet(request)
    }

    suspend fun updatePet(petId: String, request: ShelterPetCreateRequestDto): Result<PetDto> = runCatching {
        api.updateMyShelterPet(petId, request)
    }

    suspend fun updatePetStatus(petId: String, status: String): Result<PetDto> = runCatching {
        api.updateMyShelterPetStatus(petId, PetStatusUpdateRequestDto(status))
    }

    suspend fun deletePet(petId: String): Result<PetDto> = runCatching {
        api.deleteMyShelterPet(petId)
    }

    suspend fun uploadPetPhoto(petId: String, bytes: ByteArray, mimeType: String, fileName: String): Result<PhotoUploadResponseDto> =
        runCatching {
            val body = bytes.toRequestBody(mimeType.toMediaTypeOrNull())
            val part = MultipartBody.Part.createFormData("file", fileName, body)
            api.uploadPetPhoto(petId, part)
        }

    suspend fun getApplications(status: String? = null, petId: String? = null): Result<List<ShelterApplicationDto>> =
        runCatching {
            api.getMyShelterApplications(status = status, petId = petId)
        }

    suspend fun getApplication(appId: String): Result<ShelterApplicationDto> = runCatching {
        api.getMyShelterApplication(appId)
    }

    suspend fun updateApplicationStage(
        appId: String,
        stageStatus: String,
        shelterNote: String? = null
    ): Result<ShelterApplicationDto> = runCatching {
        api.updateApplicationStage(appId, ShelterStageUpdateRequestDto(stageStatus, shelterNote))
    }

    suspend fun getStats(): Result<ShelterStatsDto> = runCatching {
        api.getMyShelterStats()
    }

    suspend fun getNotifications(unreadOnly: Boolean = false): Result<List<NotificationDto>> = runCatching {
        api.getNotifications(unreadOnly = unreadOnly)
    }

    suspend fun getUnreadCount(): Result<Int> = runCatching {
        api.getUnreadNotificationCount().unreadCount
    }

    suspend fun markNotificationRead(notifId: String): Result<NotificationDto> = runCatching {
        api.markNotificationRead(notifId)
    }

    suspend fun markAllNotificationsRead(): Result<Unit> = runCatching {
        api.markAllNotificationsRead()
    }
}
