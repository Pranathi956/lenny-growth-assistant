import ReactMarkdown from 'react-markdown'

export default function MessageList({ messages, loading }) {
  return (
    <div className="message-list">
      {messages.map((m, i) => (
        <div key={i} className={`message ${m.role}`}>
          <div className="message-role">{m.role === 'user' ? 'You' : 'Assistant'}</div>
          <div className="message-content">
            <ReactMarkdown>{m.content}</ReactMarkdown>
          </div>
          {m.sources && m.sources.length > 0 && (
            <div className="message-sources">
              <details>
                <summary>{m.sources.length} source{m.sources.length > 1 ? 's' : ''}</summary>
                {m.sources.map((s, j) => (
                  <div key={j} className="source-item">
                    <strong>{s.title}</strong>
                    <p>{s.snippet}…</p>
                  </div>
                ))}
              </details>
            </div>
          )}
        </div>
      ))}
      {loading && <div className="message assistant loading">Thinking…</div>}
    </div>
  )
}
