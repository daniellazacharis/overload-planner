import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Stress-Free Weekly Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
PRIORITY_WEIGHT = {"High":3,"Medium":2,"Low":1}
DAY_CAPACITY = 12  # default available hours per day

# ---------------- UTILITIES ----------------

def time_to_float(t):
    dt = datetime.strptime(t, "%I:%M %p")
    return dt.hour + dt.minute/60

def calculate_available_hours(day):
    blocked = 0
    for start,end in st.session_state.availability[day]:
        blocked += max(0, time_to_float(end) - time_to_float(start))
    return max(0, DAY_CAPACITY - blocked)

# ---------------- STATE ----------------

if "page" not in st.session_state:
    st.session_state.page = "home"

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "availability" not in st.session_state:
    st.session_state.availability = {d: [] for d in DAYS}

if "schedule" not in st.session_state:
    st.session_state.schedule = {d: [] for d in DAYS}

# ---------------- HOME ----------------

if st.session_state.page == "home":

    st.markdown("<h1 style='text-align:center;'>🌿 Welcome</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>Build a week that feels balanced.</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:18px;'>Plan your tasks around your real availability — not your ideal schedule.</p>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2,1,2])
    with c2:
        if st.button("Let’s Get Started 🌿", use_container_width=True):
            st.session_state.page = "planning"
            st.rerun()

# ---------------- PLANNING ----------------

if st.session_state.page == "planning":

    st.markdown("<h1 style='text-align:center;'>Plan Your Week</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Let’s organize your time in a way that actually feels doable.</p>", unsafe_allow_html=True)

    left, right = st.columns([1.2,1])

    # -------- TASKS --------
    with left:
        st.subheader("Start with your to-do list")
        st.caption("Add each task and estimate the time it might take.")

        name = st.text_input("Task Name")
        hours = st.number_input("Estimated Time (hours)", min_value=0.25, step=0.25)
        priority = st.selectbox("Priority", ["High","Medium","Low"])

        if st.button("Add Task", use_container_width=True):
            if name.strip():
                st.session_state.tasks.append({
                    "name": name,
                    "hours": hours,
                    "priority": priority
                })
                st.rerun()

        st.markdown("---")

        for i, task in enumerate(st.session_state.tasks):
            row = st.columns([5,1])
            with row[0]:
                st.markdown(f"""
                **{task['name']}**  
                {task['hours']} hrs • {task['priority']}
                """)
            with row[1]:
                if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                    st.session_state.tasks.pop(i)
                    st.rerun()

    # -------- AVAILABILITY --------
    with right:
        st.subheader("When are you unavailable?")
        st.caption("Block off work, class, sleep, or personal time.")

        times = []
        for h in range(24):
            for m in [0,30]:
                suffix = "AM" if h < 12 else "PM"
                h12 = h % 12
                h12 = 12 if h12 == 0 else h12
                times.append(f"{h12}:{m:02d} {suffix}")

        for d in DAYS:
            with st.expander(f"{d} (Available: {calculate_available_hours(d):.1f} hrs)"):
                start = st.selectbox(f"{d} Start", times, key=f"{d}_start")
                end = st.selectbox(f"{d} End", times, key=f"{d}_end")

                if st.button(f"Add Block {d}", key=f"block_{d}", use_container_width=True):
                    st.session_state.availability[d].append((start,end))
                    st.rerun()

                for idx, block in enumerate(st.session_state.availability[d]):
                    r = st.columns([4,1])
                    with r[0]:
                        st.caption(f"{block[0]} → {block[1]}")
                    with r[1]:
                        if st.button("❌", key=f"del_block_{d}_{idx}", use_container_width=True):
                            st.session_state.availability[d].pop(idx)
                            st.rerun()

    st.markdown("---")

    # -------- SMART SCHEDULING --------
    if st.button("Create My Week 🌿", use_container_width=True):

        sorted_tasks = sorted(
            st.session_state.tasks,
            key=lambda x: PRIORITY_WEIGHT[x["priority"]],
            reverse=True
        )

        st.session_state.schedule = {d: [] for d in DAYS}
        remaining = {d: calculate_available_hours(d) for d in DAYS}

        for task in sorted_tasks:
            placed = False
            for d in DAYS:
                if remaining[d] >= task["hours"]:
                    st.session_state.schedule[d].append(task)
                    remaining[d] -= task["hours"]
                    placed = True
                    break
            if not placed:
                st.warning(f"⚠️ Could not place '{task['name']}' due to lack of available time.")

    # -------- OUTPUT --------
    if any(st.session_state.schedule[d] for d in DAYS):

        st.markdown("## Your Week Schedule")

        for d in DAYS:
            if st.session_state.schedule[d]:

                used = sum(t["hours"] for t in st.session_state.schedule[d])
                available = calculate_available_hours(d)

                st.markdown(f"### {d} ({used:.1f}/{available:.1f} hrs used)")

                if used > available:
                    st.error("Overloaded day")

                for task in st.session_state.schedule[d]:
                    st.write(f"• {task['name']} ({task['hours']} hrs)")
