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

# Initialize deep session state caches tracking your structural database schema tables
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
        {"log_id": "L3", "workout_id": "W5", "athlete_id": "UUID_A4", "type": "20m_fly", "raw_input_time": 2.15, "normalized_fat_time": 2.15, "projected_100m": 11.75, "is_pr": True, "date": "2026-06-25"},
        {"log_id": "L4", "workout_id": "W5", "athlete_id": "UUID_A7", "type": "20m_fly", "raw_input_time": 2.32, "normalized_fat_time": 2.32, "projected_100m": 12.55, "is_pr": True, "date": "2026-06-25"}
    ])

# Global options state for available sub-rosters
if "training_groups" not in st.session_state:
    st.session_state.training_groups = ["Short Sprinters", "Long Sprinters", "Hurdlers", "Throwers", "Distance", "Hurt/Injured"]

if "active_session_logs" not in st.session_state: st.session_state.active_session_logs = []
if "keypad_buffer" not in st.session_state: st.session_state.keypad_buffer = ""
if "active_athlete_input_id" not in st.session_state: st.session_state.active_athlete_input_id = None

# Inject high-contrast styles
timing_method = st.sidebar.radio("⚙️ Global Timing Input Method:", ["Freelap/FAT", "Hand-Timed"], index=0)
is_hand = timing_method == "Hand-Timed"
bg_color = "#fff3cd" if is_hand else "#ffffff"
border_color = "#ffc107" if is_hand else "#ff4b4b"

st.markdown(f"""
<style>
    .reportview-container, .main .block-container {{ background-color: {bg_color}; }}
    .metric-card {{ background-color: #f8f9fa; border-radius: 10px; padding: 15px; border-left: 5px solid {border_color}; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .badge-top-speed {{ background-color: #f1c40f; color: black; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px;}}
    .badge-tag-varsity {{ background-color: #4a90e2; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px; }}
    .badge-tag-group {{ background-color: #9013fe; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; display: inline-block; margin-right: 5px; }}
    .print-document {{ background-color: white !important; color: black !important; font-family: 'Courier New', Courier, monospace !important; padding: 25px; border: 2px solid black; }}
</style>
""", unsafe_allow_html=True)

def get_best_historical_fat(athlete_id, run_type="20m_fly"):
    logs = st.session_state.workout_logs[(st.session_state.workout_logs["athlete_id"] == athlete_id) & (st.session_state.workout_logs["type"] == run_type)]
    if logs.empty: return float('inf')
    return logs["normalized_fat_time"].min()

def project_100m_dash(fat_time, gender):
    if not fat_time or fat_time == 0: return 0.0
    return round((fat_time + (7.0 * (fat_time / 2.0))) + (0.12 if gender == "male" else 0.15), 2)

# Navigation Controller Layout
st.sidebar.title("⚡ RDZ Navigation")
app_portal = st.sidebar.radio("Go To Module Portal:", [
    "👥 Roster & Onboarding Hub", 
    "⏱️ Live Session Dashboard", 
    "🏆 Team Leaderboards", 
    "📈 Athlete Progress Trends", 
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
                        st.session_state.pending_registrations = pd.concat([st.session_state.pending_registrations, pd.DataFrame([{
                            "first_name": s_first, "last_name": s_last, "gender": s_gender, "graduation_year": s_grad, "grade": calc_grade
                        }])], ignore_index=True)
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
                    st.session_state.athletes = pd.concat([st.session_state.athletes, pd.DataFrame([{
                        "athlete_id": next_id, "first_name": p["first_name"], "last_name": p["last_name"],
                        "gender": p["gender"], "grade": p["grade"], "status": "varsity", "group": "Short Sprinters"
                    }])], ignore_index=True)
                st.session_state.pending_registrations = pd.DataFrame(columns=["first_name", "last_name", "gender", "graduation_year", "grade"])
                st.success("Roster updated successfully without typing inputs!")
                st.rerun()
        else:
            st.info("No pending requests to verify.")
            
        st.markdown("---")
        st.subheader("⚙️ ROSTER ACTIONS & DATA TOOLS")
        act_col1, act_col2, act_col3 = st.columns(3)
        
        with act_col1:
            st.markdown("**A. CSV/Excel Bulk Import Engine**")
            uploaded_file = st.file_uploader("Drag and drop standard roster spreadsheets (Columns: first_name, last_name, gender, grade, status, group)", type=["csv"])
            if uploaded_file is not None:
                try:
                    imported_df = pd.read_csv(uploaded_file)
                    required_cols = ["first_name", "last_name", "gender", "grade", "status", "group"]
                    if all(col in imported_df.columns for col in required_cols):
                        imported_df["athlete_id"] = [f"UUID_A{len(st.session_state.athletes) + i + 1}" for i in range(len(imported_df))]
                        st.session_state.athletes = pd.concat([st.session_state.athletes, imported_df[required_cols + ["athlete_id"]]], ignore_index=True)
st.success(f"Successfully appended {len(imported_df)} roster profiles via bulk data mapper link!")
st.rerun()
else: st.error(f"Spreadsheet must strictly match schemas headers: {required_cols}")
except Exception as e: st.error(f"Data stream fault: {str(e)}")
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
# Archive or filter out Grade 12 seniors (Graduated alumni)
active_undergrads = st.session_state.athletes[st.session_state.athletes["grade"] < 12].copy()
# Advance remaining grades by 1 year
active_undergrads["grade"] = active_undergrads["grade"] + 1
st.session_state.athletes = active_undergrads.reset_index(drop=True)
st.success("Rollover processing finalized! Database adjusted, clean, and optimized for the next track year sequence.")
st.rerun()
# Display Control Center Matrix Core Rows
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



👤 {row['last_name']}, {row['first_name']} (Grade {row['grade']})
• Best Season 20m Fly Metric parameter: {best_fly_str}


{row['status'].upper()}
{row['group'].upper()}



""", unsafe_allow_html=True)
m_c1, m_c2 = st.columns(2)
with m_c1: new_g = st.selectbox("➡️ Move to Group...", st.session_state.training_groups, index=st.session_state.training_groups.index(row["group"]) if row["group"] in st.session_state.training_groups else 0, key=f"sel_{a_id}")
with m_c2:
if st.button("Commit Group Move", key=f"mov_btn_{a_id}"):
st.session_state.athletes.loc[st.session_state.athletes["athlete_id"] == a_id, "group"] = new_g
st.success(f"Shifted group alignment parameters for {row['first_name']}")
st.rerun()
==========================================
MODULE 2: LIVE SESSION DASHBOARD (WITH DYNAMIC SUB-ROSTER FILTERING)
==========================================
elif app_portal == "⏱️ Live Session Dashboard":
st.title("⏱️ Live Session Tracker")
# B. Dynamic "Training Groups" Sub-Roster Filter Integration
st.markdown("#### 🎯 Filter Active Lane Lines By Event Group Assignment")
active_group_filter = st.selectbox("Select Active Group At Sprints Line:", ["All Active Roster"] + st.session_state.training_groups)
col_h1, col_h2 = st.columns(2)
with col_h1: st.subheader("🗓️ CURRENT WORKOUT: Max Velocity Flys")
with col_h2:
if st.button("🔴 END ACTIVE SESSION", use_container_width=True):
if st.session_state.active_session_logs:
st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame(st.session_state.active_session_logs)], ignore_index=True)
st.session_state.active_session_logs = []
st.success("Session saved successfully!")
else: st.warning("No runs logged yet.")
search_query = st.text_input("🔍 Quick Search Athlete...", "").strip().lower()
# Filter working data subset based on coach parameters selection
roster_working_subset = st.session_state.athletes.copy()
if active_group_filter != "All Active Roster":
roster_working_subset = roster_working_subset[roster_working_subset["group"] == active_group_filter]
st.caption(f"Showing {len(roster_working_subset)} athletes standing at the sprint line.")
for _, athlete in roster_working_subset.iterrows():
full_name = f"{athlete['first_name']} {athlete['last_name']}"
if search_query and search_query not in full_name.lower(): continue
a_id = athlete["athlete_id"]
past_logs = st.session_state.workout_logs[st.session_state.workout_logs["athlete_id"] == a_id]
last_time_str = f"{past_logs.iloc[-1]['raw_input_time']:.2f}s" if not past_logs.empty else "N/A"
r_col1, r_col2 = st.columns(2)
with r_col1: st.markdown(f"👤 {athlete['last_name']}, {athlete['first_name']} [Last Run: {last_time_str}]")
with r_col2:
if st.button(f"Enter Time", key=f"btn_{a_id}", use_container_width=True):
st.session_state.active_athlete_input_id = a_id
st.session_state.keypad_buffer = ""
st.rerun()
# Smart Keypad Interceptor Panel
if st.session_state.active_athlete_input_id:
target_id = st.session_state.active_athlete_input_id
ath_info = st.session_state.athletes[st.session_state.athletes["athlete_id"] == target_id].iloc
st.markdown(f"### 🎛️ Smart Keypad: {ath_info['first_name']} {ath_info['last_name']}")
k_col1, k_col2 = st.columns([2, 1.2])
with k_col1:
row1 = st.columns(3); row2 = st.columns(3); row3 = st.columns(3); row4 = st.columns(3)
if row1.button("1", key="k1", use_container_width=True): st.session_state.keypad_buffer += "1"; st.rerun()
if row1.button("2", key="k2", use_container_width=True): st.session_state.keypad_buffer += "2"; st.rerun()
if row1.button("3", key="k3", use_container_width=True): st.session_state.keypad_buffer += "3"; st.rerun()
if row2.button("4", key="k4", use_container_width=True): st.session_state.keypad_buffer += "4"; st.rerun()
if row2.button("5", key="k5", use_container_width=True): st.session_state.keypad_buffer += "5"; st.rerun()
if row2.button("6", key="k6", use_container_width=True): st.session_state.keypad_buffer += "6"; st.rerun()
if row3.button("7", key="k7", use_container_width=True): st.session_state.keypad_buffer += "7"; st.rerun()
if row3.button("8", key="k8", use_container_width=True): st.session_state.keypad_buffer += "8"; st.rerun()
if row3.button("9", key="k9", use_container_width=True): st.session_state.keypad_buffer += "9"; st.rerun()
if row4.button(".", key="k_dot", use_container_width=True): st.session_state.keypad_buffer += "."; st.rerun()
if row4.button("0", key="k0", use_container_width=True): st.session_state.keypad_buffer += "0"; st.rerun()
if row4.button("⌫ Clear", key="k_clear", use_container_width=True): st.session_state.keypad_buffer = ""; st.rerun()
with k_col2:
raw_buffer = st.session_state.keypad_buffer
if len(raw_buffer) == 3 and "." not in raw_buffer: raw_buffer = f"{raw_buffer}.{raw_buffer[1:]}"
st.markdown(f"#### Typed Input: {raw_buffer}")
try:
val_input = float(raw_buffer)
norm_fat = round(val_input + 0.15, 2) if is_hand else round(val_input, 2)
st.write(f"📊 FAT Converted Standard: {norm_fat:.2f}s FAT")
if st.button("🎯 COMMIT & OK", use_container_width=True, type="primary"):
st.session_state.active_session_logs.append({
"log_id": f"LOG_L{len(st.session_state.workout_logs)+1}",
"workout_id": "WORKOUT_ACTIVE", "athlete_id": target_id, "type": "20m_fly",
"raw_input_time": val_input, "normalized_fat_time": norm_fat,
"projected_100m": project_100m_dash(norm_fat, ath_info["gender"]),
"is_pr": norm_fat < get_best_historical_fat(target_id),
"date": datetime.today().strftime('%Y-%m-%d'), "display_name": f"{ath_info['first_name']} {ath_info['last_name']}"
})
st.session_state.active_athlete_input_id = None; st.session_state.keypad_buffer = ""; st.rerun()
except ValueError: st.caption("Awaiting completed numbers...")
==========================================
MODULE 3: TEAM LEADERBOARDS
==========================================
elif app_portal == "🏆 Team Leaderboards":
st.title("🔥 Team Leaderboards (The Engagement Engine)")
seg_filter = st.radio("Segment Filter:", ["⚡ 20m Fly Rankings", "⏱️ Projected 100m"], horizontal=True)
if not st.session_state.workout_logs.empty:
merged_rank = pd.merge(st.session_state.workout_logs, st.session_state.athletes, on="athlete_id")
idx_bests = merged_rank.groupby("athlete_id")["normalized_fat_time"].idxmin()
leaderboard_df = merged_rank.loc[idx_bests].sort_values(by="normalized_fat_time").reset_index(drop=True)
for rank_idx, row in leaderboard_df.iterrows():
medal = "🥇" if rank_idx == 0 else ("🥈" if rank_idx == 1 else ("🥉" if rank_idx == 2 else "👤"))
score = f"{row['normalized_fat_time']:.2f}s FAT" if seg_filter == "⚡ 20m Fly Rankings" else f"{row['projected_100m']:.2f}s (Proj 100m)"
st.markdown(f"{medal} {rank_idx+1}. {row['first_name']} {row['last_name']} (Grade {row['grade']}) {score}", unsafe_allow_html=True)
==========================================
MODULE 4: ATHLETE PROGRESS TRENDS
==========================================
elif app_portal == "📈 Athlete Progress Trends":
st.title("📈 Individual Deep-Dive Progression Curve")
athlete_options = {f"{row['first_name']} {row['last_name']}": row['athlete_id'] for _, row in st.session_state.athletes.iterrows()}
selected_display = st.selectbox("🔍 Profile Selection:", list(athlete_options.keys()))
target_athlete_id = athlete_options[selected_display]
raw_logs = st.session_state.workout_logs[st.session_state.workout_logs["athlete_id"] == target_athlete_id].copy()
if not raw_logs.empty:
raw_logs["date_parsed"] = pd.to_datetime(raw_logs["date"])
raw_logs["training_week"] = raw_logs["date_parsed"].dt.isocalendar().week
filtered_progress = raw_logs.loc[raw_logs.groupby("training_week")["normalized_fat_time"].idxmin()].sort_values(by="date")
fig_deep = px.line(filtered_progress, x="date", y="normalized_fat_time", markers=True)
fig_deep.update_yaxes(autorange="reverse")
st.plotly_chart(fig_deep, use_container_width=True)
==========================================
MODULE 5: PDF REPORT GENERATOR
==========================================
elif app_portal == "📄 AD Report Export":
st.title("📄 Athletic Director Executive Export")
roster_rows_html = ""
for _, athlete in st.session_state.athletes.iterrows():
a_id = athlete["athlete_id"]
a_logs = st.session_state.workout_logs[(st.session_state.workout_logs["athlete_id"] == a_id) & (st.session_state.workout_logs["type"] == "20m_fly")]
if not a_logs.empty:
baseline = a_logs["normalized_fat_time"].iloc[0]
current_pr = a_logs["normalized_fat_time"].min()
net_delta = current_pr - baseline
proj_100 = project_100m_dash(current_pr, athlete["gender"])
state_star = "*" if proj_100 <= 11.00 else ""
roster_rows_html += f"{athlete['last_name']}, {athlete['first_name']}{baseline:.2f}s FAT{current_pr:.2f}s FAT{net_delta:+.2f}s{proj_100:.2f}s {state_star}"
st.markdown(f"""


⚡ NORTHSIDE TRACK & FIELD — 2026 SEASON SPEED REPORT
Report Generated: {datetime.today().strftime('%B %d, %Y')} | Head Coach: John Doe


[ SQUAD OVERVIEW: VARSITY BOYS ]
Total Athletes Tracked: {len(st.session_state.athletes)} active roster profiles


📊 PERFORMANCE ROSTER & 100M PROJECTED RANKINGS


📄 Verified by RDZ Speed Intelligence System — Verification Code: AUTH-SECURE-2026


""", unsafe_allow_html=True)





