package com.pawfect.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class AuthRequestDto(
    val email: String,
    val password: String,
    val name: String? = null,
    @SerialName("housing_type") val housingType: String = "apartment",
    @SerialName("has_children") val hasChildren: Boolean = false,
    @SerialName("has_other_pets") val hasOtherPets: Boolean = false,
    @SerialName("energy_budget") val energyBudget: Int = 3
)

@Serializable
data class AuthResponseDto(
    @SerialName("user_id") val userId: String,
    val name: String,
    val email: String,
    val token: String,
    @SerialName("housing_type") val housingType: String? = null,
    @SerialName("has_children") val hasChildren: Boolean? = null,
    @SerialName("has_other_pets") val hasOtherPets: Boolean? = null,
    @SerialName("energy_budget") val energyBudget: Int? = null,
    @SerialName("saved_pets") val savedPets: List<String> = emptyList()
)

@Serializable
data class DirectEvalRequestDto(
    @SerialName("session_id") val sessionId: String,
    @SerialName("pet_id") val petId: String,
    @SerialName("housing_type") val housingType: String? = "apartment",
    @SerialName("has_children") val hasChildren: Boolean? = false,
    @SerialName("has_other_pets") val hasOtherPets: Boolean? = false,
    @SerialName("energy_budget") val energyBudget: Int? = 3,
    val notes: String? = null
)

@Serializable
data class DirectEvalResponseDto(
    @SerialName("pet_id") val petId: String,
    @SerialName("pet_name") val petName: String,
    @SerialName("compatibility_score") val compatibilityScore: Int,
    val pros: List<String> = emptyList(),
    val caveats: List<String> = emptyList(),
    @SerialName("reasoning_summary") val reasoningSummary: String
)

@Serializable
data class AdoptionApplyRequestDto(
    @SerialName("user_id") val userId: String,
    @SerialName("pet_id") val petId: String,
    @SerialName("applicant_name") val applicantName: String,
    @SerialName("applicant_email") val applicantEmail: String,
    @SerialName("applicant_phone") val applicantPhone: String? = null,
    @SerialName("housing_details") val housingDetails: String? = null,
    @SerialName("household_members") val householdMembers: String? = null,
    val notes: String? = null
)

@Serializable
data class AdoptionStatusResponseDto(
    @SerialName("application_id") val applicationId: String,
    @SerialName("user_id") val userId: String,
    @SerialName("pet_id") val petId: String,
    @SerialName("pet_name") val petName: String? = null,
    @SerialName("stage_status") val stageStatus: String,
    @SerialName("applicant_name") val applicantName: String,
    @SerialName("submitted_at") val submittedAt: String,
    @SerialName("updated_at") val updatedAt: String
)

@Serializable
data class UserProfileDto(
    @SerialName("_id") val id: String,
    val name: String,
    val email: String,
    @SerialName("avatar_url") val avatarUrl: String? = null,
    @SerialName("housing_type") val housingType: String? = null,
    @SerialName("has_children") val hasChildren: Boolean? = null,
    @SerialName("has_other_pets") val hasOtherPets: Boolean? = null,
    @SerialName("energy_budget") val energyBudget: Int? = null,
    @SerialName("saved_pets") val savedPets: List<String> = emptyList(),
    @SerialName("created_at") val createdAt: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null
)

@Serializable
data class UserProfileUpdateDto(
    val name: String? = null,
    val email: String? = null,
    @SerialName("avatar_url") val avatarUrl: String? = null,
    @SerialName("housing_type") val housingType: String? = null,
    @SerialName("has_children") val hasChildren: Boolean? = null,
    @SerialName("has_other_pets") val hasOtherPets: Boolean? = null,
    @SerialName("energy_budget") val energyBudget: Int? = null
)

@Serializable
data class FavoriteToggleResponseDto(
    @SerialName("user_id") val userId: String,
    @SerialName("pet_id") val petId: String,
    @SerialName("is_favorited") val isFavorited: Boolean,
    @SerialName("saved_pets_count") val savedPetsCount: Int
)
