# app.py
import streamlit as st
from datetime import date, timedelta

# ----------------------------
# App config
# ----------------------------
st.set_page_config(
    page_title="Weekly Overload Planner",
    page_icon="🗓️",
    layout="wide",
)

# ----------------------------
# Helpers
# ----------------------------
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DIFFICULTIES = ["Low", "Med", "High"]

def init_state():
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "generated" not in st.session_state:
        st.session_state.generated = False

def add_task(name: str, hours: float, difficulty: str, due: date):
    st.session_state.tasks.append(
        {"name": name.strip(), "hours": float(hours), "difficulty": difficulty, "due": due}
    )

def reset_generation():
    st.session_state.generated = False

def placeholder_schedule(tasks, availability):
    """
    Simple placeholder schedule:
    - Just displays availability + up to 2 tasks per day (not a real optimizer).
    - If no tasks, shows an example "Study / Admin / Life" block.
    """
    schedule = {d: [] for d in DAYS}

    # Example fallbacks
    example_blocks = {
        "Mon": [("Study Chapter 3", 1.5), ("Discussion Post", 0.5)],
        "Tue": [("Project Work", 2.0)],
        "Wed": [("Problem Set", 1.5), ("Email / Admin", 0.5)],
        "Thu": [("Review Notes", 1.0), ("Quiz Prep", 1.0)],
        "Fri": [("Catch-up Block", 1.5)],
        "Sat": [("Life + Reset", 1.0)],
        "Sun": [("Plan Next Week", 0.5), ("Light Review", 1.0)],
    }

    if not tasks:
        for d in DAYS:
            schedule[d] = example_blocks.get(d, [])
        return schedule

    # Naive placement: cycle through days and add tasks until each day has 2 items
    day_idx = 0
    for t in tasks:
        placed = False
        for _ in range(len(DAYS) * 2):
            d = DAYS[day_idx % len(DAYS)]
            if len(schedule[d]) < 2:
                schedule[d].append((t["name"], t["hours"]))
                placed = True
                day_idx += 1
                break
            day_idx += 1
        if not placed:
            # If everything is full, just append to Monday
            schedule["Mon"].append((t["name"], t["hours"]))

    return schedule

# ----------------------------
# State init
# ----------------------------
init_state()

# ----------------------------
# Sidebar navigation
# ----------------------------
st.sidebar.title("Weekly Overload Planner")
page = st.sidebar.radio("Navigate", ["Planner", "About", "How It Works"], index=0)

st.sidebar.divider()
st.sidebar.caption("Tip: Add tasks first, then set your Mon–Sun availability.")

# ----------------------------
# Pages
# ----------------------------
if page == "Planner":
    st.title("🗓️ Weekly Overload Planner")
    st.caption('Plan a realistic week, not a perfect one.')

    left, right = st.columns([1, 1], gap="large")

    # --- Left: Inputs
    with left:
        st.subheader("Input")

        st.markdown("### Add Task")
        with st.form("add_task_form", clear_on_submit=False):
            task_name = st.text_input("Task Name", placeholder="e.g., Study Chapter 3")
            col_a, col_b = st.columns(2)
            with col_a:
                task_hours = st.number_input("Estimated Time (hours)", min_value=0.0, value=1.0, step=0.5)
            with col_b:
                task_difficulty = st.selectbox("Difficulty", DIFFICULTIES, index=1)

            task_due = st.date_input("Due Date", value=date.today() + timedelta(days=2))

            submitted = st.form_submit_button("➕ Add Task", on_click=reset_generation)

        # Handle adding task (after submit)
        if submitted:
            if not task_name.strip():
                st.warning("Please enter a task name.")
            else:
                add_task(task_name, task_hours, task_difficulty, task_due)
                st.success("Task added!")

        # Show current tasks
        st.markdown("### Tasks")
        if st.session_state.tasks:
            for i, t in enumerate(st.session_state.tasks, start=1):
                st.write(
                    f"**{i}. {t['name']}** — {t['hours']}h — {t['difficulty']} — due {t['due'].strftime('%b %d, %Y')}"
                )

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("🧹 Clear tasks", type="secondary"):
                    st.session_state.tasks = []
                    st.session_state.generated = False
                    st.toast("Tasks cleared.")
            with c2:
                st.write("")  # spacer
        else:
            st.info("No tasks yet. Add a few above.")

        st.markdown("---")
        st.markdown("### Daily Availability (hours)")
        availability = {}
        avail_cols = st.columns(7)
        for idx, day in enumerate(DAYS):
            with avail_cols[idx]:
                availability[day] = st.number_input(
                    day,
                    min_value=0.0,
                    value=2.0 if day in ["Mon", "Tue", "Wed", "Thu"] else 1.0,
                    step=0.5,
                    key=f"avail_{day}",
                )

        st.markdown("---")
        if st.button("✨ Generate My Week", type="primary"):
            st.session_state.generated = True

    # --- Right: Output
    with right:
        st.subheader("Output")

        if not st.session_state.generated:
            st.info("Click **Generate My Week** to see your schedule.")
        else:
            st.markdown("### Your Balanced Week (placeholder)")
            schedule = placeholder_schedule(st.session_state.tasks, availability)

            # Display as day cards
            for day in DAYS:
                with st.container(border=True):
                    st.markdown(f"#### {day}  ·  Available: **{availability[day]}h**")
                    items = schedule.get(day, [])
                    if not items:
                        st.write("No tasks scheduled.")
                    else:
                        for (name, hrs) in items:
                            st.checkbox(f"{name} ({hrs}h)", value=False, key=f"chk_{day}_{name}_{hrs}")

            st.caption("This is a placeholder layout. You can later upgrade it to actually allocate tasks by due date, difficulty, and daily hours.")

elif page == "About":
    st.title("About")
    st.write(
        """
        **Weekly Overload Planner** helps you map tasks to a realistic week by combining:
        - A list of tasks (with estimated time, difficulty, and due dates)
        - Your daily availability (Mon–Sun)

        This starter app includes a **placeholder schedule** after you click “Generate My Week.”
        """
    )
    st.write("Built with Streamlit. 🧠")

elif page == "How It Works":
    st.title("How It Works")
    st.markdown(
        """
        1. **Add tasks** with a name, estimated hours, difficulty, and due date.
        2. **Set your availability** for each day (Mon–Sun).
        3. Click **Generate My Week** to show a schedule.

        **Current behavior:** the schedule is a placeholder meant to show layout and flow.
        You can later replace it with an allocation algorithm that:
        - prioritizes earlier due dates
        - spreads “High” difficulty tasks across the week
        - prevents exceeding daily availability
        """
    )
