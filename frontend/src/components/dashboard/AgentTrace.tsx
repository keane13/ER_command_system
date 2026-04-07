"use client";

import React from "react";
import { TRACE_STEPS } from "../../lib/api";

interface AgentTraceProps {
  traceStep: number;
}

const AgentTrace: React.FC<AgentTraceProps> = ({ traceStep }) => {
  if (traceStep < 0) return null;

  return (
    <div className="slide-up" style={{ background: "rgba(15,23,42,.8)", border: "1px solid rgba(34,211,238,.15)", borderRadius: 14, padding: "12px 14px", marginTop: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span className="b1" style={{ width: 5, height: 5, borderRadius: "50%", background: "#22d3ee", display: "inline-block" }} />
        <span className="b2" style={{ width: 5, height: 5, borderRadius: "50%", background: "#22d3ee", display: "inline-block" }} />
        <span className="b3" style={{ width: 5, height: 5, borderRadius: "50%", background: "#22d3ee", display: "inline-block" }} />
        <span style={{ fontSize: 10.5, color: "#22d3ee", fontWeight: 500, letterSpacing: ".02em" }}>Orchestrating Agents...</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {TRACE_STEPS.slice(0, traceStep + 1).map((step, ti) => (
          <div key={ti} className="fade-in" style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={ti < traceStep ? "#34d399" : "#22d3ee"} strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
            <span style={{ fontSize: 10.5, color: ti < traceStep ? "#475569" : "#94a3b8" }}>{step.text}</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10, height: 2, background: "rgba(51,65,85,.6)", borderRadius: 99, overflow: "hidden" }}>
        <div className="bar-anim" style={{ height: "100%", background: "linear-gradient(90deg,#0e7490,#22d3ee)", borderRadius: 99 }} />
      </div>
    </div>
  );
};

export default AgentTrace;
