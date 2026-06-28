import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# SOURCE OF TRUTH: KINEMATIC ENGINE
# ==========================================
def get_unified_projection(session_type, fat_time, block_val, fly_val, gender):
    """
    Unified projection model:
    Primary: 30m Block + (3.5 * 20m Fly) + C
    Fallback: (20m Fly / 2 * 10) + Gender Constant
    """
    is_female = 'female' in str(gender).lower()
    f_val = fly_val if (fly_val and fly_val > 0) else fat_time
    b_val = block_val if (block_val and block_val > 0) else None
    
    if b_val is not None:
        base_proj = b_val + (3.5 * f_val)
        c = (0.15 if base_proj < 12.2 else 0.25) if is_female else (0.12 if base_proj < 11.0 else 0.18)
        return round(b_val + (3.5 * f_val) + c, 2)
    
    else:
        gender_const = 1.15 if is_female else 1.05 
        projection = (f_val / 2 * 10) + gender_const
        return round(projection, 2)

def get_go_mark_logic(f, b, gen):
    # Differential Gap Formula: [(20/Fly * (Start * 0.71)) - 20m - 0.70m] * 3.28
    steps = (((20 / (f if f != 99.0 else 2.20)) * ((b if b != 99.0 else 4.20) * 0.71)) - 20 - 0.70) * 3.28
    raw = int(round(steps))
    if 'female' in str(gen).lower():
        tier = "Varsity" if (15 <= raw <= 22) else "Developing"
    else:
        tier = "Varsity" if (19 <= raw <= 26) else "Developing"
    return raw, tier

# ==========================================
# INITIALIZATION & STATE
# ==========================================
def init_app():
    if 'athletes' not in st.session_state:
        try:
            st.session_state.athletes = pd.read_csv("roster_storage.csv")
        except:
            st.session_state.athletes = pd.DataFrame(columns=["id", "name", "gender", "grade", "group", "tier", "status"])
    if 'workout_logs' not in st.session_state:
        try:
            st.session_state.workout_logs = pd.read_csv("workout_logs_storage.csv")
        except:
            st.session_state.workout_logs = pd.DataFrame(columns=["date", "athlete_id", "type", "fat", "proj_100"])

init_app()

# ==========================================
# NAVIGATION
# ==========================================
st.sidebar.title("⚡ RDZ Speed Intelligence")
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
# CORE MODULES GATEWAY
# ==========================================

# ==========================================
# MODULE 1: ROSTER & ONBOARDING HUB
# ==========================================
if app_portal == "👥 Roster & Onboarding Hub":
    st.title("👥 Roster & Onboarding Hub")
st.subheader("➕ Onboard New Athlete")
with st.form("add_athlete"):
    c1, c2 = st.columns(2)
    name = c1.text_input("Full Name")
    gender = c2.selectbox("Gender", ["Male", "Female"])
    
    c3, c4 = st.columns(2)
    grade = c3.selectbox("Grade Level", [7, 8, 9, 10, 11, 12])
    group = c4.selectbox("Training Group", ["Sprints", "Distance", "Multi-Events", "Jumps"])
    
    submitted = st.form_submit_button("Add to Roster")
    if submitted and name:
        new_row = {
            "id": str(len(st.session_state.athletes) + 1),
            "name": name,
            "gender": gender,
            "grade": grade,
            "group": group,
            "tier": "Varsity", # Default
            "status": "Active"
        }
        st.session_state.athletes = pd.concat([st.session_state.athletes, pd.DataFrame([new_row])], ignore_index=True)
        st.success(f"Added {name}!")

st.write("---")
st.subheader("📋 Current Team Roster")

# Roster Management Table
if not st.session_state.athletes.empty:
    roster = st.session_state.athletes.copy()
    
    # Interface to Toggle/Remove
    for idx, row in roster.iterrows():
        cols = st.columns([3, 2, 2, 1])
        cols[0].write(f"**{row['name']}** (Gr: {row['grade']})")
        
        # Toggle Active Status
        is_active = cols[1].toggle("Active", value=(row['status'] == 'Active'), key=f"toggle_{idx}")
        st.session_state.athletes.at[idx, 'status'] = 'Active' if is_active else 'Inactive'
        
        # Removal Option
        if cols[3].button("🗑️", key=f"del_{idx}"):
            st.session_state.athletes = st.session_state.athletes.drop(idx)
            st.rerun()
else:
    st.info("No athletes onboarded yet.")
    
# 2. Workout Module
elif app_portal == "⏱️ Workout Tracker":
    st.title("⏱️ Unified Workout Hub")
    # [PASTE WORKOUT TRACKER CODE HERE]

# 3. Live Dashboard
elif app_portal == "📆 Live Session Dashboard":
    st.title("📆 Today's Live Session Dashboard")
    # [PASTE LIVE SESSION CODE HERE]

# ==========================================
# MODULE 4: RELAY OPTIMIZER POOL
# ==========================================
elif app_portal == "🤝 Relay Optimizer Pool": 
    st.title("🏆 Data-Optimized 4x100m Relay Builder")
    
    # 1. Gender and Active Status Filter
    gender_choice = st.radio("Select Division:", ["Male", "Female"], horizontal=True)
    # Filter: Only Active athletes of the chosen gender
    active_pool = st.session_state.athletes[
        (st.session_state.athletes['status'] == 'Active') & 
        (st.session_state.athletes['gender'] == gender_choice)
    ]
    
    if len(active_pool) < 4:
        st.warning(f"⚠️ Need 4+ Active {gender_choice} athletes to optimize.")
    else:
        # 2. Metric Collection
        logs = st.session_state.workout_logs
        metrics = []
        for _, ath in active_pool.iterrows():
            a_id = str(ath['id'])
            # Fetch bests for this specific athlete
            fly = logs[(logs['athlete_id'] == a_id) & (logs['type'] == '20m_fly')]['fat'].min()
            block = logs[(logs['athlete_id'] == a_id) & (logs['type'] == '30m_block')]['fat'].min()
            metrics.append({
                "name": ath['name'], 
                "fly": fly if pd.notna(fly) else 99.0, 
                "block": block if pd.notna(block) else 99.0
            })
        
        rdf = pd.DataFrame(metrics)
        
        # 3. Suggestion Engine (Best 4 automatically)
        s_leg1 = rdf.sort_values(by='block').iloc[0]
        rem = rdf[rdf['name'] != s_leg1['name']].sort_values(by='fly')
        s_leg2, s_leg3, s_leg4 = rem.iloc[0], rem.iloc[1], rem.iloc[2]
        
        # 4. Manual Overrides (Dropdowns)
        st.subheader("Manual Lineup Override")
        c1, c2, c3, c4 = st.columns(4)
        names = rdf['name'].tolist()
        l1 = c1.selectbox("Leg 1", names, index=names.index(s_leg1['name']))
        l2 = c2.selectbox("Leg 2", names, index=names.index(s_leg2['name']))
        l3 = c3.selectbox("Leg 3", names, index=names.index(s_leg3['name']))
        l4 = c4.selectbox("Leg 4", names, index=names.index(s_leg4['name']))
        
        # 5. Calculation Logic (Bridge to the Go-Mark formula)
        if st.button("Calculate Best Go-Marks"):
            run_map = {m['name']: m for m in metrics}
            
            # Using the restored Go-Mark physics
            m12, _ = get_go_mark_logic(run_map[l1]['fly'], run_map[l2]['block'], gender_choice)
            m23, _ = get_go_mark_logic(run_map[l2]['fly'], run_map[l3]['block'], gender_choice)
            m34, _ = get_go_mark_logic(run_map[l3]['fly'], run_map[l4]['block'], gender_choice)
            
            # Save to state for PDF export later
            st.session_state['relay_go_marks'] = {'1to2': m12, '2to3': m23, '3to4': m34}
            st.success(f"Success! Marks: Ex1={m12} steps, Ex2={m23} steps, Ex3={m34} steps")

        # 6. PDF Export Placeholder
        if st.button("Export Lineup PDF"):
            st.info("Triggering PDF generation (Ensure PDF generation logic is linked here).")

# 5. Trends
elif app_portal == "📈 Athlete Progress Trends":
    st.title("📈 The Athlete Progress Screen")
    # [PASTE PROGRESS TRENDS CODE HERE]

# 6. Leaderboard
elif app_portal == "🏆 Team Leaderboards":
    st.title("🔥 Team Leaderboards")
    # [PASTE LEADERBOARD CODE HERE]

# 7. AD Report
elif app_portal == "📄 AD Report Export":
    st.title("📄 Executive AD Report Generator")
    # [PASTE AD REPORT CODE HERE]

# ==========================================
# FOOTER / PERSISTENCE
# ==========================================
if st.sidebar.button("Save All Data"):
    st.session_state.athletes.to_csv("roster_storage.csv", index=False)
    st.session_state.workout_logs.to_csv("workout_logs_storage.csv", index=False)
    st.sidebar.success("Data saved successfully!")
