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

# ---------------- TIME HELPERS ----------------

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

# ---------------- STATE ----------------

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

# ---------------- UI ----------------

st.title("🌿 Stress-Free Weekly Planner")

left,right = st.columns([1.2,1])

# -------- TASKS --------
with left:
    st.subheader("Add Tasks")

    name = st.text_input("Task Name")
    hours = st.number_input("Hours Needed", min_value=0.5, step=0.5)
    priority = st.selectbox("Priority", ["High","Medium","Low"])

    if st.button("Add Task"):
        if name.strip():
            st.session_state.tasks.append({
                "name": name,
                "hours": hours,
                "priority": priority
            })

    for i,t in enumerate(st.session_state.tasks):
        if st.button(f"Delete {t['name']}", key=f"d{i}"):
            st.session_state.tasks.pop(i)
            st.rerun()

# -------- SLEEP + COMMITMENTS --------
with right:

    st.subheader("Sleep Window")
    sleep_start = st.selectbox("Sleep Start", TIMES)
    sleep_end = st.selectbox("Sleep End", TIMES)
    st.session_state.sleep=(sleep_start,sleep_end)

    st.subheader("Commitments")

    for d in DAYS:
        with st.expander(d):
            label = st.text_input(f"{d} Label", key=f"{d}_label")
            start = st.selectbox(f"{d} Start", TIMES, key=f"{d}_start")
            end = st.selectbox(f"{d} End", TIMES, key=f"{d}_end")

            if st.button(f"Add {d}", key=f"add_{d}"):
                if label.strip():
                    st.session_state.commitments[d].append((label,start,end))

# -------- GENERATE --------

if st.button("Generate Week"):

    st.session_state.schedule = {d: [] for d in DAYS}
    st.session_state.unscheduled = []

    sleep_start_f = time_to_float(st.session_state.sleep[0])
    sleep_end_f = time_to_float(st.session_state.sleep[1])

    tasks = sorted(
        [{"name":t["name"],"hours":t["hours"]} for t in st.session_state.tasks],
        key=lambda x: PRIORITY_WEIGHT[[tt for tt in st.session_state.tasks if tt["name"]==x["name"]][0]["priority"]],
        reverse=True
    )

    for d in DAYS:

        # Build blocked intervals
        blocked = []

        # Sleep
        if sleep_start_f > sleep_end_f:
            blocked.append((sleep_start_f,24,"Sleep"))
            blocked.append((0,sleep_end_f,"Sleep"))
        else:
            blocked.append((sleep_start_f,sleep_end_f,"Sleep"))

        # Commitments
        for c in st.session_state.commitments[d]:
            blocked.append((time_to_float(c[1]),time_to_float(c[2]),c[0]))

        blocked.sort(key=lambda x:x[0])

        # Merge overlapping
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

        # Fill gaps
        day_schedule=[]
        for start,end,label in merged:
            day_schedule.append((label,start,end))

        for gap_start,gap_end in gaps:
            while tasks and gap_start < gap_end:
                task=tasks[0]
                available = gap_end-gap_start
                place=min(task["hours"],available)

                day_schedule.append((task["name"],gap_start,gap_start+place))

                task["hours"]-=place
                gap_start+=place

                if task["hours"]<=0:
                    tasks.pop(0)

        st.session_state.schedule[d]=sorted(day_schedule,key=lambda x:x[1])

    # Remaining tasks
    for t in tasks:
        st.session_state.unscheduled.append((t["name"],t["hours"]))

# -------- OUTPUT --------

if any(st.session_state.schedule[d] for d in DAYS):

    for d in DAYS:
        if st.session_state.schedule[d]:
            st.markdown(f"### {d}")
            for item in st.session_state.schedule[d]:
                st.write(f"{item[0]}: {float_to_time(item[1])} → {float_to_time(item[2])}")

    if st.session_state.unscheduled:
        st.warning("Unscheduled Tasks:")
        for u in st.session_state.unscheduled:
            st.write(f"{u[0]} — {u[1]:.1f} hrs remaining")
