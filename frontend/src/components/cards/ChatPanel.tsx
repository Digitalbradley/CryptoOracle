import { useRef, useState, useEffect, type FormEvent, type KeyboardEvent } from 'react';
import { useChat } from '../../hooks/useChat';

export default function ChatPanel() {
  const { messages, sendMessage, isLoading } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    sendMessage(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div style={{ borderTop: '1px solid var(--border-primary)' }}>
      {/* Messages area */}
      <div
        style={{
          maxHeight: 320,
          overflowY: 'auto',
          padding: '12px 0',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {messages.length === 0 && (
          <p
            className="text-xs"
            style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '16px 0' }}
          >
            Ask a question about the current signals...
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '8px 12px',
                borderRadius: 8,
                fontSize: 13,
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
                ...(msg.role === 'user'
                  ? {
                      backgroundColor: 'rgba(212, 168, 70, 0.12)',
                      borderRight: '2px solid var(--accent-gold)',
                      color: 'var(--text-primary)',
                    }
                  : {
                      backgroundColor: 'var(--surface-secondary, rgba(255,255,255,0.04))',
                      color: 'var(--text-secondary)',
                    }),
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                backgroundColor: 'var(--surface-secondary, rgba(255,255,255,0.04))',
              }}
            >
              <span className="typing-dots" style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                Thinking
                <span className="dot">.</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          gap: 8,
          padding: '8px 0 0',
          borderTop: '1px solid var(--border-primary)',
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about signals..."
          rows={1}
          disabled={isLoading}
          style={{
            flex: 1,
            resize: 'none',
            border: '1px solid var(--border-primary)',
            borderRadius: 6,
            padding: '8px 10px',
            fontSize: 13,
            fontFamily: 'inherit',
            backgroundColor: 'var(--surface-primary, #0a0b0f)',
            color: 'var(--text-primary)',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          style={{
            padding: '8px 16px',
            borderRadius: 6,
            border: 'none',
            backgroundColor:
              isLoading || !input.trim()
                ? 'rgba(212, 168, 70, 0.3)'
                : 'var(--accent-gold)',
            color: '#0a0b0f',
            fontWeight: 600,
            fontSize: 13,
            cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          Send
        </button>
      </form>

      <style>{`
        .typing-dots .dot {
          animation: blink 1.4s infinite both;
        }
        .typing-dots .dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink {
          0%, 20% { opacity: 0; }
          50% { opacity: 1; }
          100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
