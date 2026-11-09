package com.pawfect.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ChatRequestDto(
    @SerialName("session_id") val sessionId: String,
    val message: String,
    @SerialName("user_id") val userId: String? = null,
    val stream: Boolean = false
)

@Serializable
data class ChatResponseDto(
    @SerialName("session_id") val sessionId: String,
    @SerialName("response_message") val responseMessage: String,
    @SerialName("quick_replies") val quickReplies: List<String> = emptyList(),
    @SerialName("is_complete") val isComplete: Boolean = false,
    @SerialName("candidate_matches") val candidateMatches: List<PetDto> = emptyList(),
    val evaluations: List<PetEvaluationDto> = emptyList()
)

@Serializable
data class PetEvaluationDto(
    @SerialName("pet_id") val petId: String,
    @SerialName("pet_name") val petName: String,
    @SerialName("compatibility_score") val compatibilityScore: Int,
    val pros: List<String> = emptyList(),
    val caveats: List<String> = emptyList(),
    @SerialName("reasoning_summary") val reasoningSummary: String
)

sealed class SseChatEvent {
    data class Typing(val status: String) : SseChatEvent()
    data class Token(val token: String) : SseChatEvent()
    data class QuickReplies(val quickReplies: List<String>) : SseChatEvent()
    data class Matches(val candidateMatches: List<PetDto>, val evaluations: List<PetEvaluationDto>) : SseChatEvent()
    data class Done(val responseMessage: String, val isComplete: Boolean) : SseChatEvent()
    data class Error(val throwable: Throwable) : SseChatEvent()
}

