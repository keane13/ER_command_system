"use client";

import React from "react";
import { TASK_PRIO_STYLE } from "../../lib/api";

interface Task {
  id: number;
  task: string;
  done: boolean;
  priority: string;
}

interface TaskListProps {
  tasks: Task[];
  toggleTask: (id: number) => void;
  highlightedTask: number | null;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, toggleTask, highlightedTask }) => {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "8px 16px", borderBottom: "1px solid rgba(51,65,85,.4)", display: "flex", alignItems: "center", gap: 7 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2"><polyline points="9 11 12 14 22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
        <span style={{ fontSize: 11, fontWeight: 600, color: "#94a3b8", letterSpacing: ".03em", textTransform: "uppercase" }}>Staff Task List</span>
        <span style={{ marginLeft: "auto", fontSize: 10, background: "rgba(30,41,59,.8)", color: "#64748b", border: "1px solid rgba(51,65,85,.5)", borderRadius: 99, padding: "1px 8px" }}>{tasks.filter((t) => !t.done).length} active</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 12px", display: "flex", flexDirection: "column", gap: 5 }}>
        {tasks.map((t) => (
          <div
            key={t.id}
            onClick={() => toggleTask(t.id)}
            className={t.id === highlightedTask ? "task-flash fade-in" : "fade-in"}
            style={{
              display: "flex", alignItems: "center", gap: 9, padding: "7px 10px", borderRadius: 10,
              background: t.done ? "rgba(15,23,42,.2)" : "rgba(15,23,42,.5)",
              border: `1px solid ${t.done ? "rgba(51,65,85,.2)" : "rgba(51,65,85,.35)"}`,
              cursor: "pointer", opacity: t.done ? 0.55 : 1, transition: "all .2s",
            }}
          >
            <div style={{
              width: 16, height: 16, borderRadius: 5, flexShrink: 0,
              border: `1px solid ${t.done ? "#059669" : "rgba(100,116,139,.6)"}`,
              background: t.done ? "#059669" : "transparent",
              display: "flex", alignItems: "center", justifyContent: "center", transition: "all .2s",
            }}>
              {t.done && <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>}
            </div>
            <span style={{ flex: 1, fontSize: 11, color: t.done ? "#334155" : "#cbd5e1", textDecoration: t.done ? "line-through" : "none", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.task}</span>
            <span style={{ fontSize: 9.5, flexShrink: 0, padding: "2px 7px", borderRadius: 99, ...(TASK_PRIO_STYLE[t.priority]) }}>{t.priority}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskList;
