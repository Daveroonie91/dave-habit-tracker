import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# Set page config for collapsible sidebar and page title
st.set_page_config(
    page_title="Lift Tracker", # Updated page title
    initial_sidebar_state="collapsed"
)

st.title("🏋️ Lift Tracker")

# --- Configuration ---
LIFT_LOG_FILE = "lift_log.csv"
WEIGHT_CSV_INITIAL_IMPORT = "weight.csv" # The file to import from

# --- Data Loading and Initial Import ---
if os.path.exists(LIFT_LOG_FILE):
    lift_df = pd.read_csv(LIFT_LOG_FILE)
    # Ensure 'Date' is datetime for proper sorting and plotting
    lift_df['Date'] = pd.to_datetime(lift_df['Date'], errors='coerce')
    # Drop rows where date parsing failed
    lift_df = lift_df.dropna(subset=['Date']).reset_index(drop=True)
else:
    # If lift_log.csv doesn't exist, try to import from weight.csv
    if os.path.exists(WEIGHT_CSV_INITIAL_IMPORT):
        st.info(f"Importing data from {WEIGHT_CSV_INITIAL_IMPORT}...")
        initial_df = pd.read_csv(WEIGHT_CSV_INITIAL_IMPORT)
        
        # Correct Column Name: "Weight" to "Body Weight (lbs)"
        initial_df = initial_df.rename(columns={"Weight": "Body Weight (lbs)"})
        
        # Add 'Exercise Weight (lbs)' column, initialized to None
        initial_df["Exercise Weight (lbs)"] = None
        
        # Add 'Workout Type' column if it doesn't exist in the imported CSV
        if 'Workout Type' not in initial_df.columns:
            initial_df["Workout Type"] = "Body Weight Tracking" # Default value for imported data
        
        # Robust Date Parsing: Combine 'Date' and 'Year' if 'Year' exists, otherwise use current year
        # First, ensure 'Year' column exists and fill NaNs with current year
        if 'Year' not in initial_df.columns:
            initial_df['Year'] = datetime.now().year
        initial_df['Year'] = initial_df['Year'].fillna(datetime.now().year).astype(int)

        # Create a combined date string and then parse
        # Handle cases where 'Date' might already contain year or be just Month Day
        initial_df['FullDateString'] = initial_df.apply(
            lambda row: f"{row['Date']} {row['Year']}" if pd.notna(row['Year']) else f"{row['Date']} {datetime.now().year}",
            axis=1
        )
        initial_df['Date'] = pd.to_datetime(initial_df['FullDateString'], errors='coerce')
        
        # Drop rows where date parsing failed
        initial_df = initial_df.dropna(subset=['Date']).reset_index(drop=True)

        # Select and reorder columns to match the expected DataFrame structure
        lift_df = initial_df[["Date", "Workout Type", "Body Weight (lbs)", "Exercise Weight (lbs)"]]
        
        # Save to lift_log.csv immediately after import
        lift_df.to_csv(LIFT_LOG_FILE, index=False)
        st.success(f"Data imported from {WEIGHT_CSV_INITIAL_IMPORT} and saved to {LIFT_LOG_FILE}!")
        st.rerun() # Rerun to display updated data
    else:
        lift_df = pd.DataFrame(columns=["Date", "Workout Type", "Body Weight (lbs)", "Exercise Weight (lbs)"])


# --- Input Form ---
st.subheader("Add New Lift Entry")

# Date picker (only past/today dates)
entry_date = st.date_input("Date", value=date.today(), max_value=date.today())

# Workout Type selection (using the same types as in Home.py for consistency)
workout_types = ["Run", "Yoga", "Boxing", "Strength Training", "Functional Training", "Misc Cardio"]
selected_workout_type = st.selectbox("Workout Type", options=[""] + workout_types) # Add empty option

body_weight = st.number_input("Body Weight (lbs)", min_value=0.0, format="%.1f")
exercise_weight = st.number_input("Exercise Weight (lbs) (Optional)", min_value=0.0, format="%.1f")

if st.button("Add Lift Entry"):
    if selected_workout_type == "":
        st.warning("Please select a Workout Type.")
    else:
        new_entry = {
            "Date": entry_date,
            "Workout Type": selected_workout_type,
            "Body Weight (lbs)": body_weight,
            "Exercise Weight (lbs)": exercise_weight if exercise_weight > 0 else None # Store None if 0
        }
        
        # Convert new_entry to DataFrame and ensure consistent column order
        new_entry_df = pd.DataFrame([new_entry])
        
        # Concatenate and sort
        lift_df = pd.concat([lift_df, new_entry_df], ignore_index=True)
        lift_df = lift_df.sort_values(by="Date", ascending=True).reset_index(drop=True)
        
        lift_df.to_csv(LIFT_LOG_FILE, index=False)
        st.success("Lift entry added!")
        st.rerun()

# --- Lift History Table ---
st.subheader("Lift History")
if not lift_df.empty:
    # Display the DataFrame, hide index
    st.dataframe(lift_df.sort_values(by="Date", ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)
else:
    st.write("No lift entries yet.")

# --- Weight Progress Visualization ---
st.subheader("Weight Progress (Body Weight)")
if not lift_df.empty and "Body Weight (lbs)" in lift_df.columns and lift_df["Body Weight (lbs)"].dropna().any():
    # Filter out entries where Body Weight is 0 or None
    body_weight_data = lift_df[lift_df["Body Weight (lbs)"] > 0].set_index('Date')["Body Weight (lbs)"]
    if not body_weight_data.empty:
        st.line_chart(body_weight_data)
    else:
        st.write("No body weight data to display in graph.")
else:
    st.write("No body weight data to display in graph.")

st.subheader("Weight Progress (Exercise Weight)")
if not lift_df.empty and "Exercise Weight (lbs)" in lift_df.columns and lift_df["Exercise Weight (lbs)"].dropna().any():
    # Filter out entries where Exercise Weight is 0 or None
    exercise_weight_data = lift_df[lift_df["Exercise Weight (lbs)"] > 0].set_index('Date')["Exercise Weight (lbs)"]
    if not exercise_weight_data.empty:
        st.line_chart(exercise_weight_data)
    else:
        st.write("No exercise weight data to display in graph.")
else:
    st.write("No exercise weight data to display in graph.")
