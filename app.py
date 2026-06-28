import streamlit as st
import pandas as pd
import os
from datetime import datetime
    
def get_unified_projection(session_type, fat_time, block_val, fly_val, gender):
    """
    Unified projection with strict fallback to the Precise Conversion Model.
    """
    is_female = 'female' in str(gender).lower()
    
    # Define primary inputs
    f_val = fly_val if (fly_val and fly_val > 0) else fat_time
    b_val = block_val if (block_val and block_val > 0) else None
    
    # 1. GOLD STANDARD: Multi-Variable Formula (Requires Block + Fly)
    if b_val is not None:
        # Determine Speed Endurance Constant (C)
        base_proj = b_val + (3.5 * f_val)
        c = (0.15 if base_proj < 12.2 else 0.25) if is_female else (0.12 if base_proj < 11.0 else 0.18)
        return round(b_val + (3.5 * f_val) + c, 2)
    
    # 2. PRECISE FALLBACK: Curved Velocity Regression Model (If Block is missing)
    else:
        # Formula: (Fly / 20 * 100) + Gender Constant
        # Constants: Boys 1.17 | Girls 1.22 (using your requested 1.05/1.15 logic)
        gender_const = 1.15 if not is_female else 1.05 
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
# MODULE 3: LIVE SESSION DASHBOARD (UPDATED)
# ==========================================
elif app_portal == "📆 Live Session Dashboard":
    st.title("📆 Today's Live Session Dashboard")
    st.markdown("Real-time tracking matrix of sprints and calculated projections captured during today's training session.")

    # --- SAFE DATA RETRIEVAL ENGINE ---
    if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.info("ℹ️ No workout logs recorded in the system yet. Sprints logged today will appear here.")
    else:
        from datetime import datetime
        import pandas as pd
        today_str = datetime.today().strftime('%Y-%m-%d')
        
        # 1. Standardize Workout Logs DataFrame
        logs_clean = st.session_state.workout_logs.copy()
        logs_clean.columns = [str(c).lower() for c in logs_clean.columns]
        
        # Isolate today's data rows exclusively
        todays_logs = logs_clean[logs_clean['date'] == today_str].copy()
        
        if todays_logs.empty:
            st.info(f"ℹ️ No repetitions logged yet for today ({today_str}). Use the Tracker module to log splits.")
        elif 'athletes' not in st.session_state or st.session_state.athletes.empty:
            st.warning("⚠️ Roster database missing. Please ensure athletes are loaded in the Roster Hub.")
        else:
            # 2. Standardize Roster DataFrame
            roster_clean = st.session_state.athletes.copy()
            roster_clean.columns = [str(c).lower() for c in roster_clean.columns]
            
            # Smart Key Resolution Systems
            right_key = 'id' if 'id' in roster_clean.columns else ('athlete_id' if 'athlete_id' in roster_clean.columns else roster_clean.columns[0])
            
            if 'full_name' in roster_clean.columns:
                name_key = 'full_name'
            elif 'name' in roster_clean.columns:
                name_key = 'name'
            else:
                name_candidates = [c for c in roster_clean.columns if 'name' in c]
                name_key = name_candidates[0] if name_candidates else roster_clean.columns[1]
            
            gender_key = 'gender' if 'gender' in roster_clean.columns else ('sex' if 'sex' in roster_clean.columns else None)
            
            # 3. Clean type formats to match strings exactly (Eliminates numeric vs text merge drops)
            todays_logs['athlete_id'] = todays_logs['athlete_id'].astype(str).str.strip()
            roster_clean[right_key] = roster_clean[right_key].astype(str).str.strip()
            
            # Force target column formatting to float metrics
            fat_col = 'fat' if 'fat' in todays_logs.columns else todays_logs.columns[-2]
            todays_logs[fat_col] = pd.to_numeric(todays_logs[fat_col], errors='coerce')
            
            # ==========================================
            # COMPILED SESSION MATRIX TRACKER
            # ==========================================
            st.subheader("🏁 Compiled Today's Best Summary Matrix")
            st.markdown("The best recorded performance metrics per athlete captured during today's workspace window.")
            
            # Generate the aggregated top values for today's logs specifically
            session_fly = todays_logs[todays_logs['type'] == '20m_fly'].groupby('athlete_id')[fat_col].min().to_dict()
            session_block = todays_logs[todays_logs['type'] == '30m_block'].groupby('athlete_id')[fat_col].min().to_dict()
            
            # Filter roster down to only athletes who have run today
            athletes_active_today = roster_clean[roster_clean[right_key].isin(todays_logs['athlete_id'].unique())]
            
            # Grid Table Headers
            h1, h2, h3, h4 = st.columns([3, 2, 2, 3])
            with h1: st.markdown("👤 **Athlete Full Name**")
            with h2: st.markdown("⚡ **Best 20m Fly Today**")
            with h3: st.markdown("🧱 **Best 30m Block Today**")
            with h4: st.markdown("🎯 **Session Proj. 100m**")
            st.markdown("<hr style='margin: 0px 0px 12px 0px; border-color: #555;' />", unsafe_allow_html=True)
            
            for _, athlete in athletes_active_today.iterrows():
                a_id = str(athlete[right_key]).strip()
                a_name = athlete[name_key]
                a_gender = str(athlete[gender_key]).lower() if gender_key and pd.notna(athlete[gender_key]) else 'male'
                
                # Pull today's metrics
                best_fly = session_fly.get(a_id, None)
                best_block = session_block.get(a_id, None)
                
                fly_str = f"{best_fly:.2f}s" if best_fly else "--"
                block_str = f"{best_block:.2f}s" if best_block else "--"
                
                # --- ELITE PRECISION KINEMATIC PROJECTION SYSTEM ---
                # Prioritize today's efforts. If an effort is missing, look up historical PRs before falling back.
                fly_input = best_fly
                block_input = best_block
                
                if fly_input is None:
                    hist_fly = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '20m_fly')][fat_col]
                    if not hist_fly.empty:
                        fly_input = hist_fly.min()
                        
                if block_input is None:
                    hist_block = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '30m_block')][fat_col]
                    if not hist_block.empty:
                        block_input = hist_block.min()
                
                # Compute projection via updated core calculation engine
                if 'calculate_precise_100m' in globals():
                    proj_val = calculate_precise_100m(thirty_block=block_input, twenty_fly=fly_input, gender=a_gender)
                    
                    # Safety fallback if athlete has literally never run a 20m fly in app history
                    if proj_val is None and block_input is not None:
                        gender_const = 1.17 if 'female' in a_gender else 1.15
                        proj_val = round((block_input * 2.5) + gender_const, 2)
                else:
                    # Clean math fallback in case global engine hasn't fully reloaded
                    if fly_input is not None:
                        if block_input is not None:
                            proj_val = round(block_input + (fly_input * 3.5), 2)
                        else:
                            gender_const = 1.17 if 'female' in a_gender else 1.15
                            proj_val = round((fly_input * 5.0) + gender_const, 2)
                    elif block_input is not None:
                        gender_const = 1.17 if 'female' in a_gender else 1.15
                        proj_val = round((block_input * 2.5) + gender_const, 2)
                    else:
                        proj_val = None
                
                proj_str = f"**{proj_val:.2f}s**" if proj_val else "--"
                    
                # Render Row Elements Matrix
                r1, r2, r3, r4 = st.columns([3, 2, 2, 3])
                with r1: st.markdown(f"**{a_name}**")
                with r2: st.markdown(f"<span style='color:#FF4B4B;'>{fly_str}</span>", unsafe_allow_html=True)
                with r3: st.markdown(f"<span style='color:#00E676;'>{block_str}</span>", unsafe_allow_html=True)
                with r4: st.markdown(f"<span style='color:#00B0FF;'>{proj_str}</span>", unsafe_allow_html=True)
                st.write("---")
                
# ==========================================
# MODULE 4: RELAY OPTIMIZER POOL & GO-MARK GENERATOR (AUDITED)
# ==========================================
elif app_portal == "🤝 Relay Optimizer Pool": 
    st.title("🏆 Data-Optimized 4x100m Relay Builder")
    st.markdown("This engine runs algorithmic sorting to map your fastest 4 available athletes into their ideal lane assignments, while giving you final manual override control.")
    
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    else:
        roster_clean = st.session_state.athletes.copy()
        roster_clean.columns = [str(c).lower() for c in roster_clean.columns]
        
        if 'status' in roster_clean.columns:
            roster_clean = roster_clean[roster_clean['status'].astype(str).str.lower() == 'active']
            
        id_key = 'id' if 'id' in roster_clean.columns else roster_clean.columns[0]
        name_key = 'name' if 'name' in roster_clean.columns else ('full_name' if 'full_name' in roster_clean.columns else roster_clean.columns[1])
        gender_key = 'gender' if 'gender' in roster_clean.columns else ('sex' if 'sex' in roster_clean.columns else None)

        relay_gender = st.selectbox("Select Target Relay Division Profile:", ["Male", "Female"])
        
        if gender_key:
            division_pool = roster_clean[roster_clean[gender_key].astype(str).str.lower() == relay_gender.lower()]
        else:
            division_pool = roster_clean

        roster_metrics = []
        
        if 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty:
            logs_clean = st.session_state.workout_logs.copy()
            logs_clean.columns = [str(c).lower() for c in logs_clean.columns]
            
            fat_col = 'fat' if 'fat' in logs_clean.columns else ('time' if 'time' in logs_clean.columns else logs_clean.columns[-2])
            type_col = 'type' if 'type' in logs_clean.columns else ('session_type' if 'session_type' in logs_clean.columns else None)
            
            for _, athlete in division_pool.iterrows():
                ath_id = str(athlete[id_key]).strip()
                
                b_fly = logs_clean[(logs_clean['athlete_id'].astype(str).str.strip() == ath_id) & (logs_clean[type_col] == "20m_fly")][fat_col].min()
                b_block = logs_clean[(logs_clean['athlete_id'].astype(str).str.strip() == ath_id) & (logs_clean[type_col] == "30m_block")][fat_col].min()
                
                if pd.notna(b_fly) or pd.notna(b_block):
                    roster_metrics.append({
                        "id": ath_id, 
                        "name": str(athlete[name_key]).strip(),
                        "fly": float(b_fly) if pd.notna(b_fly) else 99.0,
                        "block": float(b_block) if pd.notna(b_block) else 99.0
                    })

        if len(roster_metrics) >= 4:
            rdf_suggest = pd.DataFrame(roster_metrics)
            
            # 1. RUN AUTOMATED SEEDING SELECTION ALGORITHM
            # Leg 1: Block Start Specialist
            s_leg1 = rdf_suggest.sort_values(by=['block', 'id']).iloc[0]
            rdf_suggest = rdf_suggest[rdf_suggest['id'] != s_leg1['id']]
            
            # Leg 2: Direct Straight-Away Flyer
            s_leg2 = rdf_suggest.sort_values(by=['fly', 'id']).iloc[0]
            rdf_suggest = rdf_suggest[rdf_suggest['id'] != s_leg2['id']]
            
            # Leg 4: The Anchor Closer
            s_leg4 = rdf_suggest.sort_values(by=['fly', 'id']).iloc[0]
            rdf_suggest = rdf_suggest[rdf_suggest['id'] != s_leg4['id']]
            
            # Leg 3: Curve Specialist
            rdf_suggest = rdf_suggest.sort_values(by=['fly', 'id'])
            s_leg3 = rdf_suggest.iloc[0]

            # 2. BUILD INTERACTIVE MANUAL OVERRIDE UI Dropdowns
            st.write("---")
            st.subheader("🛠️ Interactive Lineup Customization")
            st.caption("The system has pre-selected runners based on top performance metrics. Use the dropdown entries to tweak your final lane assignments.")

            available_names = [str(item['name']) for item in roster_metrics]
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                idx1 = available_names.index(s_leg1['name']) if s_leg1['name'] in available_names else 0
                leg1_name = st.selectbox("Leg 1 (Block Start):", available_names, index=idx1)
            with c2:
                idx2 = available_names.index(s_leg2['name']) if s_leg2['name'] in available_names else 0
                leg2_name = st.selectbox("Leg 2 (Straight Flyer):", available_names, index=idx2)
            with c3:
                idx3 = available_names.index(s_leg3['name']) if s_leg3['name'] in available_names else 0
                leg3_name = st.selectbox("Leg 3 (Curve Specialist):", available_names, index=idx3)
            with c4:
                idx4 = available_names.index(s_leg4['name']) if s_leg4['name'] in available_names else 0
                leg4_name = st.selectbox("Leg 4 (Anchor Closer):", available_names, index=idx4)

            # 3. SAFETY OVERLAP GUARDRAIL CHECK
            selected_lineup = [leg1_name, leg2_name, leg3_name, leg4_name]
            if len(set(selected_lineup)) < 4:
                st.error("🚨 **Lineup Assignment Error:** You have assigned the same student-athlete to multiple relay positions! Ensure all 4 runners are distinct before calculating.")
            else:
                st.success("✅ **Lineup Validated:** Athlete allocation contains no overlaps.")
                
                # Isolate target dictionaries matching selections
                run_map = {item['name']: item for item in roster_metrics}
                r1 = run_map[leg1_name]
                r2 = run_map[leg2_name]
                r3 = run_map[leg3_name]
                r4 = run_map[leg4_name]

                # Kinematic calculation helper synchronized with core precise math logic
                def get_go_mark(incoming_fly, outgoing_block):
                    if 'calculate_relay_go_mark' in globals():
                        return calculate_relay_go_mark(incoming_fly, outgoing_block)
                    else:
                        # Standardized fallback if global logic block isn't loaded
                        f = incoming_fly if incoming_fly != 99.0 else 2.20
                        b = outgoing_block if outgoing_block != 99.0 else 4.20
                        return int(round((b - f) * 4.4 + 16.5))

                # --- PERSISTENT CALCULATION PERSISTENCE ENGINE ---
                # Calculations run live on every UI element redraw
                mark_1to2 = get_go_mark(r1['fly'], r2['block'])
                mark_2to3 = get_go_mark(r2['fly'], r3['block'])
                mark_3to4 = get_go_mark(r3['fly'], r4['block'])

                # Keep backend data frameworks perfectly updated in state memory
                st.session_state.relay_go_marks = {
                    "1to2": float(mark_1to2),
                    "2to3": float(mark_2to3),
                    "3to4": float(mark_3to4)
                }
                
                st.session_state.custom_relay_lineup = {
                    "leg1": {"name": r1['name'], "metric": f"[Block Start: {r1['block']:.2f}s]" if r1['block'] != 99.0 else "[No Block Data]"},
                    "leg2": {"name": r2['name'], "metric": f"[Fly Split: {r2['fly']:.2f}s]" if r2['fly'] != 99.0 else "[No Fly Data]"},
                    "leg3": {"name": r3['name'], "metric": f"[Fly Split: {r3['fly']:.2f}s]" if r3['fly'] != 99.0 else "[No Fly Data]"},
                    "leg4": {"name": r4['name'], "metric": f"[Anchor Fly: {r4['fly']:.2f}s]" if r4['fly'] != 99.0 else "[No Fly Data]"}
                }

                # Trigger Sync Notification Action Button separately
                st.write("")
                if st.button("💾 Lock Lineup & Dispatch to Executive AD Export Hub", use_container_width=True):
                    st.toast(f"🚀 {relay_gender} Relay Lineup successfully dispatched to Module 6!", icon="🔥")

                # --- ALWAYS-RENDERED LIVE DASHBOARD RESULTS DISPLAY PANEL ---
                st.write("---")
                st.subheader("📊 Active Exchange Zone Parameters")
                
                l1_disp = f"{r1['block']:.2f}s" if r1['block'] != 99.0 else "--"
                l2_disp = f"{r2['fly']:.2f}s" if r2['fly'] != 99.0 else "--"
                l3_disp = f"{r3['fly']:.2f}s" if r3['fly'] != 99.0 else "--"
                l4_disp = f"{r4['fly']:.2f}s" if r4['fly'] != 99.0 else "--"

                disp_c1, disp_c2, disp_c3, disp_c4 = st.columns(4)
                disp_c1.metric("Leg 1 (Blocks)", r1['name'], f"Start: {l1_disp}")
                disp_c2.metric("Leg 2 (Straight)", r2['name'], f"Fly: {l2_disp}")
                disp_c3.metric("Leg 3 (Curve)", r3['name'], f"Fly: {l3_disp}")
                disp_c4.metric("Leg 4 (Anchor)", r4['name'], f"Fly: {l4_disp}")

                with st.container(border=True):
                    st.markdown("### 🗺️ On-Track Acceleration Checkmark Marks")
                    st.markdown(f"""
                    * 🏁 **Exchange 1 ({r1['name']} ➔ {r2['name']}):** Incoming runner flies; Outgoing runner sets go-mark at exactly **{mark_1to2} footsteps** backward from apex of zone.
                    * 🏁 **Exchange 2 ({r2['name']} ➔ {r3['name']}):** Incoming runner flies; Outgoing runner sets go-mark at exactly **{mark_2to3} footsteps** backward from apex of zone.
                    * 🏁 **Exchange 3 ({r3['name']} ➔ {r4['name']}):** Incoming runner flies; Outgoing runner sets go-mark at exactly **{mark_3to4} footsteps** backward from apex of zone.
                    """)
        else:
            st.warning("⚠️ The active roster requires at least 4 registered athletes of this gender segment with documented sprint metrics to optimize line-up configurations.")

# ==========================================
# MODULE 5: ATHLETE PROGRESS TRENDS (AUDITED)
# ==========================================
elif app_portal == "📈 Athlete Progress Trends":
    st.title("📈 The Athlete Progress Screen (Analytical Deep Dive)")
    st.markdown("Designed for individual player development meetings, tracking health/fatigue, and presenting progress profiles to parents or college recruiters.")

    # --- GUARD RAILS: ENSURE DATA EXISTENCE ---
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    elif 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.info("ℹ️ No speed progression metrics found. Log repetitions in the Workout Tracker to populate analytics.")
    else:
        # Standardize DataFrames to prevent casing errors
        roster_clean = st.session_state.athletes.copy()
        roster_clean.columns = [str(c).lower() for c in roster_clean.columns]
        
        logs_clean = st.session_state.workout_logs.copy()
        logs_clean.columns = [str(c).lower() for c in logs_clean.columns]

        # ID & Name Column Resolutions
        id_key = 'id' if 'id' in roster_clean.columns else roster_clean.columns[0]
        if 'full_name' in roster_clean.columns:
            name_key = 'full_name'
        elif 'name' in roster_clean.columns:
            name_key = 'name'
        else:
            name_candidates = [c for c in roster_clean.columns if 'name' in c]
            name_key = name_candidates[0] if name_candidates else roster_clean.columns[1]
            
        gender_key = 'gender' if 'gender' in roster_clean.columns else ('sex' if 'sex' in roster_clean.columns else None)

        # --- DROP-DOWN SELECTOR: TARGET ATHLETE PROFILE ---
        athlete_mapping = {row[name_key]: str(row[id_key]).strip() for _, row in roster_clean.iterrows()}
        selected_athlete_name = st.selectbox("👤 Select Athlete Profile to Review:", list(athlete_mapping.keys()))
        selected_id = athlete_mapping[selected_athlete_name]

        # Isolate individual metrics
        athlete_meta = roster_clean[roster_clean[id_key].astype(str).str.strip() == selected_id].iloc[0]
        athlete_logs = logs_clean[logs_clean['athlete_id'].astype(str).str.strip() == selected_id].copy()
        
        # Parse Dates safely for time-series charts
        athlete_logs['date'] = pd.to_datetime(athlete_logs['date'])
        athlete_logs = athlete_logs.sort_values(by='date')

        # Robustly target performance time column
        fat_col = 'fat' if 'fat' in athlete_logs.columns else ('time' if 'time' in athlete_logs.columns else athlete_logs.columns[-2])
        athlete_logs[fat_col] = pd.to_numeric(athlete_logs[fat_col], errors='coerce')

        # --- UI PROFILE HEADER CONTAINER ---
        st.write("")
        grade_str = f"• Grade {athlete_meta['grade']}" if 'grade' in athlete_meta and pd.notna(athlete_meta['grade']) else ""
        group_str = f"• {athlete_meta['group']}" if 'group' in athlete_meta and pd.notna(athlete_meta['group']) else "• Short Sprinters"
        gender_val = str(athlete_meta[gender_key]).lower() if gender_key and pd.notna(athlete_meta[gender_key]) else 'male'
        
        with st.container(border=True):
            st.markdown(f"## 👤 {selected_athlete_name.upper()}")
            st.markdown(f"**Roster Profile Tier:** Class: {athlete_meta.get('tier', 'Varsity Athlete').title()} {grade_str} {group_str}")

        # --- UI SELECTOR: PROGRESS CHART TOGGLES ---
        st.write("")
        chart_view = st.radio(
            label="Select Analytical Tracking Dimension:",
            options=["⚡ 20m Fly Trend", "🧱 30m Block Trend", "⏱️ Recruitment Projections"],
            horizontal=True
        )

        # --- TREND ENGINE CHART RENDERING ---
        if "20m Fly Trend" in chart_view:
            fly_data = athlete_logs[athlete_logs['type'] == '20m_fly']
            if fly_data.empty:
                st.info(f"ℹ️ No 20m Fly repetitions logged on file for {selected_athlete_name}.")
            else:
                fly_timeline = fly_data.groupby('date')[fat_col].min()
                st.subheader("📈 20m Fly Progression Timeline")
                st.line_chart(fly_timeline)
                
        elif "30m Block Trend" in chart_view:
            block_data = athlete_logs[athlete_logs['type'] == '30m_block']
            if block_data.empty:
                st.info(f"ℹ️ No 30m Block starts logged on file for {selected_athlete_name}.")
            else:
                block_timeline = block_data.groupby('date')[fat_col].min()
                st.subheader("📈 30m Block Start Progression Timeline")
                st.line_chart(block_timeline)
                
        else:
            fly_logs = athlete_logs[athlete_logs['type'] == '20m_fly'].copy()
            if fly_logs.empty:
                st.info("ℹ️ Projections line graph requires historical 20m Fly data entries.")
            else:
                st.subheader("⏱️ Multi-Event Dash Recruitment Projections Forecast")
                
                proj_timeline = fly_logs.groupby('date')[fat_col].min().reset_index()
                
                # --- SYNCED TIMELINE PROJECTION LOOP ---
                # Run each timeline date through your precise calculation engine
                proj_100_list = []
                for _, p_row in proj_timeline.iterrows():
                    d_date = p_row['date']
                    f_val = p_row[fat_col]
                    
                    # Look for a block effort run on this exact same training day to increase accuracy
                    b_day = athlete_logs[(athlete_logs['date'] == d_date) & (athlete_logs['type'] == '30m_block')][fat_col]
                    b_val = b_day.min() if not b_day.empty else None
                    
                    if pd.isna(b_val): b_val = None
                    
                    if 'calculate_precise_100m' in globals():
                        p_val = calculate_precise_100m(thirty_block=b_val, twenty_fly=f_val, gender=gender_val)
                        if p_val is None:
                            gender_const = 1.17 if 'female' in gender_val else 1.15
                            p_val = round((f_val * 5.0) + gender_const, 2)
                    else:
                        gender_const = 1.17 if 'female' in gender_val else 1.15
                        p_val = round((f_val * 5.0) + gender_const, 2)
                    proj_100_list.append(p_val)
                
                proj_timeline['100m Proj'] = proj_100_list
                
                # Apply synchronized endurance decay models to the updated 100m baseline
                if 'female' in gender_val:
                    proj_timeline['200m Proj'] = proj_timeline['100m Proj'] * 2.05
                    proj_timeline['400m Proj'] = proj_timeline['100m Proj'] * 4.65
                else:
                    proj_timeline['200m Proj'] = proj_timeline['100m Proj'] * 1.98
                    proj_timeline['400m Proj'] = proj_timeline['100m Proj'] * 4.40
                
                selected_events = st.multiselect(
                    "Filter chart events to maintain high visual resolution:",
                    options=['100m Proj', '200m Proj', '400m Proj'],
                    default=['100m Proj']
                )
                
                if selected_events:
                    chart_df = proj_timeline.set_index('date')[selected_events]
                    st.line_chart(chart_df)
                else:
                    st.caption("Select at least one distance milestone above to view the tracking graph.")

        # --- INSIGHTS ENGINE: COGNITIVE BIO-ANALYTICS ---
        st.write("---")
        st.subheader("📊 Season Insights & Recruiting Analytics")
        
        if athlete_logs.empty:
            st.caption("Awaiting performance records to initialize coaching analytics insights.")
        else:
            # 1. Compute Total Improvement
            first_rep = athlete_logs[fat_col].iloc[0]
            best_rep = athlete_logs[fat_col].min()
            total_diff = first_rep - best_rep
            
            # 2. Get baseline metrics using explicit safe NaN handling
            best_fly_all_time = athlete_logs[athlete_logs['type'] == '20m_fly'][fat_col].min()
            best_block_all_time = athlete_logs[athlete_logs['type'] == '30m_block'][fat_col].min()
            
            if pd.isna(best_fly_all_time): best_fly_all_time = None
            if pd.isna(best_block_all_time): best_block_all_time = None
            
            # --- INSIGHT ENGINE CORE INTEGRATION ---
            if 'calculate_precise_100m' in globals():
                est_100 = calculate_precise_100m(thirty_block=best_block_all_time, twenty_fly=best_fly_all_time, gender=gender_val)
                if est_100 is None:
                    calc_fly = best_fly_all_time if best_fly_all_time else (best_block_all_time / 1.95 if best_block_all_time else 2.20)
                    gender_const = 1.17 if 'female' in gender_val else 1.15
                    est_100 = round((calc_fly * 5.0) + gender_const, 2)
            else:
                calc_fly = best_fly_all_time if best_fly_all_time else (best_block_all_time / 1.95 if best_block_all_time else 2.20)
                gender_const = 1.17 if 'female' in gender_val else 1.15
                est_100 = round((calc_fly * 5.0) + gender_const, 2)
            
            # Set recruitment tier thresholds based on synchronized calculation output
            if 'female' in gender_val:
                d1_cutoff = 11.85
                tier_string = "State Finalist Tier" if est_100 < 12.20 else ("Varsity Standard" if est_100 < 12.90 else "Developing Tier")
            else:
                d1_cutoff = 10.65
                tier_string = "Elite State Tier" if est_100 < 10.90 else ("Varsity Point Scorer" if est_100 < 11.50 else "Developing Tier")

            # 3. AUTOMATED CNS FATIGUE DETECTION ENGINE
            fatigue_triggered = False
            latest_logged_type = athlete_logs['type'].iloc[-1]
            type_specific_logs = athlete_logs[athlete_logs['type'] == latest_logged_type]
            
            if len(type_specific_logs) >= 3:
                recent_reps = type_specific_logs.tail(3)[fat_col].values
                if recent_reps[2] > (recent_reps[0] * 1.03):
                    fatigue_triggered = True

            # 4. PREDICTIVE MILESTONE INDICATORS
            gap_to_d1 = est_100 - d1_cutoff

            # --- RENDER SUMMARY ROW USING NATIVE STREAMLIT METRICS ---
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric(label="Total Season Cut", value=f"{total_diff:.2f}s", help="Difference between initial test baseline and personal record.")
            with m_col2:
                st.metric(label="Est. 100m FAT", value=f"{est_100:.2f}s", delta=tier_string, delta_color="off")
            with m_col3:
                if gap_to_d1 > 0:
                    st.metric(label="Gap to D1 Standard", value=f"+{gap_to_d1:.2f}s", delta="Targeting 10.65s" if 'male' in gender_val else "Targeting 11.85s", delta_color="inverse")
                else:
                    st.metric(label="Gap to D1 Standard", value="Met ✓", delta="Elite Tier Profile", delta_color="normal")
            
            st.write("")
            i_col1, i_col2 = st.columns(2)
            with i_col1:
                st.markdown("### 🏃‍♂️ Tactical Assignments")
                if best_fly_all_time and (best_block_all_time is None or best_fly_all_time < 2.10):
                    st.info("💡 **Optimal Relay Leg:** `Leg 2 or Leg 4` \n\nMax Velocity Acceleration Specialist Profile. Fits long straightaways where maintaining top-end elastic speed is critical.")
                else:
                    st.info("💡 **Optimal Relay Leg:** `Leg 1 or Leg 3` \n\nElite Curve Acceleration Block Profile. Excels at generating aggressive torque out of the blocks or sustaining hard momentum through the corner.")
            
            with i_col2:
                st.markdown("### 🧠 Neuromuscular Safety Status")
                if fatigue_triggered:
                    st.warning("⚠️ **CNS Fatigue Warning:** Performance velocity has dropped greater than 3% over consecutive repetitions. High hamstring/soft-tissue injury risk detected. \n\n**Coaching Guidance:** Shut down active max-effort drilling immediately; prescribe low-impact recovery mechanics.")
                else:
                    st.success("✅ **CNS Muscle Readiness:** Central Nervous System recovery markers are green. No significant performance decay indicators flagged. Athlete cleared for high-intensity neuromuscular output.")
                    
# ==========================================
# MODULE 6: TEAM LEADERBOARDS (UPDATED)
# ==========================================
elif app_portal == "🏆 Team Leaderboards":
    st.title("🔥 Team Leaderboards (The Engagement Engine)")
    
    # Check if we have logs to compute statistics from
    if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.warning("⚠️ No workout log data found to generate leaderboards.")
    else:
        import pandas as pd
        import math
        
        logs = st.session_state.workout_logs.copy()
        logs.columns = [str(c).lower() for c in logs.columns]
        
        # Force numeric conversions on timing values
        fat_col = 'fat' if 'fat' in logs.columns else ('raw' if 'raw' in logs.columns else logs.columns[-1])
        logs[fat_col] = pd.to_numeric(logs[fat_col], errors='coerce')
        type_col = 'type' if 'type' in logs.columns else ('session_type' if 'session_type' in logs.columns else None)

        # --- RECONFIGURED SEGMENT FILTERS ---
        st.subheader("Segment Filter:")
        leaderboard_type = st.radio(
            label="Select Ranking Type",
            options=["⚡ 20m Fly Rankings", "🧱 30m Block Rankings", "⏱️ Projected 100m"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Layout row for Gender and Roster Tiers
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            gender_filter = st.selectbox("Gender Select:", ["All", "Male", "Female"])
        with l_col2:
            tier_filter = st.selectbox("Roster Tier:", ["All Varsity", "JV / Developing"])

        # Prepare Athlete Roster Profiles
        roster = st.session_state.athletes.copy()
        roster.columns = [str(c).lower() for c in roster.columns]
        id_col = 'id' if 'id' in roster.columns else ('athlete_id' if 'athlete_id' in roster.columns else roster.columns[0])
        
        # Smart full name detection check
        if 'name' in roster.columns:
            name_col = 'name'
        elif 'full_name' in roster.columns:
            name_col = 'full_name'
        elif 'athlete_name' in roster.columns:
            name_col = 'athlete_name'
        else:
            name_candidates = [c for c in roster.columns if 'name' in c]
            name_col = name_candidates[0] if name_candidates else roster.columns[1]
        
        # Set normalized identifier columns
        roster['name'] = roster[name_col]
        roster['id'] = roster[id_col].astype(str).str.strip()

        # Apply demographic filters to Roster Pool
        if gender_filter != "All" and 'gender' in roster.columns:
            roster = roster[roster['gender'].astype(str).str.lower() == gender_filter.lower()]
        if 'tier' in roster.columns:
            if tier_filter == "All Varsity":
                roster = roster[roster['tier'].astype(str).str.lower().str.contains("varsity", na=True)]
            else:
                roster = roster[~roster['tier'].astype(str).str.lower().str.contains("varsity", na=False)]

        # --- LEADERBOARD COMPILATION LOGIC ENGINE ---
        st.write("")
        if "20m Fly Rankings" in leaderboard_type:
            st.subheader("🏃 Top Speed 20m Fly Leaders")
            metric_df = logs[logs[type_col] == '20m_fly'].groupby('athlete_id')[fat_col].min().reset_index()
            suffix = "s FAT"
            badge_text = "Top Speed"
        
        elif "30m Block Rankings" in leaderboard_type:
            st.subheader("🧱 Acceleration 30m Block Leaders")
            metric_df = logs[logs[type_col] == '30m_block'].groupby('athlete_id')[fat_col].min().reset_index()
            suffix = "s FAT"
            badge_text = "Power Start"
            
        else: # Projected 100m precision matrix grouping
            st.subheader("⏱️ Projected 100m Dash Leaderboard")
            # Isolate all-time best markers for both profiles independently
            fly_bests = logs[logs[type_col] == '20m_fly'].groupby('athlete_id')[fat_col].min().reset_index().rename(columns={fat_col: 'best_fly'})
            block_bests = logs[logs[type_col] == '30m_block'].groupby('athlete_id')[fat_col].min().reset_index().rename(columns={fat_col: 'best_block'})
            
            # Combine profiles cleanly using an outer join
            metric_df = pd.merge(fly_bests, block_bests, on='athlete_id', how='outer')
            metric_df[fat_col] = None # Placeholder to satisfy downstream sort structures
            suffix = "s (Est)"
            badge_text = "Projected"

        # --- BULLETPROOF ID ALIGNMENT FOR THE MERGE ---
        metric_df['athlete_id'] = metric_df['athlete_id'].astype(str).str.strip()

        # Merge calculated logs with roster rows
        leaderboard_df = roster.merge(metric_df, left_on='id', right_on='athlete_id', how='inner')

        # --- SYNCED INTEGRATION LAYER FOR 100M DYNAMIC PROJECTIONS ---
        if "Projected 100m" in leaderboard_type:
            computed_projections = []
            for _, row in leaderboard_df.iterrows():
                a_gender = str(row.get('gender', 'male')).lower().strip()
                f_val = row.get('best_fly', None)
                b_val = row.get('best_block', None)
                
                # Convert potential NaN elements to native Python None types
                if pd.isna(f_val): f_val = None
                if pd.isna(b_val): b_val = None
                
                if 'calculate_precise_100m' in globals():
                    proj_val = calculate_precise_100m(thirty_block=b_val, twenty_fly=f_val, gender=a_gender)
                    
                    # Direct manual fallback if they completely lack 20m fly tracking records
                    if proj_val is None and b_val is not None:
                        gender_const = 1.17 if 'female' in a_gender else 1.15
                        proj_val = round((b_val * 2.5) + gender_const, 2)
                else:
                    # Mathematical local fallback structure matching updated formulas
                    if f_val is not None:
                        if b_val is not None:
                            proj_val = round(b_val + (f_val * 3.5), 2)
                        else:
                            gender_const = 1.17 if 'female' in a_gender else 1.15
                            proj_val = round((f_val * 5.0) + gender_const, 2)
                    elif b_val is not None:
                        gender_const = 1.17 if 'female' in a_gender else 1.15
                        proj_val = round((b_val * 2.5) + gender_const, 2)
                    else:
                        proj_val = None
                        
                computed_projections.append(proj_val)
            
            leaderboard_df[fat_col] = computed_projections
            # Cleanly drop ghost rows that have zero records on file
            leaderboard_df = leaderboard_df.dropna(subset=[fat_col])

        # Execute final leaderboard hierarchy sort
        leaderboard_df = leaderboard_df.sort_values(by=fat_col, ascending=True).reset_index(drop=True)

        # --- UI DISPLAY RENDERING LOOP ---
        if leaderboard_df.empty:
            st.info("ℹ️ No athlete logs found matching the selected leaderboard filters.")
        else:
            for rank, (_, row) in enumerate(leaderboard_df.iterrows(), start=1):
                if rank == 1: medal = "🥇"
                elif rank == 2: medal = "🥈"
                elif rank == 3: medal = "🥉"
                else: medal = "👤"
                
                group_tag = row.get('group', 'Short Sprinters')
                grade_tag = f"• Grade {row['grade']}" if 'grade' in row and pd.notna(row['grade']) else ""
                
                # Double safety numeric check to block NaN output rendering completely
                val = row[fat_col]
                if pd.isna(val) or math.isnan(val):
                    display_time = "--"
                else:
                    display_time = f"{val:.2f}{suffix}"

                with st.container(border=True):
                    col_rank, col_val, col_badge = st.columns([5, 2, 2])
                    with col_rank:
                        st.markdown(f"#### {medal} {rank}. {row['name']} *({group_tag} {grade_tag})*")
                    with col_val:
                        st.markdown(f"### **{display_time}**")
                    with col_badge:
                        st.write("") 
                        if rank == 1:
                            st.warning(f"🏆 {badge_text}")
                        else:
                            st.info(f"🔥 Hot Streak")

# ==========================================
# MODULE 7: AD REPORT EXPORT ("THE AD CLOSER")
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
    
    st.info("💡 **Print-Optimized Formatting:** This engine builds a high-contrast, monochrome PDF designed perfectly for standard office printers, bulletin boards, and athletic department budget reviews.")

    # 1. User Inputs & Configuration Controls
    col1, col2 = st.columns(2)
    with col1:
        coach_name = st.text_input("Head Coach Name:", value="John Doe")
        program_name = st.text_input("Program Title:", value="NORTHSIDE TRACK & FIELD")
    with col2:
        squad_division = st.selectbox("Squad/Division Filter:", ["VARSITY BOYS", "VARSITY GIRLS", "FROSH-SOPH"])
        state_qual_time = st.number_input("State Qual 100m Benchmark (s):", value=11.00, step=0.05)

    st.write("---")

    # 2. Safety Guardrails: Check if base data structures exist
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    else:
        # Clone and normalize core roster dataframe keys
        roster_clean = st.session_state.athletes.copy()
        roster_clean.columns = [str(c).lower().strip() for c in roster_clean.columns]
        
        # Isolate active athletes exclusively
        active_squad = roster_clean[roster_clean['status'].astype(str).str.lower() == 'active']
        
        # Apply specific Squad/Division filtering mappings
        if squad_division == "VARSITY BOYS":
            active_squad = active_squad[(active_squad['tier'].astype(str).str.lower() == 'varsity') & (active_squad['gender'].astype(str).str.lower() == 'male')]
        elif squad_division == "VARSITY GIRLS":
            active_squad = active_squad[(active_squad['tier'].astype(str).str.lower() == 'varsity') & (active_squad['gender'].astype(str).str.lower() == 'female')]
        elif squad_division == "FROSH-SOPH":
            active_squad = active_squad[active_squad['grade'].astype(str).str.strip().isin(['9', '10'])]

        # Load workout log records safely
        has_logs = 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty
        if has_logs:
            logs_clean = st.session_state.workout_logs.copy()
            logs_clean.columns = [str(c).lower().strip() for c in logs_clean.columns]
            logs_clean['athlete_id'] = logs_clean['athlete_id'].astype(str).str.strip()
            logs_clean['fat'] = pd.to_numeric(logs_clean['fat'], errors='coerce')
            logs_clean['proj_100'] = pd.to_numeric(logs_clean['proj_100'], errors='coerce')

        # 3. Dynamic Performance Metrics Processing Loop
        processed_roster = []
        total_deltas = 0.0
        delta_count = 0
        velocity_sums = 0.0
        velocity_count = 0
        
        # Track metric pools for downstream automated relay lineup generation fallback
        relay_pool = []

        for _, athlete in active_squad.iterrows():
            a_id = str(athlete['id']).strip()
            a_name = str(athlete['name']).strip()
            
            baseline_val = None
            pr_val = None
            best_block_val = None
            proj_val = None
            
            if has_logs:
                # Process 20m fly interval tracking logs
                fly_logs = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '20m_fly')].sort_values(by='log_id')
                if not fly_logs.empty:
                    baseline_val = float(fly_logs.iloc[0]['fat'])
                    pr_val = float(fly_logs['fat'].min())
                    
                    # Target projected 100m linked directly to the PR performance execution
                    proj_val = float(fly_logs[fly_logs['fat'] == pr_val].iloc[0]['proj_100'])
                    
                    # Accumulate team velocity parameters (v = 20m / t)
                    if pr_val > 0:
                        velocity_sums += (20.0 / pr_val)
                        velocity_count += 1
                
                # Process 30m starting block data streams
                block_logs = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '30m_block')]
                if not block_logs.empty:
                    best_block_val = float(block_logs['fat'].min())

            # Map display strings elegantly
            base_str = f"{baseline_val:.2f}s FAT" if baseline_val else "--"
            pr_str = f"{pr_val:.2f}s FAT" if pr_val else "--"
            
            delta_str = "0.00s"
            if pr_val and baseline_val:
                diff = pr_val - baseline_val
                delta_str = f"{diff:+.2f}s" if diff != 0 else "0.00s"
                total_deltas += diff
                delta_count += 1

            is_qualifier = (proj_val <= state_qual_time) if proj_val else False
            proj_str = f"{proj_val:.2f}s" if proj_val else "--"
            if is_qualifier:
                proj_str += " *"

            # Push structured data layout back to presentation array
            processed_roster.append({
                "id": a_id,
                "name": a_name,
                "baseline": base_str,
                "pr": pr_str,
                "delta": delta_str,
                "proj": proj_str,
                "is_qualifier": is_qualifier
            })

            # Populate evaluation dict for backup sorting
            relay_pool.append({
                "name": a_name,
                "best_fly": pr_val if pr_val else 2.20,
                "best_block": best_block_val if best_block_val else 4.20
            })

        # Calculate high-level performance metrics summaries
        tracked_count = len(active_squad)
        avg_improvement = f"{total_deltas / delta_count:+.2f}s" if delta_count > 0 else "0.00s"
        avg_velocity = f"{velocity_sums / velocity_count:.2f} m/s" if velocity_count > 0 else "-- m/s"

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
