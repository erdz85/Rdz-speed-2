import sys
import os
import math
from datetime import datetime
import pandas as pd

# Optional ReportLab integration for professional PDF reporting
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QGroupBox, QFormLayout, QRadioButton,
    QButtonGroup, QListWidget, QAbstractItemView, QCheckBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

# ==========================================
# 1. ARCHITECTURE MODELS & BACKEND ENGINES
# ==========================================

class Athlete:
    def __init__(self, first_name, last_name, gender, grad_year, group, fly_20m=None, block_30m=None):
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender       # "Male" or "Female"
        self.grad_year = int(grad_year)
        self.group = group         # e.g., "Short Sprints", "Hurdlers", "JV Girls"
        self.raw_fly_20m = fly_20m
        self.raw_block_30m = block_30m
        self.is_hand_timed = False # Session-based timing flag
        self.history = []          # Tracks reps for CNS Fatigue Checks

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def classification(self):
        """Module 1.1: Automatically derives high school class based on current year."""
        current_year = datetime.now().year
        diff = self.grad_year - current_year
        if diff == 0: return "SR"
        elif diff == 1: return "JR"
        elif diff == 2: return "SO"
        elif diff == 3: return "FR"
        return "Alumni" if diff < 0 else "Prospect"

    # --- MODULE 2.2: TIMING NORMALIZATION ALGORITHM ---
    def get_normalized_fly(self):
        if not self.raw_fly_20m: return None
        if not self.is_hand_timed: return round(self.raw_fly_20m, 2)
        # Force round UP to nearest tenth, then apply human anticipation constant (+0.15)
        rounded = math.ceil(self.raw_fly_20m * 10) / 10.0
        return round(rounded + 0.15, 2)

    def get_normalized_block(self):
        if not self.raw_block_30m: return None
        if not self.is_hand_timed: return round(self.raw_block_30m, 2)
        rounded = math.ceil(self.raw_block_30m * 10) / 10.0
        return round(rounded + 0.15, 2)

    # --- MODULE 3: MULTI-VARIABLE 100M DASH PREDICTION ENGINE ---
    @property
    def projected_100m(self):
        fly = self.get_normalized_fly()
        block = self.get_normalized_block()
        if not fly or not block: 
            return None

        # Base Piecewise Calculation
        base_time = block + (3.5 * fly)

        # Module 3.2 Dynamic Speed Endurance Decay Constants (C)
        c_constant = 0.18  # Default Varsity Boys
        if self.gender == "Male":
            if base_time < 11.0: c_constant = 0.12
            else: c_constant = 0.18
        elif self.gender == "Female":
            if base_time < 12.2: c_constant = 0.15
            else: c_constant = 0.25

        return round(base_time + c_constant, 2)


class AppState:
    def __init__(self):
        self.organization_code = "RDZ-NORTHSIDE-2026"
        self.athletes = []
        self.pending_requests = [
            ("Marcus", "Vance", "Male", 2027, "Short Sprints", 1.98, 3.82),
            ("Jaden", "Rivers", "Male", 2026, "Short Sprints", 2.05, 3.95),
            ("Aaliyah", "Davis", "Female", 2028, "JV Girls", 2.30, 4.30),
            ("Devin", "Brooks", "Male", 2027, "Hurdlers", 2.18, 4.12)
        ]
        self._load_approved_roster()

    def _load_approved_roster(self):
        """Pre-populates the system with validated mock tracking profiles."""
        initial_roster = [
            ("Tyson", "Cross", "Male", 2026, "Short Sprints", 2.12, 4.05),
            ("Xavier", "Holt", "Male", 2027, "Short Sprints", 2.01, 3.89),
            ("Caleb", "Martinez", "Male", 2028, "Hurdlers", 2.25, 4.21),
            ("Chloe", "Lewis", "Female", 2026, "Short Sprints", 2.15, 4.10)
        ]
        for f, l, g, yr, grp, fly, blk in initial_roster:
            self.athletes.append(Athlete(f, l, g, yr, grp, fly, blk))

    def run_grade_rollover(self):
        """Module 1.2: Archives seniors and increments current active roster classes."""
        current_year = datetime.now().year
        active = [a for a in self.athletes if a.grad_year > current_year]
        for a in active:
            a.grad_year += 1
        self.athletes = active

# ==========================================
# 2. APPLICATION PRESENTATION USER INTERFACE
# ==========================================

class OnboardingRosterTab(QWidget):
    """Module 1: Manages decentralized requests and custom tracking groups."""
    def __init__(self, state, refresh_callback):
        super().__init__()
        self.state = state
        self.refresh_callback = refresh_callback
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left Column: Onboarding Approvals Queue
        left_panel = QGroupBox(f"Gatekeeper Queue - Code: {self.state.organization_code}")
        left_layout = QVBoxLayout(left_panel)
        
        self.queue_list = QListWidget()
        for f, l, g, yr, grp, _, _ in self.state.pending_requests:
            self.queue_list.addItem(f"📥 {f} {l} ({g}) - Class Year {yr} -> Subgroup: [{grp}]")
        left_layout.addWidget(self.queue_list)

        approve_btn = QPushButton("Approve Pending Roster Requests")
        approve_btn.setStyleSheet("background-color: #28A745; color: white; font-weight: bold; padding: 6px;")
        approve_btn.clicked.connect(self.approve_all)
        left_layout.addWidget(approve_btn)

        # Right Column: Active Sub-Roster Profiles View
        right_panel = QGroupBox("Sub-Roster Tagging Directory")
        right_layout = QVBoxLayout(right_panel)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter Subgroup View:"))
        self.group_combo = QComboBox()
        self.group_combo.addItems(["All Segments", "Short Sprints", "Hurdlers", "JV Girls"])
        self.group_combo.currentTextChanged.connect(self.populate_roster_table)
        filter_row.addWidget(self.group_combo)
        
        rollover_btn = QPushButton("Run Year-End Rollover")
        rollover_btn.setStyleSheet("background-color: #DC3545; color: white; font-size: 11px;")
        rollover_btn.clicked.connect(self.trigger_rollover)
        filter_row.addWidget(rollover_btn)
        right_layout.addLayout(filter_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Gender", "Class", "Group Tag", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.table)

        layout.addWidget(left_panel, int(1.2))
        layout.addWidget(right_panel, 2)
        self.populate_roster_table()

    def approve_all(self):
        if not self.state.pending_requests:
            QMessageBox.information(self, "Queue Clear", "No entry profile requests remaining.")
            return
        
        for f, l, g, yr, grp, fly, blk in self.state.pending_requests:
            self.state.athletes.append(Athlete(f, l, g, yr, grp, fly, blk))
        self.state.pending_requests.clear()
        self.queue_list.clear()
        self.populate_roster_table()
        self.refresh_callback()
        QMessageBox.information(self, "Roster Synced", "All pending athlete accounts approved into primary system.")

    def trigger_rollover(self):
        ret = QMessageBox.warning(self, "Confirm Rollover", "Archive graduating seniors and increment student class rosters by +1 year?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            self.state.run_grade_rollover()
            self.populate_roster_table()
            self.refresh_callback()

    def populate_roster_table(self):
        self.table.setRowCount(0)
        selected = self.group_combo.currentText()
        
        filtered = self.state.athletes if selected == "All Segments" else [a for a in self.state.athletes if a.group == selected]
        
        for idx, a in enumerate(filtered):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(a.name))
            self.table.setItem(idx, 1, QTableWidgetItem(a.gender))
            self.table.setItem(idx, 2, QTableWidgetItem(a.classification))
            self.table.setItem(idx, 3, QTableWidgetItem(a.group))
            self.table.setItem(idx, 4, QTableWidgetItem("Active Verified"))


class WorkoutTrackerTab(QWidget):
    """Module 2: Direct performance capture, timing engine conversion, and CNS warnings."""
    def __init__(self, state, refresh_callback):
        super().__init__()
        self.state = state
        self.refresh_callback = refresh_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Global Session Toggles Framework
        ctrl_box = QHBoxLayout()
        self.timing_toggle = QCheckBox("🚨 Hand-Timed Session Mode Active (Apply Rule Normalization)")
        self.timing_toggle.stateChanged.connect(self.sync_session_timing_mode)
        ctrl_box.addWidget(self.timing_toggle)
        ctrl_box.addStretch()
        layout.addLayout(ctrl_box)

        # Track Data Capture Form Matrix
        main_layout = QHBoxLayout()
table_group = QGroupBox("Performance Tracking Matrix")
tg_layout = QVBoxLayout(table_group)
self.table = QTableWidget(0, 5)
self.table.setHorizontalHeaderLabels(["Athlete Profile Name", "Raw 20m Fly (s)", "Raw 30m Block (s)", "FAT Normal Fly", "FAT Normal Block"])
self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
self.table.cellChanged.connect(self.handle_cell_input)
tg_layout.addWidget(self.table)
main_layout.addWidget(table_group, 3)
layout.addLayout(main_layout)
self.refresh_tracker_view()
def sync_session_timing_mode(self):
is_hand = self.timing_toggle.isChecked()
for a in self.state.athletes:
a.is_hand_timed = is_hand
self.refresh_tracker_view()
self.refresh_callback()
def handle_cell_input(self, row, col):
if col not in: return # Filter processing overrides to raw capture inputs
athlete = self.state.athletes[row]
item = self.table.item(row, col)
if not item or not item.text().strip(): return
try:
val = float(item.text())
if col == 1:
# CNS Fatigue Safety System Assessment (Module 5.2)
if athlete.raw_fly_20m and val > (athlete.raw_fly_20m * 1.05):
QMessageBox.critical(self, "🚨 CNS Fatigue Warning", f"Performance decay critical! {athlete.name}'s current rep ({val}s) has dropped over 5% below baseline mark. Suspend sprint intensity immediately to prevent injury.")
athlete.raw_fly_20m = val
elif col == 2:
athlete.raw_block_30m = val
# Repopulate tracking readouts asynchronously
self.table.blockSignals(True)
self.table.setItem(row, 3, QTableWidgetItem(f"{athlete.get_normalized_fly()} s" if athlete.get_normalized_fly() else "-"))
self.table.setItem(row, 4, QTableWidgetItem(f"{athlete.get_normalized_block()} s" if athlete.get_normalized_block() else "-"))
self.table.blockSignals(False)
self.refresh_callback()
except ValueError:
pass
def refresh_tracker_view(self):
self.table.blockSignals(True)
self.table.setRowCount(0)
for idx, a in enumerate(self.state.athletes):
self.table.insertRow(idx)
self.table.setItem(idx, 0, QTableWidgetItem(a.name))
self.table.setItem(idx, 1, QTableWidgetItem(str(a.raw_fly_20m) if a.raw_fly_20m else ""))
self.table.setItem(idx, 2, QTableWidgetItem(str(a.raw_block_30m) if a.raw_block_30m else ""))
self.table.setItem(idx, 3, QTableWidgetItem(f"{a.get_normalized_fly()} s" if a.get_normalized_fly() else "-"))
self.table.setItem(idx, 4, QTableWidgetItem(f"{a.get_normalized_block()} s" if a.get_normalized_block() else "-"))
self.table.blockSignals(False)
class LeaderboardTab(QWidget):
"""Module 5.1: Squad leaderboards with performance gamification micro-badges."""
def init(self, state):
super().init()
self.state = state
self.init_ui()
def init_ui(self):
layout = QVBoxLayout(self)
# Leaderboard Sorting Controls Row
ctrl_layout = QHBoxLayout()
ctrl_layout.addWidget(QLabel("Leaderboard Profile Track:"))
self.metric_combo = QComboBox()
self.metric_combo.addItems(["Projected 100m Dash Time", "Normalized 20m Fly Speed", "Normalized 30m Block Start"])
self.metric_combo.currentTextChanged.connect(self.render_leaderboard)
ctrl_layout.addWidget(self.metric_combo)
ctrl_layout.addStretch()
layout.addLayout(ctrl_layout)
self.table = QTableWidget(0, 5)
self.table.setHorizontalHeaderLabels(["Rank Position", "Athlete Name", "Classification", "FAT Performance Score", "Gamification Performance Badges"])
self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
layout.addWidget(self.table)
self.render_leaderboard()
def render_leaderboard(self):
self.table.setRowCount(0)
sel = self.metric_combo.currentText()
# Sorting strategy definitions
if "100m" in sel:
valid = [a for a in self.state.athletes if a.projected_100m]
ranked = sorted(valid, key=lambda x: x.projected_100m)
get_val = lambda x: f"{x.projected_100m} s"
elif "20m Fly" in sel:
valid = [a for a in self.state.athletes if a.get_normalized_fly()]
ranked = sorted(valid, key=lambda x: x.get_normalized_fly())
get_val = lambda x: f"{x.get_normalized_fly()} s"
else:
valid = [a for a in self.state.athletes if a.get_normalized_block()]
ranked = sorted(valid, key=lambda x: x.get_normalized_block())
get_val = lambda x: f"{x.get_normalized_block()} s"
for idx, athlete in enumerate(ranked, start=1):
row = self.table.rowCount()
self.table.insertRow(row)
# Visual Gold/Silver/Bronze Rank Elements
rank_item = QTableWidgetItem(f"🏆 {idx}" if idx <= 3 else str(idx))
if idx == 1: rank_item.setForeground(QColor("#D4AF37"))
# Module 5.1 System Micro-Badges
badges = []
if idx == 1: badges.append("⚡ Top Speed")
if athlete.raw_fly_20m and athlete.raw_fly_20m < 2.05: badges.append("🔥 Hot Streak")
if athlete.classification == "FR" or athlete.classification == "SO": badges.append("🚀 Big Climber")
badge_str = " ".join(badges) if badges else "• Core Tier Athlete"
self.table.setItem(row, 0, rank_item)
self.table.setItem(row, 1, QTableWidgetItem(athlete.name))
self.table.setItem(row, 2, QTableWidgetItem(f"{athlete.gender} - {athlete.classification}"))
self.table.setItem(row, 3, QTableWidgetItem(get_val(athlete)))
self.table.setItem(row, 4, QTableWidgetItem(badge_str))
class RelayBuilderTab(QWidget):
"""Module 4: 4x100m Relay Builder and Go Mark Calculator."""
def init(self, state):
super().init()
self.state = state
self.init_ui()
def init_ui(self):
layout = QHBoxLayout(self)
# Left Selection Control Panel
left_panel = QGroupBox("Relay Exchange Configurator")
left_layout = QFormLayout(left_panel)
self.incoming_combo = QComboBox()
self.outgoing_combo = QComboBox()
self.sync_athlete_combos()
left_layout.addRow(QLabel("Incoming Fast Finisher:"))
left_layout.addRow(self.incoming_combo)
left_layout.addRow(Spacer(1, 10))
left_layout.addRow(QLabel("Outgoing Acceleration Runner:"))
left_layout.addRow(self.outgoing_combo)
calc_btn = QPushButton("Calculate Go Mark Step Distance")
calc_btn.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold; padding: 8px; margin-top: 15px;")
calc_btn.clicked.connect(self.calculate_go_mark_distance)
left_layout.addRow(calc_btn)
# Right Metrics Readout Board Panel
self.right_panel = QGroupBox("Exchange Zone Output Tracking")
self.rp_layout = QVBoxLayout(self.right_panel)
self.result_lbl = QLabel("Select tactical incoming and outgoing athlete pairings to generate go marks.")
self.result_lbl.setWordWrap(True)
self.result_lbl.setStyleSheet("font-size: 13px; color: #555;")
self.rp_layout.addWidget(self.result_lbl)
layout.addWidget(left_panel, 1)
layout.addWidget(self.right_panel, 1)
def sync_athlete_combos(self):
self.incoming_combo.clear()
self.outgoing_combo.clear()
for idx, a in enumerate(self.state.athletes):
desc = f"{a.name} (Fly: {a.get_normalized_fly() if a.get_normalized_fly() else 'N/A'}s)"
self.incoming_combo.addItem(desc, idx)
desc_blk = f"{a.name} (Block: {a.get_normalized_block() if a.get_normalized_block() else 'N/A'}s)"
self.outgoing_combo.addItem(desc_blk, idx)
def calculate_go_mark_distance(self):
inc_idx = self.incoming_combo.currentData()
out_idx = self.outgoing_combo.currentData()
if inc_idx is None or out_idx is None: return
inc_athlete = self.state.athletes[inc_idx]
out_athlete = self.state.athletes[out_idx]
inc_fly = inc_athlete.get_normalized_fly()
out_block = out_athlete.get_normalized_block()
if not inc_fly or not out_block:
QMessageBox.critical(self, "Metrics Gap", "Both assigned exchange athletes must possess verified performance metric profiles.")
return
# --- MODULE 4.1: THE DIFFERENTIAL GAP FORMULA ---
try:
velocity_ratio = 20.0 / inc_fly
acceleration_displacement = out_block * 0.71
differential_distance = (velocity_ratio * acceleration_displacement) - 20.0 - 0.70
go_mark_steps = round(differential_distance * 3.28, 1)
# Dynamic Sanity Check Fallback Constraint Enforcement (Module 4.2)
if go_mark_steps < 8.0:
go_mark_steps = 13.0 # Developing Baseline Fallback
elif go_mark_steps > 28.0:
go_mark_steps = 20.0 # Varsity Baseline Fallback
except ZeroDivisionError:
go_mark_steps = 14.0
# Build Presentation Layout Cards
for i in reversed(range(self.rp_layout.count())):
w = self.rp_layout.itemAt(i).widget()
if w: w.deleteLater()
header = QLabel(f"⚡ GO MARK: {go_mark_steps} STEPS")
header.setStyleSheet("font-size: 20px; font-weight: bold; color: #007ACC; margin-bottom: 10px;")
self.rp_layout.addWidget(header)
detail_lbl = QLabel(
f"Incoming Carrier: {inc_athlete.name} ({inc_fly}s 20m Fly)\n"
f"Outgoing Carrier: {out_athlete.name} ({out_block}s 30m Block)\n\n"
f"Coaching Instructions:\n"
f"Inscribe a crisp mark exactly {go_mark_steps} heel-to-heel steps back from the apex boundary line. "
f"When the incoming runner's foot hits the tape mark, the outgoing athlete explodes into full acceleration drive."
)
detail_lbl.setWordWrap(True)
self.rp_layout.addWidget(detail_lbl)
self.rp_layout.addStretch()
class DataHubExportTab(QWidget):
"""Module 5.3: Automated AD Portfolio and verified recruitment CSV/PDF generation."""
def init(self, state):
super().init()
self.state = state
self.init_ui()
def init_ui(self):
layout = QVBoxLayout(self)
box = QGroupBox("AD Portfolio Blueprint Controls")
vbox = QVBoxLayout(box)
lbl = QLabel("Generate production-ready metrics folders and compliance sheets for athletic departments and NCAA recruitment portals.")
lbl.setStyleSheet("font-size: 12px; margin-bottom: 12px; color: #444;")
vbox.addWidget(lbl)
self.csv_btn = QPushButton(" 📊 Export Recruiter CSV Spreadsheet")
self.csv_btn.setStyleSheet("background-color: #E2F0D9; color: #385723; padding: 10px; font-weight: bold; text-align: left;")
self.csv_btn.clicked.connect(self.export_system_csv)
vbox.addWidget(self.csv_btn)
vbox.addSpacer(10)
self.pdf_btn = QPushButton(" 📕 Print High-Contrast Black & White Athletic Director PDF Report")
self.pdf_btn.setStyleSheet("background-color: #FCE4D6; color: #C65911; padding: 10px; font-weight: bold; text-align: left;")
self.pdf_btn.clicked.connect(self.export_system_pdf)
vbox.addWidget(self.pdf_btn)
layout.addWidget(box)
layout.addStretch()
def export_system_csv(self):
path, _ = QFileDialog.getSaveFileName(self, "Save Recruiter Roster Sheet", "", "CSV Files (*.csv)")
if not path: return
rows = [{
"Name": a.name, "Gender": a.gender, "Class": a.classification,
"Normalized 20m Fly": a.get_normalized_fly(), "Normalized 30m Block": a.get_normalized_block(),
"Projected 100m FAT": a.projected_100m
} for a in self.state.athletes]
pd.DataFrame(rows).to_csv(path, index=False)
QMessageBox.information(self, "Export Success", "Recruiter performance matrix compiled successfully to CSV.")
def export_system_pdf(self):
if not REPORTLAB_AVAILABLE:
QMessageBox.critical(self, "Dependency Exception", "ReportLab utility stack missing. Run 'pip install reportlab' to activate high contrast report configurations.")
return
path, _ = QFileDialog.getSaveFileName(self, "Print Portfolio Summary Document", "", "PDF Files (*.pdf)")
if not path: return
try:
doc = SimpleDocTemplate(path, pagesize=letter)
styles = getSampleStyleSheet()
story = []
title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, textColor=colors.black, spaceAfter=8)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, spaceAfter=15)
sign_style = ParagraphStyle('Sign', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=11, spaceBefore=30, textColor=colors.dimgray)
story.append(Paragraph("RDZ SPEED DEVELOPMENT PERFORMANCE PORTFOLIO", title_style))
story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d')} | High Contrast Black-and-White AD Printout", body_style))
story.append(Spacer(1, 10))
table_data = [["Athlete Profile", "Sex", "Class", "Norm 20m Fly", "Norm 30m Block", "Proj 100m FAT"]]
for a in self.state.athletes:
table_data.append([
a.name, a.gender, a.classification,
f"{a.get_normalized_fly()}s" if a.get_normalized_fly() else "-",
f"{a.get_normalized_block()}s" if a.get_normalized_block() else "-",
f"{a.projected_100m}s" if a.projected_100m else "-"
])
report_table = Table(table_data, colWidths=)
report_table.setStyle(TableStyle([
('BACKGROUND', (0,0), (-1,0), colors.black),
('TEXTCOLOR', (0,0), (-1,0), colors.white),
('ALIGN', (0,0), (-1,-1), 'CENTER'),
('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
('BOTTOMPADDING', (0,0), (-1,0), 6),
('GRID', (0,0), (-1,-1), 1, colors.black),
('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#EEEEEE')])
]))
story.append(report_table)
# Module 5.3 Required Official System Signature Block Verification Layout Element
story.append(Spacer(1, 20))
story.append(Paragraph("✍️ Verified by RDZ Speed Development Intelligence System", sign_style))
doc.build(story)
QMessageBox.information(self, "Export Success", "High-contrast AD validation file sent to storage path printer configurations.")
except Exception as e:
QMessageBox.critical(self, "Export Failure", f"Failed to assemble structural layout elements: {str(e)}")
==========================================
3. INTERACTIVE CONTAINER MAIN CONTROLLER
==========================================
class MainApplicationContainer(QMainWindow):
def init(self):
super().init()
self.setWindowTitle("RDZ Speed Development - Pro Coaching Dashboard")
self.setMinimumSize(QSize(1024, 680))
self.state = AppState()
self.init_ui()
def init_ui(self):
self.tabs = QTabWidget()
self.setCentralWidget(self.tabs)
self.onboarding_tab = OnboardingRosterTab(self.state, self.global_ui_refresh)
self.tracker_tab = WorkoutTrackerTab(self.state, self.global_ui_refresh)
self.leaderboard_tab = LeaderboardTab(self.state)
self.relay_tab = RelayBuilderTab(self.state)
self.export_tab = DataHubExportTab(self.state)
self.tabs.addTab(self.onboarding_tab, "👥 Roster Engine")
self.tabs.addTab(self.tracker_tab, "⏱️ Workout Tracker")
self.tabs.addTab(self.leaderboard_tab, "🏆 Leaderboards")
self.tabs.addTab(self.relay_tab, "⚡ 4x100 Relay Builder")
self.tabs.addTab(self.export_tab, "💾 AD Data Hub")
def global_ui_refresh(self):
"""Broadcasts structural event updates across active display tab components."""
self.tracker_tab.refresh_tracker_view()
self.leaderboard_tab.render_leaderboard()
self.relay_tab.sync_athlete_combos()
if name == "main":
app = QApplication(sys.argv)
app.setStyle("Fusion")
palette = QPalette()
palette.setColor(QPalette.ColorRole.Window, QColor("#F8F9FA"))
palette.setColor(QPalette.ColorRole.WindowText, QColor("#111111"))
app.setPalette(palette)
window = MainApplicationContainer()
window.show()
sys.exit(app.exec())
