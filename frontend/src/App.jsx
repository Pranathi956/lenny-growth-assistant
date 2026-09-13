import { useEffect, useState } from 'react'
import { api } from './api'
import ModelToggle from './components/ModelToggle'
import MessageList from './components/MessageList'
import ChatWindow from './components/ChatWindow'
import ArtifactViewer from './components/ArtifactViewer'

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [provider, setProvider] = useState('ollama')
  const [loading, setLoading] = useState(false)
  const [artifact, setArtifact] = useState(null)
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => {})
    api.createSession({ llm_provider: provider })
      .then((s) => setSessionId(s.id))
      .catch((e) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleNewSession() {
    setError(null)
    const s = await api.createSession({ llm_provider: provider })
    setSessionId(s.id)
    setMessages([])
    setArtifact(null)
  }

  async function handleSend(text) {
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const resp = await api.sendMessage({ session_id: sessionId, message: text, llm_provider: provider })
      setMessages((prev) => [...prev, { role: 'assistant', content: resp.reply, sources: resp.sources }])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerateArtifact(kind) {
    setError(null)
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')
    const instructions = lastUserMsg
      ? `Based on the conversation, create a ${kind} artifact summarizing: ${lastUserMsg.content}`
      : `Create a starter ${kind} artifact.`
    setLoading(true)
    try {
      const art = await api.generateArtifact({ session_id: sessionId, kind, instructions })
      setArtifact(art)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Lenny Growth Assistant</h1>
        <div className="header-actions">
          <ModelToggle provider={provider} onChange={setProvider} health={health} />
          <button onClick={handleNewSession}>New chat</button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="app-main">
        <section className="chat-panel">
          <MessageList messages={messages} loading={loading} />
          <ChatWindow onSend={handleSend} onGenerateArtifact={handleGenerateArtifact} disabled={loading || !sessionId} />
        </section>
        <section className="artifact-panel">
          <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />
        </section>
      </main>
    </div>
  )
}
