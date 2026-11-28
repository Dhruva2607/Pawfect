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
import javax.inject.Named
import javax.inject.Singleton

/**
 * Real-time Server-Sent Events (SSE) client using OkHttp EventSource and Coroutines callbackFlow.
 * [FROM MARKDOWN: Section 4 & Step 4.1]
 * Streams conversational AI tokens from gemini in real time with low latency.
 */
@Singleton
class PawFectSseClient @Inject constructor(
    @Named("SseClient") private val okHttpClient: OkHttpClient,
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

        // OkHttp's EventSource reports onFailure in three situations we must not
        // surface as a chat error:
        //   1. a null throwable, when the server closes right after our own close
        //   2. a cancellation, when the collector goes away (tab switch / new turn)
        //   3. any failure after the terminal `done`/`error` event
        // Tracking this here stops the bogus "could not connect" message.
        var streamFinished = false
        var failureReceived = false
        var cancelled = false

        val listener = object : EventSourceListener() {
            override fun onOpen(eventSource: EventSource, response: Response) {
                if (!response.isSuccessful) {
                    Log.e(TAG, "SSE connection failed with HTTP ${response.code}.")
                    streamFinished = true
                    failureReceived = true
                    // 429 means "slow down", not "network broken". Say so, and
                    // surface the server's Retry-After when present.
                    val message = when (response.code) {
                        429 -> {
                            val wait = response.header("Retry-After")
                            if (wait.isNullOrBlank()) {
                                "You're sending messages too quickly. Please wait a moment and try again."
                            } else {
                                "You're sending messages too quickly. Please wait ${wait}s and try again."
                            }
                        }
                        401, 403 -> "Your session expired. Please sign in again."
                        else -> "The matchmaker is unavailable right now (HTTP ${response.code})."
                    }
                    trySend(SseChatEvent.Error(IllegalStateException(message)))
                    close()
                    return
                }
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
                            streamFinished = true
                            trySend(SseChatEvent.Done(responseMsg, isComplete))
                            close()
                        }
                        "error" -> {
                            val jsonObj = json.parseToJsonElement(data).jsonObject
                            val message = jsonObj["message"]?.jsonPrimitive?.content
                                ?: "The matchmaker could not process this message."
                            streamFinished = true
                            failureReceived = true
                            trySend(SseChatEvent.Error(IllegalStateException(message)))
                            close()
                        }
                        // Server keep-alive while the model is thinking. It
                        // proves the stream is healthy; nothing to render.
                        "ping" -> Unit
                        // `: comment` keep-alives from proxies arrive with no type.
                        null -> Unit
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
                // The collector cancelled us (tab switch, new turn, screen exit).
                if (cancelled) {
                    Log.d(TAG, "Ignoring SSE failure after cancellation.")
                    close()
                    return
                }
                // Terminal event already delivered; a null throwable here is the
                // transport noticing our own close, not a real failure.
                if (streamFinished) {
                    Log.d(TAG, "Ignoring post-completion SSE close: ${t?.message}")
                    close()
                    return
                }
                if (failureReceived) {
                    close()
                    return
                }

                val failure = t ?: Exception(
                    response?.let { "SSE connection failed with HTTP ${it.code}." }
                        ?: "SSE connection failure"
                )
                Log.e(TAG, "SSE Failure: ${failure.javaClass.simpleName}: ${failure.message}")
                streamFinished = true
                failureReceived = true
                trySend(SseChatEvent.Error(failure))
                // Close normally: closing *with* a cause rethrows it into the
                // collector, which surfaced a second, unhelpful error.
                close()
            }

            override fun onClosed(eventSource: EventSource) {
                Log.d(TAG, "SSE Connection Closed.")
                if (!streamFinished && !cancelled && !failureReceived) {
                    // Server hung up without a terminal event — tell the user
                    // instead of silently ending with a half-written answer.
                    Log.w(TAG, "Stream ended without a terminal event.")
                    trySend(
                        SseChatEvent.Error(
                            IllegalStateException("The connection ended before the reply finished.")
                        )
                    )
                }
                streamFinished = true
                close()
            }
        }

        val eventSource = factory.newEventSource(request, listener)

        awaitClose {
            // The collector has gone away; suppress the failure OkHttp will
            // report for the cancelled call.
            cancelled = true
            eventSource.cancel()
        }
    }
}
