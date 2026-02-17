# app.py
import streamlit as st
from datetime import date, timedelta
import time

st.set_page_config(page_title="Weekly Overload Planner", page_icon="🗓️", layout="wide")

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DIFFICULTY_ORDER = {"Low": 1, "Med": 2, "High": 3}

# ---------- CALM UI THEME ----------
st.markdown("""
<style>

.day-card {
    border-radius: 18px;
    padding: 18px 18px 10px 18px;
    margin-bottom: 18px;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.06);
    border: 1px solid rgba(0,0,0,0.05);
}

/* Workload colors */
.light { background-color: #E8F5EC; }        /* soft green */
.moderate { background-color: #E7F1FA; }     /* calm blue */
.heavy { background-color: #FFF4E5; }        /* soft amber */
.overloaded { background-color: #FDECEC; }   /* gentle red */
.rest { background-color: #F1ECFF; }         /* lavender */

.day-title {
    font-weight: 600;
    font-size: 20px;
    margin-bottom: 4px;
}

.day-sub {
    font-size: 13px;
    opacity: 0.75;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def init_state():
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "availability" not in st.session_state:
        st.session_state.availability = {
            "Mon": 2.0, "Tue": 2.0, "Wed": 2.0,
            "Thu": 2.0, "Fri": 2.0, "Sat": 2.0, "Sun": 2.0
        }
    if "schedule" not in st.session_state:
        st.session_state.schedule = {d: [] for d in DAYS}

def add_task(name: str, hours: float, difficulty: str, due: date):
    st.session_state.tasks.append(
        {
            "name": name.strip(),
            "hours": float(hours),
            "difficulty": difficulty,
            "due": due,
        }
    )

def reset_generation():
    st.session_state.generated = False
    st.session_state.schedule = {d: [] for d in DAYS}

def delete_task(index: int):
    if 0 <= index < len(st.session_state.tasks):
        st.session_state.tasks.pop(index)
    reset_generation()

def generate_placeholder_schedule():
    """
    REAL scheduling algorithm:
    - Respects daily availability
    - Prioritizes earliest due date
    - Splits tasks across days
    - Prevents scheduling after due date when possible
    """

    today = date.today()

    # Reset schedule
    schedule = {d: [] for d in DAYS}
    remaining = {d: float(st.session_state.availability.get(d, 0.0)) for d in DAYS}

    # Map weekday index to DAYS label
    def date_to_day_label(dt):
        return DAYS[dt.weekday()]

    # Sort by due date then difficulty
    tasks = sorted(
        st.session_state.tasks,
        key=lambda t: (t["due"], DIFFICULTY_ORDER.get(t["difficulty"], 99)),
    )

    for task in tasks:
        hours_left = float(task["hours"])
        current_day = today

        # -------- Schedule BEFORE due date --------
        while hours_left > 0 and current_day <= task["due"]:
            day_label = date_to_day_label(current_day)

            if remaining[day_label] > 0:
                chunk = min(hours_left, remaining[day_label])

                schedule[day_label].append({
                    "task": task["name"],
                    "hours": round(chunk, 2),
                    "difficulty": task["difficulty"],
                    "due": task["due"],
                })

                remaining[day_label] -= chunk
                hours_left -= chunk

            current_day += timedelta(days=1)

        # -------- If still unfinished: spillover --------
        while hours_left > 0:
            day_label = date_to_day_label(current_day)

            if remaining[day_label] > 0:
                chunk = min(hours_left, remaining[day_label])

                schedule[day_label].append({
                    "task": f"{task['name']} (Overdue)",
                    "hours": round(chunk, 2),
                    "difficulty": task["difficulty"],
                    "due": task["due"],
                })

                remaining[day_label] -= chunk
                hours_left -= chunk

            current_day += timedelta(days=1)

    st.session_state.schedule = schedule
    st.session_state.generated = True

def status_label(total_hours):
    if total_hours == 0:
        return "Free"
    if total_hours <= 2:
        return "Light"
    if total_hours <= 4:
        return "Balanced"
    return "Heavy"

def analyze_day(day, items):
    planned = round(sum(x["hours"] for x in items), 2)
    available = float(st.session_state.availability.get(day, 0.0))

    if planned == 0:
        return "REST", planned, available, 0

    if planned > available:
        overload = round(planned - available, 2)
        return "OVERLOAD", planned, available, overload

    return "NORMAL", planned, available, 0

def workload_classification(state, planned, available):
    if state == "REST":
        return "rest", "💪 Rest Day"

    if state == "OVERLOAD":
        return "overloaded", f"⚠️ Overloaded by {round(planned-available,2)}h"

    ratio = planned / available if available > 0 else 0

    if ratio <= 0.4:
        return "light", "Light Workload"
    elif ratio <= 0.75:
        return "moderate", "Moderate Workload"
    else:
        return "heavy", "Heavy Workload"

# ---------- App ----------
init_state()

st.title("Weekly Overload Planner")
st.caption("Plan a realistic week, not a perfect one.")

page = st.sidebar.radio("Navigation", ["Planner", "About", "How It Works"])

if page == "Planner":
    left, right = st.columns([1, 1])

    # ---------------- LEFT PANEL ----------------
    with left:
        st.subheader("Add Task")

        with st.form("add_task_form", clear_on_submit=True):
            task_name = st.text_input("Task Name")
            col1, col2 = st.columns(2)
            with col1:
                task_hours = st.number_input("Estimated Time (hours)", min_value=0.0, step=0.5, value=1.0)
            with col2:
                task_difficulty = st.selectbox("Difficulty", ["Low", "Med", "High"], index=1)

            task_due = st.date_input("Due Date", value=date.today() + timedelta(days=2))

            submitted = st.form_submit_button("➕ Add Task")
            if submitted:
                if not task_name.strip():
                    st.error("Please enter a task name.")
                else:
                    add_task(task_name, task_hours, task_difficulty, task_due)
                    reset_generation()
                    st.success("Task added!")

        st.divider()
        st.subheader("Your Tasks")

        if not st.session_state.tasks:
            st.info("No tasks yet.")
        else:
            for idx, t in enumerate(st.session_state.tasks):
                row1, row2 = st.columns([0.85, 0.15])
                with row1:
                    st.write(
                        f"**{t['name']}** — {t['hours']}h · {t['difficulty']} · due {t['due'].strftime('%b %d')}"
                    )
                with row2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        delete_task(idx)
                        st.rerun()

            # ---------------- DAILY AVAILABILITY ----------------
        st.divider()
        st.subheader("Daily Availability")
        
        st.caption("How many hours can you realistically work each day?")
        
        # 7 columns across
        day_cols = st.columns(7)
        
        for i, d in enumerate(DAYS):
            with day_cols[i]:
                new_val = st.number_input(
                    d,
                    min_value=0.0,
                    max_value=24.0,
                    step=0.5,
                    value=float(st.session_state.availability[d]),
                    key=f"availability_{d}"
                )
        
                # update state live
                st.session_state.availability[d] = new_val
                
    # ---------------- RIGHT PANEL ----------------
    with right:
        st.subheader("Your Balanced Week")

        generate = st.button("✨ Generate My Week", type="primary", use_container_width=True)

        if generate:
            # Fake loading bar (5 seconds total)
            progress = st.progress(0)
            for i in range(101):
                time.sleep(0.05)  # 0.05 * 100 ≈ 5 seconds
                progress.progress(i)

            generate_placeholder_schedule()
            st.success("Week Generated!")

            if st.session_state.generated:
    
        for d in DAYS:
            items = st.session_state.schedule.get(d, [])
    
            state, planned, available, overload = analyze_day(d, items)
            css_class, label = workload_classification(state, planned, available)
    
            # Card Start
            st.markdown(f"""
            <div class="day-card {css_class}">
                <div class="day-title">{d}</div>
                <div class="day-sub">{label} • {planned}h planned / {available}h available</div>
            """, unsafe_allow_html=True)
    
            # Tasks
            if state == "REST":
                st.markdown("*No work scheduled — recovery day*", unsafe_allow_html=True)
    
            else:
                for it in items:
                    st.markdown(f"- **{it['task']}** ({it['hours']}h) · {it['difficulty']}")
    
            # Close Card
            st.markdown("</div>", unsafe_allow_html=True)

                # Show tasks grouped under the day
                for it in items:
                    st.write(f"▢ **{it['task']}** ({it['hours']}h) · {it['difficulty']}")
        
                st.divider()

elif page == "About":
    st.subheader("About Weekly Overload Planner")
    st.write("A tool to turn chaotic task lists into structured weekly plans.")

elif page == "How It Works":
    st.subheader("How It Works")
    st.write("""
1. Add tasks with hours, difficulty, and due date.
2. Click **Generate My Week**.
3. The system sorts by due date and difficulty.
4. Tasks are allocated across Mon–Sun based on available time.
""")
