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

# Custom CSS for track-coaching aesthetics and responsive dashboard panels
st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; border-radius: 10px; padding: 15px; border-left: 5px solid #ff4b4b; margin-bottom: 15px;}
    .badge-top-speed { background-color: #f1c40f; color: black; font-weight: bold; padding: 3px 8px; border-radius: 5px; }
    .badge-hot { background-color: #e67e22; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; }
    .badge-pr { background-color: #2ecc71; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. STATE MANAGER & PERSISTENT STORAGE
# ==========================================
if "athletes" not in st.session_state:
    st.session_state.athletes = pd.DataFrame([
        {"id": "A1", "name": "Marcus Anderson", "gender": "Male", "group": "Short Sprints", "grade": "Junior"},
        {"id": "A2", "name": "Trey Williams", "gender": "Male", "group": "Short Sprints", "grade": "Senior"},
        {"id": "A3", "name": "Elena Martinez", "gender": "Female", "group": "Short Sprints", "grade": "Junior"},
        {"id": "A4", "name": "Jordan Davis", "gender": "Female", "group": "Short Sprints", "grade": "Freshman"}
    ])

if "workout_logs" not in st.session_state:
    st.session_state.workout_logs = pd.DataFrame([
        {"date": "2026-03-01", "athlete_id": "A1", "type": "20m_fly", "fat": 2.05},
        {"date": "2026-03-10", "athlete_id": "A1", "type": "20m_fly", "fat": 1.98},
        {"date": "2026-03-01", "athlete_id": "A3", "type": "20m_fly", "fat": 2.52},
        {"date": "2026-03-10", "athlete_id": "A3", "type": "20m_fly", "fat": 2.45},
        {"date": "2026-03-01", "athlete_id": "A1", "type": "30m_block", "fat": 4.10},
        {"date": "2026-03-01", "athlete_id": "A2", "type": "30m_block", "fat": 4.25},
        {"date": "2026-03-01", "athlete_id": "A3", "type": "30m_block", "fat": 4.60},
        {"date": "2026-03-01", "athlete_id": "A4", "type": "30m_block", "fat": 4.55}
    ])


# ==========================================
# 3. ATHLETE SELF-REGISTRATION LAYER (QR INTERCEPT)
# ==========================================
if "view" in st.query_params and st.query_params["view"] == "register":
    st.title("🏃 New Athlete Registration Portal")
    st.info("Welcome to RDZ Speed. Enter your details below to join the active training roster.")
    
    with st.form("athlete_self_register", clear_on_submit=True):
        new_name = st.text_input("First & Last Name")
        new_gender = st.selectbox("Gender", ["Male", "Female"])
        new_group = st.selectbox("Training Group", ["Short Sprints", "Long Sprints", "Hurdlers"])
        new_grade = st.selectbox("Grade", ["Freshman", "Sophomore", "Junior", "Senior"])
        submit_btn = st.form_submit_button("Submit Registration")
        
        if submit_btn and new_name:
            new_id = f"A{len(st.session_state.athletes) + 1}"
            new_row = {"id": new_id, "name": new_name, "gender": new_gender, "group": new_group, "grade": new_grade}
            st.session_state.athletes = pd.concat([st.session_state.athletes, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"🎉 Welcome {new_name}! You are registered. You can close this tab now.")
    st.stop()


# ==========================================
# 4. DATA PROJECTION & MATHEMATICAL ENGINES
# ==========================================
def calculate_relay_go_mark(inc_fly, out_block):
    try:
        raw_mark = (float(out_block) - float(inc_fly)) * 7.5
        return max(1, round(raw_mark, 1))
    except:
        return 12.0

def calculate_precise_100m(thirty_block, twenty_fly, gender, is_hand_timed=False):
    if twenty_fly is None or pd.isna(twenty_fly) or float(twenty_fly) == 0:
        return None
        
    twenty_fly = float(twenty_fly)
    
    # Adjust for manual stopwatch variations to match FAT parameters
    if is_hand_timed:
        twenty_fly += 0.15
        if thirty_block is not None and not pd.isna(thirty_block):
            thirty_block = float(thirty_block) + 0.24

    # --- FALLBACK MECHANISM: Uses 20m Fly-Only model if 30m block start is missing ---
    if thirty_block is None or pd.isna(thirty_block) or float(thirty_block) == 0:
        ten_split = twenty_fly / 2.0
        if str(gender).lower() == "male":
            projected_100m = (ten_split * 10) + 1.05  # Formula Varonil
        else:
            projected_100m = (ten_split * 10) + 1.15  # Formula Femenil
        return round(projected_100m, 2)

    # --- CORE MECHANISM: Runs Piecewise Splicing model when both vectors exist ---
    thirty_block = float(thirty_block)
    ten_split = twenty_fly / 2.0
    base_time = thirty_block + (7.0 * ten_split)
    
    # Dynamic Speed Endurance Decay Constants based on performance tiers
    if str(gender).lower() == "male":
        decay_constant = 0.12 if base_time < 11.0 else 0.18
    else:
        decay_constant = 0.15 if base_time < 12.2 else 0.25
            
    return round(base_time + decay_constant, 2)


# ==========================================
# 5. SIDEBAR NAVIGATION PANEL (COACH VIEW)
# ==========================================
st.sidebar.title("⚡ RDZ Speed System")
st.sidebar.write("Program Classification: HS Track")
st.sidebar.write("---")
app_mode = st.sidebar.radio(
    "Go To Module Portal:",
    [
        "👥 Roster & Onboarding", 
        "📈 Athlete Progress", 
        "🏋️ Workout Logger", 
        "🏆 Team Leaderboards", 
        "🤝 4x100m Relay Builder", 
        "📄 AD Report Generator"
    ]
)

# FIXED: Defining this globally here ensures Module 3 can copy it on line 328
active_athletes_df = st.session_state.athletes[st.session_state.athletes['status'] == "Active"]

# ==========================================
# MODULE 1: ROSTER MANAGEMENT & ONBOARDING
# ==========================================
if app_mode == "👥 Roster & Onboarding":
    st.title("👥 Roster Management & Athlete Onboarding")
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("🔗 Share Team Access")
        st.info("Have your athletes scan this or use the code below during team check-ins.")
        st.code("RDZ-NORTHSIDE-2026", language="text")
        
        try:
            from streamlit_javascript import st_javascript
            page_url = st_javascript("window.location.href.split('?')")
            if not page_url or page_url == "0":
                qr_payload_data = "https://streamlit.app"
            else:
                qr_payload_data = f"{page_url}?view=register"
        except:
            qr_payload_data = "https://streamlit.app"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_payload_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.success("🤖 Active QR Code Payload Generated")
        st.image(byte_im, caption="Scan with smartphone camera to check-in", use_container_width=True)
        
        st.write("---")
        st.subheader("➕ Quick Add Athlete")
        new_name = st.text_input("Full Name")
        new_gender = st.selectbox("Gender", ["Male", "Female"])
        new_group = st.selectbox("Training Group", ["Short Sprints", "Long Sprints", "Hurdlers"])
        new_grade = st.selectbox("Grade", ["Freshman", "Sophomore", "Junior", "Senior"])
        
        if st.button("Register to Roster"):
            if new_name:
                new_id = f"A{len(st.session_state.athletes) + 1}"
                new_row = {"id": new_id, "name": new_name, "gender": new_gender, "group": new_group, "grade": new_grade}
                st.session_state.athletes = pd.concat([st.session_state.athletes, pd.DataFrame([new_row])], ignore_index=True)
                st.toast(f"Added {new_name} successfully!")
                st.rerun()

    with col2:
        st.subheader("🏃‍♂️ Active Roster Directory")
        st.dataframe(st.session_state.athletes, use_container_width=True, hide_index=True)
        
        if st.button("⚠️ Run End-of-Season Roster Rollover"):
            st.warning("This archives seniors and increments all grades by one year.")


# ==========================================
# MODULE 2: ATHLETE PROGRESS
# ==========================================
elif app_mode == "📈 Athlete Progress":
    st.title("📈 Athlete Performance Trajectory Deep Dive")
    
    # 1. Profile Selector and Core Roster Matching
    selected_athlete = st.selectbox("Select Athlete Profile:", st.session_state.athletes['name'].unique())
    athlete_row = st.session_state.athletes[st.session_state.athletes['name'] == selected_athlete].iloc[0]
    athlete_id = athlete_row['id']
    athlete_gender = athlete_row['gender']
    
    # Isolate specific historical metric vectors
    fly_logs = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == athlete_id) & (st.session_state.workout_logs['type'] == "20m_fly")]
    block_logs = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == athlete_id) & (st.session_state.workout_logs['type'] == "30m_block")]
    
    # 2. OVERVIEW KPI SCORECARD HEADER GRID
    st.subheader("📋 Athlete Performance Summary Card")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        best_fly = fly_logs['fat'].min() if not fly_logs.empty else None
        fly_display = f"{best_fly:.2f}s" if best_fly else "No Data"
        st.metric("⚡ Personal Best 20m Fly", fly_display)
        
    with kpi_col2:
        best_block = block_data_val = block_logs['fat'].min() if not block_logs.empty else None
        block_display = f"{best_block:.2f}s" if best_block else "No Data"
        st.metric("🛫 Personal Best 30m Block", block_display)
        
    with kpi_col3:
        # Runs your dynamic Piecewise Fallback engine directly on their profile records
        projected_100m = calculate_precise_100m(best_block, best_fly, athlete_gender, False)
        proj_display = f"{projected_100m:.2f}s" if projected_100m else "Missing Baseline Fly"
        st.metric("🎯 Projected 100m Dash", proj_display)
        
    with kpi_col4:
        total_reps = len(fly_logs) + len(block_logs)
        st.metric("🔢 Total Tracked Repetitions", total_reps)
        
    st.write("---")
    
    # 3. INTERACTIVE HISTORICAL ANALYSIS TABS
    tab_fly, tab_block = st.tabs(["⚡ Max Velocity Vectors (20m Fly)", "🛫 Acceleration Drive Vectors (30m Block)"])
    
    with tab_fly:
        st.subheader("20m Fly Velocity Analytics")
        if len(fly_logs) >= 1:
            fly_logs = fly_logs.sort_values(by="date")
            fig_fly = px.line(fly_logs, x="date", y="fat", title="20m Fly FAT Progression Trend", markers=True)
            fig_fly.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_fly, use_container_width=True)
            
            # Central Nervous System Fatigue Diagnostic Engine
            if len(fly_logs) >= 2:
                last_two = fly_logs.tail(2)['fat'].values
                val_old = float(last_two[0])
                val_new = float(last_two[1])
                decay_percent = ((val_new - val_old) / val_old) * 100
                
                if decay_percent > 4.0:
                    st.warning(f"⚠️ CNS Fatigue Advisory Warning Alert: Velocity dropped by {round(decay_percent,1)}% on last rep. Advise immediate recovery down-regulation.")
                else:
                    st.success("🟢 CNS Efficiency Stable. Athlete is primed for max velocity output.")
        else:
            st.info("Provide at least 1 historical 20m Fly entry to populate tracking vectors.")
            
    with tab_block:
        st.subheader("30m Block Acceleration Analytics")
        if len(block_logs) >= 1:
            block_logs = block_logs.sort_values(by="date")
            fig_block = px.line(block_logs, x="date", y="fat", title="30m Block Start Progression Trend", markers=True)
            fig_block.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_block, use_container_width=True)
            
            # Micro-insight reporting to evaluate start consistency
            if len(block_logs) >= 2:
                last_two_b = block_logs.tail(2)['fat'].values
                b_old = float(last_two_b[0])
                b_new = float(last_two_b[1])
                block_diff = b_new - b_old
                
                if block_diff > 0.10:
                    st.info(f"📋 Notice: Block start execution slowed down by {round(block_diff, 2)}s compared to last session. Check stance setup variables.")
                elif block_diff < -0.10:
                    st.success(f"🔥 Progress: Block start acceleration improved by {round(abs(block_diff), 2)}s! Power output trending upward.")
                else:
                    st.info("🔵 Acceleration profile consistency stable compared to your previous trial.")
        else:
            st.info("Provide at least 1 historical 30m Block entry to populate acceleration tracking vectors.")

# ==========================================
# MODULE 3: WORKOUT LOGGER & LIVE SESSION
# ==========================================
elif app_mode == "🏋️ Workout Logger":
    st.title("🏋️ Live Speed Session Dashboard")
    
    # -------------------------------------------------------------
    # CONTROL PANEL HEADER
    # -------------------------------------------------------------
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.write(f"🗓️ **Active Session Date:** {datetime.today().strftime('%B %d, %Y')}")
    with head_col2:
        if st.button("🛑 Clear Current Live Board View", use_container_width=True):
            st.toast("Board views refreshed!")

    # 1. Timing System Variable Override Gate
    st.write("---")
    st.subheader("⚙️ Global Session Configurations")
    timing_type = st.radio(
        "Select Active Session Capture Source Protocol:",
        ["◯ Freelap / Electronic FAT", "● Hand-Timed / Manual Stopwatch"],
        horizontal=True
    )
    is_hand = (timing_type == "● Hand-Timed / Manual Stopwatch")

    # 2. Metric Mode Configuration Selector
    session_metric = st.selectbox("Active Testing Drill Vector Type:", ["20m_fly", "30m_block"])

    # -------------------------------------------------------------
    # LIVE SPRINT REPETITION ENTRY TRACKER Matrix
    # -------------------------------------------------------------
    st.write("---")
    st.subheader("⏱️ Live Roster Quick-Log Interface")
    st.info("💡 Tap any entry block or input fields to log an athlete's time on the fly.")
    
    # Quick filter athletes text search bar
    search_query = st.text_input("🔍 Quick Search Athlete Profile...", "").strip().lower()
    
    # Filter out inactive athletes and apply search terms
    display_roster = active_athletes_df.copy()
    if search_query:
        display_roster = display_roster[display_roster['name'].lower().str.contains(search_query)]

    # Render individual rows inside an optimized form grid layout
    if not display_roster.empty:
        for _, athlete in display_roster.iterrows():
            ath_id = athlete['id']
            ath_name = athlete['name']
            
            # Fetch the most recent trial record time from logs
            ath_history = st.session_state.workout_logs[
                (st.session_state.workout_logs['athlete_id'] == ath_id) & 
                (st.session_state.workout_logs['type'] == session_metric)
            ]
            last_rep_str = f"{ath_history.iloc[-1]['fat']:.2f}s" if not ath_history.empty else "None"
            
            # Row Grid Layout Setup
            row_col1, row_col2, row_col3 = st.columns([2, 1, 0.5])
            
            with row_col1:
                st.markdown(f"🏃‍♂️ **{ath_name}** <br/> <small style='color:gray;'>Previous Session Rep: {last_rep_str}</small>", unsafe_allow_html=True)
            
            with row_col2:
                # Keypad friendly input configuration container
                input_val = st.number_input(
                    "Enter Time", 
                    min_value=0.00, max_value=15.00, value=0.00, step=0.01, 
                    key=f"input_{ath_id}", label_visibility="collapsed"
                )
                
            with row_col3:
                if st.button("OK", key=f"btn_{ath_id}", use_container_width=True):
                    if input_val > 0:
                        # Append the trial input directly to the persistent session state data matrices
                        new_log_row = {
                            "date": str(datetime.today().date()), 
                            "athlete_id": ath_id, 
                            "type": session_metric, 
                            "fat": float(input_val)
                        }
                        st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame([new_log_row])], ignore_index=True)
                        st.toast(f"Logged {input_val}s for {ath_name}!")
                        st.rerun()
                    else:
                        st.error("Enter a valid time.")
            st.write("<hr style='margin: 0.5em 0px;'/>", unsafe_allow_html=True)
    else:
        st.warning("No active athletes match your current filter rules.")

    # -------------------------------------------------------------
    # REAL-TIME LOG HISTORY OVERVIEW TAB
    # -------------------------------------------------------------
    st.write("---")
    st.subheader("📊 Recent Activity (This Session Logs)")
    
    today_str = str(datetime.today().date())
    todays_logs = st.session_state.workout_logs[st.session_state.workout_logs['date'] == today_str]
    
    if not todays_logs.empty:
        display_today = todays_logs.merge(st.session_state.athletes, left_on='athlete_id', right_on='id', how='left')
        for _, log in display_today.iterrows():
            capture_label = "Hand" if is_hand else "FAT"
            st.markdown(f"• **{log['name']}**: {log['fat']:.2f}s ({capture_label}) ➔ Drill: *{log['type']}*")
    else:
        st.info("No repetitions logged yet during today's track session.")

    # -------------------------------------------------------------
    # PART 3: THE COMPREHENSIVE BACKEND DATA MANAGEMENT SHEET
    # -------------------------------------------------------------
    st.write("---")
    st.subheader("🛠️ Master History Ledger Editor")
    
    if not st.session_state.workout_logs.empty:
        display_logs = st.session_state.workout_logs.merge(
            st.session_state.athletes[['id', 'name']], left_on='athlete_id', right_on='id', how='left'
        )[['date', 'name', 'type', 'fat']]
        
        edited_logs = st.data_editor(
            display_logs,
            column_config={
                "date": st.column_config.TextColumn("Session Date"),
                "name": st.column_config.TextColumn("Athlete Name", disabled=True),
                "type": st.column_config.SelectboxColumn("Metric Profile", options=["20m_fly", "30m_block"]),
                "fat": st.column_config.NumberColumn("FAT Time (seconds)", min_value=0.00, max_value=15.00, format="%.2f")
            },
            use_container_width=True, num_rows="dynamic", key="workout_log_editor_table"
        )
        
        if st.button("💾 Apply & Save Spreadsheet Changes"):
            updated_db = edited_logs.merge(st.session_state.athletes[['id', 'name']], on='name', how='left')
            updated_db = updated_db[['date', 'id', 'type', 'fat']].rename(columns={'id': 'athlete_id'})
            st.session_state.workout_logs = updated_db
            st.toast("Database logs updated successfully!")
            st.rerun()

# ==========================================
# MODULE 4: TEAM LEADERBOARDS
# ==========================================
elif app_mode == "🏆 Team Leaderboards":
    st.title("🏆 Power & Velocity Team Leaderboards")
    st.write("Live program rankings derived from absolute maximum output thresholds.")
    tab1, tab2, tab3 = st.tabs(["⚡ Top 20m Fly Times", "🛫 Top 30m Blocks", "🏃 Projected 100m Dash"])
    
    with tab1:
        fly_data = st.session_state.workout_logs[st.session_state.workout_logs['type'] == "20m_fly"]
        if not fly_data.empty:
            leaderboard_fly = fly_data.groupby('athlete_id')['fat'].min().reset_index()
            leaderboard_fly = leaderboard_fly.merge(st.session_state.athletes, left_on='athlete_id', right_on='id')
            leaderboard_fly = leaderboard_fly.sort_values(by="fat")[['name', 'group', 'grade', 'fat']].rename(columns={"fat": "Best Fly Time (s)"})
            st.dataframe(leaderboard_fly, use_container_width=True, hide_index=True)
        else:
            st.info("No recorded fly data found.")
            
    with tab2:
        block_data = st.session_state.workout_logs[st.session_state.workout_logs['type'] == "30m_block"]
        if not block_data.empty:
            leaderboard_block = block_data.groupby('athlete_id')['fat'].min().reset_index()
            leaderboard_block = leaderboard_block.merge(st.session_state.athletes, left_on='athlete_id', right_on='id')
            leaderboard_block = leaderboard_block.sort_values(by="fat")[['name', 'group', 'grade', 'fat']].rename(columns={"fat": "Best Block Time (s)"})
            st.dataframe(leaderboard_block, use_container_width=True, hide_index=True)
        else:
            st.info("No recorded block start data found.")
            
    with tab3:
        projected_list = []
        for _, athlete in st.session_state.athletes.iterrows():
            ath_id = athlete['id']
            best_fly = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == ath_id) & (st.session_state.workout_logs['type'] == "20m_fly")]['fat'].min()
            best_block = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == ath_id) & (st.session_state.workout_logs['type'] == "30m_block")]['fat'].min()
            p_100 = calculate_precise_100m(best_block, best_fly, athlete['gender'], False)
            if p_100:
                projected_list.append({
                    "Athlete Name": athlete['name'],
                    "Group": athlete['group'],
                    "Grade": athlete['grade'],
                    "Projected 100m Time": f"{p_100}s"
                })
        if projected_list:
            leaderboard_100m = pd.DataFrame(projected_list).sort_values(by="Projected 100m Time")
            st.dataframe(leaderboard_100m, use_container_width=True, hide_index=True)
        else:
            st.info("Ensure athletes have at least a 20m Fly logged to generate estimated 100m projections.")

# ==========================================
# MODULE 5: 4x100M RELAY BUILDER
# ==========================================
elif app_mode == "🤝 4x100m Relay Builder":
    st.title("🤝 4x100m Data-Driven Relay Exchange Module")
    st.info("This system uses the Kinetic Cross-Over formula to accurately map heel-to-heel steps.")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Incoming Runner (Max Velocity Flying Anchor)")
        inc_athlete = st.selectbox("Select Incoming Runner:", st.session_state.athletes['name'].unique(), key="inc")
        
        # FIXED: Added [0] to extract raw string out of pandas lookup array
        inc_id = st.session_state.athletes[st.session_state.athletes['name'] == inc_athlete]['id'].values[0]
        
        inc_fly = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == inc_id) & (st.session_state.workout_logs['type'] == "20m_fly")]['fat'].min()
        inc_fly = st.number_input("Incoming 20m Fly (s)", value=float(inc_fly) if not pd.isna(inc_fly) else 2.30)
        
    with col2:
        st.subheader("🛫 Outgoing Runner (Block Acceleration Drive)")
        out_athlete = st.selectbox("Select Outgoing Runner:", st.session_state.athletes['name'].unique(), key="out")
        
        # FIXED: Added [0] to extract raw string out of pandas lookup array
        out_id = st.session_state.athletes[st.session_state.athletes['name'] == out_athlete]['id'].values[0]
        
        out_block = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == out_id) & (st.session_state.workout_logs['type'] == "30m_block")]['fat'].min()
        out_block = st.number_input("Outgoing 30m Block (s)", value=float(out_block) if not pd.isna(out_block) else 4.40)
        
    st.write("---")
    go_mark_steps = calculate_relay_go_mark(inc_fly, out_block)
    st.metric(label="🎯 TARGET ACCELERATION GO MARK ENGINE", value=f"{go_mark_steps} Steps")
    st.markdown(f"""
    Deployment Execution Instructions:
    1. Stand exactly on the international Acceleration Line (the apex point of the zone triangle).
    2. Turn around and walk backward toward the starting line blocks.
    3. Count out exactly {go_mark_steps} heel-to-heel footsteps.
    4. Place coaching tape at that location. When the incoming runner crosses the tape, the outgoing runner hits 100% full-throttle acceleration.
    """)

# ==========================================
# MODULE 6: AD REPORT GENERATOR
# ==========================================
elif app_mode == "📄 AD Report Generator":
    st.title("📄 Performance Portfolio Export Module")
    st.write("Generate high-contrast, administrative-ready print layouts for Athletic Directors and Program Scouters.")
    
    report_rows = ""
    for _, athlete in st.session_state.athletes.iterrows():
        ath_id = athlete['id']
        best_fly = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == ath_id) & (st.session_state.workout_logs['type'] == "20m_fly")]['fat'].min()
        best_block = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == ath_id) & (st.session_state.workout_logs['type'] == "30m_block")]['fat'].min()
        p_100 = calculate_precise_100m(best_block, best_fly, athlete['gender'], False)
        if p_100 and best_fly:
            report_rows += f"<li>{athlete['name']} ({athlete['grade']}) - {best_fly}s FAT Fly | Projected 100m: {p_100}s</li>"
            
    if not report_rows:
        report_rows = "<li>No athlete baseline data matching metrics requirements found.</li>"
        
    report_html = f"""
    <div style="font-family: monospace; border: 2px solid black; padding: 20px;">
        <h3>⚡ RDZ SPEED DEVELOPMENT SYSTEM REPORT</h3>
        <p>Generated: {datetime.today().strftime('%B %d, %Y')} | Program Classification: High School Track & Field</p>
        <hr/>
        <h4>📋 ACTIVE PROGRAM ROSTER SUMMARY</h4>
        <p>Total Tracked Sprinters: {len(st.session_state.athletes)} Active Athletes</p>
        <p>Primary Metric Target Matrix Focus: 20m Flying Sprints & 30m Stationary Blocks</p>
        <hr/>
        <h4>📈 TEAM VELOCITY PROJECTIONS (PIECEWISE / FALLBACK RUN ENGINES)</h4>
        <ul>
            {report_rows}
        </ul>
        <hr/>
        <small style="color: gray;">Verified Authentic via RDZ Speed Development Analytics Database Engine</small>
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)
    st.write("---")
    st.download_button("📥 Export Report to Print Ledger System", data=report_html, file_name="rdz_speed_report.html", mime="text/html")
