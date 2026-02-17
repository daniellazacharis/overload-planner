# app.py
import streamlit as st
from datetime import date, timedelta
import time

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
        st.session_state.availability = {d: 2.0 for d in DAYS}
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
    tasks = sorted(
        st.session_state.tasks,
        key=lambda t: (t["due"], DIFFICULTY_ORDER.get(t["difficulty"], 99)),
    )

    remaining = {d: float(st.session_state.availability.get(d, 0.0)) for d in DAYS}
    schedule = {d: [] for d in DAYS}

    for t in tasks:
        hours_left = float(t["hours"])
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
            remaining[d] -= chunk
            hours_left -= chunk

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

def status_label(total_hours):
    if total_hours == 0:
        return "Free"
    if total_hours <= 2:
        return "Light"
    if total_hours <= 4:
        return "Balanced"
    return "Heavy"


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
                total_hours = round(sum(x["hours"] for x in items), 2)

                st.markdown(f"### {d}")
                st.write(f"**Total Planned Hours:** {total_hours}h")
                st.write(f"**Status:** {status_label(total_hours)}")

                if not items:
                    st.write("▫️ No scheduled tasks")
                else:
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
