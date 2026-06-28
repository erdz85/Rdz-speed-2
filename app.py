import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# ==========================================
# 0. INITIALIZATION & ENGINE
# ==========================================
st.set_page_config(page_title="RDZ Speed Intelligence", layout="wide")

def get_unified_projection(drill, fat, block, fly, gender):
    """Unified kinematic projection engine."""
    # Logic: 1.05 for males, 1.15 for females
    multiplier = 1.05 if 'female' not in str(gender).lower() else 1.15
    return (fly * multiplier) + 8.20 # Placeholder kinematic formula

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
# GLOBAL NAVIGATION
# ==========================================
st.sidebar.title("⚡ RDZ Navigation")
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
# MODULES 1-7 (Embedded in Portal Logic)
# ==========================================

if app_portal == "👥 Roster & Onboarding Hub":
    st.title("👥 Roster & Onboarding Hub")
    
    st.markdown("Manage your team roster, onboard new athletes, and control active training availability status.")

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
                existing_roster = st.session_state.athletes.copy()
                existing_roster.columns = [str(c).lower() for c in existing_roster.columns]
                
                # Dynamic ID generation
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
                st.session_state.athletes.to_csv("roster_storage.csv", index=False)
                st.success(f"🎉 Onboarded {new_name} successfully as {new_status}!")
                st.rerun()

    st.write("---")

    # --- SECTION 2: ROSTER MANAGEMENT MATRIX ---
    st.subheader("📋 Active Roster Management Table")
    
    if st.session_state.athletes.empty:
        st.info("ℹ️ No athletes currently registered on the roster.")
    else:
        m_roster = st.session_state.athletes.copy()
        # Ensure column consistency
        if 'id' not in m_roster.columns: m_roster.rename(columns={m_roster.columns[0]: 'id'}, inplace=True)

        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 2])
        with h1: st.markdown("🏃 **Athlete Name**")
        with h2: st.markdown("🏷️ **Group / Tier**")
        with h3: st.markdown("⚙️ **Availability Toggle**")
        with h4: st.markdown("📌 **Current Status**")
        with h5: st.markdown("❌ **Remove**")
        st.markdown("<hr style='margin: 0px 0px 15px 0px; border-color: #555;' />", unsafe_allow_html=True)

        for index, row in m_roster.iterrows():
            a_id = str(row['id']).strip()
            a_name = row['name']
            a_group = row['group']
            a_tier = row['tier']
            a_status = row['status']
            
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            with c1: st.markdown(f"**{a_name}**")
            with c2: st.caption(f"{a_group} • {a_tier}")
            with c3:
                toggle_label = "Set Inactive" if a_status == "Active" else "Set Active"
                if st.button(toggle_label, key=f"tog_{a_id}"):
                    st.session_state.athletes.loc[index, 'status'] = "Inactive" if a_status == "Active" else "Active"
                    st.session_state.athletes.to_csv("roster_storage.csv", index=False)
                    st.rerun()
            with c4:
                st.markdown(f"{'🟢 Active' if a_status == 'Active' else '🔴 Inactive'}")
            with c5:
                if st.button("Delete", key=f"del_{a_id}"):
                    st.session_state.athletes = st.session_state.athletes.drop(index)
                    st.session_state.athletes.to_csv("roster_storage.csv", index=False)
                    st.rerun()

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

    # 2. Tabs
    tab1, tab2 = st.tabs(["🆕 Log New Reps", "📊 History & Stats"])
    
    with tab1:
        col_sys, col_drill = st.columns(2)
        with col_sys:
            timing_system = st.radio("Timing System:", ["Electronic / FAT (Freelap)", "Hand-Timed (Stopwatch)"], horizontal=True)
        with col_drill:
            session_type = st.selectbox("Drill Type:", ["20m_fly", "30m_block"])
        
        st.write("---")
        
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
        if not st.session_state.workout_logs.empty:
            st.dataframe(st.session_state.workout_logs.sort_values(by='date', ascending=False), use_container_width=True)
            if st.button("🗑️ Clear All Logs"):
                st.session_state.workout_logs = pd.DataFrame(columns=["date", "athlete_id", "type", "fat", "proj_100"])
                st.session_state.workout_logs.to_csv("workout_logs_storage.csv", index=False)
                st.rerun()
        else:
            st.info("No records found.")
    
elif app_portal == "📆 Live Session Dashboard":
    st.title("📆 Today's Live Session Dashboard")
    
    if st.session_state.workout_logs.empty:
        st.info("ℹ️ No workout logs recorded today.")
    else:
        today_str = datetime.today().strftime('%Y-%m-%d')
        logs_clean = st.session_state.workout_logs.copy()
        todays_logs = logs_clean[logs_clean['date'] == today_str]
        
        if todays_logs.empty:
            st.info(f"ℹ️ No repetitions logged yet for today ({today_str}).")
        else:
            st.subheader("🏁 Compiled Today's Best Summary Matrix")
            # Loop for rendering today's session summary
            for _, athlete in st.session_state.athletes.iterrows():
                a_id = str(athlete['id']).strip()
                # Fetch bests for display
                fly = todays_logs[(todays_logs['athlete_id'] == a_id) & (todays_logs['type'] == '20m_fly')]['fat'].min()
                block = todays_logs[(todays_logs['athlete_id'] == a_id) & (todays_logs['type'] == '30m_block')]['fat'].min()
                
                if pd.notna(fly) or pd.notna(block):
                    proj = get_unified_projection("20m_fly", fly, block, fly, athlete.get('gender', 'male'))
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.markdown(f"**{athlete['name']}**")
                    with c2: st.markdown(f"{fly:.2f}s" if pd.notna(fly) else "--")
                    with c3: st.markdown(f"{block:.2f}s" if pd.notna(block) else "--")
                    with c4: st.markdown(f"**{proj:.2f}s**")
                        
elif app_portal == "🤝 Relay Optimizer Pool": 
    st.title("🏆 Data-Optimized 4x100m Relay Builder")
    st.markdown("Algorithmic sorting mapped with kinematic go-mark physics.")
    
    if st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster Hub first.")
    else:
        # Prep data
        roster_df = st.session_state.athletes.copy()
        relay_gender = st.selectbox("Select Target Relay Division:", ["Male", "Female"])
        
        # Filter for gender
        active_pool = roster_df[roster_df['gender'].str.lower() == relay_gender.lower()]
        
        if len(active_pool) >= 4:
            # Gather metrics
            logs = st.session_state.workout_logs
            metrics = []
            for _, ath in active_pool.iterrows():
                a_id = str(ath['id'])
                fly = logs[(logs['athlete_id'] == a_id) & (logs['type'] == '20m_fly')]['fat'].min()
                block = logs[(logs['athlete_id'] == a_id) & (logs['type'] == '30m_block')]['fat'].min()
                metrics.append({"name": ath['name'], "fly": fly if pd.notna(fly) else 99.0, "block": block if pd.notna(block) else 99.0})
            
            rdf = pd.DataFrame(metrics)
            # Simple Sort for defaults
            c1, c2, c3, c4 = st.columns(4)
            names = rdf['name'].tolist()
            leg1 = c1.selectbox("Leg 1 (Block):", names, index=0)
            leg2 = c2.selectbox("Leg 2 (Straight):", names, index=1)
            leg3 = c3.selectbox("Leg 3 (Curve):", names, index=2)
            leg4 = c4.selectbox("Leg 4 (Anchor):", names, index=3)

            # Kinematic Logic
            def get_go_mark(f, b):
                # Using your differential gap formula
                steps = (((20 / (f if f < 99 else 2.2)) * ((b if b < 99 else 4.2) * 0.71)) - 20 - 0.70) * 3.28
                return int(round(steps))

            run_map = {m['name']: m for m in metrics}
            m12 = get_go_mark(run_map[leg1]['fly'], run_map[leg2]['block'])
            m23 = get_go_mark(run_map[leg2]['fly'], run_map[leg3]['block'])
            m34 = get_go_mark(run_map[leg3]['fly'], run_map[leg4]['block'])

            with st.container(border=True):
                st.markdown("### 🗺️ Acceleration Checkmark Marks")
                st.write(f"* 🏁 **Exchange 1:** {m12} footsteps")
                st.write(f"* 🏁 **Exchange 2:** {m23} footsteps")
                st.write(f"* 🏁 **Exchange 3:** {m34} footsteps")
        else:
            st.warning("⚠️ Need 4+ athletes with metrics to optimize.")
                
elif app_portal == "📈 Athlete Progress Trends":
    st.title("📈 The Athlete Progress Screen")
    
    if st.session_state.athletes.empty:
        st.info("ℹ️ No roster data.")
    else:
        athlete_map = {row['name']: str(row['id']) for _, row in st.session_state.athletes.iterrows()}
        selected_name = st.selectbox("👤 Select Athlete:", list(athlete_map.keys()))
        s_id = athlete_map[selected_name]
        
        logs = st.session_state.workout_logs[st.session_state.workout_logs['athlete_id'] == s_id]
        
        view = st.radio("Dimension:", ["⚡ 20m Fly", "🧱 30m Block", "⏱️ Recruitment Forecast"], horizontal=True)
        
        if "Forecast" in view:
            st.subheader("⏱️ Recruitment Projections")
            # Uses unified engine
            data = logs[logs['type'] == '20m_fly'].copy()
            data['proj'] = data.apply(lambda r: get_unified_projection("20m_fly", r['fat'], None, r['fat'], "male"), axis=1)
            st.line_chart(data.set_index('date')['proj'])
        else:
            t = "20m_fly" if "Fly" in view else "30m_block"
            st.line_chart(logs[logs['type'] == t].set_index('date')['fat'])

        # CNS Logic
        if len(logs) >= 3:
            recent = logs.tail(3)['fat']
            if recent.iloc[-1] > (recent.iloc[0] * 1.03):
                st.warning("⚠️ CNS Fatigue Detected.")
            else:
                st.success("✅ CNS Muscle Readiness: Normal.")

elif app_portal == "🏆 Team Leaderboards":
    st.title("🔥 Team Leaderboards")

    if st.session_state.workout_logs.empty:
        st.warning("⚠️ No workout log data found.")
    else:
        logs = st.session_state.workout_logs
        roster = st.session_state.athletes
        
        # UI Filters
        l_col1, l_col2 = st.columns(2)
        gender_filter = l_col1.selectbox("Gender Select:", ["All", "Male", "Female"])
        
        leaderboard_type = st.radio("Select Ranking:", ["⚡ 20m Fly", "🧱 30m Block", "⏱️ Projected 100m"], horizontal=True)

        if "20m Fly" in leaderboard_type:
            metric_df = logs[logs['type'] == '20m_fly'].groupby('athlete_id')['fat'].min().reset_index()
            suffix = "s"
        elif "30m Block" in leaderboard_type:
            metric_df = logs[logs['type'] == '30m_block'].groupby('athlete_id')['fat'].min().reset_index()
            suffix = "s"
        else:
            # PROJECTED 100M: UNIFIED ENGINE CALL
            fly_bests = logs[logs['type'] == '20m_fly'].groupby('athlete_id')['fat'].min().reset_index()
            block_bests = logs[logs['type'] == '30m_block'].groupby('athlete_id')['fat'].min().reset_index()
            
            combined = pd.merge(fly_bests.rename(columns={'fat': 'fly'}), 
                                block_bests.rename(columns={'fat': 'block'}), 
                                on='athlete_id', how='outer')
            
            computed_projections = []
            for _, row in combined.iterrows():
                ath_row = roster[roster['id'].astype(str) == str(row['athlete_id'])]
                g = ath_row['gender'].iloc[0] if not ath_row.empty else 'male'
                proj = get_unified_projection("20m_fly", row['fly'], row['block'], row['fly'], g)
                computed_projections.append(proj)
            
            combined['fat'] = computed_projections
            metric_df = combined[['athlete_id', 'fat']]
            suffix = "s (Est)"

        # Merge and Sort
        leaderboard_df = roster.merge(metric_df, left_on='id', right_on='athlete_id', how='inner')
        leaderboard_df = leaderboard_df.sort_values(by='fat').reset_index(drop=True)

        # UI Rendering
        for rank, (_, row) in enumerate(leaderboard_df.iterrows(), start=1):
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"#### {rank}. {row['name']} *({row.get('group', 'Sprints')})*")
                c2.markdown(f"### **{row['fat']:.2f}{suffix}**")
                
elif app_portal == "📄 AD Report Export":
    st.title("📄 Executive AD Report Generator")
    # [Insert your AD Report Export Code Here]
