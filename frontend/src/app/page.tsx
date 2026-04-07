"use client";

import React, { useState, useEffect, useCallback } from "react";
import AriaChat from "../components/chat/AriaChat";
import BedGrid from "../components/dashboard/BedGrid";
import CallList from "../components/scheduler/CallList";
import TaskList from "../components/scheduler/TaskList";
import {
  TRACE_STEPS,
  fetchBeds,
  fetchSchedule,
  fetchTasks,
  sendTriageMessage,
  Bed,
  ScheduleItem,
  StaffTask,
} from "../lib/api";

export default function ERCommandCenter() {
  const [beds, setBeds] = useState<Bed[]>([]);
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [tasks, setTasks] = useState<StaffTask[]>([]);


  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome to the ER Command Center. I'm ARIA — AI Medical Assistant. I'm ready to help coordinate patients, allocate beds, and manage medical procedure schedules. How can I help you?",
      time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [isOrchestrating, setIsOrch] = useState(false);
  const [traceStep, setTraceStep] = useState(-1);
  const [highlightedBed, setHLBed] = useState<string | null>(null);
  const [highlightedTask, setHLTask] = useState<number | null>(null);
  const [currentTime, setTime] = useState(new Date());
  const [responseCount, setRespCt] = useState(0);
  const [sessionId] = useState(`session-${Math.random().toString(36).substr(2, 9)}`);

  // Initial Data Fetch
  const refreshData = useCallback(async () => {
    try {
      const [newBeds, newSchedules, newTasks] = await Promise.all([
        fetchBeds(),
        fetchSchedule(),
        fetchTasks()
      ]);
      setBeds(newBeds);
      setSchedules(newSchedules);
      setTasks(newTasks);
    } catch (error) {
      console.error("Failed to refresh dashboard data:", error);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

  const handleSend = useCallback(async () => {
    if (!input.trim() || isOrchestrating) return;
    const userMsg = input.trim();
    const msgTime = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    setInput("");
    setMessages((p) => [...p, { role: "user", content: userMsg, time: msgTime }]);
    setIsOrch(true);

    try {
      // 1. Call the real Triage API
      // We simulate some progress steps while waiting, or use the real trace_logs if available
      setTraceStep(0); // Connecting
      const response = await sendTriageMessage(sessionId, userMsg);
      
      // 2. Animate the remaining trace steps quickly for UX
      for (let i = 1; i < 6; i++) {
        setTraceStep(i);
        await sleep(150);
      }

      // 3. Update dashboard state from backend
      await refreshData();

      // 4. Handle UI highlights based on response
      if (response.status === "draft_pending" || response.status === "executed") {
        // Find the most recently updated bed or specific bed if mentioned (mock highlight for now)
        // In a real app, the API might return the affected bed ID
        const lastBed = beds.find(b => b.status === "observation" || b.status === "critical");
        if (lastBed) {
          setHLBed(lastBed.id);
          setTimeout(() => setHLBed(null), 3500);
        }
      }

      // 5. Add AI Reply
      const replyTime = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
      setMessages((p) => [...p, { 
        role: "assistant", 
        content: response.reply_text, 
        time: replyTime 
      }]);

    } catch (error) {
      console.error("API Error:", error);
      const errorTime = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
      setMessages((p) => [...p, { 
        role: "assistant", 
        content: "I'm sorry, I encountered an error connecting to the medical systems. Please try again or contact IT.", 
        time: errorTime 
      }]);
    } finally {
      setTraceStep(-1);
      setIsOrch(false);
    }
  }, [input, isOrchestrating, beds, sessionId, refreshData]);

  const toggleTask = (id: number) =>
    setTasks((p) => p.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));

  return (
    <div style={{ background: "#020817", minHeight: "100vh", display: "flex", flexDirection: "column", color: "#e2e8f0", overflow: "hidden" }}>
      {/* HEADER */}
      <header style={{ borderBottom: "1px solid rgba(51,65,85,.6)", background: "rgba(2,8,23,.85)", backdropFilter: "blur(12px)", padding: "10px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 34, height: 34, borderRadius: 10, background: "rgba(6,182,212,.12)", border: "1px solid rgba(6,182,212,.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, letterSpacing: "-.01em", color: "#f1f5f9" }}>ER Command Center</div>
            <div style={{ fontSize: 11, color: "#475569" }}>Central Hospital · Emergency Department</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="pulse-dot" style={{ width: 7, height: 7, borderRadius: "50%", background: "#34d399", display: "inline-block" }} />
            <span style={{ fontSize: 11, color: "#64748b" }}>System Active</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#475569" }}>
            <span className="mono" style={{ color: "#94a3b8", fontSize: 12, fontWeight: 500 }}>{currentTime.toLocaleTimeString("en-US")}</span>
            <span>{currentTime.toLocaleDateString("en-US", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</span>
          </div>
        </div>
      </header>

      {/* BODY */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <AriaChat
          messages={messages}
          input={input}
          setInput={setInput}
          handleSend={handleSend}
          isOrchestrating={isOrchestrating}
          traceStep={traceStep}
        />

        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <BedGrid beds={beds} highlightedBed={highlightedBed} />
          
          <div style={{ height: 220, display: "flex", flexShrink: 0 }}>
            <CallList schedules={schedules} />
            <TaskList tasks={tasks} toggleTask={toggleTask} highlightedTask={highlightedTask} />
          </div>
        </div>
      </div>
    </div>
  );
}
