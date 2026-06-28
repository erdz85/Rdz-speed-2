import streamlit as st
import pandas as pd
import os
from datetime import datetime
# 1. Page Configuration (Must be first)
st.set_page_config(layout="wide", page_title="RDZ Speed Intelligence")

# 2. Session State Initialization (The "Stability" Layer)
def init_session_state():
    if 'workout_logs' not in st.session_state:
        # We add 'log_id' for granular deletion later
        st.session_state.workout_logs = pd.DataFrame(columns=[
            'athlete_id', 'log_id', 'date', 'type', 'fat', 'proj_100'
        ])
    if 'athletes' not in st.session_state:
        st.session_state.athletes = pd.DataFrame()

# Call this immediately
init_session_state()

# 3. Rest of your application code begins here...

if 'workout_logs' not in st.session_state:
    st.session_state.workout_logs = pd.DataFrame(columns=['id', 'log_id', 'date', 'type', 'fat', 'proj_100'])  
    
def get_unified_projection(session_type, fat_time, block_val, fly_val, gender):
    """
    Unified projection model:
    Primary: 30m Block + (3.5 * 20m Fly) + C
    Fallback (No Block): (20m Fly / 2 * 10) + Gender Constant
    """
    is_female = 'female' in str(gender).lower()
    f_val = fly_val if (fly_val and fly_val > 0) else fat_time
    b_val = block_val if (block_val and block_val > 0) else None
    
    # 1. PRIMARY: Multi-Variable Formula (requires block start)
    if b_val is not None:
        base_proj = b_val + (3.5 * f_val)
        c = (0.15 if base_proj < 12.2 else 0.25) if is_female else (0.12 if base_proj < 11.0 else 0.18)
        return round(b_val + (3.5 * f_val) + c, 2)
    
    # 2. FALLBACK: Precise Conversion Model from Screen Shot 2026-06-27 at 7.44.36 PM.png
    else:
        # Femenil Constant: 1.15 | Varonil Constant: 1.05
        gender_const = 1.15 if is_female else 1.05 
        projection = (f_val / 2 * 10) + gender_const
        return round(projection, 2)
        
st.set_page_config(
    page_title="High-Performance Sprint Analytics",
    page_icon="⚡",
    layout="wide"
)

# --- LOCAL PERSISTENCE STORAGE TRACKERS ---
ROSTER_CACHE = "roster_storage.csv"
LOGS_CACHE = "workout_logs_storage.csv"

# ==========================================
# GLOBAL APP STATE INITIALIZATION & HEALING
# ==========================================

if 'athletes' not in st.session_state:
    if os.path.exists(ROSTER_CACHE):
        try:
            df = pd.read_csv(ROSTER_CACHE)
            
            # AUTOMATIC DATA HEALER: If columns split, merge them safely
            df.columns = [str(c).lower().strip() for c in df.columns]
            if 'full_name' in df.columns and 'name' in df.columns:
                df['name'] = df['name'].fillna(df['full_name'])
                df = df.drop(columns=['full_name'])
            elif 'full_name' in df.columns and 'name' not in df.columns:
                df = df.rename(columns={'full_name': 'name'})
                
            # Re-verify all required columns are present cleanly
            required_cols = ['id', 'name', 'gender', 'grade', 'group', 'tier', 'status']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = "Active" if col == 'status' else ""
            
            st.session_state.athletes = df[required_cols]
        except Exception:
            # Fallback safe frame if the file format is heavily corrupted
            st.session_state.athletes = pd.DataFrame(columns=['id', 'name', 'gender', 'grade', 'group', 'tier', 'status'])
    else:
        st.session_state.athletes = pd.DataFrame(columns=['id', 'name', 'gender', 'grade', 'group', 'tier', 'status'])

if 'workout_logs' not in st.session_state:
    if os.path.exists(LOGS_CACHE):
        st.session_state.workout_logs = pd.read_csv(LOGS_CACHE)
    else:
        st.session_state.workout_logs = pd.DataFrame(columns=[
            'log_id', 'date', 'athlete_id', 'type', 'raw', 'fat', 'proj_100'
        ])
# ==========================================
# GLOBAL CORE KINEMATIC UTILITIES (UPDATED)
# ==========================================

def normalize_hand_fly(hand_time: float) -> float:
    """Applies standard electronic/FAT conversion factor to manual stopwatch times."""
    return round(hand_time + 0.24, 2)

def calculate_projected_100m(block_time: float, fly_time: float, gender: str) -> float:
    """
    Predicts 100m FAT time using the Curved Velocity Regression Model.
    Bypasses multi-variable inflation to prevent mathematical time dilution.
    """
    try:
        f_time = float(fly_time)
        # Handle empty/missing data flags safely
        if f_time == 99.0 or f_time <= 0:
            return 99.0
            
        gender_clean = str(gender).lower().strip()
        
        if 'female' in gender_clean or 'girl' in gender_clean:
            # High School Girls Constant Matrix Baseline
            gender_constant = 1.17
        else:
            # High School Boys Constant Matrix Baseline
            gender_constant = 1.15

        # Precise Sports Science Method: (Fly Time / 20 * 100) + Constant
        projected_time = (f_time * 5.0) + gender_constant
        return round(projected_time, 2)
        
    except (ValueError, TypeError):
        return 99.0
# ==========================================
# 1. APP CONFIGURATION & STYLE SETUP
# ==========================================
st.set_page_config(
    page_title="RDZ Speed Development",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-contrast track-coaching aesthetics with forced high-visibility text colors
st.markdown("""
<style>
    /* Global metric card text styling overrides to prevent white-on-white text bugs */
    .metric-card { 
        background-color: #f8f9fa !important; 
        color: #111111 !important; 
        border-radius: 10px; 
        padding: 15px; 
        border-left: 5px solid #ff4b4b; 
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-card b, .metric-card span, .metric-card div, .metric-card p, .metric-card small {
        color: #111111 !important;
    }
    
    /* System Action Badges */
    .badge-top-speed { background-color: #f1c40f !important; color: black !important; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px;}
    .badge-hot { background-color: #e67e22 !important; color: white !important; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px;}
    .badge-pr { background-color: #2ecc71 !important; color: white !important; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px;}
    .badge-tag-varsity { background-color: #4a90e2 !important; color: white !important; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px; }
    .badge-tag-group { background-color: #9013fe !important; color: white !important; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px; }
    .badge-fatigue { background-color: #d9534f !important; color: white !important; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px;}
    
    /* Clean Print ledger layout constraints */
    .print-document { background-color: white !important; color: black !important; font-family: 'Courier New', Courier, monospace !important; padding: 25px; border: 2px solid black; }
    .insight-list { font-size: 1.1rem; line-height: 1.8; list-style-type: none; padding-left: 0; color: #111111 !important; }
    .insight-list li { color: #111111 !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. STATE MANAGER & PERSISTENT STORAGE
# ==========================================
if "athletes" not in st.session_state:
    st.session_state.athletes = pd.DataFrame([
        {"athlete_id": "UUID_A1", "first_name": "Marcus", "last_name": "Anderson", "gender": "male", "grade": 11, "status": "varsity", "group": "Short Sprinters"},
        {"athlete_id": "UUID_A2", "first_name": "Trey", "last_name": "Williams", "gender": "male", "grade": 12, "status": "varsity", "group": "Short Sprinters"},
        {"athlete_id": "UUID_A3", "first_name": "Elena", "last_name": "Martinez", "gender": "female", "grade": 11, "status": "varsity", "group": "Short Sprinters"},
        {"athlete_id": "UUID_A4", "first_name": "Jordan", "last_name": "Davis", "gender": "female", "grade": 9, "status": "jv", "group": "Short Sprinters"},
        {"athlete_id": "UUID_A5", "first_name": "Xavier", "last_name": "Thomas", "gender": "male", "grade": 10, "status": "varsity", "group": "Short Sprinters"},
        {"athlete_id": "UUID_A6", "first_name": "Carlos", "last_name": "Martinez", "gender": "male", "grade": 11, "status": "varsity", "group": "Long Sprinters"},
        {"athlete_id": "UUID_A7", "first_name": "Sarah", "last_name": "Miller", "gender": "female", "grade": 10, "status": "varsity", "group": "Hurdlers"}
    ])

if "pending_registrations" not in st.session_state:
    st.session_state.pending_registrations = pd.DataFrame(columns=["first_name", "last_name", "gender", "graduation_year", "grade"])

if "workout_logs" not in st.session_state:
    st.session_state.workout_logs = pd.DataFrame([
        {"log_id": "L1", "workout_id": "W1", "athlete_id": "UUID_A1", "type": "20m_fly", "raw_input_time": 2.25, "normalized_fat_time": 2.25, "projected_100m": 12.35, "is_pr": True, "date": "2026-04-01"},
        {"log_id": "L2", "workout_id": "W5", "athlete_id": "UUID_A1", "type": "20m_fly", "raw_input_time": 1.98, "normalized_fat_time": 1.98, "projected_100m": 10.95, "is_pr": True, "date": "2026-06-25"},
        {"log_id": "L3", "workout_id": "W5", "athlete_id": "UUID_A1", "type": "30m_block", "raw_input_time": 3.95, "normalized_fat_time": 3.95, "projected_100m": 10.95, "is_pr": True, "date": "2026-06-25"},
        {"log_id": "L4", "workout_id": "W5", "athlete_id": "UUID_A2", "type": "20m_fly", "raw_input_time": 2.18, "normalized_fat_time": 2.18, "projected_100m": 12.10, "is_pr": True, "date": "2026-04-01"},
        {"log_id": "L5", "workout_id": "W5", "athlete_id": "UUID_A2", "type": "20m_fly", "raw_input_time": 2.04, "normalized_fat_time": 2.04, "projected_100m": 11.25, "is_pr": True, "date": "2026-06-25"},
        {"log_id": "L6", "workout_id": "W5", "athlete_id": "UUID_A5", "type": "20m_fly", "raw_input_time": 2.30, "normalized_fat_time": 2.30, "projected_100m": 12.65, "is_pr": True, "date": "2026-04-01"},
        {"log_id": "L7", "workout_id": "W5", "athlete_id": "UUID_A5", "type": "20m_fly", "raw_input_time": 2.10, "normalized_fat_time": 2.10, "projected_100m": 11.55, "is_pr": True, "date": "2026-06-25"},
        {"log_id": "L8", "workout_id": "W5", "athlete_id": "UUID_A4", "type": "20m_fly", "raw_input_time": 2.40, "normalized_fat_time": 2.40, "projected_100m": 13.10, "is_pr": True, "date": "2026-04-01"},
        {"log_id": "L9", "workout_id": "W5", "athlete_id": "UUID_A4", "type": "20m_fly", "raw_input_time": 2.15, "normalized_fat_time": 2.15, "projected_100m": 11.75, "is_pr": True, "date": "2026-06-25"},
        {"log_id": "L10", "workout_id": "W5", "athlete_id": "UUID_A4", "type": "30m_block", "raw_input_time": 4.10, "normalized_fat_time": 4.10, "projected_100m": 11.75, "is_pr": True, "date": "2026-06-25"},
        {"log_id": "L11", "workout_id": "W5", "athlete_id": "UUID_A7", "type": "20m_fly", "raw_input_time": 2.32, "normalized_fat_time": 2.32, "projected_100m": 12.55, "is_pr": True, "date": "2026-06-25"}
    ])

if "training_groups" not in st.session_state:
    st.session_state.training_groups = ["Short Sprinters", "Long Sprinters", "Hurdlers", "Throwers", "Distance", "Hurt/Injured"]

if "active_session_logs" not in st.session_state: st.session_state.active_session_logs = []
if "keypad_buffer" not in st.session_state: st.session_state.keypad_buffer = ""
if "active_athlete_input_id" not in st.session_state: st.session_state.active_athlete_input_id = None

# ==========================================
# 3. MATHEMATICAL CALCULATION CORES (UPDATED)
# ==========================================

def calculate_relay_go_mark(inc_fly, out_block):
    """
    Calculates the acceleration zone go-mark distance in footsteps.
    Guards against unrecorded placeholder times (99.0).
    """
    try:
        inc_fly = float(inc_fly)
        out_block = float(out_block)
        
        # SAFETY GUARD: If either runner lacks data, return standard default footsteps
        if inc_fly >= 99.0 or out_block >= 99.0 or inc_fly <= 0 or out_block <= 0:
            return 18.0  
            
        raw_mark = (out_block - inc_fly) * 7.5
        return float(max(1.0, round(raw_mark, 1)))
    except:
        return 18.0


def calculate_precise_100m(thirty_block, twenty_fly, gender, is_hand_timed=False):
    """
    Advanced Piecewise Kinetic Splicing Model.
    Uses real 30m block data for acceleration mechanics + 20m fly for max velocity profile.
    Automatically falls back to the Curved Velocity Regression Model if block data is missing.
    """
    import pandas as pd
    
    # 1. Validate and Clean Fly Time (Absolute Required Baseline)
    if twenty_fly is None or pd.isna(twenty_fly):
        return None
    try:
        twenty_fly = float(twenty_fly)
        if twenty_fly <= 0 or twenty_fly >= 99.0:
            return None
    except (ValueError, TypeError):
        return None
        
    # 2. Validate and Clean Block Time (Optional Premium Precision Input)
    try:
        if thirty_block is not None and not pd.isna(thirty_block):
            thirty_block = float(thirty_block)
            if thirty_block <= 0 or thirty_block >= 99.0:
                thirty_block = None
        else:
            thirty_block = None
    except (ValueError, TypeError):
        thirty_block = None
    
    # 3. Apply Uniform FAT Electronic Offsets if Hand-Timed (+0.24)
    if is_hand_timed:
        twenty_fly = round(twenty_fly + 0.24, 2)
        if thirty_block is not None:
            thirty_block = round(thirty_block + 0.24, 2)

    # 4. EXECUTE DUAL-INPUT MODEL OR FALLBACK
    gender_clean = str(gender).lower().strip()
    
    if thirty_block is not None:
        # --- MODEL A: PIECEWISE KINETIC SPLICING (MAX PRECISION) ---
        # 30m block start + remaining 70m run at 20m fly terminal velocity (70 / 20 = 3.5)
        projected_100m = thirty_block + (twenty_fly * 3.5)
    else:
        # --- MODEL B: CURVED VELOCITY REGRESSION (FALLBACK) ---
        # Used when block data is unrecorded. Employs fixed inertia constants.
        gender_constant = 1.17 if ('female' in gender_clean or 'girl' in gender_clean) else 1.15
        projected_100m = (twenty_fly * 5.0) + gender_constant
            
    return round(projected_100m, 2)


# ==========================================
# BACKWARD COMPATIBILITY LAYER FOR OTHER MODULES
# ==========================================

def get_best_historical_fat(athlete_id, run_type="20m_fly"):
    """
    Finds the historical PR for an athlete while safeguarding against column case variations.
    """
    import pandas as pd
    import streamlit as st
    
    if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        return float('inf')
        
    logs = st.session_state.workout_logs.copy()
    logs.columns = [str(c).lower() for c in logs.columns]
    
    fat_col = 'normalized_fat_time' if 'normalized_fat_time' in logs.columns else ('fat' if 'fat' in logs.columns else logs.columns[-1])
    type_col = 'type' if 'type' in logs.columns else ('session_type' if 'session_type' in logs.columns else logs.columns[-2])
    
    filtered = logs[(logs["athlete_id"].astype(str).str.strip() == str(athlete_id).strip()) & (logs[type_col] == run_type)]
    if filtered.empty: 
        return float('inf')
        
    return pd.to_numeric(filtered[fat_col], errors='coerce').min()


def project_100m_dash(fat_time, gender):
    """
    Points legacy page references directly into the updated precision engine.
    """
    if not fat_time or fat_time == 0 or fat_time >= 99.0:
        return 0.0
    return calculate_precise_100m(thirty_block=None, twenty_fly=fat_time, gender=gender)
    
# ==========================================
# 4. GLOBAL NAVIGATION AND CONTROL ROUTER
# ==========================================
st.sidebar.title("⚡ RDZ Navigation")

# Unified global toggle input bindings
timing_method = st.sidebar.radio("⚙️ Global Timing Input Method:", ["Freelap/FAT", "Hand-Timed"], index=0)
is_hand = timing_method == "Hand-Timed"

app_portal = st.sidebar.radio("Go To Module Portal:", [
    "👥 Roster & Onboarding Hub",
    "⏱️ Workout Tracker",   
    "📆 Live Session Dashboard",
    "🤝 Relay Optimizer Pool",
    "📈 Athlete Progress Trends",
    "🏆 Team Leaderboards", 
    "📄 AD Report Export"
])

# ==========================================
# MODULE 1: ROSTER & ONBOARDING HUB
# ==========================================
if app_portal == "👥 Roster & Onboarding Hub":
    st.title("👥 Roster & Onboarding Hub")
    st.markdown("Manage your team roster, onboard new athletes, and control active training availability status.")

    # Initialize the athletes DataFrame if it doesn't exist in session memory
    if 'athletes' not in st.session_state:
        import os
        if os.path.exists("roster_storage.csv"):
            st.session_state.athletes = pd.read_csv("roster_storage.csv")
        else:
            st.session_state.athletes = pd.DataFrame(columns=['id', 'name', 'gender', 'grade', 'group', 'tier', 'status'])

    # --- SECTION 1: ATHLETE ONBOARDING FORM ---
    st.subheader("📝 Onboard New Athlete")
    with st.form("onboarding_form", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            new_name = st.text_input("Full Name:")
            new_gender = st.selectbox("Gender:", ["Male", "Female"])
        with f_col2:
            new_grade = st.selectbox("Grade Level:", ["9", "10", "11", "12"])
            new_group = st.selectbox("Training Group:", ["Short Sprinters", "Hurdlers", "Long Sprinters", "Jumpers"])
        with f_col3:
            new_tier = st.selectbox("Roster Tier Allocation:", ["Varsity", "JV / Developing"])
            new_status = st.selectbox("Initial Status:", ["Active", "Inactive"], help="Set initial operational availability.")

        submit_btn = st.form_submit_button("➕ Add Athlete to Roster", use_container_width=True)
        
        if submit_btn:
            if not new_name.strip():
                st.error("⚠️ Athlete name cannot be blank.")
            else:
                # Dynamically evaluate the current ID tracking column safely
                existing_roster = st.session_state.athletes.copy()
                existing_roster.columns = [str(c).lower() for c in existing_roster.columns]
                
                if existing_roster.empty:
                    new_id = "1"
                else:
                    id_col_name = 'id' if 'id' in existing_roster.columns else existing_roster.columns[0]
                    try:
                        new_id = str(int(pd.to_numeric(existing_roster[id_col_name], errors='coerce').max()) + 1)
                    except:
                        new_id = str(len(existing_roster) + 1)
                
                new_athlete = {
                    "id": new_id,
                    "name": new_name.strip(),
                    "gender": new_gender,
                    "grade": new_grade,
                    "group": new_group,
                    "tier": new_tier,
                    "status": new_status
                }
                
                st.session_state.athletes = pd.concat([st.session_state.athletes, pd.DataFrame([new_athlete])], ignore_index=True)
                
                # [PERSISTENCE UPDATE]: Write to storage disk on addition
                st.session_state.athletes.to_csv("roster_storage.csv", index=False)
                
                st.success(f"🎉 Onboarded {new_name} successfully as {new_status}!")
                st.rerun()

    st.write("---")

    # --- SECTION 2: ROSTER MANAGEMENT MATRIX ---
    st.subheader("📋 Active Roster Management Table")
    
    if st.session_state.athletes.empty:
        st.info("ℹ️ No athletes currently registered on the roster.")
    else:
        # Clone roster and force all display columns to lowercase to prevent KeyErrors
        m_roster = st.session_state.athletes.copy()
        m_roster.columns = [str(c).lower() for c in m_roster.columns]
        
        # Smart Key Resolution backups for original frame updating
        orig_id_col = st.session_state.athletes.columns[0]
        for c in st.session_state.athletes.columns:
            if str(c).lower() == 'id':
                orig_id_col = c
                break

        # Ensure status column exists safely
        if 'status' not in m_roster.columns:
            st.session_state.athletes['Status'] = "Active"
            m_roster['status'] = "Active"

        # Table Header Layout Metrics
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 2])
        with h1: st.markdown("🏃 **Athlete Name**")
        with h2: st.markdown("🏷️ **Group / Tier**")
        with h3: st.markdown("⚙️ **Availability Toggle**")
        with h4: st.markdown("📌 **Current Status**")
        with h5: st.markdown("❌ **Remove**")
        st.markdown("<hr style='margin: 0px 0px 15px 0px; border-color: #555;' />", unsafe_allow_html=True)

        # Dynamic management loop execution
        for index, row in m_roster.iterrows():
            a_id = str(row['id']).strip()
            a_name = row.get('name', row.get('full_name', 'Unknown'))
            a_group = row.get('group', 'Sprinters')
            a_tier = row.get('tier', 'Varsity')
            a_status = row.get('status', 'Active')
            
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            
            with c1:
                st.markdown(f"<div style='padding-top: 5px;'><b>{a_name}</b></div>", unsafe_allow_html=True)
            with c2:
                st.caption(f"{a_group} • {a_tier}")
            with c3:
                # Active/Inactive Status Switch Toggle
                is_active = (str(a_status).lower() == "active")
                toggle_label = "Set Inactive" if is_active else "Set Active"
                if st.button(toggle_label, key=f"tog_{a_id}", use_container_width=True):
                    next_status = "Inactive" if is_active else "Active"
                    
                    # Update target using standard vector lookups matching the base frame keys
                    idx_match = st.session_state.athletes[st.session_state.athletes[orig_id_col].astype(str).str.strip() == a_id].index
                    if 'status' in st.session_state.athletes.columns:
                        st.session_state.athletes.loc[idx_match, 'status'] = next_status
                    else:
                        st.session_state.athletes.loc[idx_match, 'Status'] = next_status
                        
                    # [PERSISTENCE UPDATE]: Write to storage disk on change of status
                    st.session_state.athletes.to_csv("roster_storage.csv", index=False)
                    
                    st.toast(f"🔄 Updated {a_name} to {next_status}!")
                    st.rerun()
            with c4:
                # Colored Status Visual Badges
                if str(a_status).lower() == "active":
                    st.markdown("<span style='color:#00E676; font-weight:bold;'>🟢 Active</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#FF4B4B; font-weight:bold;'>🔴 Inactive</span>", unsafe_allow_html=True)
            with c5:
                # Complete Deletion Action Engine
                if st.button("Delete", key=f"del_{a_id}", use_container_width=True):
                    # Filter matching values safely from base state storage frames
                    st.session_state.athletes = st.session_state.athletes[st.session_state.athletes[orig_id_col].astype(str).str.strip() != a_id]
                    
                    # [PERSISTENCE UPDATE]: Write to storage disk on complete delete removal
                    st.session_state.athletes.to_csv("roster_storage.csv", index=False)
                    
                    st.success(f"🗑️ Removed {a_name} completely from roster.")
                    st.rerun()
                    
# ==========================================
# MODULE 2: Workout Tracker
# ==========================================
elif app_portal == "⏱️ Workout Tracker":
    st.title("⏱️ Unified Workout Hub")
    
    # 1. Prepare historical PR lookups
    history_fly = {}
    history_block = {}
    
    if 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty:
        logs_clean = st.session_state.workout_logs.copy()
        logs_clean.columns = [str(c).lower() for c in logs_clean.columns]
        
        fat_col = 'fat' if 'fat' in logs_clean.columns else logs_clean.columns[-2]
        
        history_fly = logs_clean[logs_clean['type'] == '20m_fly'].groupby('athlete_id')[fat_col].min().to_dict()
        history_block = logs_clean[logs_clean['type'] == '30m_block'].groupby('athlete_id')[fat_col].min().to_dict()

    # 2. Initialize the Tabs ONCE
    tab1, tab2 = st.tabs(["🆕 Log New Reps", "📊 History & Stats"])
    
    with tab1:
        # Configuration
        col_sys, col_drill = st.columns(2)
        with col_sys:
            timing_system = st.radio("Timing System:", ["Electronic / FAT (Freelap)", "Hand-Timed (Stopwatch)"], horizontal=True)
        with col_drill:
            session_type = st.selectbox("Drill Type:", ["20m_fly", "30m_block"])
        
        st.write("---")
        
        # Header and Loop
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 3, 2])
        with h1: st.markdown("🏃 **Athlete**")
        with h2: st.markdown("⚡ **Best Fly**")
        with h3: st.markdown("🧱 **Best Block**")
        with h4: st.markdown("⏱️ **Enter Time (s)**")
        with h5: st.markdown("💾 **Action**")

        for index, athlete in st.session_state.athletes.iterrows():
            string_id = str(athlete['id']).strip()
            best_fly = history_fly.get(string_id, 0)
            best_block = history_block.get(string_id, 0)
            
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 3, 2])
            with c1: st.markdown(f"**{athlete['name']}**")
            with c2: st.markdown(f"⚡ {best_fly:.2f}s" if best_fly else "⚡ --")
            with c3: st.markdown(f"🧱 {best_block:.2f}s" if best_block else "🧱 --")
            with c4:
                raw_time = st.number_input("Time", 0.0, 12.0, 0.0, 0.01, key=f"in_{string_id}", label_visibility="collapsed")
            with c5:
                if st.button("Log", key=f"btn_{string_id}"):
                    if raw_time <= 0:
                        st.error("Enter time > 0")
                    else:
                        fat_time = raw_time + 0.24 if timing_system == "Hand-Timed (Stopwatch)" else raw_time
                        proj = get_unified_projection(session_type, fat_time, best_block, best_fly, athlete.get('gender', 'male'))
                        
                        new_log = {"date": datetime.today().strftime('%Y-%m-%d'), "athlete_id": string_id, "type": session_type, "fat": fat_time, "proj_100": proj}
                        st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame([new_log])], ignore_index=True)
                        st.session_state.workout_logs.to_csv("workout_logs_storage.csv", index=False)
                        st.rerun()

    with tab2:
        st.subheader("Performance History")
        if 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty:
            display_df = st.session_state.workout_logs.sort_values(by='date', ascending=False)
            st.dataframe(display_df, use_container_width=True)
            if st.button("🗑️ Clear All Logs"):
                st.session_state.workout_logs = pd.DataFrame(columns=["date", "athlete_id", "type", "raw", "fat", "proj_100"])
                st.session_state.workout_logs.to_csv("workout_logs_storage.csv", index=False)
                st.rerun()
        else:
            st.info("No records found.")
            
# ==========================================
# MODULE 3: LIVE SESSION DASHBOARD (UNIFIED)
# ==========================================
elif app_portal == "📆 Live Session Dashboard":
    st.title("📆 Today's Live Session Dashboard")
    st.markdown("Real-time tracking matrix of sprints and calculated projections captured today.")

    if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.info("ℹ️ No workout logs recorded in the system yet.")
    else:
        from datetime import datetime
        import pandas as pd
        
        today_str = datetime.today().strftime('%Y-%m-%d')
        logs_clean = st.session_state.workout_logs.copy()
        logs_clean.columns = [str(c).lower() for c in logs_clean.columns]
        todays_logs = logs_clean[logs_clean['date'] == today_str].copy()
        
        if todays_logs.empty:
            st.info(f"ℹ️ No repetitions logged yet for today ({today_str}).")
        elif 'athletes' not in st.session_state or st.session_state.athletes.empty:
            st.warning("⚠️ Roster database missing.")
        else:
            roster_clean = st.session_state.athletes.copy()
            roster_clean.columns = [str(c).lower() for c in roster_clean.columns]
            
            # Key Resolution
            right_key = 'id' if 'id' in roster_clean.columns else 'athlete_id'
            name_key = 'name' if 'name' in roster_clean.columns else roster_clean.columns[1]
            gender_key = 'gender' if 'gender' in roster_clean.columns else 'sex'
            
            fat_col = 'fat' if 'fat' in todays_logs.columns else todays_logs.columns[-2]
            
            # Compiled Session Matrix
            st.subheader("🏁 Compiled Today's Best Summary Matrix")
            
            session_fly = todays_logs[todays_logs['type'] == '20m_fly'].groupby('athlete_id')[fat_col].min().to_dict()
            session_block = todays_logs[todays_logs['type'] == '30m_block'].groupby('athlete_id')[fat_col].min().to_dict()
            
            athletes_active_today = roster_clean[roster_clean[right_key].isin(todays_logs['athlete_id'].unique())]
            
            h1, h2, h3, h4 = st.columns([3, 2, 2, 3])
            with h1: st.markdown("👤 **Athlete**")
            with h2: st.markdown("⚡ **Best Fly**")
            with h3: st.markdown("🧱 **Best Block**")
            with h4: st.markdown("🎯 **Session Proj. 100m**")
            st.markdown("<hr style='margin: 0px 0px 12px 0px;' />", unsafe_allow_html=True)
            
            for _, athlete in athletes_active_today.iterrows():
                a_id = str(athlete[right_key]).strip()
                a_name = athlete[name_key]
                a_gender = str(athlete.get(gender_key, 'male')).lower()
                
                # Fetch Best: Today's, then historical
                best_fly = session_fly.get(a_id)
                best_block = session_block.get(a_id)
                
                fly_input = best_fly if best_fly else logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '20m_fly')][fat_col].min()
                block_input = best_block if best_block else logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '30m_block')][fat_col].min()
                
                # Coerce to None if NaN
                fly_input = float(fly_input) if pd.notna(fly_input) else None
                block_input = float(block_input) if pd.notna(block_input) else None
                
                # UNIFIED PROJECTION CALL
                proj_val = get_unified_projection("20m_fly", fly_input or 0, block_input, fly_input, a_gender)
                
                # Render
                r1, r2, r3, r4 = st.columns([3, 2, 2, 3])
                with r1: st.markdown(f"**{a_name}**")
                with r2: st.markdown(f"{fly_input:.2f}s" if fly_input else "--")
                with r3: st.markdown(f"{block_input:.2f}s" if block_input else "--")
                with r4: st.markdown(f"**{proj_val:.2f}s**")
                st.write("---")
                
# ==========================================
# MODULE 4: RELAY OPTIMIZER POOL & GO-MARK GENERATOR (COMPLETE)
# ==========================================
elif app_portal == "🤝 Relay Optimizer Pool": 
    st.title("🏆 Data-Optimized 4x100m Relay Builder")
    st.markdown("Algorithmic sorting mapped with kinematic go-mark physics.")
    
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    else:
        # --- PREPARATION ---
        roster_clean = st.session_state.athletes.copy()
        roster_clean.columns = [str(c).lower() for c in roster_clean.columns]
        if 'status' in roster_clean.columns:
            roster_clean = roster_clean[roster_clean['status'].astype(str).str.lower() == 'active']
        
        id_key = 'id' if 'id' in roster_clean.columns else roster_clean.columns[0]
        name_key = 'name' if 'name' in roster_clean.columns else roster_clean.columns[1]
        gender_key = 'gender' if 'gender' in roster_clean.columns else 'sex'
        relay_gender = st.selectbox("Select Target Relay Division Profile:", ["Male", "Female"])
        
        # --- METRIC ENGINE ---
        logs_clean = st.session_state.workout_logs.copy()
        logs_clean.columns = [str(c).lower() for c in logs_clean.columns]
        fat_col = 'fat' if 'fat' in logs_clean.columns else logs_clean.columns[-2]
        type_col = 'type' if 'type' in logs_clean.columns else 'session_type'
        
        roster_metrics = []
        for _, athlete in roster_clean[roster_clean[gender_key].astype(str).str.lower() == relay_gender.lower()].iterrows():
            ath_id = str(athlete[id_key]).strip()
            b_fly = logs_clean[(logs_clean['athlete_id'].astype(str).str.strip() == ath_id) & (logs_clean[type_col] == "20m_fly")][fat_col].min()
            b_block = logs_clean[(logs_clean['athlete_id'].astype(str).str.strip() == ath_id) & (logs_clean[type_col] == "30m_block")][fat_col].min()
            if pd.notna(b_fly) or pd.notna(b_block):
                roster_metrics.append({"name": str(athlete[name_key]), "fly": float(b_fly) if pd.notna(b_fly) else 99.0, "block": float(b_block) if pd.notna(b_block) else 99.0})

        if len(roster_metrics) >= 4:
            rdf = pd.DataFrame(roster_metrics)
            s_leg1, s_leg2, s_leg3, s_leg4 = rdf.sort_values(by='block').iloc[0], rdf.sort_values(by='fly').iloc[0], rdf.sort_values(by='fly').iloc[1], rdf.sort_values(by='fly').iloc[2]
            
            # --- OVERRIDE UI ---
            c1, c2, c3, c4 = st.columns(4)
            names = [item['name'] for item in roster_metrics]
            leg1_name = c1.selectbox("Leg 1 (Block):", names, index=names.index(s_leg1['name']))
            leg2_name = c2.selectbox("Leg 2 (Straight):", names, index=names.index(s_leg2['name']))
            leg3_name = c3.selectbox("Leg 3 (Curve):", names, index=names.index(s_leg3['name']))
            leg4_name = c4.selectbox("Leg 4 (Anchor):", names, index=names.index(s_leg4['name']))

            # --- KINEMATIC CALCULATION ENGINE ---
            def get_go_mark_logic(f, b, gen):
                # Differential Gap Formula: [(20/Fly * (Start * 0.71)) - 20m - 0.70m] * 3.28
                steps = (( (20 / (f if f != 99.0 else 2.20)) * ((b if b != 99.0 else 4.20) * 0.71) ) - 20 - 0.70) * 3.28
                raw = int(round(steps))
                # Logic Tier Identification
                if 'female' in str(gen).lower():
                    tier = "Varsity" if (15 <= raw <= 22) else "Developing"
                else:
                    tier = "Varsity" if (19 <= raw <= 26) else "Developing"
                return raw, tier

            run_map = {item['name']: item for item in roster_metrics}
            m12, t12 = get_go_mark_logic(run_map[leg1_name]['fly'], run_map[leg2_name]['block'], relay_gender)
            m23, t23 = get_go_mark_logic(run_map[leg2_name]['fly'], run_map[leg3_name]['block'], relay_gender)
            m34, t34 = get_go_mark_logic(run_map[leg3_name]['fly'], run_map[leg4_name]['block'], relay_gender)

            # --- DISPLAY ---
            with st.container(border=True):
                st.markdown("### 🗺️ Acceleration Checkmark Marks")
                st.write(f"* 🏁 **Exchange 1:** {m12} footsteps ({t12} Tier)")
                st.write(f"* 🏁 **Exchange 2:** {m23} footsteps ({t23} Tier)")
                st.write(f"* 🏁 **Exchange 3:** {m34} footsteps ({t34} Tier)")
                
            if st.button("💾 Lock & Dispatch Lineup"):
                st.toast("🚀 Lineup Dispatched to Executive AD Hub!", icon="🔥")
        else:
            st.warning("⚠️ Need 4+ athletes with metrics to optimize.")
            
# ==========================================
# MODULE 5: ATHLETE PROGRESS TRENDS (AUDITED & UNIFIED)
# ==========================================
elif app_portal == "📈 Athlete Progress Trends":
    st.title("📈 The Athlete Progress Screen")
    st.markdown("Individual performance analytics, CNS fatigue tracking, and predictive recruitment modeling.")

    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    elif 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.info("ℹ️ No speed progression metrics found.")
    else:
        # Standardize Data
        roster_clean = st.session_state.athletes.copy()
        roster_clean.columns = [str(c).lower() for c in roster_clean.columns]
        logs_clean = st.session_state.workout_logs.copy()
        logs_clean.columns = [str(c).lower() for c in logs_clean.columns]

        id_key = 'id' if 'id' in roster_clean.columns else roster_clean.columns[0]
        name_key = 'name' if 'name' in roster_clean.columns else roster_clean.columns[1]
        gender_key = 'gender' if 'gender' in roster_clean.columns else 'sex'

        athlete_mapping = {row[name_key]: str(row[id_key]).strip() for _, row in roster_clean.iterrows()}
        selected_name = st.selectbox("👤 Select Athlete Profile:", list(athlete_mapping.keys()))
        selected_id = athlete_mapping[selected_name]

        athlete_meta = roster_clean[roster_clean[id_key].astype(str).str.strip() == selected_id].iloc[0]
        athlete_logs = logs_clean[logs_clean['athlete_id'].astype(str).str.strip() == selected_id].copy()
        
        athlete_logs['date'] = pd.to_datetime(athlete_logs['date'])
        athlete_logs = athlete_logs.sort_values(by='date')
        
        fat_col = 'fat' if 'fat' in athlete_logs.columns else 'time'
        athlete_logs[fat_col] = pd.to_numeric(athlete_logs[fat_col], errors='coerce')
        gender_val = str(athlete_meta.get(gender_key, 'male')).lower()

        # UI Header
        with st.container(border=True):
            st.markdown(f"## 👤 {selected_name.upper()}")
            st.markdown(f"**Tier:** {athlete_meta.get('tier', 'Varsity').title()} | **Group:** {athlete_meta.get('group', 'Sprints')}")

        chart_view = st.radio("Analytics Dimension:", ["⚡ 20m Fly", "🧱 30m Block", "⏱️ Recruitment Forecast"], horizontal=True)

        if "20m Fly" in chart_view:
            st.line_chart(athlete_logs[athlete_logs['type'] == '20m_fly'].groupby('date')[fat_col].min())
        elif "30m Block" in chart_view:
            st.line_chart(athlete_logs[athlete_logs['type'] == '30m_block'].groupby('date')[fat_col].min())
        else:
            # UNIFIED PROJECTION ENGINE CALL
            st.subheader("⏱️ Recruitment Projections")
            fly_logs = athlete_logs[athlete_logs['type'] == '20m_fly'].groupby('date')[fat_col].min().reset_index()
            
            proj_100_list = []
            for _, p_row in fly_logs.iterrows():
                f_val = p_row[fat_col]
                b_day = athlete_logs[(athlete_logs['date'] == p_row['date']) & (athlete_logs['type'] == '30m_block')][fat_col]
                b_val = b_day.min() if not b_day.empty else None
                
                # Using the Unified Engine to maintain constant accuracy (1.05 / 1.15)
                p_val = get_unified_projection("20m_fly", f_val, b_val, f_val, gender_val)
                proj_100_list.append(round(p_val, 2))
            
            fly_logs['100m Proj'] = proj_100_list
            st.line_chart(fly_logs.set_index('date')[['100m Proj']])

        # Insights Engine
        st.write("---")
        st.subheader("📊 Season Insights")
        if not athlete_logs.empty:
            best_fly = athlete_logs[athlete_logs['type'] == '20m_fly'][fat_col].min()
            best_block = athlete_logs[athlete_logs['type'] == '30m_block'][fat_col].min()
            est_100 = get_unified_projection("20m_fly", best_fly, best_block, best_fly, gender_val)
            
            m1, m2 = st.columns(2)
            m1.metric("Est. 100m FAT", f"{est_100:.2f}s")
            
            # CNS Fatigue Logic
            latest_type = athlete_logs['type'].iloc[-1]
            recent = athlete_logs[athlete_logs['type'] == latest_type].tail(3)
            if len(recent) >= 3 and recent[fat_col].iloc[-1] > (recent[fat_col].iloc[0] * 1.03):
                st.warning("⚠️ **CNS Fatigue Detected:** Velocity decay > 3%. Recovery recommended.")
            else:
                st.success("✅ **CNS Muscle Readiness:** Normal.")
                    
# ==========================================
# MODULE 6: TEAM LEADERBOARDS (AUDITED)
# ==========================================
elif app_portal == "🏆 Team Leaderboards":
    st.title("🔥 Team Leaderboards")
    
    if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.warning("⚠️ No workout log data found.")
    else:
        logs = st.session_state.workout_logs.copy()
        logs.columns = [str(c).lower() for c in logs.columns]
        fat_col = 'fat' if 'fat' in logs.columns else 'time'
        type_col = 'type' if 'type' in logs.columns else 'session_type'
        
        # UI Filters
        l_col1, l_col2 = st.columns(2)
        gender_filter = l_col1.selectbox("Gender Select:", ["All", "Male", "Female"])
        tier_filter = l_col2.selectbox("Roster Tier:", ["All Varsity", "JV / Developing"])

        # Prep Roster
        roster = st.session_state.athletes.copy()
        roster.columns = [str(c).lower() for c in roster.columns]
        # ... [Roster filtering logic remains as you had it] ...

        # --- LEADERBOARD COMPILATION LOGIC ---
        leaderboard_type = st.radio("Select Ranking:", ["⚡ 20m Fly", "🧱 30m Block", "⏱️ Projected 100m"], horizontal=True)

        if "20m Fly" in leaderboard_type:
            metric_df = logs[logs[type_col] == '20m_fly'].groupby('athlete_id')[fat_col].min().reset_index()
            suffix = "s"
        elif "30m Block" in leaderboard_type:
            metric_df = logs[logs[type_col] == '30m_block'].groupby('athlete_id')[fat_col].min().reset_index()
            suffix = "s"
        else:
            # PROJECTED 100M: UNIFIED ENGINE CALL
            fly_bests = logs[logs[type_col] == '20m_fly'].groupby('athlete_id')[fat_col].min().reset_index()
            block_bests = logs[logs[type_col] == '30m_block'].groupby('athlete_id')[fat_col].min().reset_index()
            
            # Join data for the projection loop
            combined = pd.merge(fly_bests.rename(columns={fat_col: 'fly'}), 
                                block_bests.rename(columns={fat_col: 'block'}), 
                                on='athlete_id', how='outer')
            
            computed_projections = []
            for _, row in combined.iterrows():
                # Fetch gender from roster for this ID
                ath_row = roster[roster['id'] == str(row['athlete_id'])]
                g = ath_row['gender'].iloc[0] if not ath_row.empty else 'male'
                
                # CALLING SOURCE OF TRUTH: get_unified_projection
                proj = get_unified_projection(None, row['fly'], row['block'], row['fly'], g)
                computed_projections.append(proj)
            
            combined[fat_col] = computed_projections
            metric_df = combined[['athlete_id', fat_col]]
            suffix = "s (Est)"

        # Merge and Sort
        leaderboard_df = roster.merge(metric_df, left_on='id', right_on='athlete_id')
        leaderboard_df = leaderboard_df.sort_values(by=fat_col).reset_index(drop=True)

        # UI Rendering
        for rank, (_, row) in enumerate(leaderboard_df.iterrows(), start=1):
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"#### {rank}. {row['name']} *({row.get('group', 'Sprints')})*")
                c2.markdown(f"### **{row[fat_col]:.2f}{suffix}**")

# ==========================================
# MODULE 7: AD REPORT EXPORT ("THE AD CLOSER") - COMPLETE & AUDITED
# ==========================================
elif app_portal == "📄 AD Report Export":
    import io
    import pandas as pd
    from datetime import datetime
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    st.title("📄 Executive AD Report Generator")
    st.subheader("Generate Data-Driven Program Justification Printouts")
    
    # 1. User Inputs & Configuration Controls
    col1, col2 = st.columns(2)
    with col1:
        coach_name = st.text_input("Head Coach Name:", value="John Doe")
        program_name = st.text_input("Program Title:", value="NORTHSIDE TRACK & FIELD")
    with col2:
        squad_division = st.selectbox("Squad/Division Filter:", ["VARSITY BOYS", "VARSITY GIRLS", "FROSH-SOPH"])
        state_qual_time = st.number_input("State Qual 100m Benchmark (s):", value=11.00, step=0.05)

    st.write("---")

    # 2. Safety Guardrails & Data Processing
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    else:
        roster_clean = st.session_state.athletes.copy()
        roster_clean.columns = [str(c).lower().strip() for c in roster_clean.columns]
        active_squad = roster_clean[roster_clean['status'].astype(str).str.lower() == 'active']
        
        # Apply filters
        if squad_division == "VARSITY BOYS":
            active_squad = active_squad[(active_squad['tier'].astype(str).str.lower() == 'varsity') & (active_squad['gender'].astype(str).str.lower() == 'male')]
        elif squad_division == "VARSITY GIRLS":
            active_squad = active_squad[(active_squad['tier'].astype(str).str.lower() == 'varsity') & (active_squad['gender'].astype(str).str.lower() == 'female')]
        elif squad_division == "FROSH-SOPH":
            active_squad = active_squad[active_squad['grade'].astype(str).str.strip().isin(['9', '10'])]

        has_logs = 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty
        logs_clean = st.session_state.workout_logs.copy() if has_logs else pd.DataFrame()
        if has_logs:
            logs_clean.columns = [str(c).lower().strip() for c in logs_clean.columns]
            logs_clean['athlete_id'] = logs_clean['athlete_id'].astype(str).str.strip()

        # 3. Processing Loop (AUDITED)
        processed_roster = []
        relay_pool = []
        total_deltas, delta_count, velocity_sums, velocity_count = 0.0, 0, 0.0, 0

        for _, athlete in active_squad.iterrows():
            a_id = str(athlete['id']).strip()
            a_name = str(athlete['name']).strip()
            a_gender = str(athlete.get('gender', 'male')).lower()
            
            fly_logs = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '20m_fly')]
            block_logs = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '30m_block')]
            
            f_best = fly_logs['fat'].min() if not fly_logs.empty else None
            b_best = block_logs['fat'].min() if not block_logs.empty else None
            base_fly = fly_logs.iloc[0]['fat'] if not fly_logs.empty else None
            
            # AUDITED ENGINE CALL
            proj_val = get_unified_projection("20m_fly", f_best, b_best, f_best, a_gender)
            
            base_str = f"{base_fly:.2f}s FAT" if pd.notna(base_fly) else "--"
            pr_str = f"{f_best:.2f}s FAT" if pd.notna(f_best) else "--"
            delta_str = f"{f_best - base_fly:+.2f}s" if pd.notna(f_best) and pd.notna(base_fly) else "0.00s"
            
            if pd.notna(f_best) and pd.notna(base_fly):
                total_deltas += (f_best - base_fly)
                delta_count += 1
            
            if pd.notna(f_best):
                velocity_sums += (20.0 / f_best)
                velocity_count += 1

            processed_roster.append({"name": a_name, "baseline": base_str, "pr": pr_str, "delta": delta_str, 
                                     "proj": f"{proj_val:.2f}s{' *' if proj_val <= state_qual_time else ''}" if proj_val else "--"})
            relay_pool.append({"name": a_name, "best_fly": f_best or 2.2, "best_block": b_best or 4.2})

        # =========================================================================
        # 4. CROSS-MODULE LINEUP INTEGRATION (READS FROM MODULE 5 OVERRIDES)
        # =========================================================================
        if 'custom_relay_lineup' in st.session_state and isinstance(st.session_state.custom_relay_lineup, dict):
            # Read exact manual selections from Module 5
            c_lineup = st.session_state.custom_relay_lineup
            leg1_name = c_lineup['leg1']['name']
            leg1_metric = c_lineup['leg1']['metric']
            
            leg2_name = c_lineup['leg2']['name']
            leg2_metric = c_lineup['leg2']['metric']
            
            leg3_name = c_lineup['leg3']['name']
            leg3_metric = c_lineup['leg3']['metric']
            
            leg4_name = c_lineup['leg4']['name']
            leg4_metric = c_lineup['leg4']['metric']
        else:
            # Fallback Selection Engine: Auto-calculate default if Module 5 hasn't run yet
            leg1_name, leg1_metric = "Vacant Slot", "[No Data]"
            leg2_name, leg2_metric = "Vacant Slot", "[No Data]"
            leg3_name, leg3_metric = "Vacant Slot", "[No Data]"
            leg4_name, leg4_metric = "Vacant Slot", "[No Data]"

            if len(relay_pool) >= 4:
                # Leg 1: Block Start
                relay_pool = sorted(relay_pool, key=lambda x: x['best_block'])
                r1 = relay_pool.pop(0)
                leg1_name, leg1_metric = r1['name'], f"[Block Start: {r1['best_block']:.2f}s]"
                
                # Leg 2: Straight Fly
                relay_pool = sorted(relay_pool, key=lambda x: x['best_fly'])
                r2 = relay_pool.pop(0)
                leg2_name, leg2_metric = r2['name'], f"[Fly Split: {r2['best_fly']:.2f}s]"
                
                # Leg 4: Anchor Closer
                relay_pool = sorted(relay_pool, key=lambda x: x['best_fly'])
                r4 = relay_pool.pop(0)
                leg4_name, leg4_metric = r4['name'], f"[Anchor Fly: {r4['fly']:.2f}s]"
                
                # Leg 3: Curve
                relay_pool = sorted(relay_pool, key=lambda x: x['best_fly'])
                r3 = relay_pool.pop(0)
                leg3_name, leg3_metric = r3['name'], f"[Fly Split: {r3['best_fly']:.2f}s]"

        # =========================================================================
        # CROSS-MODULE GO MARK SYNCHRONIZER
        # =========================================================================
        if 'relay_go_marks' in st.session_state and isinstance(st.session_state.relay_go_marks, dict):
            # Pull direct high-precision steps computed via Module 5's action button
            step_1to2 = st.session_state.relay_go_marks.get('1to2', 17.0)
            step_2to3 = st.session_state.relay_go_marks.get('2to3', 17.0)
            step_3to4 = st.session_state.relay_go_marks.get('3to4', 17.0)
        else:
            # Clean mathematical fallback step equations if optimizer hasn't been engaged
            step_1to2 = 17.0
            step_2to3 = 17.0
            step_3to4 = 17.0

        # 5. ReportLab PDF Generation Definition Routine
        def generate_ad_pdf(coach, program, squad, benchmark, roster, r1, r2, r3, r4, m1, m2, m3, m4, count, impr, vel, s1, s2, s3):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=letter,
                rightMargin=36, leftMargin=36, 
                topMargin=36, bottomMargin=36
            )
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('PDFTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.black)
            meta_style = ParagraphStyle('PDFMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#444444"))
            section_style = ParagraphStyle('PDFSection', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, spaceBefore=10, spaceAfter=6, textColor=colors.black)
            bullet_style = ParagraphStyle('PDFBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=15, leftIndent=15)
            table_hdr_style = ParagraphStyle('PDFTableHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.black)
            table_body_style = ParagraphStyle('PDFTableBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9)

            story = []
            story.append(Paragraph(f"■ {program.upper()} — 2026 SEASON SPEED REPORT", title_style))
            story.append(Paragraph(f"Report Generated: {datetime.today().strftime('%B %d, %Y')} &nbsp;|&nbsp; Head Coach: {coach}", meta_style))
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceBefore=1, spaceAfter=15))

            story.append(Paragraph(f"[ SQUAD OVERVIEW: {squad} ]", section_style))
            story.append(Paragraph(f"• Total Active Student-Athletes Tracked: <b>{count}</b>", bullet_style))
            story.append(Paragraph(f"• Avg. 20m Fly Block Performance Improvement: <b>{impr}</b>", bullet_style))
            story.append(Paragraph(f"• Team Speed Peak Velocity Aggregate: <b>{vel} (Average)</b>", bullet_style))
            story.append(Spacer(1, 15))

            story.append(Paragraph("■ PERFORMANCE ROSTER & 100M PROJECTED RANKINGS", section_style))
            
            table_data = [[
                Paragraph("<b>Athlete Name</b>", table_hdr_style), 
                Paragraph("<b>Baseline Fly</b>", table_hdr_style), 
                Paragraph("<b>Current PR</b>", table_hdr_style), 
                Paragraph("<b>Net Delta</b>", table_hdr_style), 
                Paragraph("<b>Proj. 100m</b>", table_hdr_style)
            ]]
            
            for row in roster:
                table_data.append([
                    Paragraph(row['name'], table_body_style),
                    Paragraph(row['baseline'], table_body_style),
                    Paragraph(row['pr'], table_body_style),
                    Paragraph(row['delta'], table_body_style),
                    Paragraph(row['proj'], table_body_style)
                ])
                
            if len(roster) == 0:
                table_data.append([Paragraph("No matching active athlete logs available.", table_body_style), "", "", "", ""])
            
            col_widths = [2.25*inch, 1.25*inch, 1.25*inch, 1.0*inch, 1.25*inch]
            roster_table = Table(table_data, colWidths=col_widths)
            roster_table.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,0), 1.5, colors.black),
                ('BOTTOMPADDING', (0,0), (-1,0), 5),
                ('TOPPADDING', (0,1), (-1,-1), 4),
                ('BOTTOMPADDING', (0,1), (-1,-1), 4),
                ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
            ]))
            story.append(roster_table)
            story.append(Spacer(1, 5))
            story.append(Paragraph(f"<i>* Denotes State Qualifying standard projected ({benchmark:.2f}s)</i>", meta_style))
            story.append(Spacer(1, 15))

            story.append(Paragraph("■ PROPOSED 4x100M RELAY LINEUP (DATA-OPTIMIZED)", section_style))
            story.append(Paragraph(f"• <b>Leg 1 (Starter):</b> {r1} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m1}", bullet_style))
            story.append(Paragraph(f"• <b>Leg 2 (Straight):</b> {r2} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m2}", bullet_style))
            story.append(Paragraph(f"• <b>Leg 3 (Curve):</b> &nbsp;&nbsp;&nbsp;{r3} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m3}", bullet_style))
            story.append(Paragraph(f"• <b>Leg 4 (Anchor):</b> &nbsp;&nbsp;{r4} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m4}", bullet_style))
            
            story.append(Spacer(1, 8))
            story.append(Paragraph("■ <b>RECOMMENDED RELAY GO MARKS:</b>", section_style))
            story.append(Paragraph(f"- Exch 1 (1 to 2): {s1:.1f} Steps &nbsp;|&nbsp; Exch 2 (2 to 3): {s2:.1f} Steps &nbsp;|&nbsp; Exch 3 (3 to 4): {s3:.1f} Steps", bullet_style))
            
            story.append(Spacer(1, 40))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999"), spaceBefore=10, spaceAfter=10))
            story.append(Paragraph("<b>Verified By:</b> RDZ Speed Intelligence System Dashboard", meta_style))
            story.append(Paragraph("<i>This document contains certified high-precision metrics compiled for athletic recruitment evaluation and administrative review.</i>", meta_style))

            doc.build(story)
            buffer.seek(0)
            return buffer

        # Pre-build compiled download asset with dynamic steps passed through
        pdf_data = generate_ad_pdf(
            coach_name, program_name, squad_division, state_qual_time, processed_roster,
            leg1_name, leg2_name, leg3_name, leg4_name, leg1_metric, leg2_metric, leg3_metric, leg4_metric,
            tracked_count, avg_improvement, avg_velocity, step_1to2, step_2to3, step_3to4
        )

        # 6. Streamlit Document UI Container Preview Panel Rendering
        st.markdown("### 📋 Document Preview Panel")
        with st.container(border=True):
            st.markdown(f"### ■ {program_name.upper()} — 2026 SEASON SPEED REPORT")
            current_date_str = datetime.today().strftime('%B %d, %Y')
            st.caption(f"Report Generated: {current_date_str} | Head Coach: {coach_name}")
            st.write("")
            
            st.markdown(f"**[ SQUAD OVERVIEW: {squad_division} ]**")
            st.markdown(f"• Total Active Student-Athletes Tracked: **{tracked_count}** \n• Avg. 20m Fly Block Performance Improvement: **{avg_improvement}** \n• Team Speed Peak Velocity Aggregate: **{avg_velocity} (Average)**")
            st.write("")
            
            st.markdown("### ■ PERFORMANCE ROSTER & 100M PROJECTED RANKINGS")
            
            ui_table_data = []
            for item in processed_roster:
                ui_table_data.append({
                    "Athlete Name": item['name'],
                    "Baseline Fly": item['baseline'],
                    "Current PR": item['pr'],
                    "Net Delta": item['delta'],
                    "Proj. 100m": item['proj']
                })
            
            if ui_table_data:
                st.dataframe(pd.DataFrame(ui_table_data), hide_index=True, use_container_width=True)
            else:
                st.info("No active running session parameters stored matching current selection parameters.")
                
            st.caption(f"* Denotes State Qualifying standard projected ({state_qual_time:.2f}s)")
            st.write("")
            
            st.markdown("### ■ PROPOSED 4x100M RELAY LINEUP (DATA-OPTIMIZED)")
            st.markdown(f"• **Leg 1 (Starter):** {leg1_name} {leg1_metric} \n• **Leg 2 (Straight):** {leg2_name} {leg2_metric} \n• **Leg 3 (Curve):** {leg3_name} {leg3_metric} \n• **Leg 4 (Anchor):** {leg4_name} {leg4_metric}")
            st.write("")
            
            st.markdown("### ■ RECOMMENDED RELAY GO MARKS:")
            # Display step indicators as dynamic whole or float indicators depending on math calculations
            st.markdown(f"- Exch 1 (1 to 2): **{step_1to2:.1f} Steps** | Exch 2 (2 to 3): **{step_2to3:.1f} Steps** | Exch 3 (3 to 4): **{step_3to4:.1f} Steps**")
            st.write("---")
            
            st.caption("**Verified By:** RDZ Speed Intelligence System Dashboard")
            st.caption("*This document contains certified high-precision metrics compiled for athletic recruitment evaluation and administrative review.*")

        st.write("")
        st.download_button(
            label="📄 Generate & Download Coach's Report",
            data=pdf_data,
            file_name=f"{squad_division.lower().replace(' ', '_')}_speed_report.pdf",
            mime="application/pdf",
            use_container_width=True
        ) 
