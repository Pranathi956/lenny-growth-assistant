const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function req(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => req('/health'),
  createSession: (payload) => req('/sessions', { method: 'POST', body: JSON.stringify(payload) }),
  getMessages: (sessionId) => req(`/sessions/${sessionId}/messages`),
  sendMessage: (payload) => req('/chat', { method: 'POST', body: JSON.stringify(payload) }),
  generateArtifact: (payload) => req('/artifacts', { method: 'POST', body: JSON.stringify(payload) }),
}
