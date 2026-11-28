package com.pawfect.app.data.model

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Contract tests for the near-match disclosure fields introduced with the
 * honest-relaxation change. The backend sets `is_relaxed_match` /
 * `relaxed_fields` on candidates it had to relax preferences for; the client
 * must decode them so the UI can warn instead of implying an exact fit.
 */
class PetDtoRelaxedMatchTest {

    private val json = Json { ignoreUnknownKeys = true }

    private fun basePetJson(extra: String = "") = """
        {
          "_id": "pet_dog_001",
          "name": "Buddy",
          "species": "dog",
          "breed": "Golden Retriever",
          "age_months": 24,
          "gender": "Male",
          "size": "medium",
          "energy_level": 3,
          "good_with_kids": true,
          "good_with_other_pets": true,
          "housing_requirement": "apartment_or_house",
          "bio_text": "Friendly dog."
          $extra
        }
    """.trimIndent()

    @Test
    fun relaxedFieldsDecode() {
        val pet = json.decodeFromString<PetDto>(
            basePetJson(
                """
                ,"is_relaxed_match": true,
                 "relaxed_fields": ["housing_type", "energy_budget"]
                """.trimIndent()
            )
        )

        assertTrue(pet.isRelaxedMatch)
        assertEquals(listOf("housing_type", "energy_budget"), pet.relaxedFields)
    }

    @Test
    fun exactMatchDefaultsToNotRelaxed() {
        val pet = json.decodeFromString<PetDto>(basePetJson())

        assertFalse(pet.isRelaxedMatch)
        assertTrue(pet.relaxedFields.isEmpty())
    }

    @Test
    fun relaxedFlagWithoutFieldsStillDecodes() {
        val pet = json.decodeFromString<PetDto>(
            basePetJson(""","is_relaxed_match": true""")
        )

        assertTrue(pet.isRelaxedMatch)
        assertTrue(pet.relaxedFields.isEmpty())
    }
}
