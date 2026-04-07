import os
import dotenv
from google.adk.agents import LlmAgent as Agent, SequentialAgent

# Import modul tools final kita
import tools

dotenv.load_dotenv()
# Menggunakan Gemini 2.5 Pro untuk penalaran klinis tingkat tinggi
model_name = "gemini-2.5-pro" 

# ==============================================================================
# 1. INISIALISASI NATIVE MCP TOOLS
# ==============================================================================
print("Mempersiapkan koneksi Native BigQuery MCP...")
try:
    bq_toolset = tools.get_bigquery_mcp_toolset()
    bigquery_mcp_tools = bq_toolset.get_tools()
except Exception as e:
    print(f"⚠️ Peringatan: Gagal memuat BigQuery MCP. Error: {e}")
    bigquery_mcp_tools = []

# ==============================================================================
# 2. DEFINISI AGENT SPESIALIS (WORKFLOW TRIASE)
# ==============================================================================

clinical_context_agent = Agent(
    name="clinical_context_agent",
    model=model_name,
    description="Mengekstrak riwayat medis, alergi, dan penyakit kronis pasien dari BigQuery.",
    instruction="""
    You are the Clinical Context Agent, an expert medical historian.
    Your goal is to investigate the patient's background based on the user's PROMPT.
    
    You have access to:
    1. BigQuery MCP (to query `patient_registry` and `hospital_clinical_notes`).
    
    First, analyze the PROMPT to find the Patient ID or name.
    Then, use BigQuery to gather their history and past clinical notes.
    Synthesize your findings into a concise clinical summary focusing ONLY on:
    - Allergies
    - Chronic Illnesses
    - Past major surgeries/events (e.g., prior STEMI).

    PROMPT:
    {{ PROMPT }}
    """,
    tools=bigquery_mcp_tools, # Hanya alat baca riwayat
    output_key="clinical_data" 
)

facility_operations_agent = Agent(
    name="facility_operations_agent",
    model=model_name,
    description="Mengatur alokasi ranjang IGD dan memasukkan pasien ke sistem antrean (Triage Flow).",
    instruction="""
    You are the Facility Operations Agent. Your goal is to find an available bed 
    based on the severity indicated in the CLINICAL_DATA and PROMPT.
    
    You MUST use the `allocate_bed_and_triage` tool.
    
    Determine these parameters based on the clinical context:
    1. priority_level: 'Red (Critical)', 'Yellow (Urgent)', or 'Green (Stable)'.
    2. zone_required: 'Resuscitation' (for Red), 'Observation' (for Yellow), or 'Fast Track' (for Green).
    
    Execute the tool to lock the bed or queue the patient. Return the confirmation status.

    CLINICAL_DATA:
    {{ clinical_data }}
    
    PROMPT:
    {{ PROMPT }}
    """,
    tools=[tools.allocate_bed_and_triage], # Alat pendaftaran & pengunci ranjang
    output_key="bed_data" 
)

pharmacy_agent = Agent(
    name="pharmacy_agent",
    model=model_name,
    description="Mengecek ketersediaan fisik obat darurat di apotek IGD.",
    instruction="""
    You are the ER Pharmacy Agent. 
    Analyze the PROMPT and CLINICAL_DATA to anticipate what emergency drugs might be needed 
    (e.g., Aspirin/Heparin for chest pain, Epinephrine for allergies).
    
    You MUST use the `check_pharmacy_inventory` tool to verify if the required drugs are in stock.
    
    - Suggest the required medications.
    - Note any warnings if a drug is 'Out of Stock' or 'Low Stock'.
    - Note any contraindications based on the patient's allergies in CLINICAL_DATA.

    CLINICAL_DATA:
    {{ clinical_data }}
    """,
    tools=[tools.check_pharmacy_inventory], # Alat cek stok obat
    output_key="pharmacy_data" 
)

triage_chief_agent = Agent(
    name="triage_chief_agent",
    model=model_name,
    description="Mensintesis semua data spesialis menjadi Draf Triase resmi untuk disetujui dokter.",
    instruction="""
    You are ARIA, the Triage Chief. Your task is to take all the gathered data 
    and present it to the doctor as a friendly, structured '[ TRIAGE DRAFT ]' for approval.

    Create a highly professional UI-ready response containing:
    1. Patient Summary (from PROMPT & CLINICAL_DATA)
    2. Proposed Priority & Bed Status (from BED_DATA - note if they are queued)
    3. Drug Availability & Warnings (from PHARMACY_DATA)
    4. A final question: "Do you APPROVE this triage plan for execution?"

    Do NOT execute any tasks here. Just present the synthesis.

    CLINICAL_DATA:
    {{ clinical_data }}
    
    BED_DATA:
    {{ bed_data }}
    
    PHARMACY_DATA:
    {{ pharmacy_data }}
    """
)

# ==============================================================================
# 3. EXECUTION AGENT (AKSI SETELAH DISETUJUI)
# ==============================================================================

care_coordinator_agent = Agent(
    name="care_coordinator_agent",
    model=model_name,
    description="Mengeksekusi tugas fisik (perawat, paging dokter, kalender) setelah dokter menyetujui triase.",
    instruction="""
    You are the Care Coordinator. You ONLY act when the user says "Approved" or "Setuju".
    
    You have access to:
    1. `assign_nurse_task` (to delegate physical actions like drawing blood or EKG)
    2. `send_telegram_page` (to page specialists via Telegram)
    3. `schedule_google_calendar` (to book operations or imaging)
    
    Review the approved Triage Draft. 
    - Create necessary tasks for the nurses.
    - Page the necessary doctors via Telegram if the condition is critical.
    - Book necessary schedules in the Calendar (like X-Ray or Surgery).
    - Confirm to the user that all actions have been executed and the dashboard is updated.
    """,
    tools=[
        tools.assign_nurse_task, 
        tools.send_telegram_page, 
        tools.schedule_google_calendar
    ]
)

# ==============================================================================
# 4. WORKFLOW & ROOT ROUTER
# ==============================================================================

triage_evaluation_workflow = SequentialAgent(
    name="triage_evaluation_workflow",
    description="Pipa utama (pipeline) triase dari awal hingga draf akhir.",
    sub_agents=[
        clinical_context_agent,    # Langkah 1: Cek Riwayat
        facility_operations_agent, # Langkah 2: Kunci Ranjang / Antre
        pharmacy_agent,            # Langkah 3: Cek Stok Obat
        triage_chief_agent         # Langkah 4: Format Draf
    ]
)

root_agent = Agent(
    name="aria_greeter",
    model=model_name,
    description="Resepsionis IGD dan Router AI Utama.",
    instruction="""
    Kamu adalah ARIA, Resepsionis dan AI Medical Assistant di Pusat Komando IGD.
    
    ALUR KERJA WAJIB:
    1. Jika pengguna datang membawa pasien baru dengan keluhan, cek identitasnya.
    2. Gunakan alat BigQuery MCP (query_bigquery_data) untuk mencari pasien tersebut di `patient_registry`.
       - JIKA TIDAK ADA / TIDAK DITEMUKAN: Berhenti. Tanyakan kepada pengguna: "Saya tidak menemukan rekam medis pasien ini. Boleh sebutkan Nama Lengkap, Tanggal Lahir (YYYY-MM-DD), dan Jenis Kelamin untuk saya daftarkan?"
       - Jika pengguna merespons dengan data lengkap, gunakan alat `register_new_patient` untuk mendaftarkan pasien.
    3. Jika pasien sudah terdaftar ATAU baru saja selesai didaftarkan, segera transfer kontrol ke 'triage_evaluation_workflow'.
    4. Jika pengguna hanya merespons "Approved", "Setuju", atau "Laksanakan" dari draf sebelumnya, transfer kontrol ke 'care_coordinator_agent'.
    """,
    # Root agent punya akses baca BigQuery (untuk ngecek) dan alat registrasi
    tools=bigquery_mcp_tools + [tools.register_new_patient], 
    sub_agents=[
        triage_evaluation_workflow, 
        care_coordinator_agent
    ]
)