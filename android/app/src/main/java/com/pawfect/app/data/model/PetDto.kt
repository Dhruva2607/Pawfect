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
    @SerialName("age_group") val ageGroup: String? = null,
    val gender: String,
    val size: String,
    @SerialName("weight_lbs") val weightLbs: Int? = null,
    @SerialName("energy_level") val energyLevel: Int,
    @SerialName("grooming_needs") val groomingNeeds: String? = null,
    @SerialName("shedding_level") val sheddingLevel: String? = null,
    @SerialName("noise_level") val noiseLevel: String? = null,
    @SerialName("alone_time_tolerance") val aloneTimeTolerance: String? = null,
    @SerialName("experience_level_required") val experienceLevelRequired: String? = null,
    @SerialName("training_level") val trainingLevel: String? = null,
    @SerialName("coat_type") val coatType: String? = null,
    @SerialName("special_needs") val specialNeeds: Boolean? = null,
    @SerialName("good_with_kids") val goodWithKids: Boolean,
    @SerialName("good_with_other_pets") val goodWithOtherPets: Boolean,
    val temperament: List<String> = emptyList(),
    @SerialName("housing_requirement") val housingRequirement: String,
    @SerialName("bio_text") val bioText: String,
    val quirks: List<String> = emptyList(),
    @SerialName("exercise_needs") val exerciseNeeds: String? = null,
    val triggers: List<String> = emptyList(),
    @SerialName("photo_url") val photoUrl: String? = null,
    @SerialName("shelter_id") val shelterId: String? = null,
    @SerialName("shelter_name") val shelterName: String? = null,
    @SerialName("shelter_city") val shelterCity: String? = null,
    val status: String? = null,
    val hypoallergenic: Boolean = false,
    @SerialName("embedding_pending") val embeddingPending: Boolean = false,
    val vaccinated: Boolean? = null,
    val neutered: Boolean? = null,
    val microchipped: Boolean? = null,
    @SerialName("adoption_fee") val adoptionFee: Double? = null,
    @SerialName("requires_yard") val requiresYard: Boolean? = null,
    @SerialName("min_experience") val minExperience: String? = null,
    @SerialName("not_suitable_for_young_children") val notSuitableForYoungChildren: Boolean? = null,
    @SerialName("ideal_adopter_notes") val idealAdopterNotes: String? = null,
    @SerialName("listed_at") val listedAt: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null,
    val score: Double? = null
)

