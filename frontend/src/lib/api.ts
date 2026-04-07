export const INITIAL_BEDS = [
  { id: "R-01", status: "empty", patient: null, diagnosis: null, time: null },
  { id: "R-02", status: "critical", patient: "James Thornton", diagnosis: "Cardiac Arrest", time: "06:14" },
  { id: "R-03", status: "observation", patient: "Sarah Mitchell", diagnosis: "Hypertension Grade III", time: "07:30" },
  { id: "R-04", status: "empty", patient: null, diagnosis: null, time: null },
  { id: "R-05", status: "critical", patient: "Michael Hayes", diagnosis: "Ischemic Stroke", time: "05:45" },
  { id: "R-06", status: "observation", patient: "Linda Carter", diagnosis: "Acute Dyspnea", time: "08:00" },
  { id: "R-07", status: "empty", patient: null, diagnosis: null, time: null },
  { id: "R-08", status: "observation", patient: "David Nguyen", diagnosis: "Appendicitis", time: "07:55" },
  { id: "R-09", status: "empty", patient: null, diagnosis: null, time: null },
  { id: "R-10", status: "critical", patient: "Emily Russo", diagnosis: "Sepsis", time: "04:20" },
  { id: "R-11", status: "observation", patient: "Chris Patel", diagnosis: "Femur Fracture", time: "08:10" },
  { id: "R-12", status: "empty", patient: null, diagnosis: null, time: null },
];

export const INITIAL_SCHEDULES = [
  { id: 1, time: "08:00", patient: "James Thornton", procedure: "Cardiology Consultation", doctor: "Dr. A. Chen, MD", status: "pending" },
  { id: 2, time: "09:15", patient: "Sarah Mitchell", procedure: "Vital Signs Check", doctor: "Dr. R. Singh, MD", status: "done" },
  { id: 3, time: "10:00", patient: "Michael Hayes", procedure: "Head CT Scan", doctor: "Dr. B. Torres, Rad", status: "in-progress" },
  { id: 4, time: "11:30", patient: "Linda Carter", procedure: "Chest X-Ray", doctor: "Dr. S. Kim, Rad", status: "pending" },
];

export const INITIAL_TASKS = [
  { id: 1, task: "EKG — Bed R-02 · James Thornton", done: false, priority: "high" },
  { id: 2, task: "Replace IV Line — Bed R-05", done: true, priority: "medium" },
  { id: 3, task: "Draw Blood Labs — Bed R-10", done: false, priority: "high" },
  { id: 4, task: "Monitor Vitals — Beds R-03 & R-06", done: false, priority: "medium" },
  { id: 5, task: "Complete SOAP Notes — Bed R-08", done: true, priority: "low" },
];

export const TRACE_STEPS = [
  { text: "Connecting to Agent Orchestrator..." },
  { text: "Loading patient history from BigQuery..." },
  { text: "Checking ER bed availability..." },
  { text: "Updating schedule via Calendar MCP..." },
  { text: "Syncing tasks to Task MCP..." },
  { text: "Generating final response..." },
];

export const AI_RESPONSES = [
  (bed: string) => `Bed ${bed} has been successfully allocated for the incoming patient with Observation status. A physician evaluation schedule and triage task have been automatically added to the system.`,
  (bed: string) => `Instruction processed. Patient allocated to ${bed}. All agents updated — calendar, task manager, and bed tracker are now in sync.`,
  (bed: string) => `Agents executed successfully. ${bed} is now in Observation status. Notifications sent to the on-call physician and duty nurse.`,
];

export const BED_META: Record<string, any> = {
  empty:       { label: "Available",   dot: "#34d399", textColor: "#6ee7b7", bg: "rgba(2,30,18,.45)",   border: "rgba(52,211,153,.3)" },
  observation: { label: "Observation", dot: "#fbbf24", textColor: "#fcd34d", bg: "rgba(44,26,2,.5)",    border: "rgba(251,191,36,.35)" },
  critical:    { label: "Critical",    dot: "#f87171", textColor: "#fca5a5", bg: "rgba(44,2,2,.55)",    border: "rgba(239,68,68,.4)" },
};

export const SCHED_STATUS_STYLE: Record<string, any> = {
  pending:     { color: "#64748b", borderColor: "rgba(51,65,85,.6)",      background: "rgba(15,23,42,.6)" },
  "in-progress":{ color: "#fcd34d", borderColor: "rgba(120,53,15,.5)",   background: "rgba(44,26,2,.4)" },
  done:        { color: "#34d399", borderColor: "rgba(6,95,70,.5)",       background: "rgba(2,30,18,.4)" },
};

export const TASK_PRIO_STYLE: Record<string, any> = {
  high:   { color: "#fca5a5", border: "1px solid rgba(127,29,29,.5)",  background: "rgba(44,2,2,.4)" },
  medium: { color: "#fcd34d", border: "1px solid rgba(120,53,15,.5)",  background: "rgba(44,26,2,.4)" },
  low:    { color: "#64748b", border: "1px solid rgba(51,65,85,.5)",   background: "rgba(15,23,42,.4)" },
};

// ==========================================
// API INTEGRATION
// ==========================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface DashboardMetrics {
  totalBeds: number;
  available: number;
  activePatients: number;
  critical: number;
}

export interface Bed {
  id: string;
  status: "empty" | "observation" | "critical";
  patient: string | null;
  diagnosis: string | null;
  time: string | null;
}

export interface ScheduleItem {
  id: number;
  time: string;
  patient: string;
  procedure: string;
  doctor: string;
  status: string;
}


export interface StaffTask {
  id: number;
  task: string;
  priority: string;
  done: boolean;
}

export interface ChatResponse {
  session_id: string;
  reply_text: string;
  status: string;
  trace_logs: string[];
}

/**
 * Fetches dashboard metrics from the FastAPI backend.
 */
export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_BASE_URL}/api/dashboard/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

/**
 * Fetches bed monitoring data and maps to frontend format.
 */
export async function fetchBeds(): Promise<Bed[]> {
  const res = await fetch(`${API_BASE_URL}/api/dashboard/beds`);
  if (!res.ok) throw new Error("Failed to fetch beds");
  const data = await res.json();
  
  return data.map((b: any) => ({
    id: b.id,
    status: b.status === "Available" ? "empty" : b.status.toLowerCase(),
    patient: b.patientName === "No patient" ? null : b.patientName,
    diagnosis: b.diagnosis,
    time: b.time
  }));
}

/**
 * Fetches upcoming schedules and maps to frontend format.
 */
export async function fetchSchedule(): Promise<ScheduleItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/dashboard/schedule`);
  if (!res.ok) throw new Error("Failed to fetch schedule");
  const data = await res.json();
  
  return data.map((s: any, idx: number) => {
    // Backend description format: "Patient Name · Doctor Name"
    const [patient, doctor] = (s.description || "Unknown · Unknown").split(" · ");
    return {
      id: idx, // or s.id if backend provides it
      time: s.time,
      patient: patient || "Unknown",
      procedure: s.title,
      doctor: doctor || "Unknown",
      status: s.status
    };
  });
}

/**
 * Fetches staff tasks and maps to frontend format.
 */
export async function fetchTasks(): Promise<StaffTask[]> {
  const res = await fetch(`${API_BASE_URL}/api/dashboard/tasks`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  const data = await res.json();
  
  return data.map((t: any) => ({
    id: t.id,
    task: t.description,
    priority: t.priority,
    done: t.isCompleted
  }));
}

/**
 * Sends a message to the Triage Agent.
 */
export async function sendTriageMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/api/triage/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error("Failed to get agent response");
  return res.json();
}

// Legacy placeholder kept for compatibility during migration if needed
export const apiFetchAgentResponse = async (input: string) => {
  return sendTriageMessage("default-session", input);
};
