# app.py
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="Weekly Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# =========================
# CALM LIGHT THEME
# =========================
st.markdown("""
<style>

.stApp {
    background-color: #F8F5F0;
}

.big-title {
    font-size: 48px;
    font-weight: 600;
    text-align: center;
    color: #2F4F3E;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    font-size: 20px;
    color: #5F6F65;
    margin-bottom: 20px;
}

.support-text {
    text-align: center;
    font-size: 16px;
    color: #7A8B80;
    max-width: 600px;
    margin: 0 auto 40px auto;
}

.section-title {
    font-size: 22px;
    font-weight: 600;
    color: #2F4F3E;
}

.section-sub {
    font-size: 14px;
    color: #7A8B80;
    margin-bottom: 15px;
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] > div {
    background-color: #FFFFFF !important;
    color: #2F4F3E !important;
    border-radius: 10px;
}

details > summary {
    color: #2F4F3E !important;
    font-weight: 500;
}

.stButton > button {
    background-color: #7A9E7E;
    color: white;
    border-radius: 30px;
    padding: 14px 0px;
    font-size: 16px;
}

.stButton > button:hover {
    background-color: #6A8C6F;
}

</style>
""", unsafe_allow_html=True)

# =========================
# STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "blocked" not in st.session_state:
    st.session_state.blocked = {d: [] for d in DAYS}

if "schedule" not in st.session_state:
    st.session_state.schedule = {d: [] for d in DAYS}

if "generated" not in st.session_state:
    st.session_state.generated = False

# =========================
# HELPERS
# =========================
def decimal_to_time_str(value):
    hours = int(value)
    minutes = int((value - hours) * 60)
    suffix = "AM" if hours < 12 else "PM"
    hour_12 = hours % 12
    hour_12 = 12 if hour_12 == 0 else hour_12
    return f"{hour_12}:{minutes:02d} {suffix}"

def generate_time_options():
    options = []
    for hour in range(24):
        for minute in [0, 30]:
            decimal = hour + minute / 60
            label = decimal_to_time_str(decimal)
            options.append((label, decimal))
    return options

def compute_availability():
    availability = {}
    for d in DAYS:
        blocked_hours = sum(
            max(0, block["end"] - block["start"])
            for block in st.session_state.blocked[d]
        )
        availability[d] = max(0, 16 - blocked_hours)
    return availability

def generate_schedule():
    schedule = {d: [] for d in DAYS}
    availability = compute_availability()
    remaining = availability.copy()

    for task in st.session_state.tasks:
        hours_left = task["hours"]
        for d in DAYS:
            if remaining[d] > 0 and hours_left > 0:
                chunk = min(hours_left, remaining[d])
                schedule[d].append({
                    "task": task["name"],
                    "hours": chunk
                })
                remaining[d] -= chunk
                hours_left -= chunk

    st.session_state.schedule = schedule
    st.session_state.generated = True

# =====================================================
# ===================== HOME PAGE =====================
# =====================================================

if st.session_state.page == "Home":
    
    st.markdown("""
    <div style='
        text-align: center;
        padding-top: 120px;
        padding-bottom: 120px;
    '>
    
        <div style='
            font-size: 48px;
            font-weight: 600;
            color: #2F4F3E;
            margin-bottom: 15px;
        '>
            🌿 Welcome
        </div>
    
        <div style='
            font-size: 22px;
            color: #556B5D;
            margin-bottom: 25px;
        '>
            Build a week that feels balanced.
        </div>
    
        <div style='
            font-size: 16px;
            color: #7A8B80;
            max-width: 600px;
            margin: 0 auto 50px auto;
            line-height: 1.6;
        '>
            Plan your tasks around your real availability — not your ideal schedule.
        </div>
    
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        if st.button("Let’s Get Started 🌿", use_container_width=True):
            st.session_state.page = "Planning"
            st.rerun()

# =====================================================
# =================== PLANNING PAGE ===================
# =====================================================

elif st.session_state.page == "Planning":

    st.markdown("<div class='big-title'>Plan Your Week</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Let’s organize your time in a way that actually feels doable.</div>", unsafe_allow_html=True)

    left, right = st.columns(2)

    # LEFT COLUMN
    with left:
        st.markdown("<div class='section-title'>Start with your to-do list</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Add each task and estimate the time it might take.</div>", unsafe_allow_html=True)

        name = st.text_input("Task Name")

        hours = st.number_input(
            "Estimated Time (hours)",
            min_value=0.0,
            max_value=20.0,
            step=0.25,
            format="%.2f"
        )

        if st.button("Add Task"):
            if name.strip():
                st.session_state.tasks.append({
                    "name": name,
                    "hours": hours
                })

        st.divider()

        for i, task in enumerate(st.session_state.tasks):
            colA, colB = st.columns([0.85,0.15])
            with colA:
                st.write(f"{task['name']} — {task['hours']}h")
            with colB:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.tasks.pop(i)
                    st.rerun()

    # RIGHT COLUMN
    with right:
        st.markdown("<div class='section-title'>When are you unavailable?</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Block off work, class, sleep, or personal time.</div>", unsafe_allow_html=True)

        time_options = generate_time_options()
        labels = [opt[0] for opt in time_options]
        mapping = dict(time_options)

        for d in DAYS:
            with st.expander(d):

                start_label = st.selectbox(f"{d} Start", labels, key=f"start_{d}")
                end_label = st.selectbox(f"{d} End", labels, key=f"end_{d}")

                start = mapping[start_label]
                end = mapping[end_label]

                if st.button(f"Add Block {d}", key=f"block_{d}"):
                    if end > start:
                        st.session_state.blocked[d].append({
                            "start": start,
                            "end": end
                        })

                for j, block in enumerate(st.session_state.blocked[d]):
                    colC, colD = st.columns([0.85,0.15])
                    with colC:
                        st.write(
                            f"{decimal_to_time_str(block['start'])} → "
                            f"{decimal_to_time_str(block['end'])}"
                        )
                    with colD:
                        if st.button("❌", key=f"delblock_{d}_{j}"):
                            st.session_state.blocked[d].pop(j)
                            st.rerun()

    # CENTER BUTTON
    st.markdown("<div style='text-align:center; margin-top:40px;'>", unsafe_allow_html=True)
    if st.button("Create My Week 🌿"):
        generate_schedule()
    st.markdown("</div>", unsafe_allow_html=True)

    # RESULTS
    if st.session_state.generated:
        st.divider()
        availability = compute_availability()

        for d in DAYS:
            planned = sum(t["hours"] for t in st.session_state.schedule[d])
            st.markdown(f"### {d} — {planned}h planned / {availability[d]}h available")

            for t in st.session_state.schedule[d]:
                st.write(f"- {t['task']} ({t['hours']}h)")
