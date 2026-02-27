# app.py
import streamlit as st

st.set_page_config(
    page_title="Weekly Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# =========================
# COMPLETE STYLE OVERRIDE
# =========================
st.markdown("""
<style>

/* Remove Streamlit header */
header[data-testid="stHeader"] {display:none;}
.block-container {padding-top:6rem !important;}
.stApp {background:#F8F5F0;}

/* ---------- Typography ---------- */
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

/* ---------- TEXT INPUT ---------- */
div[data-testid="stTextInput"] > div > div{
    background:#FFFFFF !important;
    border-radius:16px !important;
    border:1px solid #D8D2C6 !important;
}
div[data-testid="stTextInput"] input{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

/* ---------- NUMBER INPUT FULL FIX ---------- */

/* Outer wrapper */
div[data-testid="stNumberInput"]{
    background:transparent !important;
}

/* Input container */
div[data-testid="stNumberInput"] > div{
    background:#FFFFFF !important;
    border-radius:16px !important;
    border:1px solid #D8D2C6 !important;
}

/* Actual input field */
div[data-testid="stNumberInput"] input{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

/* +/- button container */
div[data-testid="stNumberInput"] button{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
    border:none !important;
}

/* Remove dark fill behind number */
input[type="number"]{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

/* ---------- SELECTBOX ---------- */

div[data-testid="stSelectbox"] > div{
    background:#FFFFFF !important;
    border-radius:16px !important;
    border:1px solid #D8D2C6 !important;
}
div[data-testid="stSelectbox"] div{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

/* Dropdown popover FIX */
div[data-baseweb="popover"]{
    background:#FFFFFF !important;
}
div[role="listbox"]{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

/* Dropdown options */
li{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}
li:hover{
    background:#F2EEE7 !important;
}

/* ---------- EXPANDER ---------- */

div[data-testid="stExpander"]{
    background:#FFFFFF !important;
    border-radius:20px !important;
    border:1px solid #E6E0D5 !important;
}

/* Header */
div[data-testid="stExpander"] summary{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
    font-weight:600 !important;
    border-radius:20px !important;
}

/* Remove black open state */
details[open] > summary{
    background:#FFFFFF !important;
    color:#2F4F3E !important;
}

/* Remove hover flash */
details summary:hover{
    background:#FDFCF9 !important;
}

/* ---------- BUTTONS ---------- */
.stButton > button{
    background:#7A9E7E;
    color:white;
    border-radius:18px;
    padding:16px 28px;
    font-size:16px;
    border:none;
}
.stButton > button:hover{
    background:#6A8C6F;
}

/* ---------- Focus ---------- */
input:focus, select:focus{
    outline:none !important;
    box-shadow:0 0 0 2px #7A9E7E !important;
    border-color:#7A9E7E !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# UI
# =========================
st.markdown("<div class='big-title'>Plan Your Week</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Let’s organize your time in a way that actually feels doable.</div>", unsafe_allow_html=True)

left,right = st.columns([1.2,1])

with left:
    st.markdown("<div class='section-title'>Start with your to-do list</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Add each task and estimate the time it might take.</div>", unsafe_allow_html=True)

    st.text_input("Task Name")
    st.number_input("Estimated Time (hours)", min_value=0.0, step=0.25)

    st.button("Add Task")

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
            st.selectbox(f"{d} Start", time_options)
            st.selectbox(f"{d} End", time_options)
