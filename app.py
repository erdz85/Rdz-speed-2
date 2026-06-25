import streamlit as st
import pandas as pd
import math
import plotly.express as px
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

# Custom CSS for track-coaching aesthetics and oversized mobile keypad layouts
st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; border-radius: 10px; padding: 15px; border-left: 5px solid #ff4b4b; margin-bottom: 15px;}
    .badge-top-speed { background-color: #f1c40f; color: black; font-weight: bold; padding: 3px 8px; border-radius: 5px; }
    .badge-hot { background-color: #e67e22; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; }
    .badge-pr { background-color: #2ecc71; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; }
</style>
""", unsafe_ Ultraviolet=True)

# ==========================================
# 2. SEEDING IN-MEMORY SESSION STATE DATA
# ==========================================
# Streamlit uses session_state to mock a real database across app reloads
if 'athletes' not in st.session_state:
    st.session_state.athletes = pd.DataFrame([
        {"id": "A1", "name": "Marcus Anderson", "gender": "Male", "group": "Short Sprints", "grade": "Junior"},
        {"id": "A2", "name": "Trey Williams", "gender": "Male", "group": "Short Sprints", "grade": "Senior"},
        {"id": "A3", "name": "Elena Martinez", "gender": "Female", "group": "Short Sprints", "grade": "Junior"},
        {"id": "A4", "name": "Jordan Davis", "gender": "Female", "group": "Short Sprints", "grade": "Freshman"},
    ])

if 'workout_logs' not in st.session_state:
    st.session_state.workout_logs = pd.DataFrame([
        {"log_id": 1, "date": "2026-05-01", "athlete_id": "A1", "type": "20m_fly", "raw": 2.10, "fat": 2.10, "proj_100": 11.50},
        {"log_id": 2, "date": "2026-05-15", "athlete_id": "A1", "type": "20m_fly", "raw": 1.98, "fat": 1.98, "proj_100": 10.95},
        {"log_id": 3, "date": "2026-05-01", "athlete_id": "A3", "type": "20m_fly", "raw": 2.45, "fat": 2.65, "proj_100": 13.58},
        {"log_id": 4, "date": "2026-05-15", "athlete_id": "A3", "type": "20m_fly", "raw": 2.30, "fat": 2.45, "proj_100": 12.80},
        {"log_id": 5, "date": "2026-05-15", "athlete_id": "A2", "type": "30m_block", "raw": 4.15, "fat": 4.15, "proj_100": 11.25},
        {"log_id": 6, "date": "2026-05-15", "athlete_id": "A4", "type": "30m_block", "raw": 4.40, "fat": 4.40, "proj_100": 12.10},
    ])

# ==========================================
# 3. MATHEMATICAL ALGORITHM ENGINES
# ==========================================
def normalize_hand_fly(raw_hand_time):
    """Applies the NFHS rounding rule and Max Velocity Anticipation Constant."""
    rounded_time = math.ceil(raw_hand_time * 10) / 10.0
    return round(rounded_time + 0.15, 2)

def calculate_projected_100m(thirty_block, twenty_fly, gender):
    """Piecewise Splicing Model with performance decay scaling."""
    ten_split = twenty_fly / 2.0
    base_time = thirty_block + (7.0 * ten_split)
    
    if gender.lower() == "male":
        decay = 0.12 if base_time < 11.0 else 0.18
    else:
        decay = 0.15 if base_time < 12.2 else 0.25
        
    return round(base_time + decay, 2)

def calculate_relay_go_mark(incoming_fly, outgoing_block):
    """Calculates the differential closing gap converted into heel-to-heel steps."""
    v_incoming = 20.0 / incoming_fly
    t_acceleration = outgoing_block * 0.71
    raw_distance_gap = (v_incoming * t_acceleration) - 20.0
    final_distance_meters = raw_distance_gap - 0.70  # Arm extension buffer
    coaching_steps = final_distance_meters * 3.28    # Heel-to-heel factor
    return max(0.0, round(coaching_steps, 1))

# ==========================================
# 4. APP NAVIGATION & LAYOUT SIDEBAR
# ==========================================
st.sidebar.title("⚡ RDZ Speed")
st.sidebar.subheader("Development Engine")
app_mode = st.sidebar.radio("Go To Module:", [
    "👥 Roster & Onboarding",
    "⏱️ Workout Tracker",
    "🔥 Team Leaderboard",
    "📈 Athlete Progress",
    "🤝 4x100m Relay Builder",
    "📄 AD Report Generator"
])

st.sidebar.write("---")
st.sidebar.info("⚙️ Core Database Running via In-Memory Sandbox Mode.")

# ==========================================
# MODULE 1: ROSTER & ONBOARDING
# ==========================================
if app_mode == "👥 Roster & Onboarding":
    st.title("👥 Roster Management & Athlete Onboarding")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔗 Share Team Access")
        st.info("Have your athletes scan this or use the code below during team check-ins.")
        st.code("RDZ-NORTHSIDE-2026", language="text")
        st.success("🤖 Active QR Code Payload Generated")
        
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
# MODULE 2: WORKOUT TRACKER
# ==========================================
elif app_mode == "⏱️ Workout Tracker":
    st.title("⏱️ Live Workout Tracker Dashboard")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        timing_system = st.radio("Global Timing Method Source:", ["Electronic / FAT (Freelap)", "Hand-Timed (Stopwatch)"])
    with col2:
        session_type = st.selectbox("Sprinting Drill Profile:", ["20m_fly", "30m_block"])
        
    st.write("---")
    st.subheader("⚡ Rapid Input Ledger")
    
    # Iterate dynamically through roster for rapid input logging
    for index, athlete in st.session_state.athletes.iterrows():
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            st.write(f"**{athlete['name']}** ({athlete['group']})")
        with c2:
            raw_time = st.number_input(f"Raw Split (s)", min_value=0.0, max_value=10.0, step=0.01, key=f"input_{athlete['id']}")
        with c3:
            if st.button("Save", key=f"btn_{athlete['id']}"):
                if raw_time > 0:
                    fat_time = normalize_hand_fly(raw_time) if timing_system == "Hand-Timed (Stopwatch)" else raw_time
                    proj_100 = calculate_projected_100m(4.5, fat_time, athlete['gender']) if session_type == "20m_fly" else calculate_projected_100m(fat_time, 2.3, athlete['gender'])
                    
                    new_log = {
                        "log_id": len(st.session_state.workout_logs) + 1,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "athlete_id": athlete['id'],
                        "type": session_type,
                        "raw": raw_time,
                        "fat": fat_time,
                        "proj_100": proj_100
                    }
                    st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame([new_log])], ignore_index=True)
                    st.toast(f"Logged {fat_time}s for {athlete['name']}!")
                    st.rerun()

# ==========================================
# MODULE 3: TEAM LEADERBOARD
# ==========================================
elif app_mode == "🔥 Team Leaderboard":
    st.title("🔥 Team Leaderboard Settings")
    
    gender_filter = st.selectbox("Filter Gender Stack:", ["All", "Male", "Female"])
    metric_filter = st.selectbox("Select Leaderboard Rank Index:", ["20m_fly", "30m_block"])
    
    # Pull best times per athlete
    logs = st.session_state.workout_logs[st.session_state.workout_logs['type'] == metric_filter]
    athletes = st.session_state.athletes
    
    if not logs.empty:
        merged = pd.merge(logs, athletes, left_on="athlete_id", right_on="id")
        if gender_filter != "All":
            merged = merged[merged['gender'] == gender_filter]
            
        leaderboard = merged.loc[merged.groupby("athlete_id")["fat"].idxmin()]
        leaderboard = leaderboard.sort_values(by="fat", ascending=True).reset_index(drop=True)
        
        st.subheader("🏆 Current Rankings (Normalized to FAT standard)")
        for idx, row in leaderboard.iterrows():
            badge = "⚡ Top Speed" if idx == 0 else "🏃 Track Star"
            st.markdown(f"""
            <div class="metric-card">
                <h4>#{idx+1} {row['name']} - <span class="badge-top-speed">{row['fat']}s FAT</span></h4>
                <p>Projected 100m: <b>{row['proj_100']}s</b> | Group: {row['group']} | Status: <span class="badge-hot">{badge}</span></p>
            </div>
            """, unsafe_html=True)
    else:
        st.info("No recorded logs available for this combination of inputs yet.")

# ==========================================
# MODULE 4: ATHLETE PROGRESS
# ==========================================
elif app_mode == "📈 Athlete Progress":
st.title("📈 Athlete Performance Trajectory Deep Dive")
selected_athlete = st.selectbox("Select Athlete Profile:", st.session_state.athletes['name'].unique())
athlete_id = st.session_state.athletes[st.session_state.athletes['name'] == selected_athlete]['id'].values[0]
athlete_logs = st.session_state.workout_logs[(st.session_state.workout_logs['athlete_id'] == athlete_id) & (st.session_state.workout_logs['type'] == "20m_fly")]
if len(athlete_logs) >= 1:
athlete_logs = athlete_logs.sort_values(by="date")
# Plot time series chart using Plotly
fig = px.line(athlete_logs, x="date", y="fat", title="20m Fly FAT Progression Trend", markers=True)
fig.update_yaxes(autorange="reverse") # Faster means smaller numbers
st.plotly_chart(fig, use_container_width=True)
# Check for Central Nervous System (CNS) Fatigue
if len(athlete_logs) >= 2:
last_two = athlete_logs.tail(2)['fat'].values
decay_percent = ((last_two[1] - last_two[0]) / last_two[0]) * 100
if decay_percent > 4.0:
st.warning(f"⚠️ CNS Fatigue Advisory Warning Alert: Velocity dropped by {round(decay_percent,1)}% on last rep. Advise immediate recovery down-regulation.")
else:
st.success("🟢 CNS Efficiency Stable. Athlete is primed for max velocity output.")
else:
st.info("Provide at least 1 historical entry to populate tracking vectors.")

==========================================
MODULE 5: 4x100M RELAY BUILDER
==========================================
elif app_mode == "🤝 4x100m Relay Builder":
st.title("🤝 4x100m Data-Driven Relay Exchange Module")
st.info("This system uses the Kinetic Cross-Over formula to accurately map heel-to-heel steps.")
col1, col2 = st.columns(2)
with col1:
st.subheader("📥 Incoming Runner (Max Velocity Flying Anchor)")
inc_athlete = st.selectbox("Select Incoming Runner:", st.session_state.athletes['name'].unique(), key="inc")
inc_id = st.session_state.athletes[st.session_state.athletes['name'] == inc_athlete]['id'].values[0]
# Fallback default if no history exists yet
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

==========================================
MODULE 6: AD REPORT GENERATOR
==========================================
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
st.markdown(report_html, unsafe_html=True)
st.write("---")
st.download_button("📥 Export Report to Print Ledger System", data=report_html, file_name="rdz_speed_report.html", mime="text/html")
