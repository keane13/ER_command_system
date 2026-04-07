"use client";

import React, { useRef, useEffect } from "react";
import AgentTrace from "../dashboard/AgentTrace";

interface Message {
  role: string;
  content: string;
  time: string;
}

interface AriaChatProps {
  messages: Message[];
  input: string;
  setInput: (val: string) => void;
  handleSend: () => void;
  isOrchestrating: boolean;
  traceStep: number;
}

const AriaChat: React.FC<AriaChatProps> = ({
  messages,
  input,
  setInput,
  handleSend,
  isOrchestrating,
  traceStep,
}) => {
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, traceStep]);

  return (
    <div style={{ width: 300, flexShrink: 0, borderRight: "1px solid rgba(51,65,85,.5)", display: "flex", flexDirection: "column", background: "rgba(2,8,23,.6)" }}>
      {/* Chat header */}
      <div style={{ padding: "12px 16px", borderBottom: "1px solid rgba(51,65,85,.4)", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#0e7490,#4f46e5)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="white"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.93V15a1 1 0 0 0-2 0v1.93A8 8 0 0 1 4.07 11H6a1 1 0 0 0 0-2H4.07A8 8 0 0 1 11 4.07V6a1 1 0 0 0 2 0V4.07A8 8 0 0 1 19.93 11H18a1 1 0 0 0 0 2h1.93A8 8 0 0 1 13 16.93z" /></svg>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#f1f5f9" }}>ARIA</div>
          <div style={{ fontSize: 10, color: "#64748b" }}>AI Medical Assistant · v2.4</div>
        </div>
        <span style={{ fontSize: 10, background: "rgba(34,211,238,.1)", color: "#22d3ee", border: "1px solid rgba(34,211,238,.2)", borderRadius: 99, padding: "2px 8px" }}>Online</span>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "14px 14px 8px", display: "flex", flexDirection: "column", gap: 10 }}>
        {messages.map((msg, i) => (
          <div key={i} className="fade-in" style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <div style={{ maxWidth: "88%" }}>
              <div style={{
                padding: "9px 12px",
                borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                fontSize: 11.5, lineHeight: 1.55,
                background: msg.role === "user" ? "linear-gradient(135deg,#0e7490,#0c4a6e)" : "rgba(30,41,59,.8)",
                color: msg.role === "user" ? "#e0f2fe" : "#cbd5e1",
                border: msg.role === "user" ? "none" : "1px solid rgba(51,65,85,.5)",
              }}>{msg.content}</div>
              <div style={{ fontSize: 9.5, color: "#334155", marginTop: 3, textAlign: msg.role === "user" ? "right" : "left", padding: "0 4px" }}>{msg.time}</div>
            </div>
          </div>
        ))}

        {/* Trace */}
        <AgentTrace traceStep={traceStep} />
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "10px 14px 14px", borderTop: "1px solid rgba(51,65,85,.4)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(15,23,42,.8)", border: "1px solid rgba(51,65,85,.5)", borderRadius: 14, padding: "8px 10px 8px 14px", transition: "border-color .2s" }}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={isOrchestrating ? "Processing..." : "Type a medical instruction..."}
            disabled={isOrchestrating}
            style={{ flex: 1, background: "transparent", fontSize: 11.5, color: "#cbd5e1" }}
          />
          <button
            onClick={handleSend}
            disabled={isOrchestrating || !input.trim()}
            style={{
              width: 30, height: 30, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center",
              background: isOrchestrating || !input.trim() ? "rgba(14,116,144,.3)" : "linear-gradient(135deg,#0e7490,#0c4a6e)",
              opacity: isOrchestrating || !input.trim() ? 0.5 : 1, transition: "all .2s",
              cursor: isOrchestrating || !input.trim() ? "not-allowed" : "pointer",
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
          </button>
        </div>
        <p style={{ fontSize: 9.5, color: "#334155", textAlign: "center", marginTop: 6 }}>Press Enter to send · AI Orchestration active</p>
      </div>
    </div>
  );
};

export default AriaChat;
