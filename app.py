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

.day-title {
    font-weight: 700;
    font-size: 20px;
}
.day-sub {
    font-size: 14px;
    margin-bottom: 10px;
}
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

# ---------- AI AVAILABILITY CALCULATION ----------
def compute_availability():
    availability = {}
    for d in DAYS:
        blocked_hours = sum(
            (b["end"] - b["start"]) for b in st.session_state.blocked[d]
        )
        availability[d] = max(0, 16 - blocked_hours)  # assume 8h sleep baseline
    return availability

# ---------- TASK MANAGEMENT ----------
def add_task(name, hours, difficulty, due):
    st.session_state.tasks.append({
        "name": name,
        "hours": hours,
        "difficulty": difficulty,
        "due": due
    })

def delete_task(index):
    st.session_state.tasks.pop(index)

# ---------- SCHEDULING + BALANCING ----------
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

    # ---- BALANCING PASS (minimize variance) ----
    daily_loads = {
        d: sum(t["hours"] * COGNITIVE_WEIGHT[t["difficulty"]] for t in schedule[d])
        for d in DAYS
    }

    avg = statistics.mean(daily_loads.values())

    for d in DAYS:
        if daily_loads[d] > avg * 1.3:
            for target in DAYS:
                if daily_loads[target] < avg * 0.7 and schedule[d]:
                    move = schedule[d].pop()
                    schedule[target].append(move)
                    break

    st.session_state.schedule = schedule
    st.session_state.unscheduled = unscheduled
    st.session_state.generated = True

# ---------- STRESS SCORE ----------
def compute_stress():
    availability = compute_availability()
    overload_hours = 0
    cognitive_loads = []

    for d in DAYS:
        planned = sum(t["hours"] for t in st.session_state.schedule[d])
        cognitive = sum(
            t["hours"] * COGNITIVE_WEIGHT[t["difficulty"]]
            for t in st.session_state.schedule[d]
        )
        cognitive_loads.append(cognitive)
        if planned > availability[d]:
            overload_hours += planned - availability[d]

    variance = statistics.pvariance(cognitive_loads)
    unscheduled_penalty = sum(u["hours"] for u in st.session_state.unscheduled)

    score = overload_hours * 2 + variance + unscheduled_penalty * 3
    return round(score, 2)

# ---------- AI INSIGHT ----------
def generate_insight():
    availability = compute_availability()
    overload_days = []
    for d in DAYS:
        planned = sum(t["hours"] for t in st.session_state.schedule[d])
        if planned > availability[d]:
            overload_days.append(d)

    if overload_days:
        return f"You are overloaded on {', '.join(overload_days)}. Consider redistributing tasks."
    if st.session_state.unscheduled:
        return "Some work could not be scheduled. Adjust deadlines or reduce scope."
    return "Your workload is well balanced this week. Great planning!"

# ---------- PDF ----------
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>AI Cognitive Weekly Plan</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = []
    headers = []
    content = []

    for d in DAYS:
        planned = sum(t["hours"] for t in st.session_state.schedule[d])
        headers.append(Paragraph(f"<b>{d}</b><br/>{planned}h", styles["Normal"]))
        tasks = "<br/>".join(
            [f"• {t['task']} ({t['hours']}h)" for t in st.session_state.schedule[d]]
        ) or "-"
        content.append(Paragraph(tasks, styles["Normal"]))

    data.append(headers)
    data.append(content)

    table = Table(data, colWidths=[100]*7)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------- UI ----------
st.title("🧠 AI Cognitive Overload Planner")
st.caption("Constraint-based intelligent workload optimization")

left, right = st.columns([1,1])

with left:
    st.subheader("Add Task")
    name = st.text_input("Task Name")
    hours = st.number_input("Estimated Hours", 0.0, 20.0, 1.0)
    difficulty = st.selectbox("Difficulty", ["Low","Med","High"])
    due = st.date_input("Due Date", value=date.today()+timedelta(days=2))
    if st.button("Add Task"):
        add_task(name, hours, difficulty, due)

    st.divider()
    st.subheader("Blocked Time (System Infers Availability)")
    for d in DAYS:
        with st.expander(d):
            start = st.number_input(f"{d} Start Hour", 0.0, 24.0, 9.0, key=f"s{d}")
            end = st.number_input(f"{d} End Hour", 0.0, 24.0, 17.0, key=f"e{d}")
            if st.button(f"Block {d}", key=f"b{d}"):
                st.session_state.blocked[d].append({"start": start, "end": end})

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

        stress = compute_stress()
        st.markdown(f"### 🧠 Weekly Stress Score: {stress}")

        st.markdown(f"<div class='insight-box'>💡 {generate_insight()}</div>", unsafe_allow_html=True)

        if st.session_state.unscheduled:
            st.warning("Some tasks could not be scheduled.")

        pdf = generate_pdf()
        st.download_button("📄 Export PDF", pdf, "ai_weekly_plan.pdf")
