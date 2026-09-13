import { useState } from 'react'

export default function ChatWindow({ onSend, onGenerateArtifact, disabled }) {
  const [text, setText] = useState('')

  function submit(e) {
    e.preventDefault()
    if (!text.trim()) return
    onSend(text)
    setText('')
  }

  return (
    <form className="chat-input" onSubmit={submit}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask a product/growth question, or say 'turn this into an essay for ship 30'…"
        rows={2}
        disabled={disabled}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) submit(e)
        }}
      />
      <div className="chat-input-actions">
        <button type="submit" disabled={disabled || !text.trim()}>Send</button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => onGenerateArtifact('markdown')}
          title="Generate a Markdown artifact from the conversation"
        >
          + Markdown artifact
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => onGenerateArtifact('html')}
          title="Generate an HTML artifact from the conversation"
        >
          + HTML artifact
        </button>
      </div>
    </form>
  )
}
