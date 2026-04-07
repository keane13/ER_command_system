"use client";

import React from "react";
import { BED_META } from "../../lib/api";

interface Bed {
  id: string;
  status: string;
  patient: string | null;
  diagnosis: string | null;
  time: string | null;
}

interface BedGridProps {
  beds: Bed[];
  highlightedBed: string | null;
}

const BedGrid: React.FC<BedGridProps> = ({ beds, highlightedBed }) => {
  const totalBeds = beds.length;
  const available = beds.filter((b) => b.status === "empty").length;
  const active = beds.filter((b) => b.status !== "empty").length;
  const critical = beds.filter((b) => b.status === "critical").length;

  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "16px 18px 12px", borderBottom: "1px solid rgba(51,65,85,.5)" }}>
      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 16 }}>
        {[
          { label: "Total Beds", value: totalBeds, accent: "#94a3b8", bg: "rgba(30,41,59,.6)", border: "rgba(51,65,85,.5)" },
          { label: "Available", value: available, accent: "#34d399", bg: "rgba(2,44,34,.4)", border: "rgba(6,95,70,.4)" },
          { label: "Active Patients", value: active, accent: "#22d3ee", bg: "rgba(2,32,46,.4)", border: "rgba(8,70,92,.4)" },
          { label: "Critical", value: critical, accent: "#f87171", bg: "rgba(44,2,2,.4)", border: "rgba(127,29,29,.4)" },
        ].map((s) => (
          <div key={s.label} style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 16, padding: "12px 14px" }}>
            <div style={{ fontSize: 10, color: "#475569", marginBottom: 4 }}>{s.label}</div>
            <div className="mono" style={{ fontSize: 26, fontWeight: 500, color: s.accent, lineHeight: 1 }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Legend row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#94a3b8", letterSpacing: ".04em", textTransform: "uppercase" }}>◈ Bed Monitoring</div>
        <div style={{ display: "flex", gap: 14 }}>
          {[{ c: "#34d399", l: "Available" }, { c: "#fbbf24", l: "Observation" }, { c: "#f87171", l: "Critical" }].map((l) => (
            <div key={l.l} style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: l.c, display: "inline-block" }} />
              <span style={{ fontSize: 10, color: "#475569" }}>{l.l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Bed grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 8 }}>
        {beds.map((bed) => {
          const meta = BED_META[bed.status];
          const isHL = bed.id === highlightedBed;
          return (
            <div key={bed.id} className={isHL ? "flash-in" : "ta"} style={{ background: meta.bg, border: `1px solid ${meta.border}`, borderRadius: 14, padding: "10px 11px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <span className="mono" style={{ fontSize: 10, fontWeight: 500, color: "#475569" }}>{bed.id}</span>
                <span className={bed.status === "critical" ? "ring-pulse" : ""} style={{ width: 7, height: 7, borderRadius: "50%", background: meta.dot, display: "inline-block" }} />
              </div>
              <div style={{ fontSize: 10, fontWeight: 600, color: meta.textColor, marginBottom: 3 }}>{meta.label}</div>
              {bed.patient ? (
                <>
                  <div style={{ fontSize: 10.5, color: "#cbd5e1", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{bed.patient}</div>
                  <div style={{ fontSize: 9.5, color: "#475569", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginTop: 1 }}>{bed.diagnosis}</div>
                  <div className="mono" style={{ fontSize: 9, color: "#334155", marginTop: 4 }}>{bed.time}</div>
                </>
              ) : (
                <div style={{ fontSize: 10, color: "#334155", fontStyle: "italic" }}>No patient</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default BedGrid;
