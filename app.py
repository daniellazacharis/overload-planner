# app.py
import streamlit as st
from datetime import date, timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from io import BytesIO

st.set_page_config(
    page_title="Weekly Planner",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---------- SOFT CALM STYLING ----------
st.markdown("""
<style>
.big-title {
    font-size: 42px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 10px;
}
.subtitle {
    text-align: center;
    font-size: 18px;
    color: #6B7280;
    margin-bottom: 40px;
}
.center-button {
    display: flex;
    justify-content: center;
    margin-top: 40px;
}
.day-card {
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ---------- STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "blocked" not in st.session_state:
    st.session_state.blocked = {d: [] for d in DAYS}
if "schedule" not in st.session_state:
    st.session_state.schedule = {d: [] for d in DAYS}
if "generated" not in st.session_state:
    st.session_state.generated = False

# ---------- TIME HELPERS ----------
def decimal_to_time_str(value):
    hours = int(value)
    minutes = int((value - hours) * 60)
    suffix = "AM" if hours < 12 else "PM"
    hour_12 = hours % 12
    hour_12 = 12 if hour_12 == 0 else hour_12
    return f"{hour_12}:{minutes:02d} {suffix}"

def generate_time_options():
    options = []
    for hour in range(24):
        for minute in [0, 30]:
            decimal = hour + minute / 60
            label = decimal_to_time_str(decimal)
            options.append((label, decimal))
    return options

# ---------- AVAILABILITY ----------
def compute_availability():
    availability = {}
    for d in DAYS:
        blocked_hours = sum(
            max(0, block["end"] - block["start"])
            for block in st.session_state.blocked[d]
        )
        availability[d] = max(0, 16 - blocked_hours)
    return availability

# ---------- SCHEDULING ----------
def generate_schedule():
    schedule = {d: [] for d in DAYS}
    availability = compute_availability()
    remaining = availability.copy()

    for task in st.session_state.tasks:
        hours_left = task["hours"]
        for d in DAYS:
            if remaining[d] > 0 and hours_left > 0:
                chunk = min(hours_left, remaining[d])
                schedule[d].append({
                    "task": task["name"],
                    "hours": chunk
                })
                remaining[d] -= chunk
                hours_left -= chunk

    st.session_state.schedule = schedule
    st.session_state.generated = True

# =====================================================
# ===================== HOME PAGE =====================
# =====================================================

if st.session_state.page == "Home":

    st.markdown("<div class='big-title'>✨ Welcome</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>A calm space to build a week you can actually breathe in.</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='center-button'>", unsafe_allow_html=True)
    if st.button("Let's Get Started 🌿"):
        st.session_state.page = "Planning"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# =================== PLANNING PAGE ===================
# =====================================================

elif st.session_state.page == "Planning":

    st.markdown("<div class='big-title'>Plan Your Week</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Add your tasks. Set your schedule. We'll help you balance it.</div>",
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    # ---------------- LEFT: TASK INPUT ----------------
    with left:
        st.subheader("Add Tasks")

        name = st.text_input("Task Name")

        # 15-minute increments (0.25 hours)
        hours = st.number_input(
            "Estimated Hours",
            min_value=0.0,
            max_value=20.0,
            step=0.25,
            format="%.2f"
        )

        if st.button("Add Task"):
            if name.strip():
                st.session_state.tasks.append({
                    "name": name,
                    "hours": hours
                })

        st.divider()

        if st.session_state.tasks:
            for i, task in enumerate(st.session_state.tasks):
                col1, col2 = st.columns([0.85,0.15])
                with col1:
                    st.write(f"{task['name']} — {task['hours']}h")
                with col2:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.tasks.pop(i)
                        st.rerun()

    # ---------------- RIGHT: SCHEDULE ----------------
    with right:
        st.subheader("Your Daily Schedule")

        time_options = generate_time_options()
        labels = [opt[0] for opt in time_options]
        mapping = dict(time_options)

        for d in DAYS:
            with st.expander(d):

                start_label = st.selectbox(
                    f"{d} Start",
                    labels,
                    key=f"start_{d}"
                )
                end_label = st.selectbox(
                    f"{d} End",
                    labels,
                    key=f"end_{d}"
                )

                start = mapping[start_label]
                end = mapping[end_label]

                if st.button(f"Add Block {d}", key=f"block_{d}"):
                    if end > start:
                        st.session_state.blocked[d].append({
                            "start": start,
                            "end": end
                        })

                for j, block in enumerate(st.session_state.blocked[d]):
                    colA, colB = st.columns([0.85,0.15])
                    with colA:
                        st.write(
                            f"{decimal_to_time_str(block['start'])} → "
                            f"{decimal_to_time_str(block['end'])}"
                        )
                    with colB:
                        if st.button("❌", key=f"delblock_{d}_{j}"):
                            st.session_state.blocked[d].pop(j)
                            st.rerun()

    # ---------------- CENTER GENERATE BUTTON ----------------
    st.markdown("<div class='center-button'>", unsafe_allow_html=True)
    if st.button("✨ Build My Week"):
        generate_schedule()
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- RESULTS ----------------
    if st.session_state.generated:
        st.divider()
        availability = compute_availability()

        for d in DAYS:
            planned = sum(t["hours"] for t in st.session_state.schedule[d])
            st.markdown(f"### {d} — {planned}h planned / {availability[d]}h available")

            for t in st.session_state.schedule[d]:
                st.write(f"- {t['task']} ({t['hours']}h)")
