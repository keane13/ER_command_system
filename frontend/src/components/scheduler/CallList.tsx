"use client";

import React from "react";
import { SCHED_STATUS_STYLE } from "../../lib/api";

interface Schedule {
  id: number;
  time: string;
  patient: string;
  procedure: string;
  doctor: string;
  status: string;
}

interface CallListProps {
  schedules: Schedule[];
}

const CallList: React.FC<CallListProps> = ({ schedules }) => {
  return (
    <div style={{ flex: 1, borderRight: "1px solid rgba(51, 65, 85, .5)", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "8px 16px", borderBottom: "1px solid rgba(51, 65, 85, .4)", display: "flex", alignItems: "center", gap: 7 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>
        <span style={{ fontSize: 11, fontWeight: 600, color: "#94a3b8", letterSpacing: ".03em", textTransform: "uppercase" }}>Upcoming Schedule</span>
        <span style={{ marginLeft: "auto", fontSize: 10, background: "rgba(30, 41, 59, .8)", color: "#64748b", border: "1px solid rgba(51, 65, 85, .5)", borderRadius: 99, padding: "1px 8px" }}>{schedules.length}</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 12px", display: "flex", flexDirection: "column", gap: 5 }}>
        {schedules.map((s) => (
          <div key={s.id} className="fade-in" style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 10px", borderRadius: 10, background: "rgba(15, 23, 42, .5)", border: "1px solid rgba(51, 65, 85, .35)" }}>
            <span className="mono" style={{ fontSize: 11, fontWeight: 500, color: "#22d3ee", width: 42, flexShrink: 0 }}>{s.time}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 11, color: "#cbd5e1", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.procedure}</div>
              <div style={{ fontSize: 10, color: "#475569", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.patient} · {s.doctor}</div>
            </div>
            <span style={{ fontSize: 9.5, flexShrink: 0, padding: "2px 8px", borderRadius: 99, border: "1px solid", ...(SCHED_STATUS_STYLE[s.status] || SCHED_STATUS_STYLE.pending) }}>{s.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CallList;
