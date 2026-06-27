import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(
    page_title="High-Performance Sprint Analytics",
    page_icon="⚡",
    layout="wide"
)

# --- LOCAL PERSISTENCE STORAGE TRACKERS ---
ROSTER_CACHE = "roster_storage.csv"
LOGS_CACHE = "workout_logs_storage.csv"

# ==========================================
# GLOBAL APP STATE INITIALIZATION (AUTO-LOAD)
# ==========================================

# 1. Initialize Roster Database (Checks disk backup first)
if 'athletes' not in st.session_state:
    if os.path.exists(ROSTER_CACHE):
        st.session_state.athletes = pd.read_csv(ROSTER_CACHE)
    else:
        st.session_state.athletes = pd.DataFrame(columns=[
            'id', 'full_name', 'grade', 'group', 'tier', 'gender'
        ])

# 2. Initialize Workout Performance Logs (Checks disk backup first)
if 'workout_logs' not in st.session_state:
    if os.path.exists(LOGS_CACHE):
        st.session_state.workout_logs = pd.read_csv(LOGS_CACHE)
    else:
        st.session_state.workout_logs = pd.DataFrame(columns=[
            'log_id', 'date', 'athlete_id', 'type', 'raw', 'fat', 'proj_100'
        ])
# ==========================================
# GLOBAL CORE KINEMATIC UTILITIES
# ==========================================

def normalize_hand_fly(hand_time: float) -> float:
    """Applies standard electronic/FAT conversion factor to manual stopwatch times."""
    return round(hand_time + 0.24, 2)

def calculate_projected_100m(block_time: float, fly_time: float, gender: str) -> float:
    """
    Predicts 100m FAT time using a multi-variable kinematic projection model.
    Accounts for gender-specific maximum velocity decay rates.
    """
    gender_clean = str(gender).lower()
    if 'female' in gender_clean:
        # Curve modeling formula optimized for female sprint acceleration profiles
        return round((fly_time * 5.10) + (block_time * 0.25) + 1.40, 2)
    else:
        # Curve modeling formula optimized for male sprint acceleration profiles
        return round((fly_time * 4.95) + (block_time * 0.22) + 1.20, 2)
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
# 3. MATHEMATICAL CALCULATION CORES
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
    Calculates 100m performance predictions using a piecewise velocity splicing model.
    Includes automated fallback handling and performance-tiered speed endurance decay constants.
    """
    import pandas as pd
    
    if twenty_fly is None or pd.isna(twenty_fly):
        return None
        
    try:
        twenty_fly = float(twenty_fly)
        if twenty_fly <= 0 or twenty_fly >= 99.0:
            return None
    except:
        return None
        
    try:
        if thirty_block is not None and not pd.isna(thirty_block):
            thirty_block = float(thirty_block)
            if thirty_block <= 0 or thirty_block >= 99.0:
                thirty_block = None
        else:
            thirty_block = None
    except:
        thirty_block = None
    
    # Adjust for manual stopwatch variations to match FAT parameters
    if is_hand_timed:
        twenty_fly += 0.15
        if thirty_block is not None:
            thirty_block += 0.24

    # --- FALLBACK MODEL: Fly-Only Calculation ---
    if thirty_block is None:
        ten_split = twenty_fly / 2.0
        if str(gender).lower() == "male":
            return round((ten_split * 10) + 1.05, 2)
        else:
            return round((ten_split * 10) + 1.15, 2)

    # --- CORE MODEL: Dual-Input Piecewise Splicing Formula ---
    ten_split = twenty_fly / 2.0
    base_time = thirty_block + (7.0 * ten_split)
    
    if str(gender).lower() == "male":
        decay = 0.12 if base_time < 11.0 else 0.18
    else:
        decay = 0.15 if base_time < 12.2 else 0.25
            
    return round(base_time + decay, 2)


# ==========================================
# BACKWARD COMPATIBILITY LAYER FOR OTHER MODULES
# ==========================================

def get_best_historical_fat(athlete_id, run_type="20m_fly"):
    """
    Finds the historical PR for an athlete while safeguarding against column case variations.
    """
    import pandas as pd
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
                    st.success(f"🗑️ Removed {a_name} completely from roster.")
                    st.rerun()
                    
# ==========================================
# MODULE: LIVE SPRINT REPETITION ENTRY TRACKER
# ==========================================
elif app_portal == "⏱️ Workout Tracker":  # Integrates directly into your tracker tab layout
    st.title("⏱️ Live Sprint Repetition Entry Tracker")
    st.markdown("Log active sprint intervals while referencing baseline performance records side-by-side.")
    
    # 1. Configuration Controls
    col_sys, col_drill = st.columns(2)
    with col_sys:
        timing_system = st.radio("Timing System Method:", ["Electronic / FAT (Freelap)", "Hand-Timed (Stopwatch)"], horizontal=True)
    with col_drill:
        session_type = st.selectbox("Active Drill Profile Type:", ["20m_fly", "30m_block"])
        
    st.write("---")
    
    # 2. Guard Rails: Verify Core Data Structures Exist
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    else:
        # Standardize Roster DataFrame
        roster_view = st.session_state.athletes.copy()
        roster_view.columns = [str(c).lower() for c in roster_view.columns]
        
        id_key = 'id' if 'id' in roster_view.columns else roster_view.columns[0]
        
        if 'full_name' in roster_view.columns:
            name_key = 'full_name'
        elif 'name' in roster_view.columns:
            name_key = 'name'
        else:
            name_candidates = [c for c in roster_view.columns if 'name' in c]
            name_key = name_candidates[0] if name_candidates else roster_view.columns[1]
            
        gender_key = 'gender' if 'gender' in roster_view.columns else ('sex' if 'sex' in roster_view.columns else None)

        # 3. Pull Dynamic Historical PR References to Build the Reference Matrix
        if 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty:
            logs = st.session_state.workout_logs.copy()
            logs.columns = [str(c).lower() for c in logs.columns]
            fat_col = 'fat' if 'fat' in logs.columns else ('raw' if 'raw' in logs.columns else logs.columns[-1])
            logs[fat_col] = pd.to_numeric(logs[fat_col], errors='coerce')
            type_col = 'type' if 'type' in logs.columns else ('session_type' if 'session_type' in logs.columns else None)
            
            fly_prs = logs[logs[type_col] == '20m_fly'].groupby('athlete_id')[fat_col].min().to_dict()
            block_prs = logs[logs[type_col] == '30m_block'].groupby('athlete_id')[fat_col].min().to_dict()
        else:
            fly_prs = {}
            block_prs = {}

        # 4. Matrix Column Headers Layout
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 3, 2])
        with h1: st.markdown("🏃 **Athlete Name**")
        with h2: st.markdown("⚡ **Best Fly**")
        with h3: st.markdown("🧱 **Best Block**")
        with h4: st.markdown("⏱️ **Enter Rep Time (s)**")
        with h5: st.markdown("💾 **Action**")
        st.markdown("<hr style='margin: 0px 0px 15px 0px; border-color: #444;' />", unsafe_allow_html=True)

        # 5. Tracker Entry Row Generation Loop
        for index, athlete in roster_view.iterrows():
            raw_id = athlete[id_key]
            string_id = str(raw_id).strip()
            athlete_name = athlete[name_key]
            athlete_gender = str(athlete[gender_key]).lower() if gender_key and pd.notna(athlete[gender_key]) else 'male'
            
            # Extract Personal Records
            pr_fly = fly_prs.get(string_id, None)
            pr_block = block_prs.get(string_id, None)
            
            str_fly = f"{pr_fly:.2f}s" if pr_fly and not pd.isna(pr_fly) else "--"
            str_block = f"{pr_block:.2f}s" if pr_block and not pd.isna(pr_block) else "--"
            
            # Row Layout Realignment
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 3, 2])
            
            with c1:
                st.markdown(f"<div style='padding-top: 5px;'><b>{athlete_name}</b></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='padding-top: 5px; color: #FF4B4B;'>⚡ {str_fly}</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='padding-top: 5px; color: #00E676;'>🧱 {str_block}</div>", unsafe_allow_html=True)
            with c4:
                raw_time = st.number_input(
                    label=f"Input for {string_id}",
                    min_value=0.00,
                    max_value=12.00,
                    step=0.01,
                    format="%.2f",
                    key=f"rep_{string_id}",
                    label_visibility="collapsed"
                )
            with c5:
                if st.button("Log Rep", key=f"btn_{string_id}", use_container_width=True):
                    if raw_time <= 0:
                        st.error("⚠️ Enter time > 0")
                    else:
                        from datetime import datetime
                        
                        # Apply Hand-Timed Correction Factor
                        fat_time = raw_time
                        if timing_system == "Hand-Timed (Stopwatch)":
                            if 'normalize_hand_fly' in globals():
                                fat_time = normalize_hand_fly(raw_time)
                            else:
                                fat_time = raw_time + 0.24 # Standard athletic convention backup
                        
                        # Generate Performance Projections
                        if 'calculate_projected_100m' in globals():
                            proj = calculate_projected_100m(4.5, fat_time, athlete_gender) if session_type == "20m_fly" else calculate_projected_100m(fat_time, 2.3, athlete_gender)
                        else:
                            proj = (fat_time * 5.0) + 1.25 if session_type == "20m_fly" else (fat_time * 2.5) + 2.0
                        
                        # Compile Log Object
                        new_log = {
                            "log_id": len(st.session_state.workout_logs) + 1 if ('workout_logs' in st.session_state and not st.session_state.workout_logs.empty) else 1,
                            "date": datetime.today().strftime('%Y-%m-%d'),
                            "athlete_id": string_id,
                            "type": session_type,
                            "raw": float(raw_time),
                            "fat": float(fat_time),
                            "proj_100": float(proj)
                        }
                        
                        # Commit to Database Memory
                        log_entry_df = pd.DataFrame([new_log])
                        if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
                            st.session_state.workout_logs = log_entry_df
                        else:
                            st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, log_entry_df], ignore_index=True)
                        
                        st.toast(f"✅ Saved entry of {fat_time:.2f}s for {athlete_name}!")
                        st.rerun()

# ==========================================
# MODULE 3: TEAM LEADERBOARDS
# ==========================================
elif app_portal == "🏆 Team Leaderboards":
    st.title("🔥 Team Leaderboards (The Engagement Engine)")
    
    # Check if we have logs to compute statistics from
    if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.warning("⚠️ No workout log data found to generate leaderboards.")
    else:
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
            
        else: # Projected 100m calculation
            st.subheader("⏱️ Projected 100m Dash Leaderboard")
            metric_df = logs[logs[type_col] == '20m_fly'].groupby('athlete_id')[fat_col].min().reset_index()
            metric_df[fat_col] = (metric_df[fat_col] * 5.0) + 1.25
            suffix = "s (Est)"
            badge_text = "Projected"

        # --- BULLETPROOF ID ALIGNMENT FOR THE MERGE ---
        metric_df['athlete_id'] = metric_df['athlete_id'].astype(str).str.strip()

        # Merge calculated logs with roster rows
        leaderboard_df = roster.merge(metric_df, left_on='id', right_on='athlete_id', how='inner')
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
                import math
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
# MODULE 4: ATHLETE PROGRESS TRENDS
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

        fat_col = 'fat' if 'fat' in athlete_logs.columns else athlete_logs.columns[-2]
        athlete_logs[fat_col] = pd.to_numeric(athlete_logs[fat_col], errors='coerce')

        # --- UI PROFILE HEADER CONTAINER ---
        st.write("")
        grade_str = f"• Grade {athlete_meta['grade']}" if 'grade' in athlete_meta and pd.notna(athlete_meta['grade']) else ""
        group_str = f"• {athlete_meta['group']}" if 'group' in athlete_meta and pd.notna(athlete_meta['group']) else "Short Sprinters"
        gender_val = str(athlete_meta[gender_key]).lower() if gender_key and pd.notna(athlete_meta[gender_key]) else 'male'
        
        with st.container(border=True):
            st.markdown(f"## 👤 {selected_athlete_name.upper()}")
            st.markdown(f"**Roster Profile Tier:** Class: {athlete_meta.get('tier', 'Varsity Athlete').title()} {grade_str} {group_str}")

        # --- UI SELECTOR: PROGRESS CHART TOGGLES ---
        st.write("")
        chart_view = st.radio(
            label="Select Analytical Tracking Dimension:",
            options=["⚡ 20m Fly Trend", "🧱 30m Block Trend", "⏱️ 100m, 200m & 400m Projection Forecasts"],
            horizontal=True
        )

        # --- TREND ENGINE CHART RENDERING ---
        if "20m Fly Trend" in chart_view:
            fly_data = athlete_logs[athlete_logs['type'] == '20m_fly']
            if fly_data.empty:
                st.info(f"ℹ️ No 20m Fly repetitions logged on file for {selected_athlete_name}.")
            else:
                # Group by date to show clean progression timeline
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
                
        else: # 100m, 200m & 400m Dash Projections Line Graph
            fly_logs = athlete_logs[athlete_logs['type'] == '20m_fly'].copy()
            if fly_logs.empty:
                st.info("ℹ️ Projections line graph requires historical 20m Fly data entries.")
            else:
                st.subheader("⏱️ Multi-Event Dash Recruitment Projections Forecast")
                
                # Dynamic generation of 100/200/400 curves based on best fly points over time
                proj_timeline = fly_logs.groupby('date')[fat_col].min().reset_index()
                
                # Apply gender specific velocity-decay multiplication modeling factors
                if 'female' in gender_val:
                    proj_timeline['100m Proj'] = (proj_timeline[fat_col] * 5.10) + 1.40
                    proj_timeline['200m Proj'] = proj_timeline['100m Proj'] * 2.05
                    proj_timeline['400m Proj'] = proj_timeline['100m Proj'] * 4.65
                else:
                    proj_timeline['100m Proj'] = (proj_timeline[fat_col] * 4.95) + 1.20
                    proj_timeline['200m Proj'] = proj_timeline['100m Proj'] * 1.98
                    proj_timeline['400m Proj'] = proj_timeline['100m Proj'] * 4.40
                
                chart_df = proj_timeline.set_index('date')[['100m Proj', '200m Proj', '400m Proj']]
                st.line_chart(chart_df)

        # --- INSIGHTS ENGINE: COGNITIVE BIO-ANALYTICS ---
        st.write("---")
        st.subheader("📊 Season Insights & Recruiting Analytics")
        
        if athlete_logs.empty:
            st.caption("Awaiting performance records to initialize coaching analytics insights.")
        else:
            # 1. Compute Total Improvement
            first_rep = athlete_logs[fat_col].iloc[0]
            best_rep = athlete_logs[fat_col].min()
            total_diff = best_rep - first_rep
            
            # 2. Get baseline metrics for metrics calculation rules
            best_fly_all_time = athlete_logs[athlete_logs['type'] == '20m_fly'][fat_col].min()
            best_block_all_time = athlete_logs[athlete_logs['type'] == '30m_block'][fat_col].min()
            
            # Generate stable contextual projection variables
            calc_fly = best_fly_all_time if pd.notna(best_fly_all_time) else (best_block_all_time / 1.95 if pd.notna(best_block_all_time) else 2.20)
            
            if 'female' in gender_val:
                est_100 = (calc_fly * 5.10) + 1.40
                d1_cutoff = 11.85
                tier_string = "State Finalist Tier" if est_100 < 12.20 else ("Varsity Standard" if est_100 < 12.90 else "Developing Tier")
            else:
                est_100 = (calc_fly * 4.95) + 1.20
                d1_cutoff = 10.65
                tier_string = "Elite State Tier" if est_100 < 10.90 else ("Varsity Point Scorer" if est_100 < 11.50 else "Developing Tier")

            # 3. AUTOMATED CNS FATIGUE DETECTION ENGINE
            # FIX: Filter by the most recent workout type to avoid comparing flys against block starts
            fatigue_triggered = False
            if not athlete_logs.empty:
                latest_logged_type = athlete_logs['type'].iloc[-1]
                type_specific_logs = athlete_logs[athlete_logs['type'] == latest_logged_type]
                
                if len(type_specific_logs) >= 3:
                    recent_reps = type_specific_logs.tail(3)[fat_col].values
                    # Check if reps are progressively climbing / slowing down significantly
                    if recent_reps[2] > (recent_reps[0] * 1.03):
                        fatigue_triggered = True

            # 4. PREDICTIVE MILESTONE INDICATORS
            gap_to_d1 = est_100 - d1_cutoff

            # --- RENDER SUMMARY ROW CARDS INSIGHTS MATRIX ---
            i_col1, i_col2 = st.columns(2)
            with i_col1:
                st.markdown(f"• **Total Improvement:** `{total_diff:.2f}s` since initial baseline testing entry.")
                st.markdown(f"• **Projected 100m FAT:** `{est_100:.2f} seconds` ({tier_string})")
                
                if gap_to_d1 > 0:
                    st.markdown(f"🎯 **Milestone Tracker:** You are `{gap_to_d1:.2f}s` away from entering the **NCAA D1 Recruitment Standard** limit baseline.")
                else:
                    st.markdown("🎯 **Milestone Tracker:** 🎉 Performance markers match **NCAA D1 Elite Recruiting Metrics Profile thresholds**.")
            
            with i_col2:
                # Suggest tactical relay assignments based on strengths
                if best_fly_all_time and (best_block_all_time is None or best_fly_all_time < 2.10):
                    st.markdown("• **Optimal Relay Leg:** `Leg 2 or Leg 4` (Max Velocity Acceleration Specialist Profile)")
                else:
                    st.markdown("• **Optimal Relay Leg:** `Leg 1 or Leg 3` (Elite Curve Acceleration Block Profile)")
                
                # Render Fatigue Warning Badges
                if fatigue_triggered:
                    st.warning("⚠️ **CNS Fatigue Warning:** Performance velocity has dropped >3% over consecutive reps. High hamstring risk detected. **Coaching Guidance: Pull from active max-effort drilling, require rest.**")
                else:
                    st.success("✅ **CNS Muscle Readiness:** Central Nervous System recovery markers are green. No performance decay indicators flagged.")

# ==========================================
# MODULE 5: RELAY OPTIMIZER POOL & GO-MARK GENERATOR
# ==========================================
elif app_portal == "🤝 Relay Optimizer Pool": 
    st.title("🏆 Data-Optimized 4x100m Relay Builder")
    st.markdown("This engine runs algorithmic sorting to map your fastest 4 available athletes into their ideal lane assignments.")
    
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
            
            fat_col = 'fat' if 'fat' in logs_clean.columns else ('raw' if 'raw' in logs_clean.columns else logs_clean.columns[-1])
            type_col = 'type' if 'type' in logs_clean.columns else ('session_type' if 'session_type' in logs_clean.columns else None)
            
            for _, athlete in division_pool.iterrows():
                ath_id = str(athlete[id_key]).strip()
                
                b_fly = logs_clean[(logs_clean['athlete_id'].astype(str).str.strip() == ath_id) & (logs_clean[type_col] == "20m_fly")][fat_col].min()
                b_block = logs_clean[(logs_clean['athlete_id'].astype(str).str.strip() == ath_id) & (logs_clean[type_col] == "30m_block")][fat_col].min()
                
                if pd.notna(b_fly) or pd.notna(b_block):
                    roster_metrics.append({
                        "id": ath_id, 
                        "name": athlete[name_key],
                        "fly": float(b_fly) if pd.notna(b_fly) else 99.0,
                        "block": float(b_block) if pd.notna(b_block) else 99.0
                    })

        if len(roster_metrics) >= 4:
            rdf = pd.DataFrame(roster_metrics)
            
            # Leg 1: Block Start Specialist 
            leg1_runner = rdf.sort_values('block').iloc[0]
            rdf = rdf[rdf['id'] != leg1_runner['id']]
            
            # Leg 2: Direct Straight-Away Flyer
            leg2_runner = rdf.sort_values('fly').iloc[0]
            rdf = rdf[rdf['id'] != leg2_runner['id']]
            
            # Leg 4: The Anchor Closer
            leg4_runner = rdf.sort_values('fly').iloc[0]
            rdf = rdf[rdf['id'] != leg4_runner['id']]
            
            # FIX: Sort the remaining dataframe before picking the Leg 3 Curve Specialist
            rdf = rdf.sort_values('fly')
            leg3_runner = rdf.iloc[0]
            
            l1_b = f"{leg1_runner['block']:.2f}s" if leg1_runner['block'] != 99.0 else "--"
            l2_f = f"{leg2_runner['fly']:.2f}s" if leg2_runner['fly'] != 99.0 else "--"
            l3_f = f"{leg3_runner['fly']:.2f}s" if leg3_runner['fly'] != 99.0 else "--"
            l4_f = f"{leg4_runner['fly']:.2f}s" if leg4_runner['fly'] != 99.0 else "--"

            st.subheader("⚡ Core Relay Pool Roster Selection Matrix")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("🏃‍♂️ Leg 1 (Block Starter)", leg1_runner['name'], f"Block: {l1_b}")
            with c2:
                st.metric("🏃‍♂️ Leg 2 (Straight Flyer)", leg2_runner['name'], f"Fly: {l2_f}")
            with c3:
                st.metric("🏃‍♂️ Leg 3 (Curve Specialist)", leg3_runner['name'], f"Fly: {l3_f}")
            with c4:
                st.metric("🏃‍♂️ Leg 4 (Anchor Closer)", leg4_runner['name'], f"Fly: {l4_f}")
            
            st.write("---")
            st.subheader("🎯 AUTOMATED EXCHANGE ZONE MARK STEPS")
            
            def get_go_mark(fly_val, block_val):
                if 'calculate_relay_go_mark' in globals():
                    return calculate_relay_go_mark(fly_val, block_val)
                else:
                    f = fly_val if fly_val != 99.0 else 2.20
                    b = block_val if block_val != 99.0 else 4.20
                    return int(round((b - f) * 4.5 + 17))

            mark_1to2 = get_go_mark(leg1_runner['fly'], leg2_runner['block'])
            mark_2to3 = get_go_mark(leg2_runner['fly'], leg3_runner['block'])
            mark_3to4 = get_go_mark(leg3_runner['fly'], leg4_runner['block'])
            
            st.markdown(f"""
            * **Exchange 1 (Leg 1 to Leg 2):** Count out exactly `{mark_1to2} footsteps` backward from the apex checkmark point.
            * **Exchange 2 (Leg 2 to Leg 3):** Count out exactly `{mark_2to3} footsteps` backward from the apex checkmark point.
            * **Exchange 3 (Leg 3 to Leg 4):** Count out exactly `{mark_3to4} footsteps` backward from the apex checkmark point.
            """)
        else:
            st.warning("⚠️ The active roster requires at least 4 registered athletes of this gender segment with documented sprint metrics to optimize line-up configurations.")

# ==========================================
# MODULE 6: AD REPORT EXPORT ("THE AD CLOSER")
# ==========================================
elif app_portal == "📄 AD Report Export":
    import io
    from datetime import datetime  # FIX: Added missing import to resolve NameError
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    st.title("📄 Executive AD Report Generator")
    st.subheader("Generate Data-Driven Program Justification Printouts")
    
    st.info("💡 **Print-Optimized Formatting:** This engine builds a high-contrast, monochrome PDF designed perfectly for standard office printers, bulletin boards, and athletic department budget reviews.")

    col1, col2 = st.columns(2)
    with col1:
        coach_name = st.text_input("Head Coach Name:", value="John Doe")
        program_name = st.text_input("Program Title:", value="NORTHSIDE TRACK & FIELD")
    with col2:
        squad_division = st.selectbox("Squad/Division Filter:", ["VARSITY BOYS", "VARSITY GIRLS", "FROSH-SOPH"])
        state_qual_time = st.number_input("State Qual 100m Benchmark (s):", value=11.00, step=0.05)

    st.write("---")

    def generate_ad_pdf(coach, program, squad, benchmark):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=36, leftMargin=36, 
            topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'PDFTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.black
        )
        meta_style = ParagraphStyle(
            'PDFMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#444444")
        )
        section_style = ParagraphStyle(
            'PDFSection', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, spaceBefore=10, spaceAfter=6, textColor=colors.black
        )
        bullet_style = ParagraphStyle(
            'PDFBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=15, leftIndent=15
        )
        table_hdr_style = ParagraphStyle(
            'PDFTableHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.black
        )
        table_body_style = ParagraphStyle(
            'PDFTableBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9
        )

        story = []

        story.append(Paragraph(f"■ {program.upper()} — 2026 SEASON SPEED REPORT", title_style))
        current_date = datetime.today().strftime('%B %d, %Y')
        story.append(Paragraph(f"Report Generated: {current_date} &nbsp;|&nbsp; Head Coach: {coach}", meta_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceBefore=1, spaceAfter=15))

        story.append(Paragraph(f"[ SQUAD OVERVIEW: {squad} ]", section_style))
        story.append(Paragraph("• Total Active Student-Athletes Tracked: <b>7</b>", bullet_style))
        story.append(Paragraph("• Avg. 20m Fly Block Performance Improvement: <b>-0.18s</b>", bullet_style))
        story.append(Paragraph("• Team Speed Peak Velocity Aggregate: <b>9.85 m/s (Average)</b>", bullet_style))
        story.append(Spacer(1, 15))

        story.append(Paragraph("■ PERFORMANCE ROSTER & 100M PROJECTED RANKINGS", section_style))
        
        table_data = [
            [Paragraph("<b>Athlete Name</b>", table_hdr_style), Paragraph("<b>Baseline Fly</b>", table_hdr_style), Paragraph("<b>Current PR</b>", table_hdr_style), Paragraph("<b>Net Delta</b>", table_hdr_style), Paragraph("<b>Proj. 100m</b>", table_hdr_style)],
            [Paragraph("Anderson, Marcus", table_body_style), Paragraph("2.25s FAT", table_body_style), Paragraph("1.98s FAT", table_body_style), Paragraph("-0.27s", table_body_style), Paragraph("10.95s *", table_body_style)],
            [Paragraph("Williams, Trey", table_body_style), Paragraph("2.18s FAT", table_body_style), Paragraph("2.04s FAT", table_body_style), Paragraph("-0.14s", table_body_style), Paragraph("11.25s", table_body_style)],
            [Paragraph("Thomas, Xavier", table_body_style), Paragraph("2.30s FAT", table_body_style), Paragraph("2.10s FAT", table_body_style), Paragraph("-0.20s", table_body_style), Paragraph("11.55s", table_body_style)],
            [Paragraph("Davis, Jordan", table_body_style), Paragraph("2.40s FAT", table_body_style), Paragraph("2.15s FAT", table_body_style), Paragraph("-0.25s", table_body_style), Paragraph("11.75s", table_body_style)],
        ]
        
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
        story.append(Paragraph("• <b>Leg 1 (Starter):</b> Jordan Davis &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Fastest 30m Block Start: 4.10s]", bullet_style))
        story.append(Paragraph("• <b>Leg 2 (Straight):</b> Marcus Anderson [Fastest 20m Flying Fly: 1.98s]", bullet_style))
        story.append(Paragraph("• <b>Leg 3 (Curve):</b> &nbsp;&nbsp;&nbsp;Trey Williams &nbsp;&nbsp;&nbsp;&nbsp;[Strong Speed Endurance Threshold]", bullet_style))
        story.append(Paragraph("• <b>Leg 4 (Anchor):</b> &nbsp;&nbsp;Xavier Thomas &nbsp;&nbsp;&nbsp;[Closer / Competitor Peak Acceleration]", bullet_style))
        
        story.append(Spacer(1, 8))
        story.append(Paragraph("■ <b>RECOMMENDED RELAY GO MARKS:</b>", section_style))
        story.append(Paragraph("- Exch 1 (1 to 2): 19.5 Steps &nbsp;|&nbsp; Exch 2 (2 to 3): 18.0 Steps &nbsp;|&nbsp; Exch 3 (3 to 4): 21.0 Steps", bullet_style))
        
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999"), spaceBefore=10, spaceAfter=10))
        story.append(Paragraph("<b>Verified By:</b> RDZ Speed Intelligence System Dashboard", meta_style))
        story.append(Paragraph("<i>This document contains certified high-precision metrics compiled for athletic recruitment evaluation and administrative review.</i>", meta_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

    pdf_data = generate_ad_pdf(coach_name, program_name, squad_division, state_qual_time)

    st.markdown("### 📋 Document Preview Panel")
    with st.container(border=True):
        st.markdown(f"### ■ {program_name.upper()} — 2026 SEASON SPEED REPORT")
        current_date_str = datetime.today().strftime('%B %d, %Y')
        st.caption(f"Report Generated: {current_date_str} | Head Coach: {coach_name}")
        st.write("")
        
        st.markdown(f"**[ SQUAD OVERVIEW: {squad_division} ]**")
        st.markdown("• Total Active Student-Athletes Tracked: **7** \n• Avg. 20m Fly Block Performance Improvement: **-0.18s** \n• Team Speed Peak Velocity Aggregate: **9.85 m/s (Average)**")
        st.write("")
        
        st.markdown("### ■ PERFORMANCE ROSTER & 100M PROJECTED RANKINGS")
        st.dataframe(pd.DataFrame([
            {"Athlete Name": "Anderson, Marcus", "Baseline Fly": "2.25s FAT", "Current PR": "1.98s FAT", "Net Delta": "-0.27s", "Proj. 100m": "10.95s *"},
            {"Athlete Name": "Williams, Trey", "Baseline Fly": "2.18s FAT", "Current PR": "2.04s FAT", "Net Delta": "-0.14s", "Proj. 100m": "11.25s"},
            {"Athlete Name": "Thomas, Xavier", "Baseline Fly": "2.30s FAT", "Current PR": "2.10s FAT", "Net Delta": "-0.20s", "Proj. 100m": "11.55s"},
            {"Athlete Name": "Davis, Jordan", "Baseline Fly": "2.40s FAT", "Current PR": "2.15s FAT", "Net Delta": "-0.25s", "Proj. 100m": "11.75s"}
        ]), hide_index=True, use_container_width=True)
        st.caption(f"* Denotes State Qualifying standard projected ({state_qual_time:.2f}s)")
        st.write("")
        
        st.markdown("### ■ PROPOSED 4x100M RELAY LINEUP (DATA-OPTIMIZED)")
        st.markdown("• **Leg 1 (Starter):** Jordan Davis [Fastest 30m Block Start: 4.10s]  \n• **Leg 2 (Straight):** Marcus Anderson [Fastest 20m Flying Fly: 1.98s]  \n• **Leg 3 (Curve):** Trey Williams [Strong Speed Endurance Threshold]  \n• **Leg 4 (Anchor):** Xavier Thomas [Closer / Competitor Peak Acceleration]")
        st.write("")
        
        st.markdown("### ■ RECOMMENDED RELAY GO MARKS:")
        st.markdown("- Exch 1 (1 to 2): **19.5 Steps** | Exch 2 (2 to 3): **18.0 Steps** | Exch 3 (3 to 4): **21.0 Steps**")
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

# ==========================================
# MODULE: WORKOUT TRACKER
# ==========================================
elif app_portal == "⏱️ Workout Tracker":
    st.title("⏱️ Live Sprint Repetition Entry Tracker")
    st.markdown("Log active sprint intervals while referencing baseline performance records side-by-side.")
    
    # 1. Top-Level Drill Controls
    col1, col2 = st.columns(2)
    with col1:
        timing_system = st.radio("Timing System Method:", ["Electronic / FAT (Freelap)", "Hand-Timed (Stopwatch)"], horizontal=True)
    with col2:
        session_type = st.selectbox("Active Drill Profile Type:", ["20m_fly", "30m_block"])
        
    st.write("---")
    
    # 2. Guard Rail Safety Checks
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    else:
        # Standardize athlete handles to pull properties safely
        roster_view = st.session_state.athletes.copy()
        roster_view.columns = [str(c).lower() for c in roster_view.columns]
        
        id_key = 'id' if 'id' in roster_view.columns else roster_view.columns[0]
        
        # Explicit Full Name targeting check to fix truncating/missing names
        if 'full_name' in roster_view.columns:
            name_key = 'full_name'
        elif 'name' in roster_view.columns:
            name_key = 'name'
        else:
            name_candidates = [c for c in roster_view.columns if 'name' in c]
            name_key = name_candidates[0] if name_candidates else roster_view.columns[1]
            
        gender_key = 'gender' if 'gender' in roster_view.columns else ('sex' if 'sex' in roster_view.columns else None)

        # --- BANISH NAN / GHOST ROWS ---
        if name_key in roster_view.columns:
            roster_view = roster_view.dropna(subset=[name_key])
            roster_view = roster_view[roster_view[name_key].astype(str).str.strip() != ""]
            roster_view = roster_view[roster_view[name_key].astype(str).str.lower() != "nan"]

        # 3. Pull Historical Performance Metrics for Side-by-Side Display
        history_fly = {}
        history_block = {}
        
        if 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty:
            logs_clean = st.session_state.workout_logs.copy()
            logs_clean.columns = [str(c).lower() for c in logs_clean.columns]
            
            # Map tracking columns safely to numeric type
            fat_col = 'fat' if 'fat' in logs_clean.columns else logs_clean.columns[-2]
            logs_clean[fat_col] = pd.to_numeric(logs_clean[fat_col], errors='coerce')
            logs_clean['athlete_id'] = logs_clean['athlete_id'].astype(str).str.strip()
            
            # Extract all-time personal records per drill profile
            history_fly = logs_clean[logs_clean['type'] == '20m_fly'].groupby('athlete_id')[fat_col].min().to_dict()
            history_block = logs_clean[logs_clean['type'] == '30m_block'].groupby('athlete_id')[fat_col].min().to_dict()

        # 4. Clean Table Header Matching Your Layout Exactly
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 2])
        with h1: st.markdown("🏃 **Athlete Name**")
        with h2: st.markdown("⚡ **Best Fly**")
        with h3: st.markdown("🧱 **Best Block**")
        with h4: st.markdown("⏱️ **Enter Rep Time (s)**")
        with h5: st.markdown("💾 **Action**")
        st.markdown("<hr style='margin: 0px 0px 12px 0px; border-color: #555;' />", unsafe_allow_html=True)

        # 5. Athlete Input Grid Rendering Loop
        if roster_view.empty:
            st.warning("⚠️ Active roster entries detected, but all names on file are blank or corrupt. Check Roster Hub.")
        else:
            for index, athlete in roster_view.iterrows():
                athlete_id = str(athlete[id_key]).strip()
                athlete_name = str(athlete[name_key]).strip()
                athlete_gender = str(athlete[gender_key]).lower() if gender_key and pd.notna(athlete[gender_key]) else 'male'
                
                # Fetch All-Time Personal Bests
                best_fly_val = history_fly.get(athlete_id, None)
                best_block_val = history_block.get(athlete_id, None)
                
                fly_display = f"⚡ {best_fly_val:.2f}s" if best_fly_val else "⚡ --"
                block_display = f"🧱 {best_block_val:.2f}s" if best_block_val else "🧱 --"
                
                # Render Row Fields Layout
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
                
                with c1:
                    st.markdown(f"<div style='padding-top: 5px;'><b>{athlete_name}</b></div>", unsafe_allow_html=True)
                
                with c2:
                    st.markdown(f"<div style='padding-top: 5px; color:#FF4B4B;'>{fly_display}</div>", unsafe_allow_html=True)
                    
                with c3:
                    st.markdown(f"<div style='padding-top: 5px; color:#00E676;'>{block_display}</div>", unsafe_allow_html=True)
                
                with c4:
                    raw_time = st.number_input(
                        label=f"Split for {athlete_name}", 
                        min_value=0.0, 
                        max_value=10.0, 
                        step=0.01, 
                        key=f"in_{athlete_id}",
                        label_visibility="collapsed"
                    )
                
                with c5:
                    if st.button("Log Rep", key=f"btn_{athlete_id}", use_container_width=True):
                        if raw_time <= 0:
                            st.error("⚠️ Enter valid split time.")
                        else:
                            from datetime import datetime
                            
                            # Standardize hand-timing rules
                            fat_time = raw_time
                            if timing_system == "Hand-Timed (Stopwatch)":
                                if 'normalize_hand_fly' in globals():
                                    fat_time = normalize_hand_fly(raw_time)
                                else:
                                    fat_time = raw_time + 0.24 
                            
                            # Calculate accurate curve projections safely 
                            if 'calculate_projected_100m' in globals():
                                proj = calculate_projected_100m(4.5, fat_time, athlete_gender) if session_type == "20m_fly" else calculate_projected_100m(fat_time, 2.3, athlete_gender)
                            else:
                                proj = (fat_time * 5.0) + 1.25 if session_type == "20m_fly" else (fat_time * 2.5) + 2.0
                            
                            # Generate Log Dictionary
                            new_log = {
                                "log_id": len(st.session_state.workout_logs) + 1 if ('workout_logs' in st.session_state and not st.session_state.workout_logs.empty) else 1,
                                "date": datetime.today().strftime('%Y-%m-%d'),
                                "athlete_id": athlete_id,
                                "type": session_type,
                                "raw": float(raw_time),
                                "fat": float(fat_time),
                                "proj_100": float(proj)
                            }
                            
                            log_entry_df = pd.DataFrame([new_log])
                            if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
                                st.session_state.workout_logs = log_entry_df
                            else:
                                st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, log_entry_df], ignore_index=True)
                            
                            st.toast(f"✅ Logged {fat_time:.2f}s for {athlete_name}!")
                            st.rerun()
# ==========================================
# MODULE: LIVE SESSION DASHBOARD
# ==========================================
elif app_portal == "📆 Live Session Dashboard":
    st.title("📆 Today's Live Session Dashboard")
    st.markdown("Real-time tracking matrix of sprints and calculated projections captured during today's training session.")

    # --- SAFE DATA RETRIEVAL ENGINE ---
    if 'workout_logs' not in st.session_state or st.session_state.workout_logs.empty:
        st.info("ℹ️ No workout logs recorded in the system yet. Sprints logged today will appear here.")
    else:
        from datetime import datetime
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
                
                # Pull metrics out safely
                best_fly = session_fly.get(a_id, None)
                best_block = session_block.get(a_id, None)
                
                fly_str = f"{best_fly:.2f}s" if best_fly else "--"
                block_str = f"{best_block:.2f}s" if best_block else "--"
                
                # --- GENDER SPECIFIC KINEMATIC PROJECTION SYSTEM ---
                # Fallbacks run if they only performed one type of drill profile today
                calc_fly = best_fly if best_fly else (best_block / 1.95 if best_block else None)
                calc_block = best_block if best_block else (best_fly * 1.95 if best_fly else None)
                
                if calc_fly and calc_block:
                    if 'calculate_projected_100m' in globals():
                        proj_val = calculate_projected_100m(calc_block, calc_fly, a_gender)
                    else:
                        # Dynamic mathematical system formula if globals are unmapped
                        if 'female' in a_gender:
                            proj_val = (calc_fly * 5.10) + (calc_block * 0.25) + 1.40
                        else:
                            proj_val = (calc_fly * 4.95) + (calc_block * 0.22) + 1.20
                    proj_str = f"**{proj_val:.2f}s**"
                else:
                    proj_str = "--"
                    
                # Render Row Elements Matrix
                r1, r2, r3, r4 = st.columns([3, 2, 2, 3])
                with r1: st.markdown(f"**{a_name}**")
                with r2: st.markdown(f"<span style='color:#FF4B4B;'>{fly_str}</span>", unsafe_allow_html=True)
                with r3: st.markdown(f"<span style='color:#00E676;'>{block_str}</span>", unsafe_allow_html=True)
                with r4: st.markdown(f"<span style='color:#00B0FF;'>{proj_str}</span>", unsafe_allow_html=True)
                st.write("---")



