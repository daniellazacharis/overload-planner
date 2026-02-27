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
    st.session_state.sleep = ("11:00 PM","7:00 AM")

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

    # ---------------- LEFT ----------------
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
            st.caption("These are the tasks you've added. Use the trash icon to remove one.")

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
                            <div style="font-weight:600; font-size:15px; color:#2F4F3E;">
                                {task['name']}
                            </div>
                            <div style="font-size:13px; opacity:0.75; margin-top:4px;">
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

    # ---------------- RIGHT ----------------
    with right:

        st.subheader("Your baseline rest rhythm")
        st.caption("Set your typical sleep window so we protect your recovery first.")

        sleep_start = st.selectbox("Sleep Start", TIMES)
        sleep_end = st.selectbox("Sleep End", TIMES)
        st.session_state.sleep=(sleep_start,sleep_end)

        st.markdown("---")

        st.subheader("What’s already spoken for?")
        st.caption("Add work, class, workouts, or anything that already owns part of your day.")

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

    # ---------------- SCHEDULING ENGINE ----------------

    if st.button("Create My Stress-Free Week 🌿", use_container_width=True):

        st.session_state.schedule={d:[] for d in DAYS}
        st.session_state.unscheduled=[]

        sleep_start_f = time_to_float(st.session_state.sleep[0])
        sleep_end_f = time_to_float(st.session_state.sleep[1])

        if sleep_start_f == sleep_end_f:
            st.warning(
                "Oops — your sleep window starts and ends at the same time. "
                "We probably can’t get through the week with zero hours of rest. "
                "Please adjust your sleep window."
            )
            st.stop()

        # Sleep duration check
        if sleep_start_f > sleep_end_f:
            sleep_duration = (24 - sleep_start_f) + sleep_end_f
        else:
            sleep_duration = sleep_end_f - sleep_start_f

        if sleep_duration < 4:
            st.warning("That sleep window is very short. Less than 4 hours consistently may impact recovery.")

        if sleep_duration > 12:
            st.info("That’s a long sleep window. Just confirming it’s intentional.")

        # Build availability gaps
        availability_map = {}

        for d in DAYS:

            blocks=[]

            # Sleep blocks
            if sleep_start_f > sleep_end_f:
                blocks.append((sleep_start_f,24))
                blocks.append((0,sleep_end_f))
                wake_time = sleep_end_f
            else:
                blocks.append((sleep_start_f,sleep_end_f))
                wake_time = sleep_end_f

            # Commitments
            for c in st.session_state.commitments[d]:
                blocks.append((time_to_float(c[1]), time_to_float(c[2])))

            blocks.sort(key=lambda x:x[0])

            gaps=[]
            current = wake_time

            for start,end in blocks:
                if current < start:
                    gaps.append((current,start))
                current = max(current,end)

            availability_map[d]=gaps

        # Sort tasks by priority
        tasks = sorted(
            st.session_state.tasks,
            key=lambda x: PRIORITY_WEIGHT[x["priority"]],
            reverse=True
        )

        # Place tasks across gaps
        for task in tasks:
            hours_remaining = task["hours"]

            for d in DAYS:
                for gap_start,gap_end in availability_map[d]:

                    gap_size = gap_end - gap_start

                    if gap_size <= 0:
                        continue

                    if hours_remaining <= 0:
                        break

                    place = min(gap_size,hours_remaining)

                    st.session_state.schedule[d].append(
                        (task["name"], gap_start, gap_start+place)
                    )

                    gap_start += place
                    hours_remaining -= place

                if hours_remaining <= 0:
                    break

            if hours_remaining > 0:
                st.session_state.unscheduled.append(
                    (task["name"], hours_remaining)
                )

    # ---------------- OUTPUT ----------------

    if any(st.session_state.schedule[d] for d in DAYS):

        st.markdown("## 🌿 Your Gentle Weekly Layout")
        st.caption("Here’s how your week flows when rest and reality come first.")

        for d in DAYS:
            if st.session_state.schedule[d]:
                st.markdown(f"### {d}")
                for item in st.session_state.schedule[d]:
                    st.write(f"{item[0]}: {float_to_time(item[1])} → {float_to_time(item[2])}")

        if st.session_state.unscheduled:
            st.markdown("---")
            st.warning("Some work could not be scheduled without overloading your week.")
            for u in st.session_state.unscheduled:
                st.write(f"{u[0]} — {u[1]:.1f} hrs remaining")
