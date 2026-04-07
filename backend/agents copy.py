import os
import dotenv
import tools
from google.adk.agents import LlmAgent as Agent, SequentialAgent

dotenv.load_dotenv()
model_name = "gemini-2.0-flash"


# Mengambil Project ID dari environment
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'project_not_set')

 # Untuk data historis (OLAP)
alloydb_tools = tools.get_alloydb_mcp_toolset()   # Untuk operasional real-time (OLTP)
notes_mcp = tools.get_notes_mcp_toolset()         # File system MCP untuk membaca SOAP notes
calendar_mcp = tools.get_calendar_mcp_toolset()   # Jadwal rawat jalan
task_mcp = tools.get_task_mcp_toolset()           # Task management perawat
slack_mcp = tools.get_slack_mcp_toolset()
# Mengaktifkan BigQuery MCP
bigquery_toolset = tools.get_bigquery_mcp_toolset()

clinical_context_agent = Agent(
    name="clinical_context_agent",
    model=model_name,
    description="Extracts past medical history, chronic conditions, and allergies from BigQuery and Notes.",
    instruction=f"""
    You are the Clinical Context Agent, an expert medical historian.
    Your goal is to investigate the patient's background based on the user's PROMPT.
    
    You have access to:
    1. BigQuery MCP (to query `patient_registry` and `historical_emr_notes` in project {PROJECT_ID}).
    2. Notes MCP (to read unstructured medical PDFs).
    
    First, analyze the PROMPT to find the Patient ID or name.
    Then, gather their history.
    Synthesize your findings into a concise clinical summary focusing ONLY on:
    - Allergies
    - Chronic Illnesses
    - Past major surgeries/events (e.g., prior STEMI).

    PROMPT:
    {{ PROMPT }}
    """,
    tools=[tools.bigquery_mcp, tools.notes_mcp],
    output_key="clinical_data" # Menyimpan hasil pencarian medis ke state
)

facility_operations_agent = Agent(
    name="facility_operations_agent",
    model=model_name,
    description="Manages ER bed logistics based on clinical urgency.",
    instruction="""
    You are the Facility Operations Agent. Your goal is to find an available bed 
    based on the severity indicated in the CLINICAL_DATA and PROMPT.
    
    You have access to:
    1. AlloyDB MCP (to query `er_resource_status`).
    
    - If the condition sounds critical (e.g., chest pain, stroke), search for an 'Available' bed in the 'Resuscitation' zone.
    - If non-critical, search the 'Observation' zone.
    - DO NOT update the database yet. Just return the proposed Bed ID and its zone.

    CLINICAL_DATA:
    {{ clinical_data }}
    
    PROMPT:
    {{ PROMPT }}
    """,
    tools=[tools.alloydb_mcp],
    output_key="bed_data" # Menyimpan usulan ranjang ke state
)

pharmacy_agent = Agent(
    name="pharmacy_agent",
    model=model_name,
    description="Checks medication inventory for anticipated emergency drugs.",
    instruction="""
    You are the ER Pharmacy Agent. 
    Analyze the PROMPT and CLINICAL_DATA to anticipate what emergency drugs might be needed 
    (e.g., Aspirin/Heparin for chest pain, Epinephrine for allergies).
    
    You have access to:
    1. AlloyDB MCP (to query `medication_inventory`).
    
    - Check the stock levels of the anticipated drugs.
    - If a drug stock is 0, issue a WARNING and suggest an alternative.
    - Note any contraindications based on the patient's allergies in CLINICAL_DATA.

    CLINICAL_DATA:
    {{ clinical_data }}
    """,
    tools=[tools.alloydb_mcp],
    output_key="pharmacy_data" # Menyimpan info stok obat ke state
)

# ==========================================
# 2. FORMATTER & DECISION AGENT (The Chief)
# ==========================================

triage_chief_agent = Agent(
    name="triage_chief_agent",
    model=model_name,
    description="Synthesizes all specialist data into a formal Triage Draft for human validation.",
    instruction="""
    You are ARIA, the Triage Chief. Your task is to take all the gathered data 
    and present it to the doctor as a friendly, structured '[ TRIAGE DRAFT ]' for approval.

    Create a highly professional UI-ready response containing:
    1. Patient Summary (from PROMPT & CLINICAL_DATA)
    2. Proposed Priority (Red/Yellow/Green)
    3. Bed Allocation (from BED_DATA)
    4. Drug Availability & Warnings (from PHARMACY_DATA)
    5. A final question: "Do you APPROVE this plan or need REVISIONS?"

    Do NOT execute any tasks. Just present the synthesis.

    CLINICAL_DATA:
    {{ clinical_data }}
    
    BED_DATA:
    {{ bed_data }}
    
    PHARMACY_DATA:
    {{ pharmacy_data }}
    """
)

# ==========================================
# 3. EXECUTION AGENT (The Hands - Post Approval)
# ==========================================

care_coordinator_agent = Agent(
    name="care_coordinator_agent",
    model=model_name,
    description="Executes tasks, updates databases, and pages doctors AFTER human approval.",
    instruction="""
    You are the Care Coordinator. You only act when the user says "Approved" or "Setuju".
    
    You have access to:
    1. Task MCP (to assign nurse tasks)
    2. Slack MCP (to page specialists)
    3. Calendar MCP (to book follow-ups)
    
    Review the previous Triage Draft. 
    - Dispatch the required nurse tasks.
    - Page the necessary doctors via Slack.
    - Confirm to the user that all actions have been executed and the dashboard is updated.
    """,
    tools=[tools.task_mcp, tools.slack_mcp, tools.calendar_mcp]
)

# ==========================================
# 4. WORKFLOW ORCHESTRATION
# ==========================================

triage_evaluation_workflow = SequentialAgent(
    name="triage_evaluation_workflow",
    description="The main pipeline for gathering data and drafting the triage plan.",
    sub_agents=[
        clinical_context_agent,    # Step 1: Get history
        facility_operations_agent, # Step 2: Find a bed
        pharmacy_agent,            # Step 3: Check drug stock
        triage_chief_agent         # Step 4: Synthesize & ask for approval
    ]
)

root_agent = Agent(
    name="aria_greeter",
    model=model_name,
    description="The main entry point for the ER Command Center.",
    instruction="""
    You are ARIA, the AI Medical Assistant. 
    - Greet the user: "Welcome to the ER Command Center. Please enter the patient's symptoms and vital signs to begin triage."
    - When the user provides the medical prompt, use the 'add_prompt_to_state' tool to save their input.
    - If the user is providing new patient data, transfer control to the 'triage_evaluation_workflow' agent.
    - If the user is replying with "Approved" to a previous draft, transfer control to the 'care_coordinator_agent' for execution.
    """,
    tools=[tools.add_prompt_to_state],
    sub_agents=[
        triage_evaluation_workflow, 
        care_coordinator_agent
    ]
)