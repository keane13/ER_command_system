import os
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Import your database dependency and root agent
# Ensure you have 'database.py' and 'agents.py' in your root folder
from database import get_db
from agents import root_agent


# Initialize FastAPI
app = FastAPI(
    title="Smart ER Command Center API",
    description="Multi-Agent Orchestration & Dashboard API for ER Triage",
    version="1.0.0"
)

# CRITICAL FOR FRONTEND INTEGRATION: Setup CORS
# This allows your Next.js dashboard (running on localhost:3000) to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with ["https://your-nextjs-app.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. PYDANTIC SCHEMAS (Request & Response Validation)
# ==========================================

class ChatRequest(BaseModel):
    session_id: str          # Crucial to remember which patient/draft we are talking about
    message: str             # The text input from the doctor/nurse

class ChatResponse(BaseModel):
    session_id: str
    reply_text: str          # The markdown/text response from the AI
    status: str              # 'draft_pending', 'executed', or 'info'
    trace_logs: list[str]    # For the frontend to show the "Agent Thinking" animation

# ==========================================
# 2. SESSION STATE MANAGEMENT (In-Memory for Hackathon)
# ==========================================
active_sessions: Dict[str, Any] = {}

# ==========================================
# 3. SYSTEM ENDPOINTS
# ==========================================

@app.get("/health")
async def health_check():
    """Simple health check endpoint for Cloud Run."""
    return {"status": "System Active", "agents": "Online"}

# ==========================================
# 4. DASHBOARD UI ENDPOINTS (GET - Read Only)
# ==========================================

@app.get("/api/dashboard/metrics", response_model=Dict[str, int])
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """Fetches the 4 main metrics for the top cards on the dashboard."""
    try:
        query = text("""
            SELECT 
                (SELECT COUNT(*) FROM er_resource_status) as total_beds,
                (SELECT COUNT(*) FROM er_resource_status WHERE status = 'Available') as available_beds,
                (SELECT COUNT(*) FROM active_triage_flow WHERE status != 'Discharged') as active_patients,
                (SELECT COUNT(*) FROM active_triage_flow WHERE triage_priority = 'Red (Critical)') as critical_patients
        """)
        result = await db.execute(query)
        row = result.fetchone()
        
        return {
            "totalBeds": row.total_beds,
            "available": row.available_beds,
            "activePatients": row.active_patients,
            "critical": row.critical_patients
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/beds", response_model=List[Dict[str, Any]])
async def get_bed_monitoring(db: AsyncSession = Depends(get_db)):
    """Fetches data for the 12-bed grid monitoring UI."""
    try:
        query = text("""
            SELECT 
                b.resource_id as bed_id,
                CASE 
                    WHEN b.status = 'Available' THEN 'Available'
                    WHEN p.triage_priority = 'Red (Critical)' THEN 'Critical'
                    WHEN p.triage_priority = 'Yellow (Urgent)' THEN 'Observation'
                    ELSE 'Available'
                END as bed_status,
                COALESCE(p.patient_id, 'No patient') as patient_name,
                p.chief_complaint as diagnosis,
                TO_CHAR(p.arrival_time, 'HH24:MI') as time
            FROM er_resource_status b
            LEFT JOIN active_triage_flow p 
                   ON b.resource_id = p.assigned_resource_id 
                  AND p.status != 'Discharged'
            ORDER BY b.resource_id ASC
        """)
        result = await db.execute(query)
        
        return [
            {
                "id": row.bed_id,
                "status": row.bed_status,
                "patientName": row.patient_name,
                "diagnosis": row.diagnosis,
                "time": row.time
            }
            for row in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/schedule", response_model=List[Dict[str, Any]])
async def get_upcoming_schedule(db: AsyncSession = Depends(get_db)):
    """Fetches the upcoming schedules for the bottom-left UI."""
    try:
        query = text("""
            SELECT time, title, description, status 
            FROM upcoming_schedules 
            ORDER BY time ASC LIMIT 4
        """)
        result = await db.execute(query)
        
        schedules = [dict(row._mapping) for row in result]
        
        # If the table is empty during early testing, return the visual mock data
        if not schedules:
            return [
                {"time": "08:00", "title": "Cardiology Consultation", "description": "James Thornton · Dr. A. Chen, MD", "status": "pending"},
                {"time": "09:15", "title": "Vital Signs Check", "description": "Sarah Mitchell · Dr. R. Singh, MD", "status": "done"},
                {"time": "10:00", "title": "Head CT Scan", "description": "Michael Hayes · Dr. B. Torres, Rad", "status": "in-progress"},
                {"time": "11:30", "title": "Chest X-Ray", "description": "Linda Carter · Dr. S. Kim, Rad", "status": "pending"}
            ]
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/tasks", response_model=List[Dict[str, Any]])
async def get_staff_tasks(db: AsyncSession = Depends(get_db)):
    """Fetches the staff task list for the bottom-right UI."""
    try:
        query = text("""
            SELECT task_id as id, description, priority, is_completed as "isCompleted" 
            FROM staff_tasks 
            ORDER BY is_completed ASC, priority DESC LIMIT 5
        """)
        result = await db.execute(query)
        
        tasks = [dict(row._mapping) for row in result]
        
        # Fallback to visual mock data if empty
        if not tasks:
            return [
                {"id": 1, "description": "EKG — Bed R-02 · James Thornton", "priority": "high", "isCompleted": False},
                {"id": 2, "description": "Replace IV Line — Bed R-05", "priority": "medium", "isCompleted": True},
                {"id": 3, "description": "Draw Blood Labs — Bed R-10", "priority": "high", "isCompleted": False},
                {"id": 4, "description": "Monitor Vitals — Beds R-03 & R-06", "priority": "medium", "isCompleted": False},
                {"id": 5, "description": "Complete SOAP Notes — Bed R-08", "priority": "low", "isCompleted": True}
            ]
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 5. AGENT ORCHESTRATION ENDPOINT (POST)
# ==========================================

@app.post("/api/triage/chat", response_model=ChatResponse)
async def triage_chat(request: ChatRequest):
    """
    Main endpoint that the Next.js frontend calls when the user sends a message.
    """
    try:
        if request.session_id not in active_sessions:
            active_sessions[request.session_id] = {"history": []}
            
        current_state = active_sessions[request.session_id]
        
        # Execute the Multi-Agent Workflow
        agent_output = root_agent.run(
            prompt=request.message,
            state=current_state
        )
        
        active_sessions[request.session_id] = agent_output.get("new_state", current_state)
        reply_text = agent_output.get("response", "No response generated.")
        
        # Determine the UI Status
        ui_status = "info"
        if "[ TRIAGE DRAFT ]" in reply_text:
            ui_status = "draft_pending"
        elif "executed" in reply_text.lower() or "berhasil" in reply_text.lower():
            ui_status = "executed"
            
        return ChatResponse(
            session_id=request.session_id,
            reply_text=reply_text,
            status=ui_status,
            trace_logs=[
                "Agent System initialized...",
                "Delegating to sub-agents...",
                "Cloud SQL state retrieved...",
                "Response synthesized."
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 6. SERVER RUNNER
# ==========================================
if __name__ == "__main__":
    # Run the server locally on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)