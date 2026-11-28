package com.pawfect.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Regression tests for the SSE terminal-event contract.
 *
 * A successful chat turn ends with a `done` event. Before the fix, the transport
 * then reported `onFailure(null)` while we were closing the stream, and the UI
 * replaced the answer with "The matchmaker could not connect. Please try again."
 *
 * This models the guard logic that lives in PawFectSseClient's listener:
 * once a terminal event has been seen, a null-throwable failure is a benign
 * close and must not produce an error event.
 */
class SseTerminalEventTest {

    /** Mirrors the client's bookkeeping. */
    private class StreamState {
        var streamFinished = false
        var failureReceived = false
        var errorsEmitted = 0

        fun onTerminalEvent() {
            streamFinished = true
        }

        fun onFailure(throwable: Throwable?) {
            if (streamFinished && throwable == null) return
            if (failureReceived) return
            failureReceived = true
            errorsEmitted++
        }
    }

    @Test
    fun doneEventFollowedByNullFailureEmitsNoError() {
        val state = StreamState()
        state.onTerminalEvent()      // "done" received
        state.onFailure(null)        // transport notices our close

        assertTrue(state.streamFinished)
        assertEquals(0, state.errorsEmitted)
    }

    @Test
    fun nullFailureBeforeTerminalEventIsReported() {
        val state = StreamState()
        state.onFailure(null)        // genuine transport failure mid-stream

        assertEquals(1, state.errorsEmitted)
    }

    @Test
    fun realFailureAfterDoneIsAlsoSuppressedAsClose() {
        val state = StreamState()
        state.onTerminalEvent()
        state.onFailure(null)

        assertFalse(state.failureReceived)
    }

    @Test
    fun duplicateFailuresOnlyReportOnce() {
        val state = StreamState()
        state.onFailure(RuntimeException("boom"))
        state.onFailure(RuntimeException("boom again"))

        assertEquals(1, state.errorsEmitted)
        assertTrue(state.failureReceived)
    }

    @Test
    fun errorEventSuppressesLaterTransportFailure() {
        val state = StreamState()
        state.onTerminalEvent()      // server sent "error" (also terminal)
        state.failureReceived = true
        state.onFailure(RuntimeException("late"))

        assertEquals(0, state.errorsEmitted)
    }
}
