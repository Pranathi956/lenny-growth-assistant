import ReactMarkdown from 'react-markdown'

/**
 * Renders generated artifacts beside the chat.
 *
 * Security note (see architecture.md "Security expectation"): model-
 * generated HTML is treated as fully untrusted. It's rendered inside an
 * <iframe sandbox="allow-same-origin"> with NO "allow-scripts" -- so any
 * <script> tag the model produces simply will not execute, and the
 * backend additionally strips <script> tags and inline event handlers
 * (on click= etc.) as a second layer of defense. Markdown artifacts are
 * rendered through react-markdown, which does not execute raw HTML by
 * default.
 */
export default function ArtifactViewer({ artifact, onClose }) {
  if (!artifact) {
    return (
      <div className="artifact-viewer empty">
        <p>Generated artifacts (Markdown docs or HTML snippets) will appear here.</p>
        <p className="hint">Try: "turn this into an essay for ship 30" or "make an HTML summary card of this".</p>
      </div>
    )
  }

  return (
    <div className="artifact-viewer">
      <div className="artifact-header">
        <span>{artifact.title || 'Artifact'} <em>({artifact.kind})</em></span>
        <button onClick={onClose}>✕</button>
      </div>
      <div className="artifact-body">
        {artifact.kind === 'markdown' ? (
          <ReactMarkdown>{artifact.content}</ReactMarkdown>
        ) : (
          <iframe
            title="artifact-html-preview"
            className="artifact-iframe"
            sandbox="allow-same-origin"
            srcDoc={artifact.content}
          />
        )}
      </div>
      <details className="artifact-raw">
        <summary>View raw source</summary>
        <pre>{artifact.content}</pre>
      </details>
    </div>
  )
}
