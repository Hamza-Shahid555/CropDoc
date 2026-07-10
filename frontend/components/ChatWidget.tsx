"use client";

import { useEffect, useRef, useState } from "react";
import { sendChatMessage, ChatMessage } from "@/lib/api";

export default function ChatWidget({ detectedDisease }: { detectedDisease: string | null }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi, I'm the CropDoc assistant. Detect a disease on the left, or just ask me a plant-health question.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    const history = messages;
    const nextMessages: ChatMessage[] = [...history, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const reply = await sendChatMessage(text, history, detectedDisease);
      setMessages([...nextMessages, { role: "assistant", content: reply }]);
    } catch (e: any) {
      setError(e.message || "Chat request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card chat-panel">
      <h2>Ask CropDoc</h2>
      {detectedDisease ? (
        <div className="context-pill">Context: {detectedDisease}</div>
      ) : (
        <div className="context-pill">No disease detected yet — ask anything anyway.</div>
      )}

      <div className="chat-messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            {m.content}
          </div>
        ))}
        {loading && <div className="chat-bubble assistant">Thinking...</div>}
      </div>

      {error && <div className="error-text">{error}</div>}

      <div className="chat-input-row">
        <input
          value={input}
          placeholder="Ask a question..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={loading}
        />
        <button className="primary" onClick={send} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
