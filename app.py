# app.py
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Stress-Free Weekly Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
PRIORITY_ORDER = {"High":3,"Medium":2,"Low":1}

# ================= SESSION STATE =================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "availability" not in st.session_state:
    st.session_state.availability = {d: [] for d in DAYS}

if "schedule" not in st.session_state:
    st.session_state.schedule = {d: [] for d in DAYS}

# ================= STYLE =================
st.markdown("""
<style>
header {visibility:hidden;}
.stApp {background:#F8F5F0;}
.block-container {padding-top:5rem;}

.big-title {
    font-size:48px;
    font-weight:600;
    text-align:center;
    color:#2F4F3E;
}

.subtitle {
    text-align:center;
    font-size:20px;
    color:#556B5D;
    margin-bottom:40px;
}

.section-title {
    font-size:22px;
    font-weight:600;
    color:#2F4F3E;
}

.section-sub {
    font-size:14px;
    color:#7A8B80;
    margin-bottom:20px;
}

input, select {
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

::selection {
    background:#7A9E7E;
    color:white;
}

.stButton > button {
    background:#7A9E7E;
    color:white;
    border-radius:18px;
    padding:14px 28px;
    border:none;
}

.stButton > button:hover {
    background:#6A8C6F;
}
</style>
""", unsafe_allow_html=True)

# ================= HOME =================
if st.session_state.page == "home":

    st.markdown("<div class='big-title'>🌿 Welcome</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Build a week that feels balanced.</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Plan your tasks around your real availability — not your ideal schedule.</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Let’s Get Started 🌿"):
            st.session_state.page = "planning"
            st.rerun()

# ================= PLANNING =================
if st.session_state.page == "planning":

    st.markdown("<div class='big-title'>Plan Your Week</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Let’s organize your time in a way that actually feels doable.</div>", unsafe_allow_html=True)

    left, right = st.columns([1.2,1])

    # -------- TASK INPUT --------
    with left:
        st.markdown("<div class='section-title'>Start with your to-do list</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Add each task and estimate the time it might take.</div>", unsafe_allow_html=True)

        name = st.text_input("Task Name")
        hours = st.number_input("Estimated Time (hours)", min_value=0.25, step=0.25)
        priority = st.selectbox("Priority", ["High","Medium","Low"])

        if st.button("Add Task"):
            if name.strip():
                st.session_state.tasks.append({
                    "name": name,
                    "hours": hours,
                    "priority": priority
                })
                st.rerun()

        st.markdown("---")

        for i, task in enumerate(st.session_state.tasks):
            cols = st.columns([5,1])
            with cols[0]:
                st.write(f"**{task['name']}**")
                st.caption(f"{task['hours']} hrs • {task['priority']}")
            with cols[1]:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.tasks.pop(i)
                    st.rerun()

    # -------- AVAILABILITY --------
    with right:
        st.markdown("<div class='section-title'>When are you unavailable?</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Block off work, class, sleep, or personal time.</div>", unsafe_allow_html=True)

        times = []
        for h in range(24):
            for m in [0,30]:
                suffix = "AM" if h < 12 else "PM"
                h12 = h % 12
                h12 = 12 if h12 == 0 else h12
                times.append(f"{h12}:{m:02d} {suffix}")

        for d in DAYS:
            with st.expander(d):
                start = st.selectbox(f"{d} Start", times, key=f"{d}_start")
                end = st.selectbox(f"{d} End", times, key=f"{d}_end")

                if st.button(f"Add Block {d}", key=f"block_{d}"):
                    st.session_state.availability[d].append((start,end))
                    st.rerun()

                for idx, block in enumerate(st.session_state.availability[d]):
                    c1, c2 = st.columns([4,1])
                    with c1:
                        st.caption(f"{block[0]} → {block[1]}")
                    with c2:
                        if st.button("❌", key=f"del_block_{d}_{idx}"):
                            st.session_state.availability[d].pop(idx)
                            st.rerun()

    st.markdown("---")

    # -------- SCHEDULING --------
    if st.button("Create My Week 🌿"):

        # sort by priority
        sorted_tasks = sorted(
            st.session_state.tasks,
            key=lambda x: PRIORITY_ORDER[x["priority"]],
            reverse=True
        )

        st.session_state.schedule = {d: [] for d in DAYS}

        day_index = 0
        for task in sorted_tasks:
            st.session_state.schedule[DAYS[day_index]].append(task)
            day_index = (day_index + 1) % 7

    # -------- OUTPUT --------
    if any(st.session_state.schedule[d] for d in DAYS):
        st.markdown("<div class='section-title'>Your Week Schedule</div>", unsafe_allow_html=True)

        for d in DAYS:
            if st.session_state.schedule[d]:
                st.write(f"### {d}")
                for task in st.session_state.schedule[d]:
                    st.write(f"- {task['name']} ({task['hours']} hrs)")
