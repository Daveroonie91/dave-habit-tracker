import streamlit as st
from datetime import date, datetime
from calendar import monthrange
import pandas as pd
import os

# Set page config for collapsible sidebar
st.set_page_config(
    page_title="Daily Habit Tracker",
    initial_sidebar_state="collapsed"
)

st.title("🗓️ Daily Habit Tracker")

# — Today’s Date
today = date.today()
today_str = today.strftime("%B %d, %Y").lstrip("0").replace(" 0", " ")
st.subheader(f"Today: {today_str}")

# — Habits & CSV Load
# Define the core habits, excluding 'Exercise' for now as it will be handled separately
habits = ["Read", "Write", "Night time routine", "Cognitive", "Creatine"]
workout_types = ["Run", "Yoga", "Boxing", "Strength Training", "Functional Training", "Misc Cardio"] # Specific workout types
all_columns = ["Date"] + ["Exercise"] + habits # 'Exercise' is now a single column for string storage

file_path = "habit_log.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    # Ensure 'Exercise' column exists and handle its data type
    if 'Exercise' in df.columns:
        # Check if the column contains boolean values (e.g., from old CSVs)
        # If it's boolean, convert True to the first new workout type (or empty string if no types)
        if df['Exercise'].dtype == bool:
            df['Exercise'] = df['Exercise'].apply(lambda x: workout_types[0] if x and workout_types else "")
        df['Exercise'] = df['Exercise'].fillna('').astype(str) # Ensure it's string and not NaN
    else: # If 'Exercise' column doesn't exist (very old CSV), add it as empty strings
        df['Exercise'] = ''
else:
    df = pd.DataFrame(columns=all_columns)

# — Parse Dates & Periods (for block views)
# Re-parse 'Date' column to include year for proper sorting and comparison
# This assumes 'Date' is in "Month Day" format (e.g., "May 20")
# We'll use the current year for dates that don't have a year specified in the CSV
df["Parsed"] = pd.to_datetime(
    df["Date"].apply(lambda x: f"{x} {today.year}" if len(x.split()) == 2 else x),
    format="%B %d %Y",
    errors="coerce"
)
df["Period"] = df["Parsed"].dt.to_period("M")
current_period = pd.Period(today, "M")

# — Yearly Progress Bar —
st.markdown("---")
st.subheader("Yearly Progress")

# Ensure df is populated before attempting calculations
if not df.empty:
    all_days_progress = df[df["Parsed"].dt.year == today.year].copy() # Use a copy for this section
    productive_days = 0

    if not all_days_progress.empty:
        for _, r in all_days_progress.iterrows():
            if r["Parsed"] <= pd.to_datetime(today):  # Only consider days up to today
                exercise_done = bool(r["Exercise"]) # Check if Exercise string is not empty
                cnt = sum(r[h] for h in habits) # Sum of non-exercise habits
                if exercise_done or cnt >= 4:
                    productive_days += 1

        total_days = (pd.to_datetime(today) - pd.to_datetime(date(today.year, 1, 1))).days + 1  # Days from Jan 1 to today
        progress = (productive_days / total_days) if total_days > 0 else 0
        goal = 0.65  # 65% goal
        progress_percent = progress * 100

        st.progress(progress)
        st.write(f"**Progress**: {productive_days} productive days out of {total_days} days ({progress_percent:.0f}%).")
        st.write(f"**Goal**: {goal * 100:.0f}%")
    else:
        st.write("No data for this year yet.")
else: # If df is entirely empty (e.g., first run), show no data
    st.write("No data for this year yet.")


# — Today’s Saved State
saved_data_for_selected_date = {} # Renamed from saved_today to be consistent with selected_date
row_selected_date = df[df["Date"] == today_str] # Use today_str for initial load
if not row_selected_date.empty:
    saved_data_for_selected_date = row_selected_date.iloc[0].to_dict()


# --- Date Selection for Editing ---
st.markdown("---") # Add a separator after the progress bar
st.subheader("Select Date for Entry")
selected_date = st.date_input("Choose a date:", today, max_value=today)
selected_date_str = selected_date.strftime("%B %d").lstrip("0").replace(" 0", " ")

# — Display selected date
st.markdown(f"**Entry for**: {selected_date.strftime('%A, %B %d, %Y')}")

# — Load Saved State for Selected Date (re-load for selected_date)
saved_data_for_selected_date = {}
row_selected_date = df[df["Date"] == selected_date_str]
if not row_selected_date.empty:
    saved_data_for_selected_date = row_selected_date.iloc[0].to_dict()

# — Render Input Widgets based on Selected Date's Data
results = {}

# Render checkboxes for other habits (now at the top)
for h in habits:
    results[h] = st.checkbox(h, value=saved_data_for_selected_date.get(h, False), key=f"checkbox_{h}_{selected_date_str}")

# MOVED: Multiselect for Exercise to the bottom of habit options
current_exercise_selection = []
if saved_data_for_selected_date.get("Exercise"):
    exercise_value = str(saved_data_for_selected_date["Exercise"])
    current_exercise_selection = [w.strip() for w in exercise_value.split(',') if w.strip()]

# CHANGE: Render 'Exercise' label with markdown for consistent font, and use label_visibility="hidden"
st.markdown("<p style='font-size: 1rem; font-weight: normal; margin-bottom: 0;'>Exercise</p>", unsafe_allow_html=True)
selected_workouts = st.multiselect(
    label="Exercise", # Provide a label for accessibility
    options=workout_types,
    default=current_exercise_selection,
    key=f"multiselect_exercise_{selected_date_str}",
    label_visibility="hidden" # Hide the default label visually
)
results["Exercise"] = ",".join(selected_workouts)

# — Save Logic
if st.button("Save Entry"):
    new_row = {"Date": selected_date_str}
    for col in all_columns:
        if col == "Date":
            continue
        new_row[col] = results.get(col, '')

    df = df[df["Date"] != selected_date_str]
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    df["Parsed"] = pd.to_datetime(
        df["Date"].apply(lambda x: f"{x} {today.year}" if len(x.split()) == 2 else x),
        format="%B %d %Y",
        errors="coerce"
    )
    df = df.sort_values(by="Parsed", ascending=True).reset_index(drop=True)
    
    df.to_csv(file_path, index=False)
    st.success(f"Entry for {selected_date_str} saved!")
    st.rerun()

# — Habit History Table (current month, past/present only) —
st.markdown("---")
st.subheader("📅 Habit History")
hist = df[df["Period"] == current_period].copy()
today_dt = pd.to_datetime(today)
hist = hist[hist["Parsed"] <= today_dt].copy()
if not hist.empty:
    disp = hist.copy()
    
    disp["Exercise"] = disp["Exercise"].apply(lambda x: "✓" if x else "")
    
    for h in habits:
        disp[h] = disp[h].apply(lambda x: "✓" if x else "")
        
    disp["Non_Exercise_Completed"] = hist[habits].sum(axis=1)
    
    disp["Status"] = disp.apply(
        lambda row: "✅" if bool(row["Exercise"]) or row["Non_Exercise_Completed"] >= 4 else "❌", axis=1
    )
    
    display_columns = ["Date", "Exercise"] + habits + ["Status"]
    st.dataframe(disp[display_columns], use_container_width=True, hide_index=True)
else:
    st.write("No entries for this month.")

# — Monthly View (3 across) —
st.markdown("---")
st.subheader("📆Monthly View")
periods = sorted(df["Period"].dropna().unique())
if periods:
    all_html = "<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:32px;'>"
    for period in periods:
        m_html = "<div>"
        m_html += f"<div style='font-weight:bold;margin-bottom:8px;'>{period.strftime('%B %Y')}</div>"
        m_html += "<div style='display:grid;grid-template-columns:repeat(7,36px);gap:8px;margin-bottom:8px;'>"
        for lab in ["Su","Mo","Tu","We","Th","Fr","Sa"]:
            m_html += f"<div style='text-align:center;font-size:12px;'>{lab}</div>"
        m_html += "</div>"

        sub = df[df["Period"] == period]
        day_color = {}
        for _, r in sub.iterrows():
            d = r["Parsed"].day
            exercise_done = bool(r["Exercise"])
            cnt = sum(r[h] for h in habits)
            
            if exercise_done:
                day_color[d] = "green"
            elif cnt >= 4:
                day_color[d] = "green"
            elif cnt > 0:
                day_color[d] = "red"
            else:
                day_color[d] = "gray"

        yr, mth = period.year, period.month
        ndays = monthrange(yr, mth)[1]
        start_wd = monthrange(yr, mth)[0]
        offset = (start_wd + 1) % 7
        is_cur = (period == current_period)
        today_day = today.day if is_cur else None

        m_html += "<div style='display:grid;grid-template-columns:repeat(7,36px);gap:8px;'>"
        m_html += "<div></div>" * offset
        for day in range(1, ndays + 1):
            if day in day_color:
                bg = day_color[day]
            elif is_cur and day < today_day:
                bg = "lightgray"
            elif not is_cur and datetime(yr, mth, day) < today:
                bg = "lightgray"
            else:
                bg = "white"
            fg = "black" if bg in ("white","lightgray","gray") else "white"
            m_html += (
                f"<div style='width:36px;height:36px;"
                f"background:{bg};border:1px solid #555;"
                f"border-radius:6px;text-align:center;"
                f"line-height:36px;font-size:14px;color:{fg};'>{day}</div>"
            )
        m_html += "</div></div>"
        all_html += m_html
    all_html += "</div>"
    st.markdown(all_html, unsafe_allow_html=True)
else:
    st.write("No history to display.")
