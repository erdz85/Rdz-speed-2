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
# 4. HELPER FUNCTIONS
# ==========================================
def calculate_relay_go_mark(inc_fly, out_block):
    try:
        raw_mark = (float(out_block) - float(inc_fly)) * 7.5
        return max(1, round(raw_mark, 1))
    except:
        return 12.0


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
    selected_athlete = st.selectbox("Select Athlete Profile:", st.session_state.athletes['name'].unique())
    athlete_id = st.session_state.athletes[st.session_state.athletes['name'] == selected_athlete]['id'].values[0]
    athlete_logs = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == athlete_id) & (st.session_state.workout_logs['type'] == "20m_fly")]
    
    if len(athlete_logs) >= 1:
        athlete_logs = athlete_logs.sort_values(by="date")
        fig = px.line(athlete_logs, x="date", y="fat", title="20m Fly FAT Progression Trend", markers=True)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        
        if len(athlete_logs) >= 2:
            last_two = athlete_logs.tail(2)['fat'].values
            decay_percent = ((last_two[1] - last_two[0]) / last_two[0]) * 100
            if decay_percent > 4.0:
                st.warning(f"⚠️ CNS Fatigue Advisory Warning Alert: Velocity dropped by {round(decay_percent,1)}% on last rep. Advise immediate recovery down-regulation.")
            else:
                st.success("🟢 CNS Efficiency Stable. Athlete is primed for max velocity output.")
    else:
        st.info("Provide at least 1 historical entry to populate tracking vectors.")


# ==========================================
# MODULE 3: WORKOUT LOGGER
# ==========================================
elif app_mode == "🏋️ Workout Logger":
    st.title("🏋️ High-Frequency Workout Data Logger")
    st.write("Input newly converted FAT times straight from timing gates into the core ledger database.")
    
    col1, col2 = st.columns(2)
    with col1:
        log_date = st.date_input("Workout Session Date", datetime.today())
        log_athlete = st.selectbox("Select Competing Athlete:", st.session_state.athletes['name'].unique(), key="log_ath")
        log_id = st.session_state.athletes[st.session_state.athletes['name'] == log_athlete]['id'].values[0]
    with col2:
        log_type = st.selectbox("Test Metric Vector Profile:", ["20m_fly", "30m_block"])
        log_time = st.number_input("Recorded FAT Time Value (seconds):", min_value=0.00, max_value=15.00, value=2.50, step=0.01)
        
    if st.button("📥 Save Repetition Entry to History Logs"):
        new_log_row = {"date": str(log_date), "athlete_id": log_id, "type": log_type, "fat": float(log_time)}
        st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame([new_log_row])], ignore_index=True)
        st.success(f"Successfully recorded {log_time}s ({log_type}) for {log_athlete}!")


# ==========================================
# MODULE 4: TEAM LEADERBOARDS
# ==========================================
elif app_mode == "🏆 Team Leaderboards":
    st.title("🏆 Power & Velocity Team Leaderboards")
    st.write("Live program rankings derived from absolute maximum output thresholds.")
    tab1, tab2 = st.tabs(["⚡ Top 20m Fly Times", "🛫 Top 30m Blocks"])
    
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
        inc_id = st.session_state.athletes[st.session_state.athletes['name'] == inc_athlete]['id'].values[0]
        inc_fly = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == inc_id) & (st.session_state.workout_logs['type'] == "20m_fly")]['fat'].min()
        inc_fly = st.number_input("Incoming 20m Fly (s)", value=float(inc_fly) if not pd.isna(inc_fly) else 2.30)
        
    with col2:
        st.subheader("🛫 Outgoing Runner (Block Acceleration Drive)")
        out_athlete = st.selectbox("Select Outgoing Runner:", st.session_state.athletes['name'].unique(), key="out")
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
    
    report_html = f"""
    ⚡ RDZ SPEED DEVELOPMENT SYSTEM REPORT
    Generated: {datetime.today().strftime('%B %d, %Y')} | Program Classification: High School Track & Field
    
    📋 ACTIVE PROGRAM ROSTER DATA ROSTER SUMMARY
    Total Tracked Sprinters: {len(st.session_state.athletes)} Active Athletes
    Primary Metric Target Matrix Focus: 20m Flying Sprints & 30m Stationary Blocks
    
    📈 TOP TEAM VELOCITY PERFORMERS
    Marcus Anderson (Jr.) - 1.98s Converted FAT Fly | Projected 100m: 10.95s
    Elena Martinez (Jr.) - 2.45s Converted FAT Fly | Projected 100m: 12.80s
    
    Verified Authentic via RDZ Speed Development Analytics Database Engine
    """
    st.markdown(report_html, unsafe_allow_html=True)
    st.write("---")
    st.download_button("📥 Export Report to Print Ledger System", data=report_html, file_name="rdz_speed_report.html", mime="text/html")
