/**
 * API service communicating with the FastAPI backend at /api/v1.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function listPets(filters = {}) {
  const params = new URLSearchParams();
  if (filters.species) params.append('species', filters.species);
  if (filters.size) params.append('size', filters.size);
  if (filters.goodWithKids !== undefined) params.append('good_with_kids', filters.goodWithKids);

  const res = await fetch(`${BASE_URL}/pets?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch pets');
  return res.json();
}

export async function getPet(id) {
  const res = await fetch(`${BASE_URL}/pets/${id}`);
  if (!res.ok) throw new Error(`Pet ${id} not found`);
  return res.json();
}

export async function directEval(payload) {
  const res = await fetch(`${BASE_URL}/matches/direct-eval`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to evaluate compatibility');
  return res.json();
}

export async function applyAdoption(payload) {
  const res = await fetch(`${BASE_URL}/adoptions/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to submit adoption application');
  return res.json();
}

export async function getAdoptionStatus(id) {
  const res = await fetch(`${BASE_URL}/adoptions/${id}/status`);
  if (!res.ok) throw new Error('Failed to get application status');
  return res.json();
}

export async function getSavedPets(userId = 'user_default') {
  const res = await fetch(`${BASE_URL}/users/${userId}/saved-pets`);
  if (!res.ok) throw new Error('Failed to fetch saved pets');
  return res.json();
}

export async function toggleFavorite(userId = 'user_default', petId) {
  const res = await fetch(`${BASE_URL}/users/${userId}/favorite/${petId}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to toggle favorite');
  return res.json();
}

export async function getUserProfile(userId = 'user_default') {
  const res = await fetch(`${BASE_URL}/users/${userId}/profile`);
  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json();
}

/**
 * Streams chat messages using Server-Sent Events (SSE) from POST /api/v1/chat/message.
 */
export async function streamChatMessage({
  sessionId,
  message,
  userId = 'user_default',
  onTyping,
  onToken,
  onQuickReplies,
  onMatches,
  onDone,
  onError
}) {
  try {
    const response = await fetch(`${BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
        user_id: userId,
        stream: true
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = 'message';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.replace('event:', '').trim();
        } else if (trimmed.startsWith('data:')) {
          const dataStr = trimmed.replace('data:', '').trim();
          try {
            const data = JSON.parse(dataStr);
            if (currentEvent === 'typing' && onTyping) onTyping(data);
            if (currentEvent === 'token' && onToken) onToken(data.token);
            if (currentEvent === 'quick_replies' && onQuickReplies) onQuickReplies(data.quick_replies);
            if (currentEvent === 'matches' && onMatches) onMatches(data);
            if (currentEvent === 'done' && onDone) onDone(data);
          } catch (e) {
            // raw string data
            if (currentEvent === 'token' && onToken) onToken(dataStr);
          }
        }
      }
    }
  } catch (err) {
    console.error('SSE streaming error:', err);
    if (onError) onError(err);
  }
}
