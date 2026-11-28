package com.pawfect.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PetDimensionOptionDto(
    @SerialName("adopter_field") val adopterField: String,
    @SerialName("pet_field") val petField: String,
    @SerialName("allowed_values") val allowedValues: List<String> = emptyList(),
    @SerialName("display_labels") val displayLabels: Map<String, String> = emptyMap(),
    @SerialName("is_boolean") val isBoolean: Boolean = false,
    @SerialName("is_numeric") val isNumeric: Boolean = false,
    @SerialName("required_for_listing") val requiredForListing: Boolean = true
)

@Serializable
data class PetOptionsResponseDto(
    val dimensions: Map<String, PetDimensionOptionDto> = emptyMap(),
    @SerialName("alone_hours_mapping") val aloneHoursMapping: Map<String, String> = emptyMap(),
    @SerialName("housing_normalization") val housingNormalization: Map<String, String> = emptyMap()
)

@Serializable
data class ShelterDto(
    @SerialName("_id") val id: String,
    val name: String,
    val email: String,
    @SerialName("contact_phone") val contactPhone: String = "",
    val address: String = "",
    val city: String = "",
    val state: String = "",
    val country: String = "India",
    val description: String? = null,
    @SerialName("logo_url") val logoUrl: String? = null,
    val website: String? = null,
    @SerialName("operating_hours") val operatingHours: String? = null,
    @SerialName("registration_number") val registrationNumber: String? = null,
    val verified: Boolean = false,
    @SerialName("created_at") val createdAt: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null
)

@Serializable
data class ShelterAuthResponseDto(
    val token: String,
    val role: String = "shelter",
    val shelter: ShelterDto
)

@Serializable
data class ShelterSignupRequestDto(
    val name: String,
    val email: String,
    val password: String,
    @SerialName("contact_phone") val contactPhone: String,
    val address: String,
    val city: String,
    val state: String,
    val country: String = "India",
    val description: String? = null,
    @SerialName("operating_hours") val operatingHours: String? = null,
    val website: String? = null
)

@Serializable
data class ShelterLoginRequestDto(
    val email: String,
    val password: String
)

@Serializable
data class ShelterUpdateRequestDto(
    val name: String? = null,
    @SerialName("contact_phone") val contactPhone: String? = null,
    val address: String? = null,
    val city: String? = null,
    val state: String? = null,
    val country: String? = null,
    val description: String? = null,
    @SerialName("operating_hours") val operatingHours: String? = null,
    val website: String? = null
)

@Serializable
data class ShelterPetCreateRequestDto(
    val name: String,
    val species: String,
    val breed: String,
    @SerialName("age_months") val ageMonths: Int,
    val gender: String,
    val size: String,
    @SerialName("weight_lbs") val weightLbs: Int? = null,
    @SerialName("energy_level") val energyLevel: Int,
    @SerialName("grooming_needs") val groomingNeeds: String? = null,
    @SerialName("shedding_level") val sheddingLevel: String? = null,
    @SerialName("noise_level") val noiseLevel: String? = null,
    @SerialName("alone_time_tolerance") val aloneTimeTolerance: String? = null,
    @SerialName("experience_level_required") val experienceLevelRequired: String? = null,
    @SerialName("good_with_kids") val goodWithKids: Boolean,
    @SerialName("good_with_other_pets") val goodWithOtherPets: Boolean,
    @SerialName("housing_requirement") val housingRequirement: String,
    val hypoallergenic: Boolean = false,
    @SerialName("bio_text") val bioText: String,
    val temperament: List<String> = emptyList(),
    @SerialName("exercise_needs") val exerciseNeeds: String? = null,
    val vaccinated: Boolean? = null,
    val neutered: Boolean? = null,
    val microchipped: Boolean? = null,
    @SerialName("adoption_fee") val adoptionFee: Double? = null,
    @SerialName("ideal_adopter_notes") val idealAdopterNotes: String? = null,
    val status: String = "available"
)

@Serializable
data class PetStatusUpdateRequestDto(
    val status: String
)

@Serializable
data class PhotoUploadResponseDto(
    @SerialName("pet_id") val petId: String,
    @SerialName("photo_url") val photoUrl: String
)

@Serializable
data class ShelterApplicationDto(
    @SerialName("_id") val id: String,
    @SerialName("user_id") val userId: String,
    @SerialName("pet_id") val petId: String,
    @SerialName("shelter_id") val shelterId: String? = null,
    @SerialName("pet_name") val petName: String? = null,
    @SerialName("stage_status") val stageStatus: String,
    @SerialName("applicant_name") val applicantName: String,
    @SerialName("applicant_email") val applicantEmail: String,
    @SerialName("applicant_phone") val applicantPhone: String? = null,
    @SerialName("housing_details") val housingDetails: String? = null,
    @SerialName("household_members") val householdMembers: String? = null,
    val notes: String? = null,
    @SerialName("compatibility_score") val compatibilityScore: Int? = null,
    @SerialName("compatibility_reasoning") val compatibilityReasoning: String? = null,
    @SerialName("shelter_note") val shelterNote: String? = null,
    @SerialName("stage_history") val stageHistory: List<StageHistoryEntryDto> = emptyList(),
    @SerialName("submitted_at") val submittedAt: String,
    @SerialName("updated_at") val updatedAt: String
)

@Serializable
data class ShelterStageUpdateRequestDto(
    @SerialName("stage_status") val stageStatus: String,
    @SerialName("shelter_note") val shelterNote: String? = null
)

@Serializable
data class ShelterStatsDto(
    @SerialName("available_pets") val availablePets: Int = 0,
    @SerialName("pending_pets") val pendingPets: Int = 0,
    @SerialName("adopted_pets") val adoptedPets: Int = 0,
    @SerialName("total_pets") val totalPets: Int = 0,
    @SerialName("new_applications") val newApplications: Int = 0,
    @SerialName("in_review") val inReview: Int = 0,
    @SerialName("adopted_applications") val adoptedApplications: Int = 0,
    @SerialName("rejected_applications") val rejectedApplications: Int = 0,
    @SerialName("unread_notifications") val unreadNotifications: Int = 0
)

@Serializable
data class NotificationDto(
    @SerialName("_id") val id: String,
    @SerialName("recipient_role") val recipientRole: String,
    @SerialName("recipient_id") val recipientId: String,
    val type: String,
    val title: String,
    val message: String,
    @SerialName("pet_id") val petId: String? = null,
    @SerialName("pet_name") val petName: String? = null,
    @SerialName("application_id") val applicationId: String? = null,
    @SerialName("applicant_name") val applicantName: String? = null,
    val read: Boolean = false,
    @SerialName("created_at") val createdAt: String
)

@Serializable
data class UnreadCountDto(
    @SerialName("unread_count") val unreadCount: Int = 0
)
