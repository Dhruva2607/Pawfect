package com.pawfect.app.data.local

import android.content.Context
import androidx.core.content.edit
import com.pawfect.app.data.model.ShelterAuthResponseDto
import com.pawfect.app.data.model.ShelterDto
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

data class ShelterSession(
    val shelterId: String,
    val name: String,
    val email: String,
    val token: String,
    val city: String,
    val verified: Boolean
)

@Singleton
class ShelterSessionManager @Inject constructor(
    @ApplicationContext context: Context
) {
    private val preferences = context.getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE)

    fun currentSession(): ShelterSession? {
        val shelterId = preferences.getString(KEY_SHELTER_ID, null) ?: return null
        val token = preferences.getString(KEY_TOKEN, null) ?: return null
        return ShelterSession(
            shelterId = shelterId,
            name = preferences.getString(KEY_NAME, "").orEmpty(),
            email = preferences.getString(KEY_EMAIL, "").orEmpty(),
            token = token,
            city = preferences.getString(KEY_CITY, "").orEmpty(),
            verified = preferences.getBoolean(KEY_VERIFIED, false)
        )
    }

    fun saveSession(response: ShelterAuthResponseDto) {
        preferences.edit {
            putString(KEY_SHELTER_ID, response.shelter.id)
            putString(KEY_NAME, response.shelter.name)
            putString(KEY_EMAIL, response.shelter.email)
            putString(KEY_TOKEN, response.token)
            putString(KEY_CITY, response.shelter.city)
            putBoolean(KEY_VERIFIED, response.shelter.verified)
        }
    }

    fun updateProfile(shelter: ShelterDto) {
        preferences.edit {
            putString(KEY_NAME, shelter.name)
            putString(KEY_CITY, shelter.city)
            putBoolean(KEY_VERIFIED, shelter.verified)
        }
    }

    fun logout() {
        preferences.edit { clear() }
    }

    private companion object {
        const val PREFERENCES_NAME = "pawfect_shelter_session"
        const val KEY_SHELTER_ID = "shelter_id"
        const val KEY_NAME = "name"
        const val KEY_EMAIL = "email"
        const val KEY_TOKEN = "token"
        const val KEY_CITY = "city"
        const val KEY_VERIFIED = "verified"
    }
}
