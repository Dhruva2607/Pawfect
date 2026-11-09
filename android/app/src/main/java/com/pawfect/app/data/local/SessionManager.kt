package com.pawfect.app.data.local

import android.content.Context
import androidx.core.content.edit
import com.pawfect.app.data.model.AuthResponseDto
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

data class UserSession(
    val userId: String,
    val name: String,
    val email: String,
    val token: String,
    val housingType: String,
    val hasChildren: Boolean,
    val hasOtherPets: Boolean,
    val energyBudget: Int
)

@Singleton
class SessionManager @Inject constructor(
    @ApplicationContext context: Context
) {
    private val preferences = context.getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE)

    fun currentSession(): UserSession? {
        val userId = preferences.getString(KEY_USER_ID, null) ?: return null
        val token = preferences.getString(KEY_TOKEN, null) ?: return null
        return UserSession(
            userId = userId,
            name = preferences.getString(KEY_NAME, "").orEmpty(),
            email = preferences.getString(KEY_EMAIL, "").orEmpty(),
            token = token,
            housingType = preferences.getString(KEY_HOUSING_TYPE, "apartment").orEmpty(),
            hasChildren = preferences.getBoolean(KEY_HAS_CHILDREN, false),
            hasOtherPets = preferences.getBoolean(KEY_HAS_OTHER_PETS, false),
            energyBudget = preferences.getInt(KEY_ENERGY_BUDGET, 3)
        )
    }

    fun saveSession(response: AuthResponseDto) {
        val chatSession = preferences.getString(KEY_CHAT_SESSION, null)
        preferences.edit {
            putString(KEY_USER_ID, response.userId)
            putString(KEY_NAME, response.name)
            putString(KEY_EMAIL, response.email)
            putString(KEY_TOKEN, response.token)
            putString(KEY_HOUSING_TYPE, response.housingType ?: "apartment")
            putBoolean(KEY_HAS_CHILDREN, response.hasChildren ?: false)
            putBoolean(KEY_HAS_OTHER_PETS, response.hasOtherPets ?: false)
            putInt(KEY_ENERGY_BUDGET, response.energyBudget ?: 3)
            if (chatSession.isNullOrBlank()) {
                putString(KEY_CHAT_SESSION, UUID.randomUUID().toString())
            }
        }
    }

    fun updateSession(
        name: String,
        email: String,
        housingType: String,
        hasChildren: Boolean,
        hasOtherPets: Boolean,
        energyBudget: Int
    ) {
        preferences.edit {
            putString(KEY_NAME, name)
            putString(KEY_EMAIL, email)
            putString(KEY_HOUSING_TYPE, housingType)
            putBoolean(KEY_HAS_CHILDREN, hasChildren)
            putBoolean(KEY_HAS_OTHER_PETS, hasOtherPets)
            putInt(KEY_ENERGY_BUDGET, energyBudget)
        }
    }

    fun chatSessionId(): String = preferences.getString(KEY_CHAT_SESSION, null)
        ?: UUID.randomUUID().toString().also { id ->
            preferences.edit { putString(KEY_CHAT_SESSION, id) }
        }

    fun logout() {
        preferences.edit {
            remove(KEY_USER_ID)
            remove(KEY_NAME)
            remove(KEY_EMAIL)
            remove(KEY_TOKEN)
            remove(KEY_HOUSING_TYPE)
            remove(KEY_HAS_CHILDREN)
            remove(KEY_HAS_OTHER_PETS)
            remove(KEY_ENERGY_BUDGET)
            remove(KEY_CHAT_SESSION)
            remove(KEY_CONVERSATION)
            remove(KEY_MATCH_RESULTS)
        }
    }

    fun conversationJson(): String? = preferences.getString(KEY_CONVERSATION, null)

    fun saveConversationJson(value: String) {
        preferences.edit { putString(KEY_CONVERSATION, value) }
    }

    fun matchResultsJson(): String? = preferences.getString(KEY_MATCH_RESULTS, null)

    fun saveMatchResultsJson(value: String) {
        preferences.edit { putString(KEY_MATCH_RESULTS, value) }
    }

    private companion object {
        const val PREFERENCES_NAME = "pawfect_session"
        const val KEY_USER_ID = "user_id"
        const val KEY_NAME = "name"
        const val KEY_EMAIL = "email"
        const val KEY_TOKEN = "token"
        const val KEY_HOUSING_TYPE = "housing_type"
        const val KEY_HAS_CHILDREN = "has_children"
        const val KEY_HAS_OTHER_PETS = "has_other_pets"
        const val KEY_ENERGY_BUDGET = "energy_budget"
        const val KEY_CHAT_SESSION = "chat_session"
        const val KEY_CONVERSATION = "conversation"
        const val KEY_MATCH_RESULTS = "match_results"
    }
}
