# app.py
import streamlit as st

st.set_page_config(
    page_title="Weekly Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
PRIORITY_ORDER = {"High":3,"Medium":2,"Low":1}

# =========================
# STATE
# =========================
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "generated" not in st.session_state:
    st.session_state.generated = False

# =========================
# STYLE
# =========================
st.markdown("""
<style>
header[data-testid="stHeader"] {display:none;}
.block-container {padding-top:6rem !important;}
.stApp {background:#F8F5F0;}

.big-title{
    font-size:48px;
    font-weight:600;
    text-align:center;
    color:#2F4F3E;
}
.subtitle{
    text-align:center;
    font-size:20px;
    color:#556B5D;
    margin-bottom:40px;
}
.section-title{
    font-size:22px;
    font-weight:600;
    color:#2F4F3E;
}
.section-sub{
    font-size:14px;
    color:#7A8B80;
    margin-bottom:20px;
}

label{
    color:#2F4F3E !important;
    font-weight:500 !important;
}

input, select {
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

div[data-testid="stTextInput"] > div > div,
div[data-testid="stNumberInput"] > div,
div[data-testid="stSelectbox"] > div {
    background:#FFFFFF !important;
    border-radius:16px !important;
    border:1px solid #D8D2C6 !important;
}

div[data-testid="stNumberInput"] button {
    background:#FFFFFF !important;
    color:#2F4F3E !important;
    border:none !important;
}

div[data-testid="stSelectbox"] div,
div[data-baseweb="popover"],
div[role="listbox"],
li {
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

div[data-testid="stExpander"]{
    background:#FFFFFF !important;
    border-radius:20px !important;
    border:1px solid #E6E0D5 !important;
}

div[data-testid="stExpander"] summary{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
    font-weight:600 !important;
}

details[open] > summary{
    background:#FFFFFF !important;
}

.stButton > button{
    background:#7A9E7E;
    color:white;
    border-radius:18px;
    padding:14px 28px;
    font-size:16px;
    border:none;
}
.stButton > button:hover{
    background:#6A8C6F;
}

.task-card{
    background:#FFFFFF;
    padding:18px 22px;
    border-radius:18px;
    border:1px solid #E6E0D5;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<div class='big-title'>Plan Your Week</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Let’s organize your time in a way that actually feels doable.</div>", unsafe_allow_html=True)

left,right = st.columns([1.2,1])

# =========================
# LEFT SIDE - TASKS
# =========================
with left:
    st.markdown("<div class='section-title'>Start with your to-do list</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Add each task and estimate the time it might take.</div>", unsafe_allow_html=True)

    task_name = st.text_input("Task Name")
    task_hours = st.number_input("Estimated Time (hours)", min_value=0.25, step=0.25, format="%.2f")
    task_priority = st.selectbox("Priority", ["High","Medium","Low"])

    if st.button("Add Task"):
        if task_name.strip():
            st.session_state.tasks.append({
                "name": task_name,
                "hours": task_hours,
                "priority": task_priority
            })
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Display tasks
    # Display tasks
if st.session_state.tasks:

    for i, task in enumerate(st.session_state.tasks):

        col1, col2 = st.columns([5,1], vertical_alignment="center")

        with col1:
            st.markdown(
                f"""
                <div class='task-card'>
                    <div style='font-weight:600; font-size:16px; color:#2F4F3E;'>
                        {task['name']}
                    </div>
                    <div style='font-size:13px; color:#556B5D; margin-top:4px;'>
                        {task['hours']} hrs • {task['priority']} priority
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state.tasks.pop(i)
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Create My Week 🌿"):
    st.session_state.generated = True
# =========================
# RIGHT SIDE - AVAILABILITY
# =========================
with right:
    st.markdown("<div class='section-title'>When are you unavailable?</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Block off work, class, sleep, or personal time.</div>", unsafe_allow_html=True)

    time_options = []
    for hour in range(24):
        for minute in [0,30]:
            suffix = "AM" if hour < 12 else "PM"
            h12 = hour % 12
            h12 = 12 if h12 == 0 else h12
            time_options.append(f"{h12}:{minute:02d} {suffix}")

    for d in DAYS:
        with st.expander(d):
            st.selectbox(f"{d} Start", time_options, key=f"{d}_start")
            st.selectbox(f"{d} End", time_options, key=f"{d}_end")

# =========================
# SIMPLE PRIORITY SORT DEMO
# =========================
if st.session_state.generated and st.session_state.tasks:
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Your Week Overview</div>", unsafe_allow_html=True)

    sorted_tasks = sorted(
        st.session_state.tasks,
        key=lambda x: PRIORITY_ORDER[x["priority"]],
        reverse=True
    )

    for task in sorted_tasks:
        st.markdown(
            f"<div class='task-card'><b>{task['name']}</b> — "
            f"{task['hours']} hrs • {task['priority']}</div>",
            unsafe_allow_html=True
        )
