/**
 * API service communicating with the FastAPI backend at /api/v1.
 * Supports Vite proxy, direct localhost:8000 access, and fallback sample data.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';
const FALLBACK_HOST = 'http://localhost:8000/api/v1';

async function fetchWithFallback(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (res.ok) return res;
    // If proxy failed or 404, try direct localhost
    if (API_BASE !== FALLBACK_HOST) {
      const directRes = await fetch(`${FALLBACK_HOST}${endpoint}`, options);
      if (directRes.ok) return directRes;
    }
    return res;
  } catch (err) {
    if (API_BASE !== FALLBACK_HOST) {
      try {
        const directRes = await fetch(`${FALLBACK_HOST}${endpoint}`, options);
        if (directRes.ok) return directRes;
      } catch {
        // Fallback also failed
      }
    }
    throw err;
  }
}

function normalizePet(pet) {
  if (!pet) return pet;
  const id = pet._id || pet.id;
  return {
    ...pet,
    _id: id,
    id: id
  };
}

export async function listPets(filters = {}) {
  const params = new URLSearchParams();
  if (filters.species) params.append('species', filters.species);
  if (filters.size) params.append('size', filters.size);
  if (filters.goodWithKids !== undefined) params.append('good_with_kids', filters.goodWithKids);

  const queryStr = params.toString() ? `?${params.toString()}` : '';
  const res = await fetchWithFallback(`/pets${queryStr}`);
  if (!res.ok) throw new Error('Failed to fetch pets');
  
  const data = await res.json();
  const rawList = Array.isArray(data) ? data : (data.pets || []);
  return rawList.map(normalizePet);
}

export async function getPet(id) {
  const res = await fetchWithFallback(`/pets/${id}`);
  if (!res.ok) throw new Error(`Pet ${id} not found`);
  const data = await res.json();
  return normalizePet(data);
}

export async function directEval(payload) {
  const res = await fetchWithFallback('/matches/direct-eval', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to evaluate compatibility');
  return res.json();
}

export async function applyAdoption(payload) {
  const res = await fetchWithFallback('/adoptions/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to submit adoption application');
  return res.json();
}

export async function getAdoptionStatus(id) {
  const res = await fetchWithFallback(`/adoptions/${id}/status`);
  if (!res.ok) throw new Error('Failed to get application status');
  return res.json();
}

export async function getSavedPets(userId = 'user_default') {
  try {
    const res = await fetchWithFallback(`/users/${userId}/saved-pets`);
    if (!res.ok) return [];
    const data = await res.json();
    const rawList = Array.isArray(data) ? data : (data.saved_pets || []);
    return rawList.map(normalizePet);
  } catch {
    return [];
  }
}

export async function toggleFavorite(userId = 'user_default', petId) {
  const res = await fetchWithFallback(`/users/${userId}/favorite/${petId}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to toggle favorite');
  return res.json();
}

export async function getUserProfile(userId = 'user_default') {
  const res = await fetchWithFallback(`/users/${userId}/profile`);
  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json();
}

export async function updateUserProfile(userId, profileData) {
  const res = await fetchWithFallback(`/users/${userId}/profile`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profileData)
  });
  if (!res.ok) throw new Error('Failed to update profile');
  return res.json();
}

export async function loginUser(credentials) {
  try {
    const res = await fetchWithFallback('/users/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    if (res.ok) return await res.json();
  } catch {
    // Offline / demo fallback
  }

  // Fallback demo user
  return {
    user_id: 'user_' + credentials.email.split('@')[0],
    name: credentials.email.split('@')[0].replace('.', ' '),
    email: credentials.email,
    token: 'demo_token_' + Date.now(),
    housing_type: 'apartment',
    has_children: true,
    has_other_pets: false,
    energy_budget: 3
  };
}

export async function signupUser(userData) {
  try {
    const res = await fetchWithFallback('/users/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    if (res.ok) return await res.json();
  } catch {
    // Offline / demo fallback
  }

  return {
    user_id: 'user_' + userData.email.split('@')[0],
    name: userData.name || userData.email.split('@')[0],
    email: userData.email,
    token: 'token_' + Date.now(),
    housing_type: userData.housing_type || 'apartment',
    has_children: userData.has_children ?? true,
    has_other_pets: userData.has_other_pets ?? false,
    energy_budget: userData.energy_budget ?? 3
  };
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
    let response;
    try {
      response = await fetch(`${API_BASE}/chat/message`, {
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
    } catch {
      response = await fetch(`${FALLBACK_HOST}/chat/message`, {
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
    }

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

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data:')) continue;

        const dataStr = trimmed.replace(/^data:\s*/, '');
        try {
          const event = JSON.parse(dataStr);
          switch (event.event) {
            case 'typing':
              onTyping?.(event.data);
              break;
            case 'token':
              onToken?.(event.data.token);
              break;
            case 'quick_replies':
              onQuickReplies?.(event.data.options);
              break;
            case 'matches':
              onMatches?.(event.data.matches, event.data.evaluations);
              break;
            case 'done':
              onDone?.();
              break;
            case 'error':
              onError?.(new Error(event.data.message));
              break;
          }
        } catch (e) {
          console.warn('Error parsing SSE json chunk:', e);
        }
      }
    }
  } catch (err) {
    console.error('SSE streaming failed:', err);
    onError?.(err);
  }
}
