import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# INITIALIZATION & STATE
# ==========================================
def init_app():
    # Setup Athletes DataFrame
    if 'athletes' not in st.session_state:
        try:
            st.session_state.athletes = pd.read_csv("roster_storage.csv")
        except:
            st.session_state.athletes = pd.DataFrame(columns=[
                "id", "name", "gender", "grade", "group", "tier", "status", 
                "pr_100", "pr_200", "pr_400"
            ])
            
    # Add PR columns if they don't exist
    cols_to_add = ["pr_100", "pr_200", "pr_400"]
    for col in cols_to_add:
        if col not in st.session_state.athletes.columns:
            st.session_state.athletes[col] = 0.0

    # Setup Workout Logs
    if 'workout_logs' not in st.session_state:
        try:
            st.session_state.workout_logs = pd.read_csv("workout_logs_storage.csv")
        except:
            st.session_state.workout_logs = pd.DataFrame(columns=["date", "athlete_id", "type", "fat", "proj_100"])

# Run the initialization
init_app()

# Now your Navigation code...
app_portal = st.sidebar.selectbox("Navigation", ["👥 Roster & Onboarding Hub", "⏱️ Workout Tracker", ...])
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
elif app_portal == "👥 Roster & Onboarding Hub":
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
                "tier": "Varsity",
                "status": "Active",
                "pr_100": 0.0, # New PR field
                "pr_200": 0.0, # New PR field
                "pr_400": 0.0  # New PR field
            }
            # Ensure new_row matches columns in session_state
            st.session_state.athletes = pd.concat([st.session_state.athletes, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Added {name}!")

    st.write("---")
    st.subheader("📋 Current Team Roster")

    # Roster Management Table
    if not st.session_state.athletes.empty:
        # Use a copy to iterate
        roster = st.session_state.athletes.copy()
        
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
# ==========================================
# MODULE 2. Workout Module
# ========================================== 
elif app_portal == "⏱️ Workout Tracker":
    st.title("⏱️ Unified Workout Hub")
    
    # 1. Athlete Selection
    athletes = st.session_state.athletes
    if athletes.empty:
        st.warning("Please onboard athletes in the Roster Hub first.")
    else:
        sel_name = st.selectbox("Select Athlete:", athletes['name'].tolist())
        ath = athletes[athletes['name'] == sel_name].iloc[0]
        ath_id = str(ath['id'])
        gender = ath['gender']

        with st.form("log_workout"):
            w_date = st.date_input("Date", datetime.today())
            f_val = st.number_input("20m Fly Time (s)", min_value=1.0, max_value=5.0, step=0.01, format="%.2f")
            b_val = st.number_input("30m Block Start (s) [Optional]", min_value=0.0, max_value=10.0, step=0.01, format="%.2f")
            
            if st.form_submit_button("Log Session"):
                # Pass b_val as None if 0 to trigger Fallback logic in engine
                block_input = b_val if b_val > 0 else None
                proj = get_unified_projection("manual", f_val, block_input, f_val, gender)
                
                new_log = {
                    "date": str(w_date),
                    "athlete_id": ath_id,
                    "type": "30m_block" if block_input else "20m_fly",
                    "fat": f_val,
                    "proj_100": proj
                }
                st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame([new_log])], ignore_index=True)
                st.success(f"Logged! Projected 100m Potential: {proj}s")

        # 2. History & Management Section
        st.subheader(f"History: {sel_name}")
        logs = st.session_state.workout_logs
        ath_logs = logs[logs['athlete_id'] == ath_id].copy()
        
        if not ath_logs.empty:
            for idx, row in ath_logs.iterrows():
                cols = st.columns([2, 2, 2, 1])
                cols[0].write(row['date'])
                cols[1].write(f"Fly: {row['fat']}s")
                cols[2].write(f"Proj: {row['proj_100']}s")
                if cols[3].button("❌", key=f"del_{idx}"):
                    st.session_state.workout_logs = st.session_state.workout_logs.drop(idx)
                    st.rerun()
        else:
            st.info("No logs available for this athlete.")

# ==========================================
# MODULE 3: LIVE SESSION DASHBOARD (UPDATED)
# ==========================================
elif app_portal == "📆 Live Session Dashboard":
    st.title("📆 Today's Live Session Dashboard")
    
    active_athletes = st.session_state.athletes[st.session_state.athletes['status'] == 'Active']
    
    if active_athletes.empty:
        st.info("No active athletes available.")
    else:
        st.subheader("⚡ Quick-Log Trackside")
        c1, c2, c3 = st.columns([3, 2, 2])
        
        live_ath_name = c1.selectbox("Athlete", active_athletes['name'].tolist())
        drill_type = c2.selectbox("Drill", ["20m_fly", "30m_block"])
        val = c3.number_input("Time (s)", min_value=1.0, max_value=6.0, step=0.01, format="%.2f")
        
        if st.button("Log Trackside"):
            ath_row = active_athletes[active_athletes['name'] == live_ath_name].iloc[0]
            
            # Use our unified engine: 
            # If drill is block, it will use the primary formula (if fly is known) or fallback
            proj = get_unified_projection("manual", val if drill_type == "20m_fly" else 2.20, 
                                          val if drill_type == "30m_block" else None, 
                                          val if drill_type == "20m_fly" else 2.20, 
                                          ath_row['gender'])
            
            new_log = {
                "date": str(datetime.today().date()),
                "athlete_id": str(ath_row['id']),
                "type": drill_type,
                "fat": val,
                "proj_100": proj
            }
            st.session_state.workout_logs = pd.concat([st.session_state.workout_logs, pd.DataFrame([new_log])], ignore_index=True)
            st.success(f"Logged {live_ath_name} ({drill_type}): {val}s | Proj: {proj}s")

        st.write("---")
        st.subheader("Today's Session Activity")
        today_str = str(datetime.today().date())
        today_logs = st.session_state.workout_logs[st.session_state.workout_logs['date'] == today_str]
        
        if not today_logs.empty:
            # Display current session data
            display_df = today_logs.copy()
            display_df['Name'] = display_df['athlete_id'].apply(
                lambda x: st.session_state.athletes[st.session_state.athletes['id'] == x]['name'].iloc[0] 
                if not st.session_state.athletes[st.session_state.athletes['id'] == x].empty else "Unknown"
            )
            st.table(display_df[['Name', 'type', 'fat', 'proj_100']])

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

        # 6. Integrated PDF Export (Connected to Engine)
        if st.button("Export Lineup PDF"):
            # Ensure marks were calculated
            if 'relay_go_marks' not in st.session_state:
                st.error("Please calculate Go-Marks before exporting.")
            else:
                marks = st.session_state['relay_go_marks']
                # Create clean data for the PDF
                pdf_data = generate_ad_pdf(
                    coach="Head Coach", # Or pull from session_state if available
                    program="Relay Performance Report",
                    squad=f"{gender_choice} Relay",
                    benchmark=11.0, # Or your state qual constant
                    roster=[{"name": l1, "baseline": "--", "pr": "--", "delta": "--", "proj": "--"},
                            {"name": l2, "baseline": "--", "pr": "--", "delta": "--", "proj": "--"},
                            {"name": l3, "baseline": "--", "pr": "--", "delta": "--", "proj": "--"},
                            {"name": l4, "baseline": "--", "pr": "--", "delta": "--", "proj": "--"}],
                    r1=l1, r2=l2, r3=l3, r4=l4,
                    m1=f"Leg 1", m2=f"Leg 2", m3=f"Leg 3", m4=f"Leg 4",
                    count=4, impr="N/A", vel="N/A", 
                    s1=marks['1to2'], s2=marks['2to3'], s3=marks['3to4']
                )
                st.download_button(
                    label="📥 Download Relay Lineup PDF",
                    data=pdf_data,
                    file_name="relay_lineup.pdf",
                    mime="application/pdf"
                )
# ==========================================
# MODULE 5: ATHLETE PROGRESS & PR MANAGEMENT
# ==========================================
elif app_portal == "📈 Athlete Progress Trends":
    st.title("📈 The Athlete Progress Screen")
    
    athletes = st.session_state.athletes
    if athletes.empty:
        st.info("No athletes to display.")
    else:
        sel_name = st.selectbox("Select Athlete:", athletes['name'].tolist())
        ath_idx = athletes[athletes['name'] == sel_name].index[0]
        ath = athletes.loc[ath_idx]
        
        st.subheader(f"👤 ATHLETE PROFILE: {ath['name']} (Grade: {ath['grade']})")
        
        # 1. Official PR Management Form
        with st.expander("📝 Update Official Meet PRs"):
            with st.form("update_prs"):
                col1, col2, col3 = st.columns(3)
                pr100 = col1.number_input("100m PR", value=float(ath.get('pr_100', 0.0)), step=0.01)
                pr200 = col2.number_input("200m PR", value=float(ath.get('pr_200', 0.0)), step=0.01)
                pr400 = col3.number_input("400m PR", value=float(ath.get('pr_400', 0.0)), step=0.01)
                
                if st.form_submit_button("Save PRs"):
                    st.session_state.athletes.at[ath_idx, 'pr_100'] = pr100
                    st.session_state.athletes.at[ath_idx, 'pr_200'] = pr200
                    st.session_state.athletes.at[ath_idx, 'pr_400'] = pr400
                    st.success("Official PRs updated!")
                    st.rerun()

        # 2. Progress Trends
        metric = st.radio("View Metric Trend:", ["20m Fly Trend", "30m Block Trend", "100m Projection Trend"], horizontal=True)
        ath_logs = st.session_state.workout_logs[st.session_state.workout_logs['athlete_id'] == str(ath['id'])]
        
        if metric == "20m Fly Trend":
            data = ath_logs[ath_logs['type'] == '20m_fly']
            val_col = 'fat'
        elif metric == "30m Block Trend":
            data = ath_logs[ath_logs['type'] == '30m_block']
            val_col = 'fat'
        else:
            data = ath_logs
            val_col = 'proj_100'
            
        if not data.empty:
            chart_data = data[['date', val_col]].sort_values('date')
            chart_data = chart_data.rename(columns={val_col: 'Time'})
            st.line_chart(chart_data.set_index('date'))
            
            st.write("---")
            st.subheader("📊 SEASON INSIGHTS & ANALYTICS")
            if len(data) > 1:
                improv = data.iloc[0][val_col] - data.iloc[-1][val_col]
                st.write(f"• Total Improvement: {improv:.2f}s")
            
            curr_proj = data.iloc[-1]['proj_100']
            st.write(f"• Projected 100m Potential: {curr_proj:.2f}s")
            
            fly = ath_logs[ath_logs['type'] == '20m_fly']['fat'].min()
            if pd.notna(fly) and fly < 2.10:
                st.write("• Optimal Relay Leg: Leg 2 or Leg 4 (Max Velocity Peak)")
            else:
                st.write("• Optimal Relay Leg: Leg 1 or Leg 3 (Acceleration Focus)")
        else:
            st.info("Log training data to view progress trends.")
            
# ==========================================
# MODULE 6: COMPREHENSIVE TEAM LEADERBOARD
# ==========================================
elif app_portal == "🏆 Team Leaderboards":
    st.title("🏆 Season Performance Rankings")
    division = st.radio("Division:", ["Male", "Female"], horizontal=True)
    
    # 1. Gather all data
    active_pool = st.session_state.athletes[
        (st.session_state.athletes['status'] == 'Active') & 
        (st.session_state.athletes['gender'] == division)
    ]
    
    leaderboard_data = []
    for _, ath in active_pool.iterrows():
        logs = st.session_state.workout_logs[st.session_state.workout_logs['athlete_id'] == str(ath['id'])]
        leaderboard_data.append({
            "Name": ath['name'],
            "Best Fly": logs[logs['type'] == '20m_fly']['fat'].min() or 99.0,
            "Best Block": logs[logs['type'] == '30m_block']['fat'].min() or 99.0,
            "Best Proj 100": logs['proj_100'].min() or 99.0,
            "Official 100m": ath.get('pr_100', 99.0),
            "Official 200m": ath.get('pr_200', 99.0)
        })
    
    df = pd.DataFrame(leaderboard_data)
    
    # 2. Tabs for easy switching
    tab1, tab2, tab3 = st.tabs(["Speed Metrics (Fly/Block)", "100m Projections", "Official Meet PRs"])
    
    with tab1:
        st.subheader("Training Speed Leaders")
        st.table(df.sort_values("Best Fly")[['Name', 'Best Fly', 'Best Block']])
    with tab2:
        st.subheader("Top 100m Potential")
        st.table(df.sort_values("Best Proj 100")[['Name', 'Best Proj 100']])
    with tab3:
        st.subheader("Official Meet PRs")
        st.table(df.sort_values("Official 100m")[['Name', 'Official 100m', 'Official 200m']])

# ==========================================
# MODULE 7: EXECUTIVE AD REPORT GENERATOR
# ==========================================
elif app_portal == "📋 Executive AD Report":
    st.title("📋 Athletic Director Report")
    st.write("Generate a performance summary for department review.")
    
    if st.button("Generate Executive Summary"):
        # Aggregate Performance Data
        active_athletes = st.session_state.athletes[st.session_state.athletes['status'] == 'Active']
        total_athletes = len(active_athletes)
        avg_proj = st.session_state.workout_logs['proj_100'].mean()
        
        st.subheader(f"Performance Summary: {datetime.today().strftime('%B %Y')}")
        st.write(f"- **Total Active Roster:** {total_athletes} Athletes")
        st.write(f"- **Average Projected 100m Potential:** {avg_proj:.2f}s")
        st.write("---")
        
        # 1. Gather all data for rankings
        data = []
        for _, ath in active_athletes.iterrows():
            logs = st.session_state.workout_logs[st.session_state.workout_logs['athlete_id'] == str(ath['id'])]
            data.append({
                "Name": ath['name'],
                "20m Fly": logs[logs['type'] == '20m_fly']['fat'].min() if not logs[logs['type'] == '20m_fly'].empty else 99.0,
                "30m Start": logs[logs['type'] == '30m_block']['fat'].min() if not logs[logs['type'] == '30m_block'].empty else 99.0,
                "Proj 100": logs['proj_100'].min() if not logs['proj_100'].empty else 99.0,
                "Official 100": ath.get('pr_100', 99.0),
                "Official 200": ath.get('pr_200', 99.0),
                "Official 400": ath.get('pr_400', 99.0)
            })
        
        df = pd.DataFrame(data)
        
        # 2. Display Top 5 for each category
        metrics = ["20m Fly", "30m Start", "Proj 100", "Official 100", "Official 200", "Official 400"]
        
        for m in metrics:
            st.subheader(f"Top 5: {m}")
            # Filter out the 99.0 placeholders
            top = df[df[m] < 99.0].sort_values(m).head(5)
            if not top.empty:
                st.table(top[['Name', m]])
            else:
                st.write("No data recorded.")

# ==========================================
# FOOTER / PERSISTENCE
# ==========================================
if st.sidebar.button("Save All Data"):
    st.session_state.athletes.to_csv("roster_storage.csv", index=False)
    st.session_state.workout_logs.to_csv("workout_logs_storage.csv", index=False)
    st.sidebar.success("Data saved successfully!")
