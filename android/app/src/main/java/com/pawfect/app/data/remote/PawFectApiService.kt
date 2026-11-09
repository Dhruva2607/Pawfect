package com.pawfect.app.data.remote

import com.pawfect.app.data.model.*
import retrofit2.http.*

/**
 * Retrofit 2 REST API endpoints.
 * [FROM MARKDOWN: Section 4 & Step 4.1]
 */
interface PawFectApiService {

    @GET("pets")
    suspend fun listPets(
        @Query("species") species: String? = null,
        @Query("size") size: String? = null,
        @Query("good_with_kids") goodWithKids: Boolean? = null,
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

    @POST("adoptions/apply")
    suspend fun applyAdoption(@Body request: AdoptionApplyRequestDto): AdoptionStatusResponseDto

    @GET("adoptions/{id}/status")
    suspend fun getAdoptionStatus(@Path("id") id: String): AdoptionStatusResponseDto

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
}
