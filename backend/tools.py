import os
import random
import requests
from datetime import datetime, timedelta
import google.auth
from googleapiclient.discovery import build
from google.cloud import bigquery
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams 

from langchain_core.tools import tool
from sqlalchemy import create_engine, text

# ==============================================================================
# 1. NATIVE GOOGLE MCP (HANYA UNTUK BIGQUERY)
# ==============================================================================
BIGQUERY_MCP_URL = "https://bigquery.googleapis.com/mcp" 

def get_bigquery_mcp_toolset():   
    """Koneksi native MCP ke BigQuery untuk riwayat dan rekam medis."""
    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    oauth_token = credentials.token
        
    HEADERS_WITH_OAUTH = {
        "Authorization": f"Bearer {oauth_token}",
        "x-goog-user-project": project_id
    }

    tools = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_URL,
            headers=HEADERS_WITH_OAUTH,
            timeout=30.0,          
            sse_read_timeout=300.0
        )
    )
    print("✅ BigQuery MCP Toolset configured successfully.")
    return tools

# ==============================================================================
# 2. CLOUD SQL & BIGQUERY TOOLS (LANGCHAIN FORMAT)
# ==============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password_anda@IP_ANDA/nama_db")
engine = create_engine(DATABASE_URL)

@tool
def register_new_patient(first_name: str, last_name: str, date_of_birth: str, gender: str, emergency_phone: str = "-") -> str:
    """Mendaftarkan pasien BARU ke dalam database rekam medis BigQuery jika mereka belum terdaftar.
    
    Args:
        first_name: Nama depan pasien.
        last_name: Nama belakang pasien.
        date_of_birth: Tanggal lahir pasien (format YYYY-MM-DD).
        gender: Jenis kelamin pasien (Male/Female).
        emergency_phone: Nomor telepon kontak darurat.
    """
    try:
        new_patient_id = f"P-{random.randint(1000, 9999)}"
        client = bigquery.Client()
        table_id = os.getenv("BQ_PATIENT_TABLE_ID", "PROJECT_ID.DATASET.patient_registry") 
        
        rows_to_insert = [{
            "patient_id": new_patient_id, "first_name": first_name, "last_name": last_name,
            "date_of_birth": date_of_birth, "gender": gender, "blood_type": "-",
            "insurance_provider": "-", "emergency_contact_phone": emergency_phone
        }]
        
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return f"✅ PENDAFTARAN SUKSES: Pasien terdaftar dengan ID {new_patient_id}."
        return f"❌ Gagal mendaftar ke BigQuery: {errors}"
    except Exception as e:
        return f"Error sistem: {str(e)}"

@tool
def check_pharmacy_inventory(drug_keyword: str) -> str:
    """Mengecek stok fisik obat darurat di database apotek IGD.
    
    Args:
        drug_keyword: Nama obat atau kata kunci pencarian (contoh: 'Aspirin', 'Epinephrine').
    """
    try:
        with engine.connect() as conn:
            query = text("SELECT drug_name, stock_level, unit, status FROM medication_inventory WHERE drug_name ILIKE :keyword")
            result = conn.execute(query, {"keyword": f"%{drug_keyword}%"}).fetchall()
            
            if not result:
                return f"⚠️ Obat '{drug_keyword}' tidak ditemukan di database inventaris."
            
            return "\n".join([f"- {row.drug_name}: {row.stock_level} {row.unit} (Status: {row.status})" for row in result])
    except Exception as e:
        return f"Error database: {str(e)}"

@tool
def allocate_bed_and_triage(patient_id: str, chief_complaint: str, priority_level: str, zone_required: str) -> str:
    """Mencari ranjang kosong, mendaftarkan pasien ke IGD, atau memasukkan ke daftar antrean jika IGD penuh.
    
    Args:
        patient_id: ID Pasien resmi dari database (contoh: 'P-101' atau 'P-7842').
        chief_complaint: Keluhan utama medis pasien saat ini.
        priority_level: Tingkat prioritas triase ('Red (Critical)', 'Yellow (Urgent)', atau 'Green (Stable)').
        zone_required: Zona IGD target ('Resuscitation', 'Observation', atau 'Fast Track Chair').
    """
    try:
        with engine.begin() as conn:
            find_bed_query = text("SELECT resource_id FROM er_resource_status WHERE status = 'Available' AND resource_type ILIKE :zone LIMIT 1 FOR UPDATE")
            bed_result = conn.execute(find_bed_query, {"zone": f"%{zone_required}%"}).fetchone()

            if bed_result:
                allocated_bed = bed_result[0]
                conn.execute(text("UPDATE er_resource_status SET status = 'Occupied' WHERE resource_id = :bed"), {"bed": allocated_bed})
                conn.execute(text("INSERT INTO active_triage_flow (patient_id, chief_complaint, triage_priority, assigned_resource_id, status) VALUES (:pid, :complaint, :priority, :bed, 'In Treatment')"), 
                             {"pid": patient_id, "complaint": chief_complaint, "priority": priority_level, "bed": allocated_bed})
                return f"✅ SUKSES: Pasien {patient_id} dialokasikan ke ranjang {allocated_bed} ({zone_required})."
            else:
                conn.execute(text("INSERT INTO active_triage_flow (patient_id, chief_complaint, triage_priority, assigned_resource_id, status) VALUES (:pid, :complaint, :priority, NULL, 'Waiting for Bed')"), 
                             {"pid": patient_id, "complaint": chief_complaint, "priority": priority_level})
                return f"⚠️ ANTREAN AKTIF: Zona {zone_required} PENUH. Pasien {patient_id} masuk daftar antrean (Waiting for Bed)."
    except Exception as e:
        return f"❌ Gagal melakukan alokasi: {str(e)}"

@tool
def assign_nurse_task(patient_id: str, task_description: str, urgency: str = "high") -> str:
    """Mendelegasikan tugas tindakan medis kepada perawat di IGD.
    
    Args:
        patient_id: ID Pasien target tindakan medis.
        task_description: Deskripsi jelas tentang apa yang harus dilakukan perawat.
        urgency: Tingkat urgensi tindakan ('high', 'medium', atau 'low'). Default 'high'.
    """
    try:
        with engine.begin() as conn:
            find_encounter = text("SELECT encounter_id FROM active_triage_flow WHERE patient_id = :pid AND status != 'Discharged' LIMIT 1")
            encounter_result = conn.execute(find_encounter, {"pid": patient_id}).fetchone()
            
            if not encounter_result:
                return f"Gagal membuat tugas: Pasien {patient_id} belum terdaftar di antrean IGD."
            
            insert_task = text("INSERT INTO staff_tasks (encounter_id, description, priority, is_completed) VALUES (:eid, :desc, :urgency, FALSE)")
            conn.execute(insert_task, {"eid": encounter_result[0], "desc": task_description, "urgency": urgency})
            return f"✅ Tugas perawat ditambahkan: '{task_description}' untuk pasien {patient_id}."
    except Exception as e:
        return f"Error delegasi tugas: {str(e)}"

# ==============================================================================
# 3. TELEGRAM & CALENDAR TOOLS
# ==============================================================================
@tool
def send_telegram_page(target_specialty: str, message: str) -> str:
    """Mengirim pesan Paging/Notifikasi Darurat via Telegram ke dokter spesialis jaga.
    
    Args:
        target_specialty: Bidang spesialisasi dokter yang dipanggil (contoh: 'Kardiologi', 'Bedah').
        message: Isi pesan kondisi darurat pasien secara ringkas.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return f"[MOCKUP] Simulasi berhasil: Mengirim '{message}' ke tim {target_specialty}."
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"🚨 PANGGILAN {target_specialty.upper()} 🚨\n{message}"}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return f"✅ Berhasil mengirim Telegram ke spesialis {target_specialty}."
    except Exception as e:
        return f"❌ Gagal mengirim Telegram: {str(e)}"

@tool
def schedule_google_calendar(event_title: str, description: str, minutes_from_now: int = 30) -> str:
    """Membuat jadwal prosedur medis, rontgen, atau konsultasi di Google Calendar rumah sakit.
    
    Args:
        event_title: Judul acara atau operasi medis.
        description: Detail lengkap instruksi tindakan atau tautan pasien.
        minutes_from_now: Berapa menit dari sekarang jadwal tersebut akan dimulai. Default 30.
    """
    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/calendar.events"])
        service = build('calendar', 'v3', credentials=credentials)
        
        start_time = datetime.utcnow() + timedelta(minutes=minutes_from_now)
        event = {
            'summary': event_title,
            'description': description,
            'start': {'dateTime': start_time.isoformat() + 'Z'},
            'end': {'dateTime': (start_time + timedelta(hours=1)).isoformat() + 'Z'},
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Jadwal '{event_title}' dibuat di Google Calendar. Link: {created_event.get('htmlLink')}"
    except Exception as e:
        return f"❌ Gagal membuat jadwal Google Calendar: {str(e)}"

# ==============================================================================
# 4. EXPORT TOOLS UNTUK AGENTS.PY
# ==============================================================================
langchain_tools = [
    register_new_patient,
    check_pharmacy_inventory,
    allocate_bed_and_triage,
    assign_nurse_task,
    send_telegram_page,
    schedule_google_calendar
]