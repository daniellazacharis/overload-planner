import streamlit as st

from datetime import datetime, date, timedelta

st.set_page_config(page_title="Stress-Free Weekly Planner", page_icon="🌿", layout="wide")

# ---------------- CONSTANTS ----------------

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

PRIORITY_WEIGHT = {"High":3,"Medium":2,"Low":1}

MAX_TASK_HOURS_PER_DAY = 6

MAX_BLOCK = 2

# ---------------- TIME HELPERS ----------------

def time_to_float(t):

    dt = datetime.strptime(t, "%I:%M %p")

    return dt.hour + dt.minute/60

def float_to_time(f):

    h = int(f)

    m = int((f-h)*60)

    suffix = "AM" if h < 12 else "PM"

    h12 = h % 12 or 12

    return f"{h12}:{m:02d} {suffix}"

def build_times():

    times=[]

    for h in range(24):

        for m in [0,30]:

            suffix="AM" if h<12 else "PM"

            h12=h%12 or 12

            times.append(f"{h12}:{m:02d} {suffix}")

    return times

TIMES = build_times()

# ---------------- STATE ----------------

if "tasks" not in st.session_state:

    st.session_state.tasks=[]

if "commitments" not in st.session_state:

    st.session_state.commitments={d:[] for d in DAYS}

if "sleep" not in st.session_state:

    st.session_state.sleep=("11:00 PM","7:00 AM")

if "schedule" not in st.session_state:

    st.session_state.schedule={d:[] for d in DAYS}

if "unscheduled" not in st.session_state:

    st.session_state.unscheduled=[]

if "week_start" not in st.session_state:

    today=date.today()

    st.session_state.week_start=today - timedelta(days=today.weekday())

# ---------------- INPUT UI ----------------

st.title("🌿 Weekly Overload Planner")

st.subheader("Week Start")

st.session_state.week_start = st.date_input("", value=st.session_state.week_start)

# ---------------- TASK INPUT ----------------

st.subheader("Tasks")

name=st.text_input("Task Name")

hours=st.number_input("Hours", min_value=0.5, step=0.5)

priority=st.selectbox("Priority",["High","Medium","Low"])

due=st.date_input("Due Date")

if st.button("Add Task"):

    if name:

        st.session_state.tasks.append({

            "name":name,

            "hours":hours,

            "priority":priority,

            "due":due

        })

for i,t in enumerate(st.session_state.tasks):

    col1,col2=st.columns([5,1])

    col1.write(f"{t['name']} | {t['hours']}h | {t['priority']} | due {t['due']}")

    if col2.button("❌", key=i):

        st.session_state.tasks.pop(i)

        st.rerun()

# ---------------- SLEEP ----------------

st.subheader("Sleep")

sleep_start=st.selectbox("Sleep Start",TIMES)

sleep_end=st.selectbox("Sleep End",TIMES)

st.session_state.sleep=(sleep_start,sleep_end)

# ---------------- COMMITMENTS ----------------

st.subheader("Fixed Schedule")

for d in DAYS:

    with st.expander(d):

        label=st.text_input(f"{d} label", key=d)

        s=st.selectbox(f"{d} start",TIMES,key=d+"s")

        e=st.selectbox(f"{d} end",TIMES,key=d+"e")

        if st.button(f"Add {d}"):

            if label:

                st.session_state.commitments[d].append((label,s,e))

# ---------------- SCHEDULING ----------------

if st.button("Create Schedule"):

    st.session_state.schedule={d:[] for d in DAYS}

    st.session_state.unscheduled=[]

    week_dates={DAYS[i]:st.session_state.week_start+timedelta(days=i) for i in range(7)}

    tasks=sorted(st.session_state.tasks, key=lambda x:(x["due"], -PRIORITY_WEIGHT[x["priority"]]))

    # build day free hours

    day_capacity={d:MAX_TASK_HOURS_PER_DAY for d in DAYS}

    for task in tasks:

        due_index=(task["due"]-st.session_state.week_start).days

        allowed_days=DAYS[:due_index+1]

        remaining=task["hours"]

        for d in allowed_days:

            if remaining<=0:

                break

            available=day_capacity[d]

            if available<=0:

                continue

            chunk=min(MAX_BLOCK, remaining, available)

            st.session_state.schedule[d].append({

                "name":task["name"],

                "hours":chunk,

                "priority":task["priority"]

            })

            remaining-=chunk

            day_capacity[d]-=chunk

        if remaining>0:

            st.session_state.unscheduled.append((task["name"],remaining))

# ---------------- SUMMARY ----------------

if any(st.session_state.schedule.values()):

    st.header("📊 Weekly Summary")

    total_tasks=sum(t["hours"] for t in st.session_state.tasks)

    total_scheduled=sum(sum(i["hours"] for i in st.session_state.schedule[d]) for d in DAYS)

    col1,col2,col3=st.columns(3)

    col1.metric("Total Task Hours", total_tasks)

    col2.metric("Scheduled", total_scheduled)

    col3.metric("Unscheduled", total_tasks-total_scheduled)

    # ---------------- GRID VIEW ----------------

    st.header("🗓️ Timeline View")

    for d in DAYS:

        st.subheader(d)

        total=sum(i["hours"] for i in st.session_state.schedule[d])

        if total<2:

            label="🟢 Light"

        elif total<4:

            label="🟡 Balanced"

        elif total<6:

            label="🟠 Heavy"

        else:

            label="🔴 Overloaded"

        st.caption(label)

        for item in st.session_state.schedule[d]:

            color = "#FDECEC" if item["priority"]=="High" else "#FFF5E6" if item["priority"]=="Medium" else "#EEF7ED"

            st.markdown(f"""

            <div style="background:{color};padding:10px;border-radius:10px;margin-bottom:6px">

            <b>{item['name']}</b> — {item['hours']} hrs

            </div>

            """, unsafe_allow_html=True)

# ---------------- UNSCHEDULED ----------------

if st.session_state.unscheduled:

    st.warning("Not enough time before due dates:")

    for u in st.session_state.unscheduled:

        st.write(f"{u[0]} — {u[1]} hrs")