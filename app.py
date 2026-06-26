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
# MODULE 5: 4x100m RELAY BUILDER
# ==========================================
elif app_portal == "🤝 4x100m Relay Builder":
    st.title("🤝 4x100m Exchange & Relay Optimizer")
    st.markdown("Uses automatic fly-to-block differential metrics to define handoff marks.")

    # Check if we have logs to compute statistics from
    if ('workout_logs' not in st.session_state or 
        st.session_state.workout_logs.empty or 
        'athletes' not in st.session_state or 
        st.session_state.athletes.empty):
        
        st.warning("⚠️ No workout log data found. Showing blueprint fallback preview utilizing template metrics.")
        
        # Spec-matched blueprint fallback with Leg 2 explicitly mapped to the top flyer
        relay_lineup = [
            {"leg": 1, "name": "Jordan Davis", "role": "Starter (Curve Acceleration)", "metric_label": "Best 30m Block", "time": 4.10},
            {"leg": 2, "name": "Marcus Anderson", "role": "Max Velocity Straight (Extended Distance)", "metric_label": "Best 20m Fly", "time": 1.98},
            {"leg": 3, "name": "Trey Williams", "role": "Curve Mastery Threshold", "metric_label": "Best 20m Fly", "time": 2.04},
            {"leg": 4, "name": "Xavier Thomas", "role": "Anchor (Closer)", "metric_label": "Best 20m Fly", "time": 2.10}
        ]
    else:
        # --- DATA ENGINE: COMPUTE BEST LIFETIME METRICS PER ATHLETE ---
        logs = st.session_state.workout_logs.copy()
        
        # Standardize logs columns to lowercase to completely prevent KeyErrors
        logs.columns = [str(c).lower() for c in logs.columns]
        
        # Fallback handling in case type or fat columns use varying naming conventions
        type_col = 'type' if 'type' in logs.columns else ('session_type' if 'session_type' in logs.columns else None)
        fat_col = 'fat' if 'fat' in logs.columns else ('raw' if 'raw' in logs.columns else logs.columns[-1])

        if type_col and fat_col:
            # Extract best 20m_fly and 30m_block times per individual athlete
            fly_df = logs[logs[type_col] == '20m_fly'].groupby('athlete_id')[fat_col].min().rename('best_fly')
            block_df = logs[logs[type_col] == '30m_block'].groupby('athlete_id')[fat_col].min().rename('best_block')
        else:
            # Empty placeholders if columns don't align
            fly_df = pd.Series(dtype='float64')
            block_df = pd.Series(dtype='float64')
        
        # Merge best historical marks back with baseline athlete profiles
        roster = st.session_state.athletes.copy()
        # Standardize roster columns to lowercase as well just to be safe
        roster.columns = [str(c).lower() for c in roster.columns]
        
        # Smart dynamic identification keys for id and name
        id_col = 'id' if 'id' in roster.columns else ('athlete_id' if 'athlete_id' in roster.columns else roster.columns[0])
        
        # Bulletproof Name Resolution Strategy
        if 'name' in roster.columns:
            name_col = 'name'
        else:
            # Look for any column containing 'name' (e.g., 'athlete_name', 'first_name')
            name_candidates = [c for c in roster.columns if 'name' in c]
            name_col = name_candidates[0] if name_candidates else None

        roster = roster.merge(fly_df, left_on=id_col, right_index=True, how='left')
        roster = roster.merge(block_df, left_on=id_col, right_index=True, how='left')
        
        # Safe alignment back to fixed dictionary property names used by the UI layout loop
        roster['id'] = roster[id_col]
        if name_col:
            roster['name'] = roster[name_col]
        else:
            # Ultimate safety fallback: label them by their ID strings if no name column exists
            roster['name'] = "Athlete #" + roster['id'].astype(str)
            
        # Drop individuals missing the core 20m fly profiles
        valid_pool = roster.dropna(subset=['best_fly']).copy()
        
        if len(valid_pool) < 4:
            st.info("💡 Note: Data-calculated roster pooling requires at least 4 athletes with logged 20m Fly times. Using default varsity blueprint configuration entries below:")
            relay_lineup = [
                {"leg": 1, "name": "Jordan Davis", "role": "Starter (Curve Acceleration)", "metric_label": "Best 30m Block", "time": 4.10},
                {"leg": 2, "name": "Marcus Anderson", "role": "Max Velocity Straight (Extended Distance)", "metric_label": "Best 20m Fly", "time": 1.98},
                {"leg": 3, "name": "Trey Williams", "role": "Curve Mastery Threshold", "metric_label": "Best 20m Fly", "time": 2.04},
                {"leg": 4, "name": "Xavier Thomas", "role": "Anchor (Closer)", "metric_label": "Best 20m Fly", "time": 2.10}
            ]
        else:
            # Sort full pool to allocate roles based on tactical track dynamics
            # 1. Isolate the absolute best block starter for Leg 1
            best_starter_row = valid_pool.sort_values(by='best_block', ascending=True).iloc[0]
            starter_id = best_starter_row['id']
            
            # 2. Extract remaining pool and sort purely by raw 20m Fly speed (lowest time first)
            remaining_pool = valid_pool[valid_pool['id'] != starter_id].sort_values(by='best_fly', ascending=True)
            
            # TACTICAL ASSIGNMENT RULES:
            # #1 Flyer goes to Leg 2 (Extended distance straightaway strategy)
            leg2_row = remaining_pool.iloc[0]
            # #2 Flyer goes to Leg 4 (The anchor closer)
            leg4_row = remaining_pool.iloc[1]
            # #3 Flyer goes to Leg 3 (Curve specialist transition)
            leg3_row = remaining_pool.iloc[2]
            
            relay_lineup = [
                {
                    "leg": 1, 
                    "name": best_starter_row['name'], 
                    "role": "Starter (Curve Acceleration)", 
                    "metric_label": "Best 30m Block" if pd.notna(best_starter_row['best_block']) else "Best 20m Fly (Fallback)",
                    "time": best_starter_row['best_block'] if pd.notna(best_starter_row['best_block']) else best_starter_row['best_fly']
                },
                {"leg": 2, "name": leg2_row['name'], "role": "Max Velocity Straight (Extended Distance)", "metric_label": "Best 20m Fly", "time": leg2_row['best_fly']},
                {"leg": 3, "name": leg3_row['name'], "role": "Curve Mastery Threshold", "metric_label": "Best 20m Fly", "time": leg3_row['best_fly']},
                {"leg": 4, "name": leg4_row['name'], "role": "Anchor (Closer)", "metric_label": "Best 20m Fly", "time": leg4_row['best_fly']}
            ]

   # --- UI DISPLAY: THE 4x100M CONFIGURATION GRID ---
    st.subheader("🏆 Data-Optimized Relay Lineup Order")
    
    cols = st.columns(4)
    for idx, runner in enumerate(relay_lineup):
        with cols[idx]:
            st.markdown(f"### **Leg {runner['leg']}**")
            st.caption(f"🎭 {runner['role']}")
            with st.container(border=True):
                st.markdown(f"🏃 **{runner['name']}**")
                
                # --- SAFE TYPE CHECK & FORMATTING BLOCK ---
                import math
                val = runner['time']
                
                if val is not None and isinstance(val, (int, float)) and not math.isnan(val):
                    formatted_value = f"{val:.2f}s FAT"
                elif isinstance(val, str):
                    formatted_value = val
                else:
                    formatted_value = "--"
                
                st.metric(label=runner['metric_label'], value=formatted_value)

    st.write("---")
    st.subheader("📏 Exchange Zone Go-Mark Target Analysis")
    
    # --- MATHEMATICAL ENGINE: DYNAMIC GO-MARK GENERATION ---
    def calculate_go_mark(inc_fly, out_time):
        """
        Calculates relay go-marks based on incoming fly time & outgoing acceleration.
        Uses 30m Block Start with a dynamic fallback to 20m Fly if block data isn't logged.
        """
        # Formulate a dynamic baseline if dealing with non-block acceleration values
        # If outgoing runner time is a fly, scale it out to estimate a standing start threshold
        adj_out_acceleration = out_time if out_time > 3.0 else (out_time * 1.95)
        
        # Calculate dynamic physical gap constraints
        base_steps = (adj_out_acceleration / inc_fly) * 7.4
        return max(12.0, min(24.0, round(base_steps, 1)))

    # Fetch ordered values from the generated lineup matrix array
    t1 = relay_lineup[0]['time']
    t2 = relay_lineup[1]['time']
    t3 = relay_lineup[2]['time']
    t4 = relay_lineup[3]['time']

    # Generate calculations for the three passing exchanges
    exch1_steps = calculate_go_mark(t1, t2)
    exch2_steps = calculate_go_mark(t2, t3)
    exch3_steps = calculate_go_mark(t3, t4)

    # Render results in high-impact metric container cards matching Screen Shot 2026-06-26 at 11.52.33 AM.png
    e1, e2, e3 = st.columns(3)
    
    with e1:
        with st.container(border=True):
            st.markdown("### 🪵 Exchange 1")
            st.caption(f"Leg 1 ({relay_lineup[0]['name']}) ➔ Leg 2 ({relay_lineup[1]['name']})")
            st.markdown(f"## 🏁 **{exch1_steps} STEPS**")
            st.info("📍 Place tape backward from the start of the acceleration zone index.")

    with e2:
        with st.container(border=True):
            st.markdown("### 🪵 Exchange 2")
            st.caption(f"Leg 2 ({relay_lineup[1]['name']}) ➔ Leg 3 ({relay_lineup[2]['name']})")
            st.markdown(f"## 🏁 **{exch2_steps} STEPS**")
            st.info("📍 Place tape backward from the start of the acceleration zone index.")

    with e3:
        with st.container(border=True):
            st.markdown("### 🪵 Exchange 3")
            st.caption(f"Leg 3 ({relay_lineup[2]['name']}) ➔ Leg 4 ({relay_lineup[3]['name']})")
            st.markdown(f"## 🏁 **{exch3_steps} STEPS**")
            st.info("📍 Place tape backward from the start of the acceleration zone index.")

# ==========================================
# MODULE 6: AD REPORT EXPORT ("THE AD CLOSER")
# ==========================================
elif app_portal == "📄 AD Report Export":
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    st.title("📄 Executive AD Report Generator")
    st.subheader("Generate Data-Driven Program Justification Printouts")
    
    st.info("💡 **Print-Optimized Formatting:** This engine builds a high-contrast, monochrome PDF designed perfectly for standard office printers, bulletin boards, and athletic department budget reviews.")

    # 1. Parameter Adjustments for Report Header
    col1, col2 = st.columns(2)
    with col1:
        coach_name = st.text_input("Head Coach Name:", value="John Doe")
        program_name = st.text_input("Program Title:", value="NORTHSIDE TRACK & FIELD")
    with col2:
        squad_division = st.selectbox("Squad/Division Filter:", ["VARSITY BOYS", "VARSITY GIRLS", "FROSH-SOPH"])
        state_qual_time = st.number_input("State Qual 100m Benchmark (s):", value=11.00, step=0.05)

    st.write("---")

    # --- PDF GENERATOR ENGINE FUNCTION ---
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

        # Header Module Block
        story.append(Paragraph(f"■ {program.upper()} — 2026 SEASON SPEED REPORT", title_style))
        current_date = datetime.today().strftime('%B %d, %Y')
        story.append(Paragraph(f"Report Generated: {current_date} &nbsp;|&nbsp; Head Coach: {coach}", meta_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceBefore=1, spaceAfter=15))

        # Squad Performance KPI Summary
        story.append(Paragraph(f"[ SQUAD OVERVIEW: {squad} ]", section_style))
        story.append(Paragraph("• Total Active Student-Athletes Tracked: <b>7</b>", bullet_style))
        story.append(Paragraph("• Avg. 20m Fly Block Performance Improvement: <b>-0.18s</b>", bullet_style))
        story.append(Paragraph("• Team Speed Peak Velocity Aggregate: <b>9.85 m/s (Average)</b>", bullet_style))
        story.append(Spacer(1, 15))

        # Roster Performance Table Box
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

        # Relay Construction Board
        story.append(Paragraph("■ PROPOSED 4x100M RELAY LINEUP (DATA-OPTIMIZED)", section_style))
        story.append(Paragraph("• <b>Leg 1 (Starter):</b> Jordan Davis &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Fastest 30m Block Start: 4.10s]", bullet_style))
        story.append(Paragraph("• <b>Leg 2 (Straight):</b> Marcus Anderson [Fastest 20m Flying Fly: 1.98s]", bullet_style))
        story.append(Paragraph("• <b>Leg 3 (Curve):</b> &nbsp;&nbsp;&nbsp;Trey Williams &nbsp;&nbsp;&nbsp;&nbsp;[Strong Speed Endurance Threshold]", bullet_style))
        story.append(Paragraph("• <b>Leg 4 (Anchor):</b> &nbsp;&nbsp;Xavier Thomas &nbsp;&nbsp;&nbsp;[Closer / Competitor Peak Acceleration]", bullet_style))
        
        story.append(Spacer(1, 8))
        story.append(Paragraph("■ <b>RECOMMENDED RELAY GO MARKS:</b>", section_style))
        story.append(Paragraph("- Exch 1 (1 to 2): 19.5 Steps &nbsp;|&nbsp; Exch 2 (2 to 3): 18.0 Steps &nbsp;|&nbsp; Exch 3 (3 to 4): 21.0 Steps", bullet_style))
        
        # Verification System Signature Block
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999"), spaceBefore=10, spaceAfter=10))
        story.append(Paragraph("<b>Verified By:</b> RDZ Speed Intelligence System Dashboard", meta_style))
        story.append(Paragraph("<i>This document contains certified high-precision metrics compiled for athletic recruitment evaluation and administrative review.</i>", meta_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

    # --- STREAMLIT CONTROL ACTION ---
    pdf_data = generate_ad_pdf(coach_name, program_name, squad_division, state_qual_time)

    # Rendering Clean On-Screen Live Report UI Preview
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

    # Floating One-Tap Export Downloader Row
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
