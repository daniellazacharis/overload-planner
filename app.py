# app.py
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Weekly Overload Planner", page_icon="🗓️", layout="wide")

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DIFFICULTY_ORDER = {"Low": 1, "Med": 2, "High": 3}

# ---------- Helpers ----------
def init_state():
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "availability" not in st.session_state:
        st.session_state.availability = {d: 2.0 for d in DAYS}  # default
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

def clear_tasks():
    st.session_state.tasks = []
    st.session_state.generated = False
    st.session_state.schedule = {d: [] for d in DAYS}

def generate_placeholder_schedule():
    """
    Placeholder schedule:
    - Sort tasks by due date then difficulty
    - Allocate tasks sequentially through the week based on daily availability
    - This is intentionally simple; you can upgrade later.
    """
    tasks = sorted(
        st.session_state.tasks,
        key=lambda t: (t["due"], DIFFICULTY_ORDER.get(t["difficulty"], 99)),
    )

    remaining = {d: float(st.session_state.availability.get(d, 0.0)) for d in DAYS}
    schedule = {d: [] for d in DAYS}

    for t in tasks:
        hours_left = float(t["hours"])
        if hours_left <= 0:
            continue

        for d in DAYS:
            if hours_left <= 0:
                break
            if remaining[d] <= 0:
                continue

            chunk = min(hours_left, remaining[d])
            schedule[d].append(
                {
                    "task": t["name"],
                    "hours": round(chunk, 2),
                    "difficulty": t["difficulty"],
                }
            )
            remaining[d] = round(remaining[d] - chunk, 2)
            hours_left = round(hours_left - chunk, 2)

        # If we couldn't fit it, park what's left in the last day as "Overflow"
        if hours_left > 0:
            schedule["Sun"].append(
                {
                    "task": f"{t['name']} (Overflow)",
                    "hours": round(hours_left, 2),
                    "difficulty": t["difficulty"],
                }
            )

    st.session_state.schedule = schedule
    st.session_state.generated = True

def status_label(items):
    """Light / Balanced / Heavy based on number of scheduled items & total hours."""
    if not items:
        return "Free"
    total_hours = sum(x["hours"] for x in items)
    if total_hours <= 2:
        return "Light"
    if total_hours <= 4:
        return "Balanced"
    return "Heavy"


# ---------- App ----------
init_state()

st.title("Weekly Overload Planner")
st.caption('Plan a realistic week, not a perfect one.')

page = st.sidebar.radio("Navigation", ["Planner", "About", "How It Works"], index=0)

if page == "Planner":
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Add Task")

        with st.form("add_task_form", clear_on_submit=True):
            task_name = st.text_input("Task Name", placeholder="e.g., Study Chapter 3")
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
                    st.success("Task added!")

        st.divider()
        st.subheader("Daily Availability (hours)")

        av_cols = st.columns(7)
        for i, d in enumerate(DAYS):
            with av_cols[i]:
                st.session_state.availability[d] = st.number_input(
                    d,
                    min_value=0.0,
                    step=0.5,
                    value=float(st.session_state.availability.get(d, 0.0)),
                    key=f"avail_{d}",
                )

        st.divider()
        st.subheader("Your Tasks")

        if not st.session_state.tasks:
            st.info("No tasks yet. Add a few on the form above.")
        else:
            # display a compact list
            for idx, t in enumerate(st.session_state.tasks, start=1):
                st.write(
                    f"**{idx}. {t['name']}** — {t['hours']}h · {t['difficulty']} · due {t['due'].strftime('%b %d, %Y')}"
                )

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("🧹 Clear Tasks", use_container_width=True):
                    clear_tasks()
                    st.rerun()

    with right:
        st.subheader("Your Balanced Week")

        generate = st.button("✨ Generate My Week", type="primary", use_container_width=True)
        if generate:
            generate_placeholder_schedule()

        if not st.session_state.generated:
            st.info("Click **Generate My Week** to see a placeholder schedule for Mon–Sun.")
        else:
            # Schedule display (placeholder allocation)
            for d in DAYS:
                items = st.session_state.schedule.get(d, [])
                st.markdown(f"### {d} — *Status: {status_label(items)}*")

                if not items:
                    st.write("▫️ No scheduled tasks")
                else:
                    for it in items:
                        st.write(f"▢ **{it['task']}** ({it['hours']}h) · {it['difficulty']}")

                st.divider()

elif page == "About":
    st.subheader("About Weekly Overload Planner")
    st.write(
        """
Weekly Overload Planner is a lightweight tool for turning a messy task list into a realistic weekly plan.
You add tasks (with estimated time, difficulty, and due date), set how many hours you can handle each day,
and generate a weekly view.

This version includes a simple placeholder allocator to demonstrate the flow.
        """.strip()
    )

elif page == "How It Works":
    st.subheader("How It Works")
    st.write(
        """
1) Add tasks with:
- **Task Name**
- **Estimated hours**
- **Difficulty**
- **Due date**

2) Set your daily availability (**Mon–Sun**) in hours.

3) Click **Generate My Week** to create a placeholder schedule.

**Current logic (placeholder):**
- Tasks are sorted by due date, then difficulty
- Time is allocated across the week until daily availability is used up
- Any leftover becomes **Overflow** (placed on Sunday)

You can upgrade this later to:
- prioritize earlier due dates more aggressively
- avoid scheduling hard tasks back-to-back
- add “rest buffers”
- drag-and-drop editing
        """.strip()
    )
