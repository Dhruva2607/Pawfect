package com.pawfect.app.data.repository

import com.pawfect.app.data.model.*
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.remote.PawFectApiService
import com.pawfect.app.data.remote.PawFectSseClient
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Named
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiService: PawFectApiService,
    private val sessionManager: SessionManager
) {
    fun currentSession() = sessionManager.currentSession()

    suspend fun login(request: AuthRequestDto): AuthResponseDto =
        apiService.login(request).also(sessionManager::saveSession)

    suspend fun signup(request: AuthRequestDto): AuthResponseDto =
        apiService.signup(request).also(sessionManager::saveSession)

    fun logout() = sessionManager.logout()
}

/**
 * Pet Repository: fetches static pet details and user favorites.
 * [FROM MARKDOWN: Step 3.1, Step 3.2, and Step 4.1]
 */
@Singleton
class PetRepository @Inject constructor(
    private val apiService: PawFectApiService
) {
    suspend fun listPets(species: String? = null, size: String? = null, goodWithKids: Boolean? = null): List<PetDto> {
        return apiService.listPets(species, size, goodWithKids)
    }

    suspend fun getPet(id: String): PetDto {
        return apiService.getPet(id)
    }

    suspend fun getSavedPets(userId: String): List<PetDto> {
        return apiService.getSavedPets(userId)
    }

    suspend fun toggleFavorite(userId: String, petId: String): FavoriteToggleResponseDto {
        return apiService.toggleFavorite(userId, petId)
    }

    suspend fun directEval(request: DirectEvalRequestDto): DirectEvalResponseDto {
        return apiService.directEval(request)
    }

    suspend fun getUserProfile(userId: String): UserProfileDto {
        return apiService.getUserProfile(userId)
    }

    suspend fun updateUserProfile(
        userId: String,
        request: UserProfileUpdateDto
    ): UserProfileDto = apiService.updateUserProfile(userId, request)
}

/**
 * Chat Repository: handles conversational counselor SSE streaming & JSON messaging.
 * [FROM MARKDOWN: Step 3.1 & Section 4]
 */
@Singleton
class ChatRepository @Inject constructor(
    private val apiService: PawFectApiService,
    private val sseClient: PawFectSseClient,
    @Named("BaseUrl") private val baseUrl: String
) {
    fun streamChat(sessionId: String, message: String, userId: String? = null): Flow<SseChatEvent> {
        return sseClient.streamChatMessage(baseUrl, sessionId, message, userId)
    }

    suspend fun sendChatMessage(sessionId: String, message: String, userId: String? = null): ChatResponseDto {
        return apiService.sendChatMessage(ChatRequestDto(sessionId, message, userId, stream = false))
    }

}

/**
 * Adoption Repository: handles application submission and status.
 * [FROM MARKDOWN: Step 3.2]
 */
@Singleton
class AdoptionRepository @Inject constructor(
    private val apiService: PawFectApiService
) {
    suspend fun applyAdoption(request: AdoptionApplyRequestDto): AdoptionStatusResponseDto {
        return apiService.applyAdoption(request)
    }

    suspend fun getAdoptionStatus(applicationId: String): AdoptionStatusResponseDto {
        return apiService.getAdoptionStatus(applicationId)
    }
}
