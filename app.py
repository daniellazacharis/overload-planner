import streamlit as st

from datetime import datetime, date, timedelta

st.set_page_config(

    page_title="Stress-Free Weekly Planner",

    page_icon="🌿",

    layout="centered",

    initial_sidebar_state="collapsed"

)

# ----------------------------------------------------

# ------------------ CONSTANTS -----------------------

# ----------------------------------------------------

DAYS = [

    "Monday", "Tuesday", "Wednesday",

    "Thursday", "Friday", "Saturday", "Sunday"

]

PRIORITY_WEIGHT = {"High": 3, "Medium": 2, "Low": 1}

MAX_TASK_HOURS_PER_DAY = 6.0

MAX_SINGLE_TASK_BLOCK = 2.0

# ----------------------------------------------------

# ------------------ TIME HELPERS --------------------

# ----------------------------------------------------

def time_to_float(t):

    dt = datetime.strptime(t, "%I:%M %p")

    return dt.hour + dt.minute / 60

def float_to_time(f):

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

def format_date(d):

    return d.strftime("%b %d, %Y")

def get_default_monday():

    today = date.today()

    return today - timedelta(days=today.weekday())

def get_sleep_duration(start_f, end_f):

    if start_f == end_f:

        return 0

    if start_f > sleep_end_f:

        return (24 - start_f) + end_f

    return end_f - start_f

TIMES = build_times()

# ----------------------------------------------------

# ------------------ SCHEDULING HELPERS --------------

# ----------------------------------------------------

def build_blocked_intervals_for_day(day_name, sleep_tuple, commitments):

    blocked = []

    sleep_start_f = time_to_float(sleep_tuple[0])

    sleep_end_f = time_to_float(sleep_tuple[1])

    # Sleep blocks

    if sleep_start_f > sleep_end_f:

        blocked.append((sleep_start_f, 24.0, "Sleep", "sleep"))

        blocked.append((0.0, sleep_end_f, "Sleep", "sleep"))

    else:

        blocked.append((sleep_start_f, sleep_end_f, "Sleep", "sleep"))

    # Commitments

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

def get_day_load_label(task_hours):

    if task_hours < 2:

        return "Light"

    elif task_hours < 4:

        return "Balanced"

    elif task_hours < 6:

        return "Heavy"

    return "Overloaded"

def item_bg_color(item):

    if item["type"] == "sleep":

        return "#EEF2FB"

    if item["type"] == "commitment":

        return "#F3F3F3"

    if item["priority"] == "High":

        return "#FDECEC"

    if item["priority"] == "Medium":

        return "#FFF5E6"

    return "#EEF7ED"

def build_timeline_html(schedule):

    slot_times = []

    current = 0.0

    while current < 24.0:

        slot_times.append(current)

        current += 0.5

    def get_cell_content(day_name, slot_start):

        slot_end = slot_start + 0.5

        for item in schedule[day_name]:

            item_start = item["start"]

            item_end = item["end"]

            if item_start < slot_end and item_end > slot_start:

                if item["type"] == "sleep":

                    return ("Sleep", "t-cell-sleep")

                elif item["type"] == "commitment":

                    short_label = item["label"][:10] + "…" if len(item["label"]) > 10 else item["label"]

                    return (short_label, "t-cell-commitment")

                else:

                    short_label = item["label"][:10] + "…" if len(item["label"]) > 10 else item["label"]

                    if item["priority"] == "High":

                        return (short_label, "t-cell-high")

                    elif item["priority"] == "Medium":

                        return (short_label, "t-cell-medium")

                    else:

                        return (short_label, "t-cell-low")

        return ("", "t-cell-empty")

    html = """

    <div class="timeline-wrap">

      <table class="timeline-table">

        <tr>

          <th class="timeline-time">Time</th>

    """

    for d in DAYS:

        html += f'<th class="timeline-day-header">{d}</th>'

    html += "</tr>"

    for slot in slot_times:

        html += "<tr>"

        html += f'<td class="timeline-time">{float_to_time(slot)}</td>'

        for d in DAYS:

            text, cell_class = get_cell_content(d, slot)

            html += f'<td class="{cell_class}">{text}</td>'

        html += "</tr>"

    html += "</table></div>"

    return html

# ----------------------------------------------------

# ------------------ STATE ---------------------------

# ----------------------------------------------------

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

# ----------------------------------------------------

# ------------------ STYLING -------------------------

# ----------------------------------------------------

st.markdown("""

<style>

html, body, [class*="css"] {

    font-family: Arial, sans-serif;

}

.block-container {

    max-width: 950px;

    padding-top: 2rem;

    padding-bottom: 3rem;

}

.home-title {

    text-align: center;

    color: #2F5E46;

    font-size: 3rem;

    font-weight: 700;

    margin-bottom: 0.25rem;

}

.home-subtitle {

    text-align: center;

    color: #2F5E46;

    font-size: 2rem;

    font-weight: 600;

    margin-bottom: 1rem;

}

.home-text {

    text-align: center;

    color: #4F695C;

    font-size: 1.2rem;

    max-width: 800px;

    margin: 0 auto 1.5rem auto;

    line-height: 1.6;

}

.legend-inline {

    display: flex;

    flex-wrap: wrap;

    gap: 8px;

    margin-bottom: 12px;

}

.legend-pill {

    padding: 6px 10px;

    border-radius: 999px;

    font-size: 12px;

    font-weight: 700;

    display: inline-block;

}

.legend-high { background: #FDECEC; border: 1px solid #F4C7C7; }

.legend-medium { background: #FFF5E6; border: 1px solid #F3D7A6; }

.legend-low { background: #EEF7ED; border: 1px solid #CFE6CC; }

.legend-sleep { background: #EEF2FB; border: 1px solid #CCD8F0; }

.legend-commitment { background: #F3F3F3; border: 1px solid #DDDDDD; }

.load-pill {

    display: inline-block;

    padding: 6px 12px;

    border-radius: 999px;

    font-size: 12px;

    font-weight: 700;

    margin-top: 6px;

    margin-bottom: 10px;

}

.load-light { background: #EEF7ED; color: #2F5E46; }

.load-balanced { background: #FFF5E6; color: #7A5A1D; }

.load-heavy { background: #FFE8CC; color: #8A4A00; }

.load-overloaded { background: #FDECEC; color: #9B2C2C; }

.timeline-wrap {

    overflow-x: auto;

    width: 100%;

}

.timeline-table {

    border-collapse: collapse;

    min-width: 980px;

    width: 100%;

    table-layout: fixed;

    font-size: 12px;

}

.timeline-table th, .timeline-table td {

    border: 1px solid #DDEAE1;

    text-align: center;

    vertical-align: middle;

    padding: 6px;

}

.timeline-time {

    width: 80px;

    background: #F8FBF9;

    font-weight: 600;

    color: #5F7567;

}

.timeline-day-header {

    background: #F3F7F4;

    color: #2F5E46;

    font-weight: 700;

    min-width: 120px;

}

.t-cell-empty { background: #FFFFFF; }

.t-cell-sleep { background: #EEF2FB; color: #35507A; font-weight: 600; }

.t-cell-commitment { background: #F3F3F3; color: #555555; font-weight: 600; }

.t-cell-high { background: #FDECEC; color: #842029; font-weight: 700; }

.t-cell-medium { background: #FFF5E6; color: #7A5A1D; font-weight: 700; }

.t-cell-low { background: #EEF7ED; color: #2F5E46; font-weight: 700; }

@media (max-width: 900px) {

    .home-title { font-size: 2.4rem; }

    .home-subtitle { font-size: 1.6rem; }

    .home-text { font-size: 1.05rem; }

}

</style>

""", unsafe_allow_html=True)

# ----------------------------------------------------

# ------------------ HOME PAGE -----------------------

# ----------------------------------------------------

if st.session_state.page == "home":

    st.markdown("<div class='home-title'>🌿 Welcome</div>", unsafe_allow_html=True)

    st.markdown("<div class='home-subtitle'>Build a week that feels balanced.</div>", unsafe_allow_html=True)

    st.markdown(

        "<div class='home-text'>Plan around your real life, protect your rest, and place what matters — gently.</div>",

        unsafe_allow_html=True

    )

    c1, c2, c3 = st.columns([1, 1.4, 1])

    with c2:

        if st.button("Let’s Get Started 🌿", use_container_width=True):

            st.session_state.page = "planning"

            st.rerun()

# ----------------------------------------------------

# ------------------ PLANNING PAGE -------------------

# ----------------------------------------------------

if st.session_state.page == "planning":

    top1, top2 = st.columns([1, 4])

    with top1:

        if st.button("← Home", use_container_width=True):

            st.session_state.page = "home"

            st.rerun()

    st.markdown("<h1 style='text-align:center;color:#2F5E46;'>🌿 Build Your Week</h1>", unsafe_allow_html=True)

    st.markdown(

        "<p style='text-align:center;color:#4F695C;'>Everything is going to be okay. Let’s organize it step by step.</p>",

        unsafe_allow_html=True

    )

    st.subheader("Week Setup")

    st.caption("Choose the Monday that starts the week you want to plan.")

    st.session_state.week_start = st.date_input(

        "Week Start Date",

        value=st.session_state.week_start

    )

    week_dates = {DAYS[i]: st.session_state.week_start + timedelta(days=i) for i in range(7)}

    st.markdown("---")

    # ---------------- TASKS ----------------

    st.subheader("What needs your attention this week?")

    st.caption("Add each task, estimate the time it realistically needs, and choose its due date.")

    name = st.text_input("Task Name")

    hours = st.number_input("Hours Needed", min_value=0.5, step=0.5)

    priority = st.selectbox("Priority", ["High", "Medium", "Low"])

    due_date = st.date_input(

        "Due Date",

        value=st.session_state.week_start + timedelta(days=6),

        min_value=st.session_state.week_start,

        max_value=st.session_state.week_start + timedelta(days=6)

    )

    if st.button("Add Task", use_container_width=True):

        if name.strip():

            st.session_state.tasks.append({

                "name": name.strip(),

                "hours": float(hours),

                "priority": priority,

                "due_date": due_date

            })

            st.session_state.generation_complete = False

            st.rerun()

    if st.session_state.tasks:

        st.markdown("### Your Added Tasks")

        st.caption("Use the trash icon to remove a task if plans change.")

        sorted_display_tasks = sorted(

            enumerate(st.session_state.tasks),

            key=lambda x: (x[1]["due_date"], -PRIORITY_WEIGHT[x[1]["priority"]], x[1]["name"].lower())

        )

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

    # ---------------- SLEEP ----------------

    st.subheader("Your Rest Window")

    st.caption("Set your consistent sleep rhythm for the week.")

    current_sleep_start = st.session_state.sleep[0]

    current_sleep_end = st.session_state.sleep[1]

    sleep_start = st.selectbox(

        "Sleep Start",

        TIMES,

        index=TIMES.index(current_sleep_start)

    )

    sleep_end = st.selectbox(

        "Sleep End",

        TIMES,

        index=TIMES.index(current_sleep_end)

    )

    st.session_state.sleep = (sleep_start, sleep_end)

    st.markdown("---")

    # ---------------- COMMITMENTS ----------------

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

    # ---------------- GENERATE BUTTON ----------------

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

                st.session_state.commitments

            )

            gaps = build_gaps_from_blocked(merged_blocked)

            free_hours = total_gap_hours(gaps)

            task_capacity = min(MAX_TASK_HOURS_PER_DAY, free_hours)

            day_items = []

            for start, end, labels, item_types in merged_blocked:

                label_text = " / ".join(labels)

                if "sleep" in item_types and len(set(item_types)) == 1:

                    block_type = "sleep"

                else:

                    block_type = "commitment"

                day_items.append({

                    "label": label_text,

                    "start": start,

                    "end": end,

                    "type": block_type

                })

            day_data[d] = {

                "date": week_dates[d],

                "gaps": [gap[:] for gap in gaps],

                "task_capacity_remaining": task_capacity,

                "items": day_items

            }

        remaining_tasks = []

        for t in st.session_state.tasks:

            remaining_tasks.append({

                "name": t["name"],

                "hours_left": float(t["hours"]),

                "priority": t["priority"],

                "due_date": t["due_date"]

            })

        remaining_tasks.sort(

            key=lambda x: (x["due_date"], -PRIORITY_WEIGHT[x["priority"]], x["name"].lower())

        )

        # Schedule only on or before due date

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

                                "due_date": task["due_date"]

                            })

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

                    "due_date": task["due_date"]

                })

        st.session_state.generation_complete = True

    # ---------------- OUTPUT ----------------

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

            time_to_float(st.session_state.sleep[1])

        )

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

        st.markdown("""

<div class="legend-inline">

    <span class="legend-pill legend-high">High Priority Task</span>

    <span class="legend-pill legend-medium">Medium Priority Task</span>

    <span class="legend-pill legend-low">Low Priority Task</span>

    <span class="legend-pill legend-sleep">Sleep</span>

    <span class="legend-pill legend-commitment">Fixed Commitment</span>

</div>

""", unsafe_allow_html=True)

        for d in DAYS:

            current_date = week_dates[d]

            day_task_hours = 0

            for item in st.session_state.schedule[d]:

                if item["type"] == "task":

                    day_task_hours += item["end"] - item["start"]

            load_label = get_day_load_label(day_task_hours)

            if load_label == "Light":

                st.success(f"{d} • {format_date(current_date)} • {load_label}")

            elif load_label == "Balanced":

                st.warning(f"{d} • {format_date(current_date)} • {load_label}")

            elif load_label == "Heavy":

                st.warning(f"{d} • {format_date(current_date)} • {load_label}")

            else:

                st.error(f"{d} • {format_date(current_date)} • {load_label}")

            if st.session_state.schedule[d]:

                for item in st.session_state.schedule[d]:

                    bg = item_bg_color(item)

                    if item["type"] == "sleep":

                        note = "Sleep window"

                    elif item["type"] == "commitment":

                        note = "Fixed commitment"

                    else:

                        note = f"Task • {item['priority']} priority • Due {format_date(item['due_date'])}"

                    with st.container(border=True):

                        st.markdown(

                            f"""

<div style="background:{bg}; padding:12px; border-radius:12px;">

    <div><strong>{item['label']}</strong></div>

    <div style="margin-top:4px; color:#5F7567;">{float_to_time(item['start'])} → {float_to_time(item['end'])}</div>

    <div style="margin-top:4px; font-size:13px; color:#6E8577;">{note}</div>

</div>

                            """,

                            unsafe_allow_html=True

                        )

            else:

                st.info("No scheduled items for this day.")

        with st.expander("🌿 Visual Timeline", expanded=False):

            st.caption("A half-hour view of your week. Best viewed on a wider screen.")

            st.markdown(build_timeline_html(st.session_state.schedule), unsafe_allow_html=True)

        if st.session_state.unscheduled:

            st.warning("There wasn’t enough room to finish everything before its due date. Here’s what remains:")

            for u in st.session_state.unscheduled:

                st.write(

                    f"**{u['name']}** — {u['hours_left']:.1f} hrs remaining • "

                    f"{u['priority']} priority • Due {format_date(u['due_date'])}"

                )