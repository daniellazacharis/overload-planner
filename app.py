# app.py
import streamlit as st
from datetime import date, timedelta
import time
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from io import BytesIO
import statistics

st.set_page_config(
    page_title="AI Cognitive Overload Planner",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DIFFICULTY_ORDER = {"Low": 1, "Med": 2, "High": 3}
COGNITIVE_WEIGHT = {"Low": 1, "Med": 1.5, "High": 2}

# ---------- STRESS-FREE COLOR SYSTEM ----------
st.markdown("""
<style>
.day-card {
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.06);
    transition: transform 0.2s ease;
}
.day-card:hover { transform: scale(1.01); }

.rest { background-color: #F3E8FF; }
.light { background-color: #E6F4EA; }
.moderate { background-color: #E7F0FA; }
.heavy { background-color: #FFF4E5; }
.overloaded { background-color: #FDECEC; }

.day-title { font-weight: 700; font-size: 20px; }
.day-sub { font-size: 14px; margin-bottom: 10px; }
.insight-box {
    background-color: #EEF2FF;
    padding: 15px;
    border-radius: 15px;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------- STATE ----------
def init_state():
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "blocked" not in st.session_state:
        st.session_state.blocked = {d: [] for d in DAYS}
    if "schedule" not in st.session_state:
        st.session_state.schedule = {d: [] for d in DAYS}
    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "unscheduled" not in st.session_state:
        st.session_state.unscheduled = []

init_state()

# ---------- TIME HELPERS ----------
def decimal_to_time_str(value, format_type):
    hours = int(value)
    minutes = int(round((value - hours) * 60))

    if format_type == "24-Hour":
        return f"{hours:02d}:{minutes:02d}"
    else:
        suffix = "AM" if hours < 12 else "PM"
        hour_12 = hours % 12
        hour_12 = 12 if hour_12 == 0 else hour_12
        return f"{hour_12}:{minutes:02d} {suffix}"

def time_str_to_decimal(hour, minute, am_pm=None):
    if am_pm:
        if am_pm == "PM" and hour != 12:
            hour += 12
        if am_pm == "AM" and hour == 12:
            hour = 0
    return hour + minute / 60

# ---------- AVAILABILITY ----------
def compute_availability():
    availability = {}
    for d in DAYS:
        blocked_hours = sum(
            max(0, block["end"] - block["start"])
            for block in st.session_state.blocked[d]
        )
        availability[d] = max(0, 16 - blocked_hours)  # assume 8h sleep
    return availability

# ---------- TASK MANAGEMENT ----------
def add_task(name, hours, difficulty, due):
    if name.strip():
        st.session_state.tasks.append({
            "name": name,
            "hours": hours,
            "difficulty": difficulty,
            "due": due
        })
        st.session_state.generated = False

def delete_task(index):
    if 0 <= index < len(st.session_state.tasks):
        st.session_state.tasks.pop(index)
        st.session_state.generated = False

# ---------- SCHEDULING ----------
def generate_schedule():
    today = date.today()
    schedule = {d: [] for d in DAYS}
    availability = compute_availability()
    remaining = availability.copy()
    unscheduled = []

    tasks = sorted(
        st.session_state.tasks,
        key=lambda t: (t["due"], DIFFICULTY_ORDER[t["difficulty"]])
    )

    def label(dt):
        return DAYS[dt.weekday()]

    for task in tasks:
        hours_left = task["hours"]
        current = today

        while hours_left > 0 and current <= task["due"]:
            d = label(current)
            if remaining[d] > 0:
                chunk = min(hours_left, remaining[d])
                schedule[d].append({
                    "task": task["name"],
                    "hours": chunk,
                    "difficulty": task["difficulty"]
                })
                remaining[d] -= chunk
                hours_left -= chunk
            current += timedelta(days=1)

        if hours_left > 0:
            unscheduled.append({
                "task": task["name"],
                "hours": hours_left
            })

    st.session_state.schedule = schedule
    st.session_state.unscheduled = unscheduled
    st.session_state.generated = True

# ---------- UI ----------
st.title("🧠 AI Cognitive Overload Planner")
st.caption("Constraint-based intelligent workload optimization")

left, right = st.columns([1,1])

with left:

    # CLOCK FORMAT
    st.subheader("Time Format")
    clock_format = st.radio(
        "Select Clock Format",
        ["24-Hour", "12-Hour"],
        horizontal=True
    )

    # ADD TASK
    st.subheader("Add Task")
    name = st.text_input("Task Name")
    hours = st.number_input("Estimated Hours", 0.0, 20.0, 1.0)
    difficulty = st.selectbox("Difficulty", ["Low","Med","High"])
    due = st.date_input("Due Date", value=date.today()+timedelta(days=2))

    if st.button("➕ Add Task"):
        add_task(name, hours, difficulty, due)
        st.success("Task added!")

    # SHOW TASKS
    st.divider()
    st.subheader("Your Tasks")

    if not st.session_state.tasks:
        st.info("No tasks added yet.")
    else:
        for i, task in enumerate(st.session_state.tasks):
            col1, col2 = st.columns([0.85,0.15])
            with col1:
                st.write(
                    f"**{task['name']}** — {task['hours']}h · {task['difficulty']} · due {task['due'].strftime('%b %d')}"
                )
            with col2:
                if st.button("🗑️", key=f"del_task_{i}"):
                    delete_task(i)
                    st.rerun()

    # BLOCKED TIME
    st.divider()
    st.subheader("Blocked Time (30-min Increments)")

    for d in DAYS:
        with st.expander(d):

            if clock_format == "24-Hour":
                start = st.number_input(
                    f"{d} Start",
                    min_value=0.0,
                    max_value=24.0,
                    step=0.5,
                    format="%.1f",
                    key=f"start_{d}"
                )
                end = st.number_input(
                    f"{d} End",
                    min_value=0.0,
                    max_value=24.0,
                    step=0.5,
                    format="%.1f",
                    key=f"end_{d}"
                )

            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    start_hour = st.selectbox(f"{d} Start Hour", list(range(1,13)), key=f"sh_{d}")
                with col2:
                    start_min = st.selectbox("Min", [0,30], key=f"sm_{d}")
                with col3:
                    start_ampm = st.selectbox("AM/PM", ["AM","PM"], key=f"sampm_{d}")
                start = time_str_to_decimal(start_hour, start_min, start_ampm)

                col4, col5, col6 = st.columns(3)
                with col4:
                    end_hour = st.selectbox(f"{d} End Hour", list(range(1,13)), key=f"eh_{d}")
                with col5:
                    end_min = st.selectbox("Min", [0,30], key=f"em_{d}")
                with col6:
                    end_ampm = st.selectbox("AM/PM", ["AM","PM"], key=f"eampm_{d}")
                end = time_str_to_decimal(end_hour, end_min, end_ampm)

            if st.button(f"Add Block to {d}", key=f"add_block_{d}"):
                if end > start:
                    st.session_state.blocked[d].append({
                        "start": start,
                        "end": end
                    })
                    st.success("Block added.")
                else:
                    st.error("End must be after start.")

            # Display Blocks
            if st.session_state.blocked[d]:
                st.markdown("**Current Blocks:**")
                for j, block in enumerate(st.session_state.blocked[d]):
                    colA, colB = st.columns([0.85,0.15])
                    with colA:
                        st.write(
                            f"{decimal_to_time_str(block['start'], clock_format)} → "
                            f"{decimal_to_time_str(block['end'], clock_format)}"
                        )
                    with colB:
                        if st.button("❌", key=f"del_block_{d}_{j}"):
                            st.session_state.blocked[d].pop(j)
                            st.rerun()

with right:
    if st.button("✨ Generate Intelligent Week"):
        generate_schedule()
        st.success("Optimized Schedule Generated")

    if st.session_state.generated:
        availability = compute_availability()

        for d in DAYS:
            planned = sum(t["hours"] for t in st.session_state.schedule[d])
            ratio = planned / availability[d] if availability[d] > 0 else 0

            if ratio == 0:
                css = "rest"
            elif ratio <= 0.4:
                css = "light"
            elif ratio <= 0.75:
                css = "moderate"
            elif ratio <= 1:
                css = "heavy"
            else:
                css = "overloaded"

            st.markdown(f"<div class='day-card {css}'>", unsafe_allow_html=True)
            st.markdown(f"<div class='day-title'>{d}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='day-sub'>{planned}h planned / {availability[d]}h available</div>", unsafe_allow_html=True)

            for t in st.session_state.schedule[d]:
                st.write(f"- {t['task']} ({t['hours']}h · {t['difficulty']})")

            st.markdown("</div>", unsafe_allow_html=True)
