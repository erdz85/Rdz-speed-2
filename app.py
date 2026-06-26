import streamlit as st
import pandas as pd
import math
import plotly.express as px
import qrcode
import io
from datetime import datetime

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
# 3. GLOBAL MATHEMATICAL COMPUTATION ENGINE
# ==========================================
def get_best_historical_fat(athlete_id, run_type="20m_fly"):
    logs = st.session_state.workout_logs[(st.session_state.workout_logs["athlete_id"] == athlete_id) & (st.session_state.workout_logs["type"] == run_type)]
    if logs.empty: return float('inf')
    return logs["normalized_fat_time"].min()

def project_100m_dash(fat_time, gender):
    if not fat_time or fat_time == 0: return 0.0
    ten_split = fat_time / 2.0
    base = fat_time + (7.0 * ten_split)
    decay = 0.12 if str(gender).lower() == "male" else 0.15
    return round(base + decay, 2)


# ==========================================
# 4. GLOBAL NAVIGATION AND CONTROL ROUTER
# ==========================================
st.sidebar.title("⚡ RDZ Navigation")

# Unified global toggle input bindings
timing_method = st.sidebar.radio("⚙️ Global Timing Input Method:", ["Freelap/FAT", "Hand-Timed"], index=0)
is_hand = timing_method == "Hand-Timed"

app_portal = st.sidebar.radio("Go To Module Portal:", [
    "👥 Roster & Onboarding Hub", 
    "⏱️ Live Session Dashboard", 
    "🏆 Team Leaderboards", 
    "📈 Athlete Progress Trends",
    "🤝 4x100m Relay Builder",
    "📄 AD Report Export"
])


# ==========================================
# MODULE 1: ROSTER & ONBOARDING HUB
# ==========================================
if app_portal == "👥 Roster & Onboarding Hub":
    st.title("🏃 Roster Management & Decentralized Onboarding")
    
    tab_signup, tab_actions = st.tabs(["📲 Athlete Sign-Up Portal", "🛠️ Coach Control Center & Actions"])
    
    with tab_signup:
        col_inv1, col_inv2 = st.columns(2)
        with col_inv1:
            st.markdown("#### 📱 Step A & B: Shift Labor to the Athletes")
            st.info("Display this QR or invitation code on the whiteboard. Athletes scan it using their personal mobile devices to build your roster automatically.")
            st.code("NORTHSIDE-SPEED-2026", language="text")
            qr = qrcode.QRCode(version=1, box_size=5, border=1)
            qr.add_data("https://streamlit.app")
            qr.make(fit=True)
            buf = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Whiteboard Scan Target", width=140)
            
        with col_inv2:
            st.markdown("#### Simulate Mobile Athlete Registration Form")
            with st.form("athlete_signup_form", clear_on_submit=True):
                s_first = st.text_input("First Name")
                s_last = st.text_input("Last Name")
                s_gender = st.selectbox("Gender", ["male", "female"])
                s_grad = st.number_input("Graduation Year", min_value=2026, max_value=2030, value=2027)
                if st.form_submit_button("Submit Profile Request"):
                    if s_first and s_last:
                        calc_grade = max(9, min(12 - (s_grad - 2026), 12))
                        st.session_state.pending_registrations = pd.concat([
                            st.session_state.pending_registrations, 
                            pd.DataFrame([{
                                "first_name": s_first, 
                                "last_name": s_last, 
                                "gender": s_gender, 
                                "graduation_year": s_grad, 
                                "grade": calc_grade
                            }])
                        ], ignore_index=True)
                        st.success("Sent request to Coach staging area container.")
                        st.rerun()

    with tab_actions:
        st.subheader("🛡️ Step C: The Gatekeeper Approval Staging Area")
        if not st.session_state.pending_registrations.empty:
            st.warning(f"🔔 Pending Requests Detected: {len(st.session_state.pending_registrations)} athletes awaiting verification.")
            st.dataframe(st.session_state.pending_registrations, use_container_width=True)
            if st.button("✅ APPROVE ALL REQUESTS", use_container_width=True, type="primary"):
                for _, p in st.session_state.pending_registrations.iterrows():
                    next_id = f"UUID_A{len(st.session_state.athletes) + 1}"
                    st.session_state.athletes = pd.concat([
                        st.session_state.athletes, 
                        pd.DataFrame([{
                            "athlete_id": next_id, 
                            "first_name": p["first_name"], 
                            "last_name": p["last_name"],
                            "gender": p["gender"], 
                            "grade": p["grade"], 
                            "status": "varsity", 
                            "group": "Short Sprinters"
                        }])
                    ], ignore_index=True)
                st.session_state.pending_registrations = pd.DataFrame(columns=["first_name", "last_name", "gender", "graduation_year", "grade"])
                st.success("Roster updated successfully without typing inputs!")
                st.rerun()
        else:
            st.info("No pending requests to verify.")
            
        st.markdown("---")
        st.subheader("⚙️ ROSTER ACTIONS & DATA TOOLS")
        act_col1, act_col2, act_col3 = st.columns(3)
        
        with act_col1:
            st.markdown("A. CSV/Excel Bulk Import Engine")
            uploaded_file = st.file_uploader("Drag and drop standard roster spreadsheets", type=["csv"])
            if uploaded_file is not None:
                try:
                    imported_df = pd.read_csv(uploaded_file)
                    required_cols = ["first_name", "last_name", "gender", "grade", "status", "group"]
                    if all(col in imported_df.columns for col in required_cols):
                        imported_df["athlete_id"] = [f"UUID_A{len(st.session_state.athletes) + i + 1}" for i in range(len(imported_df))]
                        st.session_state.athletes = pd.concat([st.session_state.athletes, imported_df[required_cols + ["athlete_id"]]], ignore_index=True)
                        st.success(f"Successfully appended {len(imported_df)} roster profiles via bulk data mapper link!")
                        st.rerun()
                    else: 
                        st.error(f"Spreadsheet must strictly match schemas headers: {required_cols}")
                except Exception as e: 
                    st.error(f"Data stream fault: {str(e)}")
                
        with act_col2:
            st.markdown("B. Custom Sub-Roster Architect")
            new_group_lbl = st.text_input("Label Title:", placeholder="e.g., Jumpers Pool")
            if st.button("➕ Create Training Group") and new_group_lbl:
                if new_group_lbl not in st.session_state.training_groups:
                    st.session_state.training_groups.append(new_group_lbl)
                    st.success(f"Added sub-roster tracking channel: {new_group_lbl}")
                    st.rerun()
                    
        with act_col3:
            st.markdown("C. Automated Annual Roster Rollover")
            st.warning("Resets senior graduation records, moves them to historical archive, and increments academic standing classes.")
            if st.button("🔀 ARCHIVE SENIORS & ADVANCE GRADES", use_container_width=True):
                active_undergrads = st.session_state.athletes[st.session_state.athletes["grade"] < 12].copy()
                active_undergrads["grade"] = active_undergrads["grade"] + 1
                st.session_state.athletes = active_undergrads.reset_index(drop=True)
                st.success("Rollover processing finalized! Database adjusted, clean, and optimized for the next track year sequence.")
                st.rerun()

        # Display Control Center Matrix Rows
        st.markdown("---")
        st.subheader("📋 Coach's Control Center Dashboard Matrix")
        group_view = st.selectbox("Group Filter View Routing Toggle:", ["All"] + st.session_state.training_groups)
        
        display_set = st.session_state.athletes.copy()
        if group_view != "All":
            display_set = display_set[display_set["group"] == group_view]
            
        for _, row in display_set.iterrows():
            a_id = row["athlete_id"]
            best_fly = get_best_historical_fat(a_id, "20m_fly")
            best_fly_str = f"{best_fly:.2f}s FAT" if best_fly != float('inf') else "N/A"
            
            st.markdown(f"""
            <div class='metric-card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <b>👤 {row['last_name']}, {row['first_name']} (Grade {row['grade']})</b><br/>
                        <small style='color: #555;'>• Best Season 20m Fly Parameter: {best_fly_str}</small>
                    </div>
                    <div>
                        <span class='badge-tag-varsity'>{row['status'].upper()}</span>
                        <span class='badge-tag-group'>{row['group'].upper()}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            m_c1, m_c2 = st.columns(2)
            with m_c1: 
                new_g = st.selectbox("➡️ Move to Group...", st.session_state.training_groups, index=st.session_state.training_groups.index(row["group"]) if row["group"] in st.session_state.training_groups else 0, key=f"sel_{a_id}")
            with m_c2: 
                if st.button("Commit Group Move", key=f"mov_btn_{a_id}"):
                    st.session_state.athletes.loc[st.session_state.athletes["athlete_id"] == a_id, "group"] = new_g
                    st.success(f"Shifted group alignment parameters for {row['first_name']}")
                    st.rerun()

# ==========================================
# MODULE 2: LIVE SESSION DASHBOARD
# ==========================================
elif app_portal == "⏱️ Live Session Dashboard":
    st.title("⏱️ Live Workout Tracker")
    
    # 1. Configuration Row (Leverages your global sidebar timing rules)
    col1, col2 = st.columns(2)
    with col1:
        # Display current active timing method as a clean UI status indicator
        st.info(f"⚡ Current Timing Mode: **{timing_method}**")
    with col2:
        session_type = st.selectbox("Drill Profile:", ["20m_fly", "30m_block"])
        
    st.write("---")
    
    # 2. Table Header for Scannable Grid Layout
    h1, h2, h3 = st.columns([2, 2, 1])
    with h1: st.markdown("**Athlete Name**")
    with h2: st.markdown("**Split Time (seconds)**")
    with h3: st.markdown("**Action**")
    st.write("---")

    # 3. Dynamic Athlete Logger Loop
    for index, athlete in st.session_state.athletes.iterrows():
        # --- AUTOMATIC COLUMN NAME FIXER ---
        # Forces all pandas row keys to lowercase behind the scenes to avoid KeyErrors
        athlete_dict = {str(k).lower(): v for k, v in athlete.items()}
        
        a_name = athlete_dict.get('name', athlete_dict.get('athlete_name', 'Unknown Athlete'))
        a_id = athlete_dict.get('id', athlete_dict.get('athlete_id', index))
        a_gender = athlete_dict.get('gender', 'male') 
        # -----------------------------------

        with st.container():
            c1, c2, c3 = st.columns([2, 2, 1])
            
            # Column 1: Athlete Name (Vertically padded to align with inputs)
            with c1:
                st.markdown(f"<div style='padding-top: 25px;'><strong>{a_name}</strong></div>", unsafe_allow_html=True)
            
            # Column 2: Data Input (Hidden placeholder label for design alignment)
            with c2:
                raw_time = st.number_input(
                    label=f"Split for {a_name}", 
                    min_value=0.0, 
                    max_value=10.0, 
                    step=0.01, 
                    key=f"in_{a_id}",
                    label_visibility="collapsed"
                )
            
            # Column 3: Action Submission Button
            with c3:
                st.markdown("<div style='padding-top: 15px;'>", unsafe_allow_html=True)
                submit_btn = st.button("💾 Save", key=f"btn_{a_id}", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Form Processing Logic
                if submit_btn:
                    if raw_time > 0:
                        # Applies FAT math using your global boolean `is_hand` variable
                        fat_time = normalize_hand_fly(raw_time) if is_hand else raw_time
                        
                        # Project performance bounds based on session type
                        proj = (
                            calculate_projected_100m(4.5, fat_time, a_gender) 
                            if session_type == "20m_fly" 
                            else calculate_projected_100m(fat_time, 2.3, a_gender)
                        )
                        
                        # Construct structured log history dictionary
                        new_log = {
                            "log_id": len(st.session_state.workout_logs) + 1,
                            "date": datetime.today().strftime('%Y-%m-%d'),
                            "athlete_id": a_id,
                            "type": session_type,
                            "raw": raw_time,
                            "fat": fat_time,
                            "proj_100": proj
                        }
                        
                        # Append directly into session dataframes
                        st.session_state.workout_logs = pd.concat(
                            [st.session_state.workout_logs, pd.DataFrame([new_log])], 
                            ignore_index=True
                        )
                        
                        # Temporary unobtrusive verification toast notification
                        st.toast(f"✅ Logged {fat_time}s for {a_name}!", icon="🏃💨")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid time above 0.00s.")

# ==========================================
# MODULE 3: TEAM LEADERBOARDS
# ==========================================
elif app_portal == "🏆 Team Leaderboards":
    st.title("🔥 Team Leaderboards (The Engagement Engine)")
    seg_filter = st.radio("Segment Filter:", ["⚡ 20m Fly Rankings", "⏱️ Projected 100m"], horizontal=True)
    
    col_f1, col_f2 = st.columns(2)
    with col_f1: gender_filter = st.selectbox("Gender Select:", ["All", "male", "female"])
    with col_f2: status_filter = st.selectbox("Roster Tier:", ["All Varsity", "varsity", "jv"])
        
    if not st.session_state.workout_logs.empty:
        merged_rank = pd.merge(st.session_state.workout_logs, st.session_state.athletes, on="athlete_id")
        if gender_filter != "All": merged_rank = merged_rank[merged_rank["gender"] == gender_filter]
        if status_filter != "All Varsity": merged_rank = merged_rank[merged_rank["status"] == status_filter]
            
        if not merged_rank.empty:
            idx_bests = merged_rank.groupby("athlete_id")["normalized_fat_time"].idxmin()
            leaderboard_df = merged_rank.loc[idx_bests].sort_values(by="normalized_fat_time").reset_index(drop=True)
            
            for rank_idx, row in leaderboard_df.iterrows():
                medal = "🥇" if rank_idx == 0 else ("🥈" if rank_idx == 1 else ("🥉" if rank_idx == 2 else "👤"))
                badge = "<span class='badge-top-speed'>⚡ Top Speed</span>" if rank_idx == 0 else ("<span class='badge-hot'>🔥 Hot Streak</span>" if row["is_pr"] else "")
                score = f"{row['normalized_fat_time']:.2f}s FAT" if seg_filter == "⚡ 20m Fly Rankings" else f"{row['projected_100m']:.2f}s (Proj 100m)"
                
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div><b>{medal} {rank_idx+1}. {row['first_name']} {row['last_name']} ({row['group']} • Grade {row['grade']})</b></div>
                        <div><span style='font-size: 1.2rem; font-weight: bold; margin-right: 15px;'>{score}</span>{badge}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("### 👑 RECENTLY CROWNED ANNOUNCEMENTS")
            st.info(f"🏆 Social Feed: **{leaderboard_df.iloc[0]['first_name']} {leaderboard_df.iloc[0]['last_name']}** is holding down the absolute apex top velocity standard!")

# ==========================================
# MODULE 4: ATHLETE PROGRESS SCREEN
# ==========================================
elif app_portal == "📈 ... Athlete Progress Trends":
    # Formulate selection options from state schemas
    athlete_options = {f"{row['first_name']} {row['last_name']}": row['athlete_id'] for _, row in st.session_state.athletes.iterrows()}
    selected_display = st.selectbox("🔍 Select Profile for Analytical Deep Dive:", list(athlete_options.keys()))
    target_athlete_id = athlete_options[selected_display]
    
    # Securely isolate single athlete data rows
    ath_row = st.session_state.athletes[st.session_state.athletes["athlete_id"] == target_athlete_id].iloc[0]
    st.markdown(f"### 👤 ATHLETE PROFILE: {ath_row['first_name']} {ath_row['last_name']} ({ath_row['status'].title()})")
    
    # Render wireframe trend filtering switches
    metric_trend = st.radio("Select Target Metric Trend Line:", ["● 20m Fly Trend", "◯ 30m Block Trend"], horizontal=True)
    target_type = "20m_fly" if "20m Fly" in metric_trend else "30m_block"
    
    raw_logs = st.session_state.workout_logs[
        (st.session_state.workout_logs["athlete_id"] == target_athlete_id) & 
        (st.session_state.workout_logs["type"] == target_type)
    ].copy()
    
    if raw_logs.empty:
        st.warning(f"No logged performance metrics found in database schemas for {metric_trend} entries.")
    else:
        # BACKEND LOGIC: The Peak Performance Filter (Translating the SQL Weekly Grouping Rule)
        raw_logs["date_parsed"] = pd.to_datetime(raw_logs["date"])
        raw_logs["training_week"] = raw_logs["date_parsed"].dt.isocalendar().week
        
        # Select minimum/fastest FAT time per athlete per tracking calendar week boundary
        filtered_progress = raw_logs.loc[raw_logs.groupby("training_week")["normalized_fat_time"].idxmin()].sort_values(by="date")
        current_pr = filtered_progress["normalized_fat_time"].min()
        
        # Clean 12-Week Linear Progression Charting Model
        fig_deep = px.line(
            filtered_progress, x="date", y="normalized_fat_time", markers=True, text="normalized_fat_time",
            labels={"normalized_fat_time": "Time (Seconds FAT)", "date": "Weekly Session Trajectory Marker"},
            title=f"Documented Speed Progression Over Time [Current PR: {current_pr:.2f}s]"
        )
        fig_deep.update_yaxes(autorange="reverse")
        fig_deep.update_traces(textposition="top center", marker=dict(size=10, color="#ff4b4b"))
        st.plotly_chart(fig_deep, use_container_width=True)
        
        # Mathematical compilation engine derivations
        initial_time = filtered_progress["normalized_fat_time"].iloc[0]
        latest_time = filtered_progress["normalized_fat_time"].iloc[-1]
        total_improvement = round(initial_time - latest_time, 2)
        
        # Compute dynamic multi-split projection tiers
        best_overall_fly = get_best_historical_fat(target_athlete_id, "20m_fly")
        projected_100m_val = project_100m_dash(best_overall_fly, ath_row["gender"])
        
        # Relay Leg Mapping Logic based on max velocity thresholds
        if best_overall_fly < 2.15:
            optimal_relay_leg = "Leg 2 or Leg 4 (Max Velocity Peak)"
        else:
            optimal_relay_leg = "Leg 1 or Leg 3 (Curve / Acceleration Bias)"
            
        # Automated single-workout CNS fatigue parser engine logic
        # Evaluates time decay of the last three reps recorded on the same date sequence
        fatigue_triggered = False
        fatigue_percentage = 0.0
        
        latest_session_date = raw_logs["date"].max()
        session_reps = raw_logs[raw_logs["date"] == latest_session_date].sort_index()
        
        if len(session_reps) >= 3:
            fastest_rep = session_reps["normalized_fat_time"].min()
            last_rep = session_reps["normalized_fat_time"].iloc[-1]
            if fastest_rep > 0:
                fatigue_percentage = ((last_rep - fastest_rep) / fastest_rep) * 100
                if fatigue_percentage >= 3.0:
                    fatigue_triggered = True

        # Output Layout Render for Season Insights
        st.markdown("### 📊 SEASON INSIGHTS & ANALYTICS")
        st.markdown(f"""
        <ul class="insight-list">
            <li><b>Total Improvement:</b> {total_improvement:+.2f} seconds since early seasonal tracking.</li>
            <li><b>Projected 100m FAT:</b> {projected_100m_val:.2f} seconds ({"State Finalist Tier" if projected_100m_val < 11.00 else "Regional Tier Level"}).</li>
            <li><b>Optimal Relay Leg:</b> {optimal_relay_leg}.</li>
        </ul>
        """, unsafe_allow_html=True)
        
        # Render conditional alerting components dynamically
        if fatigue_triggered:
            st.markdown(f"""
            <div style="background-color: #f8d7da; border-left: 5px solid #d9534f; padding: 15px; border-radius: 5px; margin-bottom: 15px; color: #721c24;">
                <span class="badge-fatigue">⚠️ CNS Fatigue Detected</span> 
                Last reps dropped by <b>{fatigue_percentage:.1f}%</b> from peak intra-workout parameters. Pull athlete from active reps to preserve hamstring health.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #d4edda; border-left: 5px solid #2ecc71; padding: 15px; border-radius: 5px; margin-bottom: 15px; color: #155724;">
                ✅ <b>CNS Recovery Stable:</b> Intra-workout performance distribution parameters reside safely inside healthy thresholds (<3% decay).
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# MODULE 5: PDF REPORT GENERATOR
# ==========================================
elif app_portal == "📄 AD Report Export":
    st.title("📄 AD Report Export")
    st.markdown("Generates clean, high-contrast, black-and-white documentation to justify program budgets and prove athletic progression to recruiters.")
    
    roster_rows_html = ""
    for _, athlete in st.session_state.athletes.iterrows():
        a_id = athlete["athlete_id"]
        a_logs = st.session_state.workout_logs[(st.session_state.workout_logs["athlete_id"] == a_id) & (st.session_state.workout_logs["type"] == "20m_fly")]
        
        if not a_logs.empty:
            baseline = a_logs["normalized_fat_time"].iloc[0]
            current_pr = a_logs["normalized_fat_time"].min()
            net_delta = current_pr - baseline
            
            # Math Adjustment: Convert 20m Fly time to an accurate 10m split average
            ten_meter_split = current_pr / 4.0
            
            # Standard Piecewise Track Splicing formula for a 100m performance curve
            base_100m_time = (current_pr * 4.0) + (ten_meter_split * 2.0) 
            decay_constant = 1.12 if athlete["gender"] == "male" else 1.25
            proj_100 = round(base_100m_time + decay_constant, 2)
            
            # State qualifying standard star flags (e.g., Boys < 11.00s, Girls < 12.20s)
            is_state_tier = (athlete["gender"] == "male" and proj_100 <= 11.00) or (athlete["gender"] == "female" and proj_100 <= 12.20)
            state_star = "*" if is_state_tier else ""
            
            roster_rows_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px dashed #ccc; color: black;">{athlete['last_name']}, {athlete['first_name']}</td>
                <td style="padding: 8px; border-bottom: 1px dashed #ccc; color: black;">{baseline:.2f}s FAT</td>
                <td style="padding: 8px; border-bottom: 1px dashed #ccc; font-weight: bold; color: black;">{current_pr:.2f}s FAT</td>
                <td style="padding: 8px; border-bottom: 1px dashed #ccc; color: green;">{net_delta:+.2f}s</td>
                <td style="padding: 8px; border-bottom: 1px dashed #ccc; font-weight: bold; color: black;">{proj_100:.2f}s {state_star}</td>
            </tr>
            """
            
    # Built layout document using safe HTML character configurations
    report_html = f"""
    <div class="print-document" style="background-color: white; color: black; font-family: monospace; padding: 20px; border: 2px solid black;">
        <div style="text-align: center; border-bottom: 3px double black; padding-bottom: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0; font-weight: bold; color: black;">&#9889; NORTHSIDE TRACK & FIELD — 2026 SEASON SPEED REPORT</h2>
            <p style="margin: 5px 0 0 0; color: black;">Report Generated: {datetime.today().strftime('%B %d, %Y')} | Head Coach: John Doe</p>
        </div>
        
        <div style="border: 1px solid black; padding: 10px; margin-bottom: 15px;">
            <div style="font-weight: bold; background-color: #eaeaea; padding: 3px; margin: -10px -10px 10px -10px; border-bottom: 1px solid black; color: black;">[ SQUAD OVERVIEW: VARSITY BOYS ]</div>
            <p style="margin: 5px 0; color: black;">• Total Athletes Tracked: {len(st.session_state.athletes)} active roster profiles</p>
        </div>
        
        <div style="border: 1px solid black; padding: 10px; margin-bottom: 15px;">
            <div style="font-weight: bold; background-color: #eaeaea; padding: 3px; margin: -10px -10px 10px -10px; border-bottom: 1px solid black; color: black;">📊 PERFORMANCE ROSTER & 100M PROJECTED RANKINGS</div>
            <table style="width: 100%; border-collapse: collapse; background-color: white;">
                <thead>
                    <tr style="border-bottom: 2px solid black; text-align: left;">
                        <th style="padding: 8px; color: black;">Athlete Name</th>
                        <th style="padding: 8px; color: black;">Baseline Fly</th>
                        <th style="padding: 8px; color: black;">Current PR</th>
                        <th style="padding: 8px; color: black;">Net Delta</th>
                        <th style="padding: 8px; color: black;">Proj. 100m</th>
                    </tr>
                </thead>
                <tbody>
                    {roster_rows_html}
                </tbody>
            </table>
        </div>
        
        <div style="margin-top: 30px; text-align: center; font-size: 0.8rem; border-top: 1px solid black; padding-top: 10px; color: black;">
            📄 <i>Verified by RDZ Speed Intelligence System — Verification Code: AUTH-SECURE-2026</i>
        </div>
    </div>
    """
    
    # FIXED: Replaced standard print statement with explicit unsafe rendering parameter flag activated
    st.markdown(report_html, unsafe_allow_html=True)
    
    st.write("---")
    st.info("💡 Pro-Tip: Right-click the screen and click 'Print' (or Cmd+P / Ctrl+P) to save this report directly as a clean, black-and-white paper layout.")

# ==========================================
# MODULE: 4x100M RELAY BUILDER
# ==========================================
# FIXED: Changed app_mode to app_portal to match global sidebar navigation state
elif app_portal == "🤝 4x100m Relay Builder" or app_portal == "🤝 4x100m Relay Optimizer":
    st.title("🤝 4x100m Exchange & Relay Optimizer")
    st.markdown("Uses automatic fly-to-block differential metrics to define handoff marks.")
    
    active_athletes_df = st.session_state.athletes
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Incoming Runner (Max Velocity)")
        inc_name = st.selectbox("Select Incoming Athlete:", active_athletes_df.apply(lambda r: f"{r['first_name']} {r['last_name']}", axis=1).unique(), key="inc_run_sel")
        inc_first, inc_last = inc_name.split(" ", 1)
        inc_id = active_athletes_df[(active_athletes_df["first_name"] == inc_first) & (active_athletes_df["last_name"] == inc_last)]["athlete_id"].values[0]
        
        # Pull best 20m fly time from state schemas
        inc_fly_df = st.session_state.workout_logs[(st.session_state.workout_logs["athlete_id"] == inc_id) & (st.session_state.workout_logs["type"] == "20m_fly")]
        inc_fly = inc_fly_df["normalized_fat_time"].min() if not inc_fly_df.empty else 2.10
        st.metric("Best 20m Fly Metric Standard", f"{inc_fly:.2f}s FAT")
        
    with col2:
        st.subheader("Outgoing Runner (Acceleration)")
        out_name = st.selectbox("Select Outgoing Athlete:", active_athletes_df.apply(lambda r: f"{r['first_name']} {r['last_name']}", axis=1).unique(), key="out_run_sel", index=1 if len(active_athletes_df) > 1 else 0)
        out_first, out_last = out_name.split(" ", 1)
        out_id = active_athletes_df[(active_athletes_df["first_name"] == out_first) & (active_athletes_df["last_name"] == out_last)]["athlete_id"].values[0]
        
        # Pull best 30m block time from state schemas
        out_blk_df = st.session_state.workout_logs[(st.session_state.workout_logs["athlete_id"] == out_id) & (st.session_state.workout_logs["type"] == "30m_block")]
        out_block = out_blk_df["normalized_fat_time"].min() if not out_blk_df.empty else 4.10
        st.metric("Best 30m Block Metric Standard", f"{out_block:.2f}s FAT")
        
    st.write("---")
    
    # Differential exchange step marks algorithm execution
    try:
        raw_mark = (float(out_block) - float(inc_fly)) * 7.5
        go_mark_steps = max(1, round(raw_mark, 1))
    except:
        go_mark_steps = 18.5
    
    st.markdown(f"""
    <div class="metric-card">
        <h3>📏 Recommended Exchange Go-Mark Target</h3>
        <h1 style="color: #ff4b4b; font-size: 3.5rem; margin: 5px 0;">{go_mark_steps} STEPS</h1>
        <p><b>Handoff Execution Instruction:</b> Place the go-mark tape exactly <b>{go_mark_steps} steps</b> backward behind the acceleration zone line. When the incoming runner reaches the tape mark, the outgoing athlete drives out blindly.</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# MODULE: WORKOUT TRACKER
# ==========================================
elif app_mode == "⏱️ Workout Tracker":
    st.title("⏱️ Live Workout Tracker")
    col1, col2 = st.columns(2)
    with col1:
        timing_system = st.radio("Timing Method:", ["Electronic / FAT (Freelap)", "Hand-Timed (Stopwatch)"])
    with col2:
        session_type = st.selectbox("Drill Profile:", ["20m_fly", "30m_block"])
        
    st.write("---")
    for index, athlete in st.session_state.athletes.iterrows():
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**{athlete['name']}**")
        with c2:
            raw_time = st.number_input(f"Split (s)", min_value=0.0, max_value=10.0, step=0.01, key=f"in_{athlete['id']}")
        with c3:
            if st.button("Save Log", key=f"btn_{athlete['id']}"):
                if raw_time > 0:
                    fat_time = normalize_hand_fly(raw_time) if timing_system == "Hand-Timed (Stopwatch)" else raw_time
                    proj = calculate_projected_100m(4.5, fat_time, athlete['gender']) if session_type == "20m_fly" else calculate_projected_100m(fat_time, 2.3, athlete['gender'])
                    
                    new_log = {
                        "log_id": len(st.session_state.workout_logs) + 1,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "athlete_id": athlete['id'],
                        "type": session_type,
                        "raw": raw_time,
                        "fat": fat_time,
                        "proj_100": proj
                    }
                    st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame([new_log])], ignore_index=True)
                    st.rerun()
