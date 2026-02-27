import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Stress-Free Weekly Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------
# ------------------ CONSTANTS -----------------------
# ----------------------------------------------------

DAYS = [
    "Monday","Tuesday","Wednesday",
    "Thursday","Friday","Saturday","Sunday"
]

PRIORITY_WEIGHT = {"High":3,"Medium":2,"Low":1}

# ----------------------------------------------------
# ------------------ TIME HELPERS --------------------
# ----------------------------------------------------

def time_to_float(t):
    dt = datetime.strptime(t, "%I:%M %p")
    return dt.hour + dt.minute/60

def float_to_time(f):
    f = f % 24
    h = int(f)
    m = int(round((f-h)*60))
    if m == 60:
        m = 0
        h = (h+1) % 24
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    h12 = 12 if h12 == 0 else h12
    return f"{h12}:{m:02d} {suffix}"

def build_times():
    times=[]
    for h in range(24):
        for m in [0,30]:
            suffix = "AM" if h < 12 else "PM"
            h12 = h % 12
            h12 = 12 if h12 == 0 else h12
            times.append(f"{h12}:{m:02d} {suffix}")
    return times

TIMES = build_times()

# ----------------------------------------------------
# ------------------ STATE ---------------------------
# ----------------------------------------------------

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

# ----------------------------------------------------
# ------------------ STYLING -------------------------
# ----------------------------------------------------

st.markdown("""
<style>

.task-card {
    background-color:#EAF4EE;
    border:1px solid #D4E6DA;
    padding:16px 20px;
    border-radius:16px;
    margin-bottom:12px;
}

.task-title {
    font-weight:600;
    font-size:16px;
}

.task-sub {
    font-size:13px;
    opacity:0.75;
}

.sleep-box {
    background-color:#F3F7F4;
    border-radius:14px;
    padding:18px;
    margin-bottom:20px;
}

.commit-box {
    background-color:#F8FBF9;
    border-radius:14px;
    padding:18px;
}

.center-button {
    text-align:center;
    margin-top:40px;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# ------------------ HOME PAGE -----------------------
# ----------------------------------------------------

if st.session_state.page == "home":

    st.markdown("<h1 style='text-align:center;'>🌿 Welcome</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Build a week that feels balanced.</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;font-size:18px;'>Plan around your real life, protect your rest, and place what matters — gently.</p>",
        unsafe_allow_html=True
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns([2,1,2])
    with c2:
        if st.button("Let’s Get Started 🌿", use_container_width=True):
            st.session_state.page = "planning"
            st.rerun()

# ----------------------------------------------------
# ------------------ PLANNING PAGE -------------------
# ----------------------------------------------------

if st.session_state.page == "planning":

    st.markdown("<h1 style='text-align:center;'>🌿 Build Your Week</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Everything is going to be okay. Let’s organize it step by step.</p>", unsafe_allow_html=True)

    left,right = st.columns([1.2,1])

    # ---------------- TASKS ----------------

    with left:

        st.subheader("What needs your attention this week?")
        st.caption("Add each task and estimate the time it realistically needs.")

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

            st.markdown("### Your Added Tasks")
            st.caption("Use the trash icon to remove a task if plans change.")

            for i,task in enumerate(st.session_state.tasks):

                cols = st.columns([6,1])

                with cols[0]:
                    st.markdown(
                        f"""
                        <div class="task-card">
                            <div class="task-title">{task['name']}</div>
                            <div class="task-sub">
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

    # ---------------- RIGHT SIDE ----------------

    with right:

        # ---- Sleep ----
        st.markdown("<div class='sleep-box'>", unsafe_allow_html=True)
        st.subheader("Your Rest Window")
        st.caption("Set your consistent sleep rhythm for the week.")

        sleep_start = st.selectbox("Sleep Start", TIMES)
        sleep_end = st.selectbox("Sleep End", TIMES)

        st.session_state.sleep = (sleep_start,sleep_end)
        st.markdown("</div>", unsafe_allow_html=True)

        # ---- Commitments ----
        st.markdown("<div class='commit-box'>", unsafe_allow_html=True)
        st.subheader("What’s already scheduled?")
        st.caption("Add work, classes, gym — anything already committed.")

        for d in DAYS:
            with st.expander(d):

                label = st.text_input(f"{d} Label", key=f"{d}_label")
                start = st.selectbox(f"{d} Start", TIMES, key=f"{d}_start")
                end = st.selectbox(f"{d} End", TIMES, key=f"{d}_end")

                if st.button(f"Add to {d}", key=f"add_{d}", use_container_width=True):
                    if label.strip():
                        st.session_state.commitments[d].append((label,start,end))
                        st.rerun()

                for idx,block in enumerate(st.session_state.commitments[d]):
                    row = st.columns([4,1])
                    with row[0]:
                        st.caption(f"{block[0]}: {block[1]} → {block[2]}")
                    with row[1]:
                        if st.button("❌", key=f"del_block_{d}_{idx}", use_container_width=True):
                            st.session_state.commitments[d].pop(idx)
                            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- GENERATE BUTTON ----------------

    st.markdown("<div class='center-button'>", unsafe_allow_html=True)

    if st.button("Create My Week 🌿", use_container_width=True):

        st.session_state.schedule = {d: [] for d in DAYS}
        st.session_state.unscheduled = []

        sleep_start_f = time_to_float(st.session_state.sleep[0])
        sleep_end_f = time_to_float(st.session_state.sleep[1])

        # ---- Sleep Validation ----
        if sleep_start_f == sleep_end_f:
            st.error("Oops — that sleep window results in 0 hours of rest. Please adjust it.")
            st.stop()

        if sleep_start_f > sleep_end_f:
            sleep_duration = (24 - sleep_start_f) + sleep_end_f
        else:
            sleep_duration = sleep_end_f - sleep_start_f

        if sleep_duration < 4:
            st.warning("That’s a short sleep window. Make sure you’re protecting your energy.")
        if sleep_duration > 12:
            st.info("That’s quite a long sleep window — just confirming that’s intentional.")

        # ---- Sort Tasks ----
        remaining_tasks = sorted(
            [{"name":t["name"],"hours":t["hours"],"priority":t["priority"]}
             for t in st.session_state.tasks],
            key=lambda x: PRIORITY_WEIGHT[x["priority"]],
            reverse=True
        )

        # ---- Build Schedule ----
        for d in DAYS:

            blocked = []

            # Sleep blocks
            if sleep_start_f > sleep_end_f:
                blocked.append((sleep_start_f,24,"Sleep"))
                blocked.append((0,sleep_end_f,"Sleep"))
            else:
                blocked.append((sleep_start_f,sleep_end_f,"Sleep"))

            # Commitments
            for c in st.session_state.commitments[d]:
                blocked.append((time_to_float(c[1]),time_to_float(c[2]),c[0]))

            blocked.sort(key=lambda x:x[0])

            merged=[]
            for start,end,label in blocked:
                if not merged:
                    merged.append([start,end,label])
                else:
                    last=merged[-1]
                    if start <= last[1]:
                        last[1]=max(last[1],end)
                    else:
                        merged.append([start,end,label])

            # Build gaps
            gaps=[]
            prev_end=0
            for start,end,label in merged:
                if prev_end < start:
                    gaps.append((prev_end,start))
                prev_end=end
            if prev_end < 24:
                gaps.append((prev_end,24))

            day_schedule=[]
            for start,end,label in merged:
                day_schedule.append((label,start,end))

            # Fill gaps
            for gap_start,gap_end in gaps:
                while remaining_tasks and gap_start < gap_end:
                    task=remaining_tasks[0]
                    available = gap_end-gap_start
                    place=min(task["hours"],available)

                    day_schedule.append((task["name"],gap_start,gap_start+place))

                    task["hours"]-=place
                    gap_start+=place

                    if task["hours"]<=0:
                        remaining_tasks.pop(0)

            st.session_state.schedule[d]=sorted(day_schedule,key=lambda x:x[1])

        # Remaining
        for t in remaining_tasks:
            st.session_state.unscheduled.append((t["name"],t["hours"]))

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- OUTPUT ----------------

    if any(st.session_state.schedule[d] for d in DAYS):

        st.markdown("## 🌿 Your Weekly Layout")

        for d in DAYS:
            if st.session_state.schedule[d]:
                st.markdown(f"### {d}")
                for item in st.session_state.schedule[d]:
                    st.write(f"{item[0]}: {float_to_time(item[1])} → {float_to_time(item[2])}")

        if st.session_state.unscheduled:
            st.markdown("---")
            st.warning("There wasn’t enough room for everything this week. Here’s what remains:")
            for u in st.session_state.unscheduled:
                st.write(f"{u[0]} — {u[1]:.1f} hrs remaining")
