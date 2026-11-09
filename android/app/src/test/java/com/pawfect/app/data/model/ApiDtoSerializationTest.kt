package com.pawfect.app.data.model

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.encodeToJsonElement
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Test

class ApiDtoSerializationTest {
    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    @Test
    fun petResponseDecodesBackendFields() {
        val pet = json.decodeFromString<PetDto>(
            """
            {
              "_id": "pet_123",
              "name": "Milo",
              "species": "dog",
              "breed": "Mixed",
              "age_months": 24,
              "gender": "Male",
              "size": "medium",
              "energy_level": 3,
              "good_with_kids": true,
              "good_with_other_pets": false,
              "housing_requirement": "apartment",
              "bio_text": "Friendly and calm.",
              "photo_url": "https://example.com/milo.jpg"
            }
            """.trimIndent()
        )

        assertEquals("pet_123", pet.id)
        assertEquals(24, pet.ageMonths)
        assertEquals("https://example.com/milo.jpg", pet.photoUrl)
    }

    @Test
    fun authRequestEncodesBackendFieldNames() {
        val request = AuthRequestDto(
            email = "adopter@example.com",
            password = "secure-password",
            name = "Alex",
            housingType = "house_with_yard",
            hasChildren = true,
            hasOtherPets = false,
            energyBudget = 4
        )

        val encoded = json.encodeToJsonElement(AuthRequestDto.serializer(), request).jsonObject

        assertEquals("house_with_yard", encoded.getValue("housing_type").jsonPrimitive.content)
        assertEquals("true", encoded.getValue("has_children").jsonPrimitive.content)
        assertEquals("false", encoded.getValue("has_other_pets").jsonPrimitive.content)
        assertEquals("4", encoded.getValue("energy_budget").jsonPrimitive.content)
    }

    @Test
    fun authResponseDecodesBackendUserAndPreferenceFields() {
        val response = json.decodeFromString<AuthResponseDto>(
            """
            {
              "user_id": "user_alex",
              "name": "Alex",
              "email": "adopter@example.com",
              "token": "token_user_alex",
              "housing_type": "apartment",
              "has_children": false,
              "has_other_pets": true,
              "energy_budget": 2,
              "saved_pets": []
            }
            """.trimIndent()
        )

        assertEquals("user_alex", response.userId)
        assertEquals(true, response.hasOtherPets)
        assertEquals(2, response.energyBudget)
    }
}
