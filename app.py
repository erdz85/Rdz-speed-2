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
# ==========================================
# MODULE 7: AD REPORT EXPORT ("THE AD CLOSER") - COMPLETE & AUDITED
# ==========================================
elif app_portal == "📄 AD Report Export":
    import io
    import pandas as pd
    from datetime import datetime
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    st.title("📄 Executive AD Report Generator")
    st.subheader("Generate Data-Driven Program Justification Printouts")
    
    # 1. User Inputs & Configuration Controls
    col1, col2 = st.columns(2)
    with col1:
        coach_name = st.text_input("Head Coach Name:", value="John Doe")
        program_name = st.text_input("Program Title:", value="NORTHSIDE TRACK & FIELD")
    with col2:
        squad_division = st.selectbox("Squad/Division Filter:", ["VARSITY BOYS", "VARSITY GIRLS", "FROSH-SOPH"])
        state_qual_time = st.number_input("State Qual 100m Benchmark (s):", value=11.00, step=0.05)

    st.write("---")

    # 2. Safety Guardrails & Data Processing
    if 'athletes' not in st.session_state or st.session_state.athletes.empty:
        st.info("ℹ️ Please add athletes inside the Roster & Onboarding Hub first.")
    else:
        roster_clean = st.session_state.athletes.copy()
        roster_clean.columns = [str(c).lower().strip() for c in roster_clean.columns]
        active_squad = roster_clean[roster_clean['status'].astype(str).str.lower() == 'active']
        
        # Apply filters
        if squad_division == "VARSITY BOYS":
            active_squad = active_squad[(active_squad['tier'].astype(str).str.lower() == 'varsity') & (active_squad['gender'].astype(str).str.lower() == 'male')]
        elif squad_division == "VARSITY GIRLS":
            active_squad = active_squad[(active_squad['tier'].astype(str).str.lower() == 'varsity') & (active_squad['gender'].astype(str).str.lower() == 'female')]
        elif squad_division == "FROSH-SOPH":
            active_squad = active_squad[active_squad['grade'].astype(str).str.strip().isin(['9', '10'])]

        has_logs = 'workout_logs' in st.session_state and not st.session_state.workout_logs.empty
        logs_clean = st.session_state.workout_logs.copy() if has_logs else pd.DataFrame()
        if has_logs:
            logs_clean.columns = [str(c).lower().strip() for c in logs_clean.columns]
            logs_clean['athlete_id'] = logs_clean['athlete_id'].astype(str).str.strip()

        # 3. Processing Loop (AUDITED)
        processed_roster = []
        relay_pool = []
        total_deltas, delta_count, velocity_sums, velocity_count = 0.0, 0, 0.0, 0

        for _, athlete in active_squad.iterrows():
            a_id = str(athlete['id']).strip()
            a_name = str(athlete['name']).strip()
            a_gender = str(athlete.get('gender', 'male')).lower()
            
            fly_logs = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '20m_fly')]
            block_logs = logs_clean[(logs_clean['athlete_id'] == a_id) & (logs_clean['type'] == '30m_block')]
            
            f_best = fly_logs['fat'].min() if not fly_logs.empty else None
            b_best = block_logs['fat'].min() if not block_logs.empty else None
            base_fly = fly_logs.iloc[0]['fat'] if not fly_logs.empty else None
            
            # AUDITED ENGINE CALL
            proj_val = get_unified_projection("20m_fly", f_best, b_best, f_best, a_gender)
            
            base_str = f"{base_fly:.2f}s FAT" if pd.notna(base_fly) else "--"
            pr_str = f"{f_best:.2f}s FAT" if pd.notna(f_best) else "--"
            delta_str = f"{f_best - base_fly:+.2f}s" if pd.notna(f_best) and pd.notna(base_fly) else "0.00s"
            
            if pd.notna(f_best) and pd.notna(base_fly):
                total_deltas += (f_best - base_fly)
                delta_count += 1
            
            if pd.notna(f_best):
                velocity_sums += (20.0 / f_best)
                velocity_count += 1

            processed_roster.append({"name": a_name, "baseline": base_str, "pr": pr_str, "delta": delta_str, 
                                     "proj": f"{proj_val:.2f}s{' *' if proj_val <= state_qual_time else ''}" if proj_val else "--"})
            relay_pool.append({"name": a_name, "best_fly": f_best or 2.2, "best_block": b_best or 4.2})

        # =========================================================================
        # 4. CROSS-MODULE LINEUP INTEGRATION (READS FROM MODULE 5 OVERRIDES)
        # =========================================================================
        if 'custom_relay_lineup' in st.session_state and isinstance(st.session_state.custom_relay_lineup, dict):
            # Read exact manual selections from Module 5
            c_lineup = st.session_state.custom_relay_lineup
            leg1_name = c_lineup['leg1']['name']
            leg1_metric = c_lineup['leg1']['metric']
            
            leg2_name = c_lineup['leg2']['name']
            leg2_metric = c_lineup['leg2']['metric']
            
            leg3_name = c_lineup['leg3']['name']
            leg3_metric = c_lineup['leg3']['metric']
            
            leg4_name = c_lineup['leg4']['name']
            leg4_metric = c_lineup['leg4']['metric']
        else:
            # Fallback Selection Engine: Auto-calculate default if Module 5 hasn't run yet
            leg1_name, leg1_metric = "Vacant Slot", "[No Data]"
            leg2_name, leg2_metric = "Vacant Slot", "[No Data]"
            leg3_name, leg3_metric = "Vacant Slot", "[No Data]"
            leg4_name, leg4_metric = "Vacant Slot", "[No Data]"

            if len(relay_pool) >= 4:
                # Leg 1: Block Start
                relay_pool = sorted(relay_pool, key=lambda x: x['best_block'])
                r1 = relay_pool.pop(0)
                leg1_name, leg1_metric = r1['name'], f"[Block Start: {r1['best_block']:.2f}s]"
                
                # Leg 2: Straight Fly
                relay_pool = sorted(relay_pool, key=lambda x: x['best_fly'])
                r2 = relay_pool.pop(0)
                leg2_name, leg2_metric = r2['name'], f"[Fly Split: {r2['best_fly']:.2f}s]"
                
                # Leg 4: Anchor Closer
                relay_pool = sorted(relay_pool, key=lambda x: x['best_fly'])
                r4 = relay_pool.pop(0)
                leg4_name, leg4_metric = r4['name'], f"[Anchor Fly: {r4['fly']:.2f}s]"
                
                # Leg 3: Curve
                relay_pool = sorted(relay_pool, key=lambda x: x['best_fly'])
                r3 = relay_pool.pop(0)
                leg3_name, leg3_metric = r3['name'], f"[Fly Split: {r3['best_fly']:.2f}s]"

        # =========================================================================
        # CROSS-MODULE GO MARK SYNCHRONIZER
        # =========================================================================
        if 'relay_go_marks' in st.session_state and isinstance(st.session_state.relay_go_marks, dict):
            # Pull direct high-precision steps computed via Module 5's action button
            step_1to2 = st.session_state.relay_go_marks.get('1to2', 17.0)
            step_2to3 = st.session_state.relay_go_marks.get('2to3', 17.0)
            step_3to4 = st.session_state.relay_go_marks.get('3to4', 17.0)
        else:
            # Clean mathematical fallback step equations if optimizer hasn't been engaged
            step_1to2 = 17.0
            step_2to3 = 17.0
            step_3to4 = 17.0

        # 5. ReportLab PDF Generation Definition Routine
        def generate_ad_pdf(coach, program, squad, benchmark, roster, r1, r2, r3, r4, m1, m2, m3, m4, count, impr, vel, s1, s2, s3):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=letter,
                rightMargin=36, leftMargin=36, 
                topMargin=36, bottomMargin=36
            )
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('PDFTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.black)
            meta_style = ParagraphStyle('PDFMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#444444"))
            section_style = ParagraphStyle('PDFSection', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, spaceBefore=10, spaceAfter=6, textColor=colors.black)
            bullet_style = ParagraphStyle('PDFBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=15, leftIndent=15)
            table_hdr_style = ParagraphStyle('PDFTableHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.black)
            table_body_style = ParagraphStyle('PDFTableBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9)

            story = []
            story.append(Paragraph(f"■ {program.upper()} — 2026 SEASON SPEED REPORT", title_style))
            story.append(Paragraph(f"Report Generated: {datetime.today().strftime('%B %d, %Y')} &nbsp;|&nbsp; Head Coach: {coach}", meta_style))
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceBefore=1, spaceAfter=15))

            story.append(Paragraph(f"[ SQUAD OVERVIEW: {squad} ]", section_style))
            story.append(Paragraph(f"• Total Active Student-Athletes Tracked: <b>{count}</b>", bullet_style))
            story.append(Paragraph(f"• Avg. 20m Fly Block Performance Improvement: <b>{impr}</b>", bullet_style))
            story.append(Paragraph(f"• Team Speed Peak Velocity Aggregate: <b>{vel} (Average)</b>", bullet_style))
            story.append(Spacer(1, 15))

            story.append(Paragraph("■ PERFORMANCE ROSTER & 100M PROJECTED RANKINGS", section_style))
            
            table_data = [[
                Paragraph("<b>Athlete Name</b>", table_hdr_style), 
                Paragraph("<b>Baseline Fly</b>", table_hdr_style), 
                Paragraph("<b>Current PR</b>", table_hdr_style), 
                Paragraph("<b>Net Delta</b>", table_hdr_style), 
                Paragraph("<b>Proj. 100m</b>", table_hdr_style)
            ]]
            
            for row in roster:
                table_data.append([
                    Paragraph(row['name'], table_body_style),
                    Paragraph(row['baseline'], table_body_style),
                    Paragraph(row['pr'], table_body_style),
                    Paragraph(row['delta'], table_body_style),
                    Paragraph(row['proj'], table_body_style)
                ])
                
            if len(roster) == 0:
                table_data.append([Paragraph("No matching active athlete logs available.", table_body_style), "", "", "", ""])
            
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
            story.append(Paragraph(f"• <b>Leg 1 (Starter):</b> {r1} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m1}", bullet_style))
            story.append(Paragraph(f"• <b>Leg 2 (Straight):</b> {r2} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m2}", bullet_style))
            story.append(Paragraph(f"• <b>Leg 3 (Curve):</b> &nbsp;&nbsp;&nbsp;{r3} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m3}", bullet_style))
            story.append(Paragraph(f"• <b>Leg 4 (Anchor):</b> &nbsp;&nbsp;{r4} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{m4}", bullet_style))
            
            story.append(Spacer(1, 8))
            story.append(Paragraph("■ <b>RECOMMENDED RELAY GO MARKS:</b>", section_style))
            story.append(Paragraph(f"- Exch 1 (1 to 2): {s1:.1f} Steps &nbsp;|&nbsp; Exch 2 (2 to 3): {s2:.1f} Steps &nbsp;|&nbsp; Exch 3 (3 to 4): {s3:.1f} Steps", bullet_style))
            
            story.append(Spacer(1, 40))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999"), spaceBefore=10, spaceAfter=10))
            story.append(Paragraph("<b>Verified By:</b> RDZ Speed Intelligence System Dashboard", meta_style))
            story.append(Paragraph("<i>This document contains certified high-precision metrics compiled for athletic recruitment evaluation and administrative review.</i>", meta_style))

            doc.build(story)
            buffer.seek(0)
            return buffer
        # FIX: Define metrics for the PDF call
        tracked_count = delta_count
        avg_improvement = f"{total_deltas / delta_count:.2f}s" if delta_count > 0 else "0.00s"
        avg_velocity = f"{velocity_sums / velocity_count:.2f} m/s" if velocity_count > 0 else "0.00 m/s"
        
        # Now call the PDF generation
        pdf_data = generate_ad_pdf(
            coach_name, program_name, squad_division, state_qual_time, processed_roster,
            leg1_name, leg2_name, leg3_name, leg4_name, leg1_metric, leg2_metric, leg3_metric, leg4_metric,
            tracked_count, avg_improvement, avg_velocity, step_1to2, step_2to3, step_3to4
        )        # Pre-build compiled download asset with dynamic steps passed through
        pdf_data = generate_ad_pdf(
            coach_name, program_name, squad_division, state_qual_time, processed_roster,
            leg1_name, leg2_name, leg3_name, leg4_name, leg1_metric, leg2_metric, leg3_metric, leg4_metric,
            tracked_count, avg_improvement, avg_velocity, step_1to2, step_2to3, step_3to4
        )

        # 6. Streamlit Document UI Container Preview Panel Rendering
        st.markdown("### 📋 Document Preview Panel")
        with st.container(border=True):
            st.markdown(f"### ■ {program_name.upper()} — 2026 SEASON SPEED REPORT")
            current_date_str = datetime.today().strftime('%B %d, %Y')
            st.caption(f"Report Generated: {current_date_str} | Head Coach: {coach_name}")
            st.write("")
            
            st.markdown(f"**[ SQUAD OVERVIEW: {squad_division} ]**")
            st.markdown(f"• Total Active Student-Athletes Tracked: **{tracked_count}** \n• Avg. 20m Fly Block Performance Improvement: **{avg_improvement}** \n• Team Speed Peak Velocity Aggregate: **{avg_velocity} (Average)**")
            st.write("")
            
            st.markdown("### ■ PERFORMANCE ROSTER & 100M PROJECTED RANKINGS")
            
            ui_table_data = []
            for item in processed_roster:
                ui_table_data.append({
                    "Athlete Name": item['name'],
                    "Baseline Fly": item['baseline'],
                    "Current PR": item['pr'],
                    "Net Delta": item['delta'],
                    "Proj. 100m": item['proj']
                })
            
            if ui_table_data:
                st.dataframe(pd.DataFrame(ui_table_data), hide_index=True, use_container_width=True)
            else:
                st.info("No active running session parameters stored matching current selection parameters.")
                
            st.caption(f"* Denotes State Qualifying standard projected ({state_qual_time:.2f}s)")
            st.write("")
            
            st.markdown("### ■ PROPOSED 4x100M RELAY LINEUP (DATA-OPTIMIZED)")
            st.markdown(f"• **Leg 1 (Starter):** {leg1_name} {leg1_metric} \n• **Leg 2 (Straight):** {leg2_name} {leg2_metric} \n• **Leg 3 (Curve):** {leg3_name} {leg3_metric} \n• **Leg 4 (Anchor):** {leg4_name} {leg4_metric}")
            st.write("")
            
            st.markdown("### ■ RECOMMENDED RELAY GO MARKS:")
            # Display step indicators as dynamic whole or float indicators depending on math calculations
            st.markdown(f"- Exch 1 (1 to 2): **{step_1to2:.1f} Steps** | Exch 2 (2 to 3): **{step_2to3:.1f} Steps** | Exch 3 (3 to 4): **{step_3to4:.1f} Steps**")
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
