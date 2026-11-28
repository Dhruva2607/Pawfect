package com.pawfect.app.data.remote

import com.pawfect.app.data.model.*
import okhttp3.MultipartBody
import retrofit2.http.*

/**
 * Retrofit 2 REST API endpoints.
 * [FROM MARKDOWN: Section 4 & Step 4.1]
 */
interface PawFectApiService {

    // ── Meta ──────────────────────────────────────────────────────────
    @GET("meta/pet-options")
    suspend fun getPetOptions(): PetOptionsResponseDto

    // ── Adopter Endpoints (unchanged contracts) ───────────────────────
    @GET("pets")
    suspend fun listPets(
        @Query("species") species: String? = null,
        @Query("size") size: String? = null,
        @Query("good_with_kids") goodWithKids: Boolean? = null,
        @Query("shelter_id") shelterId: String? = null,
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50
    ): List<PetDto>

    @GET("pets/{id}")
    suspend fun getPet(@Path("id") id: String): PetDto

    @POST("matches/direct-eval")
    suspend fun directEval(@Body request: DirectEvalRequestDto): DirectEvalResponseDto

    @POST("users/auth/login")
    suspend fun login(@Body request: AuthRequestDto): AuthResponseDto

    @POST("users/auth/signup")
    suspend fun signup(@Body request: AuthRequestDto): AuthResponseDto

    @PUT("users/{id}/profile")
    suspend fun updateUserProfile(
        @Path("id") id: String,
        @Body request: UserProfileUpdateDto
    ): UserProfileDto

    @POST("users/{id}/shelter-profile")
    suspend fun generateUserProfile(
        @Path("id") id: String
    ): GeneratedProfileResponseDto

    @POST("adoptions/apply")
    suspend fun applyAdoption(@Body request: AdoptionApplyRequestDto): AdoptionStatusResponseDto

    @GET("adoptions/mine")
    suspend fun getMyApplications(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50
    ): List<AdoptionStatusResponseDto>

    @GET("adoptions/{id}/status")
    suspend fun getAdoptionStatus(@Path("id") id: String): AdoptionStatusResponseDto

    @GET("adoptions/user/{userId}/pet/{petId}")
    suspend fun getUserPetApplication(
        @Path("userId") userId: String,
        @Path("petId") petId: String
    ): AdoptionStatusResponseDto?

    @GET("users/{id}/saved-pets")
    suspend fun getSavedPets(@Path("id") id: String): List<PetDto>

    @POST("users/{id}/favorite/{petId}")
    suspend fun toggleFavorite(
        @Path("id") userId: String,
        @Path("petId") petId: String
    ): FavoriteToggleResponseDto

    @GET("users/{id}/profile")
    suspend fun getUserProfile(@Path("id") id: String): UserProfileDto

    @POST("chat/message")
    suspend fun sendChatMessage(@Body request: ChatRequestDto): ChatResponseDto

    // ── Shelter Auth & Profile ────────────────────────────────────────
    @POST("shelters/auth/signup")
    suspend fun shelterSignUp(@Body request: ShelterSignupRequestDto): ShelterAuthResponseDto

    @POST("shelters/auth/login")
    suspend fun shelterLogin(@Body request: ShelterLoginRequestDto): ShelterAuthResponseDto

    @GET("shelters/me")
    suspend fun getMyShelter(): ShelterDto

    @PUT("shelters/me")
    suspend fun updateMyShelter(@Body request: ShelterUpdateRequestDto): ShelterDto

    // ── Shelter Pet CRUD ──────────────────────────────────────────────
    @GET("shelters/me/pets")
    suspend fun getMyShelterPets(
        @Query("status") status: String? = null,
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50
    ): List<PetDto>

    @GET("shelters/me/pets/{petId}")
    suspend fun getMyShelterPet(@Path("petId") petId: String): PetDto

    @POST("shelters/me/pets")
    suspend fun createMyShelterPet(@Body request: ShelterPetCreateRequestDto): PetDto

    @PUT("shelters/me/pets/{petId}")
    suspend fun updateMyShelterPet(
        @Path("petId") petId: String,
        @Body request: ShelterPetCreateRequestDto
    ): PetDto

    @PATCH("shelters/me/pets/{petId}/status")
    suspend fun updateMyShelterPetStatus(
        @Path("petId") petId: String,
        @Body request: PetStatusUpdateRequestDto
    ): PetDto

    @DELETE("shelters/me/pets/{petId}")
    suspend fun deleteMyShelterPet(@Path("petId") petId: String): PetDto

    @Multipart
    @POST("shelters/me/pets/{petId}/photo")
    suspend fun uploadPetPhoto(
        @Path("petId") petId: String,
        @Part file: MultipartBody.Part
    ): PhotoUploadResponseDto

    // ── Shelter Applications & Stats ──────────────────────────────────
    @GET("shelters/me/applications")
    suspend fun getMyShelterApplications(
        @Query("status") status: String? = null,
        @Query("pet_id") petId: String? = null,
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50
    ): List<ShelterApplicationDto>

    @GET("shelters/me/applications/{appId}")
    suspend fun getMyShelterApplication(@Path("appId") appId: String): ShelterApplicationDto

    @PATCH("shelters/me/applications/{appId}/stage")
    suspend fun updateApplicationStage(
        @Path("appId") appId: String,
        @Body request: ShelterStageUpdateRequestDto
    ): ShelterApplicationDto

    @GET("shelters/me/stats")
    suspend fun getMyShelterStats(): ShelterStatsDto

    // ── Notifications ─────────────────────────────────────────────────
    @GET("notifications")
    suspend fun getNotifications(
        @Query("unread_only") unreadOnly: Boolean = false,
        @Query("user_id") userId: String? = null
    ): List<NotificationDto>

    @GET("notifications/unread-count")
    suspend fun getUnreadNotificationCount(@Query("user_id") userId: String? = null): UnreadCountDto

    @PATCH("notifications/{notifId}/read")
    suspend fun markNotificationRead(
        @Path("notifId") notifId: String,
        @Query("user_id") userId: String? = null
    ): NotificationDto

    @POST("notifications/read-all")
    suspend fun markAllNotificationsRead(@Query("user_id") userId: String? = null)
}
