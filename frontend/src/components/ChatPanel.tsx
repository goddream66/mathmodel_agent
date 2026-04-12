type ChatPanelProps = {
  messages: string[];
  draftMessage: string;
  busy: boolean;
  onDraftChange: (value: string) => void;
  onSend: () => void;
};

export function ChatPanel(props: ChatPanelProps) {
  const { messages, draftMessage, busy, onDraftChange, onSend } = props;

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Conversation</p>
          <h2>Multi-turn Modeling Brief</h2>
        </div>
        <span className="pill">{messages.length} messages</span>
      </div>

      <div className="chat-stream">
        {messages.length === 0 ? (
          <div className="empty-state">
            Start by pasting the problem statement, then keep adding constraints, data hints, or writing requirements.
          </div>
        ) : (
          messages.map((message, index) => (
            <article className="message-card" key={`${index}-${message.slice(0, 12)}`}>
              <div className="message-meta">User Input {index + 1}</div>
              <p>{message}</p>
            </article>
          ))
        )}
      </div>

      <div className="composer">
        <textarea
          value={draftMessage}
          onChange={(event) => onDraftChange(event.target.value)}
          placeholder="Describe the problem, then keep refining it over multiple turns."
          rows={5}
        />
        <button className="accent-button" disabled={busy || !draftMessage.trim()} onClick={onSend}>
          Add Message
        </button>
      </div>
    </section>
  );
}
