package com.pawfect.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.model.PetEvaluationDto
import com.pawfect.app.data.model.SseChatEvent
import com.pawfect.app.data.model.StoredMatchResults
import com.pawfect.app.data.repository.ChatRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.Serializable
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject
import android.util.Log

@Serializable
data class UiChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val isUser: Boolean,
    val text: String,
    val isStreaming: Boolean = false
)

data class ChatUiState(
    val messages: List<UiChatMessage> = emptyList(),
    val isTyping: Boolean = false,
    val quickReplies: List<String> = emptyList(),
    val isComplete: Boolean = false,
    val candidateMatches: List<PetDto> = emptyList(),
    val evaluations: List<PetEvaluationDto> = emptyList(),
    val displayedMatchIndex: Int = 0,
    val sessionId: String,
    val error: String? = null
)

/**
 * ChatViewModel binding real-time SSE stream from FastAPI.
 * [FROM MARKDOWN: Section 4 & Screen 3]
 */
@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val json = Json { ignoreUnknownKeys = true }
    private val session = sessionManager.currentSession()
    private val sessionId = sessionManager.chatSessionId()
    private val _uiState = MutableStateFlow(
        ChatUiState(
            sessionId = sessionId,
            messages = loadMessages(),
            quickReplies = loadQuickReplies(),
            isComplete = sessionManager.isChatComplete(),
            candidateMatches = loadMatchResults().candidateMatches,
            evaluations = loadMatchResults().evaluations
        )
    )
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        if (_uiState.value.messages.isEmpty()) {
            _uiState.update {
                it.copy(messages = listOf(UiChatMessage(
                    isUser = false,
                    text = "Hi! I’m your PawFect matchmaker. Tell me what your home and daily life are like, and we’ll find a companion who fits."
                )))
            }
        }
    }

    fun sendMessage(text: String) {
        if (text.isBlank() || _uiState.value.isTyping) return

        val userMsg = UiChatMessage(isUser = true, text = text.trim())
        val botStreamingMsg = UiChatMessage(isUser = false, text = "", isStreaming = true)

        _uiState.update {
            it.copy(
                messages = it.messages + userMsg + botStreamingMsg,
                isTyping = true,
                quickReplies = emptyList(),
                candidateMatches = emptyList(),
                evaluations = emptyList(),
                displayedMatchIndex = 0,
                isComplete = false,
                error = null
            )
        }
        sessionManager.saveQuickRepliesJson("[]")
        sessionManager.saveChatComplete(false)

        val sessionId = _uiState.value.sessionId

        viewModelScope.launch {
            try {
                chatRepository.streamChat(
                    sessionId = sessionId,
                    message = text.trim(),
                    userId = session?.userId
                )
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
                                    state.copy(messages = updatedMessages)
                                }
                            }
                            is SseChatEvent.QuickReplies -> {
                                _uiState.update { it.copy(quickReplies = event.quickReplies) }
                                sessionManager.saveQuickRepliesJson(json.encodeToString(event.quickReplies))
                            }
                            is SseChatEvent.Matches -> {
                                _uiState.update {
                                    it.copy(
                                        candidateMatches = event.candidateMatches,
                                        evaluations = event.evaluations,
                                        displayedMatchIndex = 0,
                                        isComplete = true
                                    )
                                }
                                sessionManager.saveChatComplete(true)
                                persistMatches()
                            }
                            is SseChatEvent.Done -> {
                                _uiState.update { state ->
                                    val updatedMessages = state.messages.map { msg ->
                                        if (msg.id == botStreamingMsg.id) {
                                            msg.copy(
                                                text = msg.text.ifEmpty { event.responseMessage },
                                                isStreaming = false
                                            )
                                        } else msg
                                    }
                                    state.copy(
                                        messages = updatedMessages,
                                        isTyping = false,
                                        isComplete = event.isComplete || state.isComplete
                                    )
                                }
                                sessionManager.saveChatComplete(_uiState.value.isComplete)
                                persistMessages()
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
                                    state.copy(
                                        messages = updatedMessages,
                                        isTyping = false,
                                        error = event.throwable.localizedMessage
                                            ?: "The matchmaker could not connect. Please try again."
                                    )
                                }
                                persistMessages()
                            }
                        }
                    }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                _uiState.update { state ->
                    val updatedMessages = state.messages.map { message ->
                        if (message.id == botStreamingMsg.id) {
                            message.copy(
                                text = message.text.ifEmpty {
                                    "I couldn't reach the matchmaker. Please check your connection and try again."
                                },
                                isStreaming = false
                            )
                        } else {
                            message
                        }
                    }
                    state.copy(
                        messages = updatedMessages,
                        isTyping = false,
                        error = e.localizedMessage ?: "The matchmaker could not connect. Please try again."
                    )
                }
                persistMessages()
            }
        }
    }

    /**
     * Cycles the visible recommendation through the candidates already returned
     * by the backend, so "See other matches" shows a genuinely different pet
     * instead of asking the model for the same result again.
     */
    fun showNextMatch() {
        val count = minOf(
            _uiState.value.candidateMatches.size,
            _uiState.value.evaluations.size
        )
        if (count <= 1) return
        _uiState.update {
            it.copy(displayedMatchIndex = (it.displayedMatchIndex + 1) % count)
        }
    }

    private fun loadMessages(): List<UiChatMessage> = runCatching {
        sessionManager.conversationJson()?.let {
            json.decodeFromString<List<UiChatMessage>>(it).takeLast(MAX_PERSISTED_MESSAGES)
        }.orEmpty()
    }.getOrElse {
        Log.w("ChatViewModel", "Could not restore the local conversation.", it)
        emptyList()
    }

    private fun loadQuickReplies(): List<String> = runCatching {
        sessionManager.quickRepliesJson()?.let {
            json.decodeFromString<List<String>>(it)
        }.orEmpty()
    }.getOrElse {
        Log.w("ChatViewModel", "Could not restore quick replies.", it)
        emptyList()
    }

    private fun loadMatchResults(): StoredMatchResults = runCatching {
        sessionManager.matchResultsJson()?.let {
            json.decodeFromString<StoredMatchResults>(it)
        } ?: StoredMatchResults()
    }.getOrElse {
        Log.w("ChatViewModel", "Could not restore local match results.", it)
        StoredMatchResults()
    }

    private fun persistMessages() {
        try {
            val recentMessages = _uiState.value.messages
                .takeLast(MAX_PERSISTED_MESSAGES)
                .map { it.copy(isStreaming = false) }
            sessionManager.saveConversationJson(json.encodeToString(recentMessages))
        } catch (error: Exception) {
            Log.e("ChatViewModel", "Could not save the local conversation.", error)
            _uiState.update {
                it.copy(error = "Your chat could not be saved on this device.")
            }
        }
    }

    private fun persistMatches() {
        try {
            sessionManager.saveMatchResultsJson(
                json.encodeToString(
                    StoredMatchResults(
                        candidateMatches = _uiState.value.candidateMatches,
                        evaluations = _uiState.value.evaluations
                    )
                )
            )
        } catch (error: Exception) {
            Log.e("ChatViewModel", "Could not save local match results.", error)
            _uiState.update {
                it.copy(error = "Your latest matches could not be saved on this device.")
            }
        }
    }

    private companion object {
        const val MAX_PERSISTED_MESSAGES = 100
    }
}
