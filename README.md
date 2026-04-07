# 🚨 Smart ER Command Center (`ER_command_system`)

[![Hack2Vision](https://img.shields.io/badge/Hackathon-Hack2Vision-blue.svg)](#)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Powered-EA4335?logo=google-cloud)](#)
[![Gemini](https://img.shields.io/badge/AI-Gemini_2.5_Pro-8E75B2?logo=google)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](#)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-000000?logo=next.js)](#)

> **Team AiOne** | Pioneering the future of autonomous medical agents. Merging LLMs, real-time data pipelines, and clinical workflows to create a fully intelligent Emergency Room Command Center.

## 🏥 The Problem
Emergency Rooms are chaotic. Medical staff face extreme cognitive overload attempting to simultaneously retrieve patient histories, check bed availability, verify drug inventories, and coordinate care. This fragmentation leads to delayed triage, resource bottlenecks, and compromised patient safety.

## 💡 The Solution
The **Smart ER Command Center** is a multi-agent autonomous system built on **Gemini 2.5 Pro**. It acts as the central nervous system of the hospital, seamlessly orchestrating data between historical records, real-time resource tracking, and physical staff delegation.

### ✨ Key Capabilities
* **Zero-Friction "Cold Start" Registration:** The AI autonomously detects unregistered patients and handles front-desk registration directly into BigQuery via natural conversation.
* **Autonomous Resource Allocation:** Dynamically searches for available beds by zone (Resuscitation, Observation). If the ER is at full capacity, the AI automatically routes patients into a smart Queue/Waiting List.
* **Human-in-the-Loop (HITL) Triage:** Synthesizes complex clinical data into a clean `[ TRIAGE DRAFT ]` for a human doctor to review and approve with a single click.
* **Automated Execution:** Upon approval, the AI autonomously dispatches tasks to nurses, pages specialists via Telegram, and books X-Rays in Google Calendar.

---

## 🏗️ System Architecture

We implemented an Enterprise-Grade **Hybrid Database Architecture** to separate analytical memory from real-time transactional state, ensuring sub-millisecond UI rendering and massive analytical scale.

1.  **OLAP (Long-Term Memory): Google BigQuery**
    * Integrated natively via **Google MCP (Model Context Protocol)**.
    * Stores massive, static datasets: `patient_registry` and unstructured `hospital_clinical_notes`.
2.  **OLTP (Short-Term Memory): Cloud SQL (PostgreSQL)**
    * Integrated via **LangChain `@tool`** bindings.
    * Handles real-time concurrency for `er_resource_status` (bed locking), `active_triage_flow`, and `staff_tasks`.
3.  **Third-Party Actuators:**
    * **Telegram API:** For triggering Code Red paging to specialist doctors.
    * **Google Calendar API:** For booking operational schedules.

---

## 🤖 The Multi-Agent Ecosystem

The system utilizes a sequential and hierarchical agentic workflow orchestrated via the Google ADK:

* **1. ARIA Greeter (Root Router):** The frontline interface. Identifies patients, handles new registrations via BigQuery, and routes tasks.
* **2. Clinical Context Agent:** The medical historian. Uses BigQuery MCP to extract past allergies, surgeries, and chronic illnesses.
* **3. Facility Operations Agent:** The logistics master. Queries Cloud SQL to lock available beds or queues patients if the ER is full.
* **4. Pharmacy Agent:** The inventory checker. Verifies physical stock of anticipated emergency drugs (e.g., Epinephrine, Aspirin) and issues warnings for shortages.
* **5. Triage Chief Agent (Formatter):** Synthesizes findings from all sub-agents into a unified, professional Triage Draft for the doctor's approval.
* **6. Care Coordinator Agent (Executor):** Acts *only* after human approval. Pushes tasks to the Next.js nurse dashboard, pages Telegram, and updates Cloud SQL.

---

## 💻 Tech Stack

* **AI Engine:** Google Gemini 2.5 Pro, Google Agent Development Kit (ADK), LangChain.
* **Backend:** Python, FastAPI, Uvicorn, SQLAlchemy.
* **Frontend:** Next.js, React, TailwindCSS.
* **Infrastructure:** Google Cloud Platform (Cloud SQL, BigQuery, Cloud Run).

---

## 🚀 Quick Start / Local Development

### 1. Backend Setup (FastAPI)
```bash
# Clone the repository
git clone [https://github.com/your-username/ER_command_system.git](https://github.com/your-username/ER_command_system.git)
cd ER_command_system/backend

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env
# Fill in your GEMINI_API_KEY, DATABASE_URL, BQ_PROJECT_ID, TELEGRAM_BOT_TOKEN

# Run the API Server
uvicorn main:app --reload --port 8000
