package com.pawfect.app

import com.pawfect.app.data.model.*
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ShelterDtoSerializationTest {
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
    }

    @Test
    fun petOptionsResponse_deserializesCorrectly() {
        val raw = """
            {
              "dimensions": {
                "species": {
                  "adopter_field": "species",
                  "pet_field": "species",
                  "allowed_values": ["dog", "cat"],
                  "display_labels": {"dog": "Dog", "cat": "Cat"},
                  "is_boolean": false,
                  "is_numeric": false,
                  "required_for_listing": true
                }
              },
              "alone_hours_mapping": {"0-3": "low", "4-5": "moderate", "6+": "high"},
              "housing_normalization": {"house_without_yard": "No yard"}
            }
        """.trimIndent()

        val parsed = json.decodeFromString<PetOptionsResponseDto>(raw)
        assertEquals(listOf("dog", "cat"), parsed.dimensions["species"]?.allowedValues)
        assertEquals("high", parsed.aloneHoursMapping["6+"])
    }

    @Test
    fun petDto_isBackwardCompatibleWithLegacyAndShelterPayloads() {
        val raw = """
            {
              "_id": "pet_dog_001",
              "name": "Mochi",
              "species": "dog",
              "breed": "Beagle",
              "age_months": 18,
              "gender": "Female",
              "size": "medium",
              "energy_level": 3,
              "good_with_kids": true,
              "good_with_other_pets": true,
              "housing_requirement": "apartment_or_house",
              "bio_text": "Gentle beagle.",
              "shelter_id": "shelter_1",
              "shelter_name": "Happy Paws",
              "shelter_city": "Bengaluru",
              "status": "available",
              "hypoallergenic": true
            }
        """.trimIndent()

        val pet = json.decodeFromString<PetDto>(raw)
        assertEquals("Happy Paws", pet.shelterName)
        assertEquals("Bengaluru", pet.shelterCity)
        assertTrue(pet.hypoallergenic)
    }

    @Test
    fun adoptionStatus_deserializesRejectedAndStageHistory() {
        val raw = """
            {
              "application_id": "app_1",
              "user_id": "u_1",
              "pet_id": "p_1",
              "pet_name": "Mochi",
              "shelter_id": "s_1",
              "stage_status": "rejected",
              "applicant_name": "Priya",
              "shelter_note": "Adopted by another family",
              "compatibility_score": 91,
              "stage_history": [
                {"stage": "apply", "timestamp": "2026-11-28T09:00:00Z", "note": "Submitted"},
                {"stage": "rejected", "timestamp": "2026-11-28T10:00:00Z", "note": "Adopted by another family"}
              ],
              "submitted_at": "2026-11-28T09:00:00Z",
              "updated_at": "2026-11-28T10:00:00Z"
            }
        """.trimIndent()

        val status = json.decodeFromString<AdoptionStatusResponseDto>(raw)
        assertEquals("rejected", status.stageStatus)
        assertEquals(2, status.stageHistory.size)
        assertEquals(91, status.compatibilityScore)
    }
}
