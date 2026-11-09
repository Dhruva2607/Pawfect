package com.pawfect.app.data.remote

import android.util.Log
import com.pawfect.app.data.model.PetDto
import com.pawfect.app.data.model.PetEvaluationDto
import com.pawfect.app.data.model.ChatRequestDto
import com.pawfect.app.data.model.SseChatEvent
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.encodeToString
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Real-time Server-Sent Events (SSE) client using OkHttp EventSource and Coroutines callbackFlow.
 * [FROM MARKDOWN: Section 4 & Step 4.1]
 * Streams conversational AI tokens from gemini in real time with low latency.
 */
@Singleton
class PawFectSseClient @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val json: Json
) {
    companion object {
        private const val TAG = "PawFectSseClient"
    }

    fun streamChatMessage(
        baseUrl: String,
        sessionId: String,
        message: String,
        userId: String? = null
    ): Flow<SseChatEvent> = callbackFlow {
        val payloadJson = json.encodeToString(
            ChatRequestDto(
                sessionId = sessionId,
                message = message,
                userId = userId,
                stream = true
            )
        )

        val request = Request.Builder()
            .url("${baseUrl}chat/message")
            .header("Accept", "text/event-stream")
            .post(payloadJson.toRequestBody("application/json".toMediaType()))
            .build()

        val factory = EventSources.createFactory(okHttpClient)

        val listener = object : EventSourceListener() {
            override fun onOpen(eventSource: EventSource, response: Response) {
                Log.d(TAG, "SSE Connection Opened.")
            }

            override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
                try {
                    when (type) {
                        "typing" -> {
                            val jsonObj = json.parseToJsonElement(data).jsonObject
                            val status = jsonObj["status"]?.jsonPrimitive?.content ?: "thinking"
                            trySend(SseChatEvent.Typing(status))
                        }
                        "token" -> {
                            val jsonObj = json.parseToJsonElement(data).jsonObject
                            val token = jsonObj["token"]?.jsonPrimitive?.content ?: ""
                            trySend(SseChatEvent.Token(token))
                        }
                        "quick_replies" -> {
                            val jsonObj = json.parseToJsonElement(data).jsonObject
                            val list = jsonObj["quick_replies"]?.jsonArray
                                ?.map { it.jsonPrimitive.content }
                                .orEmpty()
                            trySend(SseChatEvent.QuickReplies(list))
                        }
                        "matches" -> {
                            val jsonObj = json.parseToJsonElement(data).jsonObject
                            val matchesJson = jsonObj["candidate_matches"]
                            val evalsJson = jsonObj["evaluations"]

                            val matches = if (matchesJson != null) {
                                json.decodeFromJsonElement(
                                    kotlinx.serialization.builtins.ListSerializer(PetDto.serializer()),
                                    matchesJson
                                )
                            } else emptyList()

                            val evals = if (evalsJson != null) {
                                json.decodeFromJsonElement(
                                    kotlinx.serialization.builtins.ListSerializer(PetEvaluationDto.serializer()),
                                    evalsJson
                                )
                            } else emptyList()

                            trySend(SseChatEvent.Matches(matches, evals))
                        }
                        "done" -> {
                            val jsonObj = json.parseToJsonElement(data).jsonObject
                            val responseMsg = jsonObj["response_message"]?.jsonPrimitive?.content ?: ""
                            val isComplete = jsonObj["is_complete"]?.jsonPrimitive?.booleanOrNull ?: false
                            trySend(SseChatEvent.Done(responseMsg, isComplete))
                            close()
                        }
                        "error" -> {
                            val jsonObj = json.parseToJsonElement(data).jsonObject
                            val message = jsonObj["message"]?.jsonPrimitive?.content
                                ?: "The matchmaker could not process this message."
                            trySend(SseChatEvent.Error(IllegalStateException(message)))
                            close()
                        }
                        else -> {
                            Log.d(TAG, "Unhandled SSE Event: $type, data: $data")
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error parsing SSE data: $data", e)
                    trySend(SseChatEvent.Error(e))
                }
            }

            override fun onFailure(eventSource: EventSource, t: Throwable?, response: Response?) {
                Log.e(TAG, "SSE Failure: ${t?.message}")
                trySend(SseChatEvent.Error(t ?: Exception("SSE connection failure")))
                close(t)
            }

            override fun onClosed(eventSource: EventSource) {
                Log.d(TAG, "SSE Connection Closed.")
                close()
            }
        }

        val eventSource = factory.newEventSource(request, listener)

        awaitClose {
            eventSource.cancel()
        }
    }
}
