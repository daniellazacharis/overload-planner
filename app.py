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

        for i,task in enumerate(st.session_state.tasks):
            row=st.columns([5,1])
            with row[0]:
                st.markdown(f"**{task['name']}**  \n{task['hours']} hrs • {task['priority']}")
            with row[1]:
                if st.button("🗑️",key=f"del_{i}",use_container_width=True):
                    st.session_state.tasks.pop(i)
                    st.rerun()

    # ---------------- RIGHT ----------------
    with right:

        st.subheader("Your baseline rest rhythm")
        st.caption("Set your typical sleep window so we protect your recovery first.")

        sleep_start = st.selectbox("Sleep Start", TIMES, index=TIMES.index(st.session_state.sleep[0]))
        sleep_end = st.selectbox("Sleep End", TIMES, index=TIMES.index(st.session_state.sleep[1]))
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

        sleep_start_f = time_to_float(st.session_state.sleep[0])
        sleep_end_f = time_to_float(st.session_state.sleep[1])

        # Guardrail: identical sleep times
        if sleep_start_f == sleep_end_f:
            st.warning(
                "Oops — it looks like your sleep window starts and ends at the same time. "
                "We probably can’t get through the week with zero hours of rest. "
                "Please adjust your sleep window so we can protect your energy."
            )
            st.stop()

        # Calculate sleep duration
        if sleep_start_f > sleep_end_f:
            sleep_duration = (24 - sleep_start_f) + sleep_end_f
        else:
            sleep_duration = sleep_end_f - sleep_start_f

        # Gentle fatigue warning
        if sleep_duration < 4:
            st.warning(
                "That sleep window looks very short. Consistently getting less than 4 hours "
                "can significantly affect focus and recovery. Are you sure this reflects your typical week?"
            )

        # Long sleep confirmation
        if sleep_duration > 12:
            st.info(
                "That’s quite a long rest window. If this is intentional, great — "
                "just confirming that your sleep times are entered correctly."
            )

        # Calculate total available hours
        total_available = 0

        for d in DAYS:
            blocks=[]

            if sleep_start_f > sleep_end_f:
                blocks.append((sleep_start_f,24))
                blocks.append((0,sleep_end_f))
            else:
                blocks.append((sleep_start_f,sleep_end_f))

            for c in st.session_state.commitments[d]:
                blocks.append((time_to_float(c[1]), time_to_float(c[2])))

            blocks.sort(key=lambda x:x[0])

            current = sleep_end_f if sleep_start_f > sleep_end_f else sleep_end_f

            for start,end in blocks:
                if current < start:
                    total_available += start - current
                current = end

        total_task_hours = sum(t["hours"] for t in st.session_state.tasks)

        if total_task_hours > total_available:
            overflow = total_task_hours - total_available

            st.warning(
                f"You’ve scheduled about {total_task_hours:.1f} hours of tasks, "
                f"but only {total_available:.1f} hours are realistically available. "
                f"Roughly {overflow:.1f} hours may not fit this week."
            )

            st.markdown("### Here are a few gentle options:")
            st.markdown("""
            - **Break larger tasks into smaller pieces** so they can fit into shorter gaps.
            - **Reprioritize what truly needs to happen this week.**
            - **Adjust fixed commitments if possible** to create breathing room.
            - **Revisit your rest window carefully** only if it truly doesn’t reflect reality.
            """)

        # Build schedule
        st.session_state.schedule={d:[] for d in DAYS}

        sorted_tasks=sorted(
            st.session_state.tasks,
            key=lambda x: PRIORITY_WEIGHT[x["priority"]],
            reverse=True
        )

        for d in DAYS:

            blocks=[]

            if sleep_start_f > sleep_end_f:
                blocks.append(("Sleep", sleep_start_f,24))
                blocks.append(("Sleep",0,sleep_end_f))
                wake_time = sleep_end_f
            else:
                blocks.append(("Sleep",sleep_start_f,sleep_end_f))
                wake_time = sleep_end_f

            for c in st.session_state.commitments[d]:
                blocks.append((c[0], time_to_float(c[1]), time_to_float(c[2])))

            blocks.sort(key=lambda x:x[1])

            current = wake_time
            day_schedule=[]

            for label,start,end in blocks:

                if current < start:
                    while sorted_tasks and current < start:
                        task=sorted_tasks[0]
                        duration=task["hours"]

                        if current+duration<=start:
                            day_schedule.append((task["name"],current,current+duration))
                            current+=duration
                            sorted_tasks.pop(0)
                        else:
                            break

                day_schedule.append((label,start,end))
                current=end

            st.session_state.schedule[d]=day_schedule

    # ---------------- OUTPUT ----------------

    if any(st.session_state.schedule[d] for d in DAYS):

        st.markdown("## 🌿 Your Gentle Weekly Layout")
        st.caption("Here’s how your week flows when rest and reality come first.")

        for d in DAYS:
            if st.session_state.schedule[d]:
                st.markdown(f"### {d}")
                for item in st.session_state.schedule[d]:
                    st.write(f"{item[0]}: {float_to_time(item[1])} → {float_to_time(item[2])}")
