package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.model.PetEvaluationDto
import com.pawfect.app.data.model.SseChatEvent
import com.pawfect.app.data.repository.ChatRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class UiChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val isUser: Boolean,
    val text: String,
    val isStreaming: Boolean = false
)

data class ChatUiState(
    val messages: List<UiChatMessage> = emptyList(),
    val isTyping: Boolean = false,
    val quickReplies: List<String> = listOf("I am looking for a dog", "I want a calm cat", "Apartment friendly"),
    val isComplete: Boolean = false,
    val candidateMatches: List<PetDto> = emptyList(),
    val evaluations: List<PetEvaluationDto> = emptyList(),
    val sessionId: String = UUID.randomUUID().toString()
)

/**
 * ChatViewModel binding real-time SSE stream from FastAPI.
 * [FROM MARKDOWN: Section 4 & Screen 3]
 */
@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        // Welcome counselor message
        val welcomeMsg = UiChatMessage(
            isUser = false,
            text = "Hello! I am your AI Pet Adoption Counselor at PawFect. 🐾\nTell me about your home and lifestyle—do you live in an apartment or house? Any kids or other pets?"
        )
        _uiState.update { it.copy(messages = listOf(welcomeMsg)) }
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        val userMsg = UiChatMessage(isUser = true, text = text)
        val botStreamingMsg = UiChatMessage(isUser = false, text = "", isStreaming = true)

        _uiState.update {
            it.copy(
                messages = it.messages + userMsg + botStreamingMsg,
                isTyping = true,
                quickReplies = emptyList()
            )
        }

        val sessionId = _uiState.value.sessionId

        viewModelScope.launch {
            try {
                chatRepository.streamChat(sessionId = sessionId, message = text, userId = "user_default")
                    .collect { event ->
                        when (event) {
                            is SseChatEvent.Typing -> {
                                _uiState.update { it.copy(isTyping = true) }
                            }
                            is SseChatEvent.Token -> {
                                _uiState.update { state ->
                                    val updatedMessages = state.messages.map { msg ->
                                        if (msg.id == botStreamingMsg.id) {
                                            msg.copy(text = msg.text + event.token)
                                        } else msg
                                    }
                                    state.copy(messages = updatedMessages, isTyping = false)
                                }
                            }
                            is SseChatEvent.QuickReplies -> {
                                _uiState.update { it.copy(quickReplies = event.quickReplies) }
                            }
                            is SseChatEvent.Matches -> {
                                _uiState.update {
                                    it.copy(
                                        candidateMatches = event.candidateMatches,
                                        evaluations = event.evaluations,
                                        isComplete = true
                                    )
                                }
                            }
                            is SseChatEvent.Done -> {
                                _uiState.update { state ->
                                    val updatedMessages = state.messages.map { msg ->
                                        if (msg.id == botStreamingMsg.id) {
                                            msg.copy(isStreaming = false)
                                        } else msg
                                    }
                                    state.copy(
                                        messages = updatedMessages,
                                        isTyping = false,
                                        isComplete = event.isComplete || state.isComplete
                                    )
                                }
                            }
                            is SseChatEvent.Error -> {
                                _uiState.update { state ->
                                    val updatedMessages = state.messages.map { msg ->
                                        if (msg.id == botStreamingMsg.id && msg.text.isEmpty()) {
                                            msg.copy(
                                                text = "I encountered an error connecting to the matchmaker. Please check that the backend is running.",
                                                isStreaming = false
                                            )
                                        } else msg.copy(isStreaming = false)
                                    }
                                    state.copy(messages = updatedMessages, isTyping = false)
                                }
                            }
                        }
                    }
            } catch (e: Exception) {
                _uiState.update { it.copy(isTyping = false) }
            }
        }
    }
}

