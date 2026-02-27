import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Stress-Free Weekly Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = [
    "Monday","Tuesday","Wednesday",
    "Thursday","Friday","Saturday","Sunday"
]

PRIORITY_WEIGHT = {"High":3,"Medium":2,"Low":1}

# ---------------- TIME UTILITIES ----------------

def time_to_float(t):
    dt = datetime.strptime(t, "%I:%M %p")
    return dt.hour + dt.minute/60

def float_to_time(f):
    if f >= 24:
        f -= 24
    h = int(f)
    m = int(round((f-h)*60))
    if m == 60:
        m = 0
        h += 1
        if h == 24:
            h = 0
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    h12 = 12 if h12 == 0 else h12
    return f"{h12}:{m:02d} {suffix}"

def build_time_list():
    times=[]
    for h in range(24):
        for m in [0,30]:
            suffix = "AM" if h < 12 else "PM"
            h12 = h % 12
            h12 = 12 if h12 == 0 else h12
            times.append(f"{h12}:{m:02d} {suffix}")
    return times

TIMES = build_time_list()

# ---------------- STATE ----------------

if "page" not in st.session_state:
    st.session_state.page = "home"

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "sleep" not in st.session_state:
    st.session_state.sleep = ("12:00 AM","6:00 AM")

if "commitments" not in st.session_state:
    st.session_state.commitments = {d: [] for d in DAYS}

if "schedule" not in st.session_state:
    st.session_state.schedule = {d: [] for d in DAYS}

if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []

# ---------------- HOME ----------------

if st.session_state.page == "home":

    st.markdown("<h1 style='text-align:center;'>🌿 Welcome</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Build a week that actually feels manageable.</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; font-size:18px;'>Plan around your real life — protect your rest — and gently place what matters.</p>",
        unsafe_allow_html=True
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns([2,1,2])
    with c2:
        if st.button("Start Building My Stress-Free Week 🌿", use_container_width=True):
            st.session_state.page="planning"
            st.rerun()

# ---------------- PLANNING ----------------

if st.session_state.page=="planning":

    st.markdown("<h1 style='text-align:center;'>🌿 Build Your Stress-Free Week</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; font-size:18px;'>Let’s gently organize your time around what actually matters.</p>",
        unsafe_allow_html=True
    )

    left,right = st.columns([1.2,1])

    # -------- TASKS --------
    with left:

        st.subheader("What needs your energy this week?")
        st.caption("Add tasks and estimate how much focus they’ll realistically need.")

        name = st.text_input("Task Name")
        hours = st.number_input("Hours Needed", min_value=0.5, step=0.5)
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

        if st.session_state.tasks:
            st.markdown("### Your Task List")
            st.caption("These are the tasks you've added.")

            for i, task in enumerate(st.session_state.tasks):
                cols = st.columns([6,1], vertical_alignment="center")

                with cols[0]:
                    st.markdown(
                        f"""
                        <div style="
                            background-color:#EAF4EE;
                            border:1px solid #D4E6DA;
                            padding:14px 18px;
                            border-radius:14px;
                            margin-bottom:10px;
                        ">
                            <div style="font-weight:600;">
                                {task['name']}
                            </div>
                            <div style="font-size:13px; opacity:0.75;">
                                {task['hours']} hrs • {task['priority']} priority
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with cols[1]:
                    if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                        st.session_state.tasks.pop(i)
                        st.rerun()

    # -------- SLEEP + COMMITMENTS --------
    with right:

        st.subheader("Your baseline rest rhythm")
        st.caption("Set your sleep window first — we protect that always.")

        sleep_start = st.selectbox("Sleep Start", TIMES)
        sleep_end = st.selectbox("Sleep End", TIMES)
        st.session_state.sleep=(sleep_start,sleep_end)

        st.markdown("---")

        st.subheader("What’s already spoken for?")
        st.caption("Add work, class, workouts, etc.")

        for d in DAYS:
            with st.expander(d):
                label = st.text_input(f"{d} Label", key=f"{d}_label")
                start = st.selectbox(f"{d} Start", TIMES, key=f"{d}_start")
                end = st.selectbox(f"{d} End", TIMES, key=f"{d}_end")

                if st.button(f"Add {d} Commitment", key=f"add_{d}", use_container_width=True):
                    if label.strip():
                        st.session_state.commitments[d].append((label,start,end))
                        st.rerun()

                for idx,block in enumerate(st.session_state.commitments[d]):
                    r=st.columns([4,1])
                    with r[0]:
                        st.caption(f"{block[0]}: {block[1]} → {block[2]}")
                    with r[1]:
                        if st.button("❌",key=f"del_{d}_{idx}",use_container_width=True):
                            st.session_state.commitments[d].pop(idx)
                            st.rerun()

    st.markdown("---")

    # -------- SCHEDULER --------

    if st.button("Create My Stress-Free Week 🌿", use_container_width=True):

        st.session_state.schedule = {d: [] for d in DAYS}
        st.session_state.unscheduled = []

        sleep_start_f = time_to_float(st.session_state.sleep[0])
        sleep_end_f = time_to_float(st.session_state.sleep[1])

        # Calculate sleep duration
        if sleep_start_f > sleep_end_f:
            sleep_duration = (24 - sleep_start_f) + sleep_end_f
        else:
            sleep_duration = sleep_end_f - sleep_start_f

        if sleep_duration < 4:
            st.warning("That sleep window is quite short. Less than 4 hours may impact recovery.")
        if sleep_duration > 12:
            st.info("That’s a long sleep window — just confirming it’s intentional.")

        # Sort tasks
        tasks = sorted(
            st.session_state.tasks,
            key=lambda x: PRIORITY_WEIGHT[x["priority"]],
            reverse=True
        )

        for d in DAYS:

            timeline=[]

            # Sleep block
            if sleep_start_f > sleep_end_f:
                timeline.append(("Sleep", sleep_start_f,24))
                timeline.append(("Sleep",0,sleep_end_f))
                current = sleep_end_f
            else:
                timeline.append(("Sleep",sleep_start_f,sleep_end_f))
                current = sleep_end_f

            # Commitments
            for c in st.session_state.commitments[d]:
                timeline.append((c[0], time_to_float(c[1]), time_to_float(c[2])))

            timeline.sort(key=lambda x:x[1])

            new_day=[]

            for label,start,end in timeline:

                # Fill gap before this block
                while tasks and current < start:
                    task = tasks[0]
                    available = start - current
                    place = min(task["hours"], available)

                    new_day.append((task["name"], current, current+place))

                    task["hours"] -= place
                    current += place

                    if task["hours"] <= 0:
                        tasks.pop(0)

                new_day.append((label,start,end))
                current = max(current,end)

            st.session_state.schedule[d]=new_day

        # Any remaining tasks
        for task in tasks:
            st.session_state.unscheduled.append((task["name"],task["hours"]))

    # -------- OUTPUT --------

    if any(st.session_state.schedule[d] for d in DAYS):

        st.markdown("## 🌿 Your Gentle Weekly Layout")

        for d in DAYS:
            if st.session_state.schedule[d]:
                st.markdown(f"### {d}")
                for item in st.session_state.schedule[d]:
                    st.write(f"{item[0]}: {float_to_time(item[1])} → {float_to_time(item[2])}")

        if st.session_state.unscheduled:
            st.markdown("---")
            st.warning("Some tasks could not be scheduled without overloading your week:")
            for u in st.session_state.unscheduled:
                st.write(f"{u[0]} — {u[1]:.1f} hrs remaining")
