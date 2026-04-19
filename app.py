import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="Stress-Free Weekly Planner",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed")

# ------------------ CONSTANTS -----------------------
DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PRIORITY_WEIGHT = {"High": 3, "Medium": 2, "Low": 1}
MAX_TASK_HOURS_PER_DAY = 6.0
MAX_SINGLE_TASK_BLOCK = 2.0
COLORS = {
    #Task Priority and Types
    "high": "#FDECEC",
    "medium": "#FFF5E6",
    "low": "#EEF7ED",
    "sleep": "#EEF2FB",
    "commitment": "#F3F3F3",
    #Box Borders
    "border_high": "#F4C7C7",
    "border_medium": "#F3D7A6",
    "border_low": "#CFE6CC",
    "border_sleep": "#CCD8F0",
    "border_commitment": "#DDDDDD",
    
    "text": "#2F5E46",
    "muted": "#6E8577"}

# ------------------ TIME HELPERS --------------------
def time_to_float(t: str) -> float:
    dt = datetime.strptime(t, "%I:%M %p")
    return dt.hour + dt.minute / 60

def float_to_time(f: float) -> str:
    f = f % 24
    h = int(f)
    m = int(round((f - h) * 60))
    if m == 60:
        m = 0
        h = (h + 1) % 24
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    h12 = 12 if h12 == 0 else h12
    return f"{h12}:{m:02d} {suffix}"

def build_times():
    times = []
    for h in range(24):
        for m in [0, 30]:
            suffix = "AM" if h < 12 else "PM"
            h12 = h % 12
            h12 = 12 if h12 == 0 else h12
            times.append(f"{h12}:{m:02d} {suffix}")
    return times

TIMES = build_times()

def format_date(d: date) -> str:
    return d.strftime("%b %d, %Y")

def get_default_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())

def get_sleep_duration(start_f: float, end_f: float) -> float:
    if start_f == end_f:
        return 0
    if start_f > end_f:
        return (24 - start_f) + end_f
    return end_f - start_f

# ------------------ SCHEDULING HELPERS --------------

def build_blocked_intervals_for_day(day_name, sleep_tuple, commitments):
    blocked = []
    sleep_start_f = time_to_float(sleep_tuple[0])
    sleep_end_f = time_to_float(sleep_tuple[1])
    if sleep_start_f > sleep_end_f:
        blocked.append((sleep_start_f, 24.0, "Sleep", "sleep"))
        blocked.append((0.0, sleep_end_f, "Sleep", "sleep"))
    else:
        blocked.append((sleep_start_f, sleep_end_f, "Sleep", "sleep"))
    for label, start, end in commitments[day_name]:
        start_f = time_to_float(start)
        end_f = time_to_float(end)
        if start_f == end_f:
            continue
        if start_f > end_f:
            blocked.append((start_f, 24.0, label, "commitment"))
            blocked.append((0.0, end_f, label, "commitment"))
        else:
            blocked.append((start_f, end_f, label, "commitment"))
    blocked.sort(key=lambda x: x[0])

    merged = []

    for start, end, label, item_type in blocked:
        if not merged:
            merged.append([start, end, [label], [item_type]])
        else:
            last = merged[-1]
            if start <= last[1]:
                last[1] = max(last[1], end)
                last[2].append(label)
                last[3].append(item_type)
            else:
                merged.append([start, end, [label], [item_type]])
    return merged

def build_gaps_from_blocked(merged_blocked):
    gaps = []
    prev_end = 0.0
    for start, end, labels, item_types in merged_blocked:
        if prev_end < start:
            gaps.append([prev_end, start])
        prev_end = end
    if prev_end < 24.0:
        gaps.append([prev_end, 24.0])
    return gaps

def total_gap_hours(gaps):
    return sum(end - start for start, end in gaps)

def place_chunk_into_gaps(gaps, chunk_hours):
    remaining = chunk_hours
    placed_segments = []
    for gap in gaps:
        gap_start, gap_end = gap
        available = gap_end - gap_start
        if available <= 0:
            continue
        place = min(remaining, available)
        if place > 0:
            placed_segments.append((gap_start, gap_start + place))
            gap[0] = gap_start + place
            remaining -= place
        if remaining <= 0:
            break
    return placed_segments, remaining
    
def sort_schedule_items(items):
    return sorted(items, key=lambda x: x["start"])

def get_day_load_label(task_hours: float) -> str:
    if task_hours < 2:
        return "Light"
    elif task_hours < 4:
        return "Balanced"
    elif task_hours < 6:
        return "Heavy"
    return "Overloaded"

def get_load_color(task_hours: float) -> str:
    label = get_day_load_label(task_hours)
    if label == "Light":
        return "#EEF7ED"
    if label == "Balanced":
        return "#FFF5E6"
    if label == "Heavy":
        return "#FFE8CC"
    return "#FDECEC"

def get_item_colors(item):
    if item["type"] == "sleep":
        return COLORS["sleep"], COLORS["border_sleep"]
    if item["type"] == "commitment":
        return COLORS["commitment"], COLORS["border_commitment"]
    if item["priority"] == "High":
        return COLORS["high"], COLORS["border_high"]
    if item["priority"] == "Medium":
        return COLORS["medium"], COLORS["border_medium"]
    return COLORS["low"], COLORS["border_low"]

def clean_label(text, max_len=18):
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"

# ------------- VISUAL TIMELINE HTML -----------------

def build_visual_timeline_html(schedule, week_dates):
    scale_marks = [0, 6, 12, 18, 24]
    scale_labels = ["12 AM", "6 AM", "12 PM", "6 PM", "12 AM"]
    html = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            color: {COLORS["text"]};
            background: white;}}
        .timeline-shell {{
            padding: 8px 4px 8px 4px;}}
        .timeline-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;}}
        .legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid #DDEAE1;
            background: #F8FBF9;}}
        .swatch {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
            display: inline-block;
            border: 1px solid rgba(0,0,0,0.08);}}
        .timeline-day {{
            border: 1px solid #DDEAE1;
            border-radius: 18px;
            padding: 14px 14px 16px 14px;
            margin-bottom: 18px;
            background: #FFFFFF;}}
        .timeline-head {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 12px;
            margin-bottom: 10px;}}
        .timeline-day-name {{
            font-size: 20px;
            font-weight: 700;
            color: {COLORS["text"]};}}
        .timeline-day-date {{
            font-size: 13px;
            color: {COLORS["muted"]};}}
        .scale {{
            position: relative;
            height: 22px;
            margin-bottom: 8px;}}
        .scale-line {{
            position: absolute;
            left: 0;
            right: 0;
            top: 14px;
            height: 1px;
            background: #DDEAE1;}}
        .tick {{
            position: absolute;
            top: 8px;
            width: 1px;
            height: 12px;
            background: #DDEAE1;}}
        .tick-label {{
            position: absolute;
            top: 0;
            transform: translateX(-50%);
            font-size: 11px;
            color: {COLORS["muted"]};
            white-space: nowrap;}}
        .track {{
            display: flex;
            width: 100%;
            height: 52px;
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid #DDEAE1;
            background: #FAFCFB;}}
        .block {{
            height: 100%;
            box-sizing: border-box;
            padding: 6px 8px;
            border-right: 1px solid rgba(255,255,255,0.9);
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;}}
        .block-title {{
            font-size: 12px;
            font-weight: 700;
            line-height: 1.1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;}}
        .block-time {{
            font-size: 10px;
            margin-top: 3px;
            opacity: 0.82;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;}}
        .block-compact .block-time {{
            display: none;}}
        .block-tiny .block-title,
        .block-tiny .block-time {{
            display: none;}}
        .note {{
            font-size: 12px;
            color: {COLORS["muted"]};
            margin-top: 8px;}}
    </style>
    </head>
    <body>
    <div class="timeline-shell">
        <div class="timeline-legend">
            <div class="legend-item"><span class="swatch" style="background:{COLORS["high"]};"></span>High Priority</div>
            <div class="legend-item"><span class="swatch" style="background:{COLORS["medium"]};"></span>Medium Priority</div>
            <div class="legend-item"><span class="swatch" style="background:{COLORS["low"]};"></span>Low Priority</div>
            <div class="legend-item"><span class="swatch" style="background:{COLORS["sleep"]};"></span>Sleep</div>
            <div class="legend-item"><span class="swatch" style="background:{COLORS["commitment"]};"></span>Fixed Commitment</div>
        </div>
    """
    for d in DAYS:
        html += f"""
        <div class="timeline-day">
            <div class="timeline-head">
                <div class="timeline-day-name">{d}</div>
                <div class="timeline-day-date">{format_date(week_dates[d])}</div>
            </div>
            <div class="scale">
                <div class="scale-line"></div>
        """
        for mark, label in zip(scale_marks, scale_labels):
            pct = (mark / 24) * 100
            html += f"""
                <div class="tick" style="left:{pct}%;"></div>
                <div class="tick-label" style="left:{pct}%;">{label}</div>
            """
        html += """</div><div class="track">"""
        if schedule[d]:
            for item in schedule[d]:
                width_pct = max(((item["end"] - item["start"]) / 24) * 100, 0.6)
                bg, border = get_item_colors(item)
                label = clean_label(item["label"], 18)
                start_text = float_to_time(item["start"])
                end_text = float_to_time(item["end"])
                block_class = ""
                if width_pct < 7:
                    block_class = "block-tiny"
                elif width_pct < 12:
                    block_class = "block-compact"
                html += f"""
                <div class="block {block_class}" style="width:{width_pct}%; background:{bg}; border-right:1px solid {border};">
                    <div class="block-title">{label}</div>
                    <div class="block-time">{start_text} → {end_text}</div>
                </div>
                """
        else:
            html += """
                <div class="block" style="width:100%; background:#FFFFFF;">
                    <div class="block-title">No scheduled items</div>
                </div>
            """
        html += """
            </div>
            <div class="note">Blocks are sized based on duration across the day.</div>
        </div>
        """
    html += """
    </div>
    </body>
    </html>
    """
    return html

# ------------------ STATE ---------------------------

if "page" not in st.session_state:
    st.session_state.page = "home"

if "week_start" not in st.session_state:
    st.session_state.week_start = get_default_monday()

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "sleep" not in st.session_state:
    st.session_state.sleep = ("11:00 PM", "7:00 AM")

if "commitments" not in st.session_state:
    st.session_state.commitments = {d: [] for d in DAYS}

if "schedule" not in st.session_state:
    st.session_state.schedule = {d: [] for d in DAYS}

if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []

if "generation_complete" not in st.session_state:
    st.session_state.generation_complete = False

# ------------------ STYLING -------------------------

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Arial, sans-serif;}
.block-container {
    max-width: 950px;
    padding-top: 2rem;
    padding-bottom: 3rem;}
.home-title {
    text-align: center;
    color: #2F5E46;
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 0.25rem;}
.home-subtitle {
    text-align: center;
    color: #2F5E46;
    font-size: 2rem;
    font-weight: 600;
    margin-bottom: 1rem;}
.home-text {
    text-align: center;
    color: #4F695C;
    font-size: 1.2rem;
    max-width: 800px;
    margin: 0 auto 1.5rem auto;
    line-height: 1.6;}
@media (max-width: 900px) {
    .home-title { font-size: 2.4rem; }
    .home-subtitle { font-size: 1.6rem; }
    .home-text { font-size: 1.05rem; }}
</style>
""", unsafe_allow_html=True)

# ------------------ HOME PAGE -----------------------

if st.session_state.page == "home":
    st.markdown("<div class='home-title'>🌿 Welcome</div>", unsafe_allow_html=True)
    st.markdown("<div class='home-subtitle'>Build a week that feels balanced.</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='home-text'>Plan around your real life, protect your rest, and place what matters — gently.</div>",
        unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        if st.button("Let’s Get Started 🌿", use_container_width=True):
            st.session_state.page = "planning"
            st.rerun()

# ------------------ PLANNING PAGE -------------------

if st.session_state.page == "planning":
    top1, top2 = st.columns([1, 4])
    with top1:
        if st.button("← Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    st.markdown("<h1 style='text-align:center;color:#2F5E46;'>🌿 Build Your Week</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#4F695C;'>Everything is going to be okay. Let’s organize it step by step.</p>",
        unsafe_allow_html=True)
    st.subheader("Week Setup")
    st.caption("Choose the Monday that starts the week you want to plan.")
    st.session_state.week_start = st.date_input(
        "Week Start Date",
        value=st.session_state.week_start)
    week_dates = {DAYS[i]: st.session_state.week_start + timedelta(days=i) for i in range(7)}
    st.markdown("---")
    st.subheader("What needs your attention this week?")
    st.caption("Add each task, estimate the time it realistically needs, and choose its due date.")
    name = st.text_input("Task Name")
    hours = st.number_input("Hours Needed", min_value=0.5, step=0.5)
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    due_date = st.date_input(
        "Due Date",
        value=st.session_state.week_start + timedelta(days=6),
        min_value=st.session_state.week_start,
        max_value=st.session_state.week_start + timedelta(days=6))
    if st.button("Add Task", use_container_width=True):
        if name.strip():
            st.session_state.tasks.append({
                "name": name.strip(),
                "hours": float(hours),
                "priority": priority,
                "due_date": due_date})
            st.session_state.generation_complete = False
            st.rerun()
    if st.session_state.tasks:
        st.markdown("### Your Added Tasks")
        st.caption("Use the trash icon to remove a task if plans change.")
        sorted_display_tasks = sorted(
            enumerate(st.session_state.tasks),
            key=lambda x: (x[1]["due_date"], -PRIORITY_WEIGHT[x[1]["priority"]], x[1]["name"].lower()))
        for original_index, task in sorted_display_tasks:
            c1, c2 = st.columns([6, 1])
            with c1:
                with st.container(border=True):
                    st.markdown(f"**{task['name']}**")
                    st.caption(f"{task['hours']:.1f} hrs • {task['priority']} priority")
                    st.caption(f"Due: {format_date(task['due_date'])}")
            with c2:
                if st.button("🗑️", key=f"del_{original_index}", use_container_width=True):
                    st.session_state.tasks.pop(original_index)
                    st.session_state.generation_complete = False
                    st.rerun()
    st.markdown("---")
    st.subheader("Your Rest Window")
    st.caption("Set your consistent sleep rhythm for the week.")
    current_sleep_start = st.session_state.sleep[0]
    current_sleep_end = st.session_state.sleep[1]
    sleep_start = st.selectbox("Sleep Start", TIMES, index=TIMES.index(current_sleep_start))
    sleep_end = st.selectbox("Sleep End", TIMES, index=TIMES.index(current_sleep_end))
    st.session_state.sleep = (sleep_start, sleep_end)
    st.markdown("---")
    st.subheader("What’s already scheduled?")
    st.caption("Add work, classes, gym — anything already committed.")

    for d in DAYS:
        with st.expander(f"{d} • {format_date(week_dates[d])}"):
            label = st.text_input(f"{d} Label", key=f"{d}_label")
            start = st.selectbox(f"{d} Start", TIMES, key=f"{d}_start")
            end = st.selectbox(f"{d} End", TIMES, key=f"{d}_end")
            if st.button(f"Add to {d}", key=f"add_{d}", use_container_width=True):
                if label.strip():
                    st.session_state.commitments[d].append((label.strip(), start, end))
                    st.session_state.generation_complete = False
                    st.rerun()
            if st.session_state.commitments[d]:
                st.markdown("**Added blocks:**")
                for idx, block in enumerate(st.session_state.commitments[d]):
                    r1, r2 = st.columns([5, 1])
                    with r1:
                        st.caption(f"{block[0]}: {block[1]} → {block[2]}")
                    with r2:
                        if st.button("❌", key=f"del_block_{d}_{idx}", use_container_width=True):
                            st.session_state.commitments[d].pop(idx)
                            st.session_state.generation_complete = False
                            st.rerun()
    st.markdown("---")
    if st.button("Create My Week 🌿", use_container_width=True):
        st.session_state.schedule = {d: [] for d in DAYS}
        st.session_state.unscheduled = []
        st.session_state.generation_complete = False
        sleep_start_f = time_to_float(st.session_state.sleep[0])
        sleep_end_f = time_to_float(st.session_state.sleep[1])
        if sleep_start_f == sleep_end_f:
            st.error("Oops — that sleep window results in 0 hours of rest. Please adjust it.")
            st.stop()
        sleep_duration = get_sleep_duration(sleep_start_f, sleep_end_f)
        if sleep_duration < 4:
            st.warning("That’s a short sleep window. Make sure you’re protecting your energy.")
        if sleep_duration > 12:
            st.info("That’s quite a long sleep window — just confirming that’s intentional.")
        day_data = {}
        for d in DAYS:
            merged_blocked = build_blocked_intervals_for_day(
                d,
                st.session_state.sleep,
                st.session_state.commitments)
            gaps = build_gaps_from_blocked(merged_blocked)
            free_hours = total_gap_hours(gaps)
            task_capacity = min(MAX_TASK_HOURS_PER_DAY, free_hours)
            day_items = []
            for start, end, labels, item_types in merged_blocked:
                label_text = " / ".join(labels)
                block_type = "sleep" if ("sleep" in item_types and len(set(item_types)) == 1) else "commitment"
                day_items.append({
                    "label": label_text,
                    "start": start,
                    "end": end,
                    "type": block_type})
            day_data[d] = {
                "date": week_dates[d],
                "gaps": [gap[:] for gap in gaps],
                "task_capacity_remaining": task_capacity,
                "items": day_items}
        remaining_tasks = []
        for t in st.session_state.tasks:
            remaining_tasks.append({
                "name": t["name"],
                "hours_left": float(t["hours"]),
                "priority": t["priority"],
                "due_date": t["due_date"]})
        remaining_tasks.sort(
            key=lambda x: (x["due_date"], -PRIORITY_WEIGHT[x["priority"]], x["name"].lower()))
        for task in remaining_tasks:
            due_index = (task["due_date"] - st.session_state.week_start).days
            allowed_days = DAYS[:due_index + 1]
            placed_something = True
            while task["hours_left"] > 0 and placed_something:
                placed_something = False
                for d in allowed_days:
                    if task["hours_left"] <= 0:
                        break
                    day_cap = day_data[d]["task_capacity_remaining"]
                    if day_cap <= 0:
                        continue
                    chunk = min(MAX_SINGLE_TASK_BLOCK, task["hours_left"], day_cap)
                    if chunk < 0.5:
                        continue
                    segments, leftover = place_chunk_into_gaps(day_data[d]["gaps"], chunk)
                    actual_placed = chunk - leftover
                    if actual_placed > 0:
                        for seg_start, seg_end in segments:
                            day_data[d]["items"].append({
                                "label": task["name"],
                                "start": seg_start,
                                "end": seg_end,
                                "type": "task",
                                "priority": task["priority"],
                                "due_date": task["due_date"]})
                        task["hours_left"] -= actual_placed
                        day_data[d]["task_capacity_remaining"] -= actual_placed
                        placed_something = True
        for d in DAYS:
            st.session_state.schedule[d] = sort_schedule_items(day_data[d]["items"])
        for task in remaining_tasks:
            if task["hours_left"] > 0:
                st.session_state.unscheduled.append({
                    "name": task["name"],
                    "hours_left": task["hours_left"],
                    "priority": task["priority"],
                    "due_date": task["due_date"]})
        st.session_state.generation_complete = True
    if st.session_state.generation_complete:
        st.markdown("---")
        st.header("🌿 Weekly Summary")
        total_task_hours = sum(task["hours"] for task in st.session_state.tasks)
        total_commitment_hours = 0
        for d in DAYS:
            for label, start, end in st.session_state.commitments[d]:
                start_f = time_to_float(start)
                end_f = time_to_float(end)
                if start_f > end_f:
                    total_commitment_hours += (24 - start_f) + end_f
                else:
                    total_commitment_hours += end_f - start_f
        sleep_duration = get_sleep_duration(
            time_to_float(st.session_state.sleep[0]),
            time_to_float(st.session_state.sleep[1]))
        total_sleep_hours = sleep_duration * 7
        total_scheduled_task_hours = 0
        for d in DAYS:
            for item in st.session_state.schedule[d]:
                if item["type"] == "task":
                    total_scheduled_task_hours += item["end"] - item["start"]
        total_unscheduled_hours = sum(item["hours_left"] for item in st.session_state.unscheduled)
        s1, s2 = st.columns(2)
        s3, s4 = st.columns(2)
        s5 = st.columns(1)[0]
        with s1:
            st.metric("Task Hours", f"{total_task_hours:.1f}")
        with s2:
            st.metric("Scheduled", f"{total_scheduled_task_hours:.1f}")
        with s3:
            st.metric("Unscheduled", f"{total_unscheduled_hours:.1f}")
        with s4:
            st.metric("Sleep Hours", f"{total_sleep_hours:.1f}")
        with s5:
            st.metric("Fixed Hours", f"{total_commitment_hours:.1f}")
        st.header("🌿 Your Weekly Layout")
        st.caption("Your schedule is generated around your rest window, existing commitments, task priorities, and due dates.")
        legend_cols = st.columns(5)
        legend_items = [
            ("High Priority", COLORS["high"]),
            ("Medium Priority", COLORS["medium"]),
            ("Low Priority", COLORS["low"]),
            ("Sleep", COLORS["sleep"]),
            ("Fixed Commitment", COLORS["commitment"])]
        for col, (label, bg) in zip(legend_cols, legend_items):
            with col:
                st.markdown(
                    f'<div style="background:{bg}; border:1px solid #DDEAE1; border-radius:999px; padding:6px 10px; text-align:center; font-size:12px; font-weight:700; color:{COLORS["text"]};">{label}</div>',
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        for d in DAYS:
            current_date = week_dates[d]
            day_task_hours = 0
            for item in st.session_state.schedule[d]:
                if item["type"] == "task":
                    day_task_hours += item["end"] - item["start"]
            st.subheader(d)
            st.caption(format_date(current_date))
            load_bg = get_load_color(day_task_hours)
            load_label = get_day_load_label(day_task_hours)
            st.markdown(
                f'<div style="display:inline-block; background:{load_bg}; color:{COLORS["text"]}; padding:6px 12px; border-radius:999px; font-size:12px; font-weight:700; margin-bottom:12px;">{load_label}</div>',
                unsafe_allow_html=True)
            if st.session_state.schedule[d]:
                for item in st.session_state.schedule[d]:
                    bg, border = get_item_colors(item)
                    if item["type"] == "sleep":
                        note = "Sleep window"
                    elif item["type"] == "commitment":
                        note = "Fixed commitment"
                    else:
                        note = f"Task • {item['priority']} priority • Due {format_date(item['due_date'])}"
                    with st.container(border=True):
                        st.markdown(
                            f'<div style="background:{bg}; border-left:8px solid {border}; padding:14px; border-radius:10px;"><div style="font-weight:700; color:{COLORS["text"]};">{item["label"]}</div><div style="margin-top:4px; color:{COLORS["muted"]};">{float_to_time(item["start"])} → {float_to_time(item["end"])}</div><div style="margin-top:6px; font-size:13px; color:{COLORS["muted"]};">{note}</div></div>',
                            unsafe_allow_html=True)
            else:
                st.info("No scheduled items for this day.")
        with st.expander("🌿 Visual Timeline", expanded=False):
            st.caption("A cleaner visual timeline of your week with continuous blocks by duration.")
            timeline_html = build_visual_timeline_html(st.session_state.schedule, week_dates)
            timeline_height = 220 + (len(DAYS) * 110)
            components.html(timeline_html, height=timeline_height, scrolling=False)
        if st.session_state.unscheduled:
            st.warning("There wasn’t enough room to finish everything before its due date. Here’s what remains:")
            for u in st.session_state.unscheduled:
                st.write(
                    f"**{u['name']}** — {u['hours_left']:.1f} hrs remaining • "
                    f"{u['priority']} priority • Due {format_date(u['due_date'])}")
