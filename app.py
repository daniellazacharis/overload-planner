# app.py
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Weekly Overload Planner", layout="wide")

# -------------------------------------------------
# RELAXING THEME CSS
# -------------------------------------------------
st.markdown(
    """
<style>

/* Overall background */
.stApp {
    background-color: #F4F7F6;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #E6EFEE;
}

/* Headers */
h1, h2, h3 {
    color: #2F3E46;
}

/* Body text */
p, label, span {
    color: #5C6B73 !important;
}

/* Card containers */
.card {
    background-color: white;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0px 4px 18px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

/* Buttons */
.stButton > button {
    background-color: #7FAFA9;
    color: white;
    border-radius: 12px;
    border: none;
    padding: 10px 18px;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #6FA8A5;
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stDateInput input {
    border-radius: 10px;
}

/* Checkbox spacing */
.stCheckbox {
    padding: 3px 0px;
}

/* Success messages */
div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Divider */
hr {
    border-top: 1px solid #DDE6E5;
}

</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# STATE
# -------------------------------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "generated" not in st.session_state:
    st.session_state.generated = False

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DIFFICULTIES = ["Low", "Med", "High"]

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("Weekly Overload Planner")
page = st.sidebar.radio("Navigate", ["Planner", "About", "How It Works"])

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def placeholder_schedule(tasks):
    schedule = {d: [] for d in DAYS}

    if not tasks:
        schedule["Mon"] = [("Light Study", 1.5)]
        schedule["Tue"] = [("Homework", 2)]
        schedule["Wed"] = [("Review", 1)]
        schedule["Thu"] = [("Prep", 1)]
        schedule["Fri"] = [("Catch-up", 1)]
        schedule["Sat"] = [("Life Admin", 1)]
        schedule["Sun"] = [("Plan Next Week", 0.5)]
        return schedule

    i = 0
    for t in tasks:
        d = DAYS[i % 7]
        schedule[d].append((t["name"], t["hours"]))
        i += 1

    return schedule


def delete_task_at_index(idx: int):
    if 0 <= idx < len(st.session_state.tasks):
        st.session_state.tasks.pop(idx)
        st.session_state.generated = False  # so they regenerate after changes


# -------------------------------------------------
# PLANNER PAGE
# -------------------------------------------------
if page == "Planner":
    st.title("🗓️ Weekly Overload Planner")
    st.caption("Plan a realistic week, not a perfect one.")

    left, right = st.columns(2)

    # INPUT CARD
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Add Task")

        with st.form("task_form", clear_on_submit=True):
            name = st.text_input("Task Name")
            c1, c2 = st.columns(2)
            with c1:
                hours = st.number_input("Hours", 0.5, 20.0, 1.0, 0.5)
            with c2:
                diff = st.selectbox("Difficulty", DIFFICULTIES)

            due = st.date_input("Due Date", date.today() + timedelta(days=2))
            submit = st.form_submit_button("Add Task")

        if submit:
            if name and name.strip():
                st.session_state.tasks.append(
                    {"name": name.strip(), "hours": float(hours), "difficulty": diff, "due": due}
                )
                st.success("Task added")
                st.session_state.generated = False
            else:
                st.warning("Please enter a task name.")

        st.markdown("</div>", unsafe_allow_html=True)

        # TASK LIST + DELETE
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Your Tasks")

        if not st.session_state.tasks:
            st.write("No tasks yet. Add one above.")
        else:
            h1, h2, h3, h4, h5 = st.columns([3.2, 1.1, 1.2, 1.6, 1.0])
            h1.markdown("**Task**")
            h2.markdown("**Hours**")
            h3.markdown("**Diff**")
            h4.markdown("**Due**")
            h5.markdown("**Delete**")
            st.markdown("<hr/>", unsafe_allow_html=True)

            for idx, t in enumerate(st.session_state.tasks):
                c1, c2, c3, c4, c5 = st.columns([3.2, 1.1, 1.2, 1.6, 1.0])
                c1.write(t["name"])
                c2.write(f'{t["hours"]:.1f}')
                c3.write(t["difficulty"])
                c4.write(t["due"].strftime("%b %d, %Y"))

                if c5.button("🗑️", key=f"del_{idx}", help="Delete this task"):
                    delete_task_at_index(idx)
                    st.rerun()

            st.markdown("<hr/>", unsafe_allow_html=True)

            if st.button("Clear All Tasks"):
                st.session_state.tasks = []
                st.session_state.generated = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # AVAILABILITY CARD
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Daily Availability")
        availability = {}
        cols = st.columns(7)
        for i, d in enumerate(DAYS):
            with cols[i]:
                availability[d] = st.number_input(d, 0.0, 12.0, 2.0, 0.5, key=f"a{i}")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Generate My Week"):
            st.session_state.generated = True

    # OUTPUT CARD
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Your Balanced Week")

        if st.session_state.generated:
            sched = placeholder_schedule(st.session_state.tasks)

            for d in DAYS:
                st.markdown(f"### {d}")
                if sched[d]:
                    for item in sched[d]:
                        # unique key to avoid collisions if same name appears twice
                        st.checkbox(f"{item[0]} ({item[1]}h)", key=f"{d}_{item[0]}_{item[1]}")
                else:
                    st.write("Rest / Flex Time")
        else:
            st.info("Click Generate My Week to see your schedule")

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# ABOUT
# -------------------------------------------------
elif page == "About":
    st.title("About")
    st.write("A calming planning tool to reduce academic overwhelm and help students organize realistically.")

# -------------------------------------------------
# HOW IT WORKS
# -------------------------------------------------
else:
    st.title("How It Works")
    st.write(
        """
1. Add tasks
2. Enter daily availability
3. Generate a balanced week
(Current version uses placeholder scheduling)
"""
    )
