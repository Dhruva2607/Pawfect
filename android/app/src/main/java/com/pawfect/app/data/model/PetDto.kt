package com.pawfect.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Pet Data Transfer Object matching backend Pet schema.
 * [FROM MARKDOWN: Step 1.1 & Step 3.1]
 */
@Serializable
data class PetDto(
    @SerialName("_id") val id: String,
    val name: String,
    val species: String,
    val breed: String,
    @SerialName("age_months") val ageMonths: Int,
    val gender: String,
    val size: String,
    @SerialName("energy_level") val energyLevel: Int,
    @SerialName("good_with_kids") val goodWithKids: Boolean,
    @SerialName("good_with_other_pets") val goodWithOtherPets: Boolean,
    val temperament: List<String> = emptyList(),
    @SerialName("housing_requirement") val housingRequirement: String,
    @SerialName("bio_text") val bioText: String,
    val quirks: List<String> = emptyList(),
    @SerialName("exercise_needs") val exerciseNeeds: String? = null,
    val triggers: List<String> = emptyList(),
    @SerialName("photo_url") val photoUrl: String? = null,
    val score: Double? = null
)

