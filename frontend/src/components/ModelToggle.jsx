export default function ModelToggle({ provider, onChange, health }) {
  return (
    <div className="model-toggle">
      <span className="model-toggle-label">Model:</span>
      <button
        className={provider === 'ollama' ? 'active' : ''}
        onClick={() => onChange('ollama')}
        title="Local model via Ollama"
      >
        Local (Ollama)
      </button>
      <button
        className={provider === 'groq' ? 'active' : ''}
        onClick={() => onChange('groq')}
        title="Cloud model via Groq API (free tier)"
      >
        Cloud (Groq)
      </button>
      {health && (
        <span className={`health-dot ${health.database === 'ok' ? 'ok' : 'bad'}`} title={`DB: ${health.database}, transcripts indexed: ${health.transcripts_indexed}`}>
          ●
        </span>
      )}
    </div>
  )
}
