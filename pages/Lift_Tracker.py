import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import altair as alt

# Set page config for collapsible sidebar and page title
st.set_page_config(
    page_title="Lift Tracker",
    initial_sidebar_state="collapsed"
)

st.title("🏋️ Lift Tracker")

# --- Configuration ---
BODY_WEIGHT_LOG_FILE = "body_weight_log.csv"
GYM_LIFT_LOG_FILE = "gym_lift_log.csv"
INITIAL_WEIGHT_DATA_SOURCE = "date_weight.csv" # Source for initial body weight data

# --- Data Loading Functions ---

def load_body_weight_data():
    if os.path.exists(BODY_WEIGHT_LOG_FILE):
        df = pd.read_csv(BODY_WEIGHT_LOG_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']).reset_index(drop=True)
        return df
    else:
        if os.path.exists(INITIAL_WEIGHT_DATA_SOURCE):
            st.info(f"Initializing body weight data from {INITIAL_WEIGHT_DATA_SOURCE}...")
            initial_df = pd.read_csv(INITIAL_WEIGHT_DATA_SOURCE)

            initial_df['FullDateString'] = initial_df['Date'].astype(str) + ' 2025'
            initial_df['Date'] = pd.to_datetime(initial_df['FullDateString'], format="%B %d %Y", errors='coerce')
            initial_df = initial_df.dropna(subset=['Date']).drop(columns=['FullDateString']).reset_index(drop=True)
            initial_df['Date'] = initial_df['Date'].dt.date # Store as date objects to remove time

            initial_df = initial_df.rename(columns={"Weight": "Body Weight (lbs)"})
            df = initial_df[["Date", "Body Weight (lbs)"]]
            df['Date'] = pd.to_datetime(df['Date']) # Convert to datetime for internal consistency

            df.to_csv(BODY_WEIGHT_LOG_FILE, index=False)
            st.success(f"Body weight data initialized from {INITIAL_WEIGHT_DATA_SOURCE} and saved to {BODY_WEIGHT_LOG_FILE}!")
            return df
        else:
            st.warning(f"Neither {BODY_WEIGHT_LOG_FILE} nor {INITIAL_WEIGHT_DATA_SOURCE} found for body weight. Starting with empty body weight data.")
            return pd.DataFrame(columns=["Date", "Body Weight (lbs)"])

def load_gym_lift_data():
    if os.path.exists(GYM_LIFT_LOG_FILE):
        df = pd.read_csv(GYM_LIFT_LOG_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']).reset_index(drop=True)
        return df
    else:
        st.warning(f"No {GYM_LIFT_LOG_FILE} found. Starting with empty gym lift data.")
        return pd.DataFrame(columns=["Date", "Exercise Name", "Set Number", "Reps", "Weight (lbs)"])

# Load dataframes
body_weight_df = load_body_weight_data()
gym_lift_df = load_gym_lift_data()

# --- Input Form for Body Weight ---
st.subheader("Add Body Weight Entry")
with st.form("body_weight_form", clear_on_submit=True):
    bw_entry_date = st.date_input("Date (Body Weight)", value=date.today(), max_value=date.today(), key="bw_date_input")
    bw_value = st.number_input("Body Weight (lbs)", min_value=0.0, format="%.1f", key="bw_value_input")
    bw_submitted = st.form_submit_button("Add Body Weight")

    if bw_submitted:
        if bw_value > 0:
            new_bw_entry = {
                "Date": pd.to_datetime(bw_entry_date), # Store as datetime
                "Body Weight (lbs)": bw_value
            }
            body_weight_df = pd.concat([body_weight_df, pd.DataFrame([new_bw_entry])], ignore_index=True)
            body_weight_df = body_weight_df.sort_values(by="Date", ascending=True).reset_index(drop=True)
            body_weight_df.to_csv(BODY_WEIGHT_LOG_FILE, index=False)
            st.success("Body weight entry added!")
            st.rerun()
        else:
            st.warning("Body Weight (lbs) must be greater than 0.")

# --- Input Form for Gym Lifts ---
st.subheader("Add Gym Lift Entry")
st.markdown("Use this section to record individual sets for an exercise.")

# Initialize session state variables for persistence and dynamic control
if 'num_sets_input_state' not in st.session_state:
    st.session_state.num_sets_input_state = 1
if 'same_sets_checkbox_state' not in st.session_state:
    st.session_state.same_sets_checkbox_state = False
if 'default_reps_input_state' not in st.session_state:
    st.session_state.default_reps_input_state = 8
if 'default_weight_input_state' not in st.session_state:
    st.session_state.default_weight_input_state = 0.0
# New session state for exercise name management
if 'current_selected_exercise' not in st.session_state:
    st.session_state.current_selected_exercise = "" # Stores the value of the selectbox/text input
if 'new_exercise_text_value' not in st.session_state:
    st.session_state.new_exercise_text_value = "" # Stores the value of the text input for "Other"

# Common exercises list
common_exercises = sorted([
    "Seated Cable Rows", "Pullups", "Lat Pull Down", "Hex bar Deadlift",
    "Leg Curls", "Rear Delt Fly", "Single arm lat pulldown", "Standing Rope Cable Row",
    "Bicep Curl", "Smith deadlift", "Squats", "Step-ups", "Chest Press",
    "Bench Press", "Pec flys", "Lunges", "Shoulder Press", "Decline chest press",
    "Skull Crushers", "Lat Raises", "Hip Thrusts", "Tricep push down", "Leg extension"
])

# Move 'Number of Sets' and 'Same reps/weight' checkbox outside the form for dynamic reactivity
st.session_state.same_sets_checkbox_state = st.checkbox(
    "Same reps and weight for all sets?", 
    value=st.session_state.same_sets_checkbox_state, 
    key="same_sets_checkbox"
)

st.session_state.num_sets_input_state = st.number_input(
    "Number of Sets", 
    min_value=1, 
    value=st.session_state.num_sets_input_state, 
    step=1, 
    key="num_sets_dynamic_input",
    disabled=st.session_state.same_sets_checkbox_state # Disable when checkbox is checked
)

with st.form("gym_lift_form", clear_on_submit=False): # Set clear_on_submit to False
    lift_entry_date = st.date_input("Date (Lift)", value=date.today(), max_value=date.today(), key="lift_date_input")
    
    # Determine the default index for the selectbox based on current_selected_exercise
    default_index = 0 # Default to empty string
    if st.session_state.current_selected_exercise in common_exercises:
        default_index = common_exercises.index(st.session_state.current_selected_exercise) + 1 # +1 for "" at index 0
    elif st.session_state.current_selected_exercise and st.session_state.current_selected_exercise not in common_exercises:
        # If it's a custom exercise previously entered, try to set the selectbox to "Other"
        default_index = len(common_exercises) + 1 # Index of "Other (type new)"

    # Selectbox for Exercise Name
    selected_option = st.selectbox(
        "Select or type an Exercise Name:",
        options=[""] + common_exercises + ["Other (type new)"],
        index=default_index,
        key="exercise_select_box"
    )

    exercise_name_to_save = ""
    if selected_option == "Other (type new)":
        # If "Other" is selected, show a text input for the new exercise name
        new_exercise_name = st.text_input(
            "Enter New Exercise Name:",
            value=st.session_state.new_exercise_text_value, # Persist value of text input
            key="new_exercise_text_input"
        )
        exercise_name_to_save = new_exercise_name.strip()
        st.session_state.new_exercise_text_value = new_exercise_name # Update session state
    else:
        # If a common exercise or empty string is selected, use that
        exercise_name_to_save = selected_option.strip()
        st.session_state.new_exercise_text_value = "" # Clear the text input's value if switching back

    # Always update the main selected exercise state for next session
    st.session_state.current_selected_exercise = exercise_name_to_save
    
    set_details = []
    st.markdown("---")
    st.markdown("**Enter details for each set:**")

    if st.session_state.same_sets_checkbox_state:
        cols = st.columns(2, gap="small")
        with cols[0]:
            default_reps = st.number_input(
                f"Reps (All Sets)", 
                min_value=1, 
                value=st.session_state.default_reps_input_state, 
                step=1, 
                key="reps_all_sets"
            )
            st.session_state.default_reps_input_state = default_reps
        with cols[1]:
            default_weight = st.number_input(
                f"Weight (lbs) (All Sets)", 
                min_value=0.0, 
                format="%.1f", 
                value=st.session_state.default_weight_input_state, 
                key="weight_all_sets"
            )
            st.session_state.default_weight_input_state = default_weight
        
        for i in range(int(st.session_state.num_sets_input_state)):
            set_details.append({"Reps": default_reps, "Weight (lbs)": default_weight})

    else:
        for i in range(int(st.session_state.num_sets_input_state)):
            cols = st.columns(2, gap="small")
            with cols[0]:
                reps = st.number_input(
                    f"Reps (Set {i+1})", 
                    min_value=1, 
                    value=st.session_state.default_reps_input_state,
                    step=1, 
                    key=f"reps_set_{i}"
                )
            with cols[1]:
                weight = st.number_input(
                    f"Weight (lbs) (Set {i+1})", 
                    min_value=0.0, 
                    format="%.1f", 
                    value=st.session_state.default_weight_input_state,
                    key=f"weight_set_{i}"
                )
            set_details.append({"Reps": reps, "Weight (lbs)": weight})

    lift_submitted = st.form_submit_button("Add Gym Lift Entry")

    if lift_submitted:
        if not exercise_name_to_save: # Check against the stripped value
            st.warning("Please enter an Exercise Name.")
        else:
            new_lift_entries = []
            for i, details in enumerate(set_details):
                if details["Reps"] > 0 and details["Weight (lbs)"] > 0:
                    new_lift_entries.append({
                        "Date": pd.to_datetime(lift_entry_date),
                        "Exercise Name": exercise_name_to_save,
                        "Set Number": i + 1,
                        "Reps": details["Reps"],
                        "Weight (lbs)": details["Weight (lbs)"]
                    })
            
            if new_lift_entries:
                gym_lift_df = pd.concat([gym_lift_df, pd.DataFrame(new_lift_entries)], ignore_index=True)
                gym_lift_df = gym_lift_df.sort_values(by=["Date", "Exercise Name", "Set Number"], ascending=True).reset_index(drop=True)
                gym_lift_df.to_csv(GYM_LIFT_LOG_FILE, index=False)
                st.success("Gym lift entry added!")
                
                # Manually reset form fields (except persistent exercise name)
                st.session_state.num_sets_input_state = 1
                st.session_state.same_sets_checkbox_state = False
                st.session_state.default_reps_input_state = 8
                st.session_state.default_weight_input_state = 0.0
                st.session_state.new_exercise_text_value = "" # Clear the text input for "Other"
                
                st.rerun() # Rerun to update the displayed table and visualizer
            else:
                st.warning("Please enter valid Reps and Weight for at least one set.")

# --- Body Weight History Table ---
st.subheader("Body Weight History")
if not body_weight_df.empty:
    display_bw_df = body_weight_df.copy()
    display_bw_df['Date'] = display_bw_df['Date'].dt.date 
    st.dataframe(display_bw_df.sort_values(by="Date", ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)
else:
    st.write("No body weight entries yet.")

# --- Gym Lift History Table ---
st.subheader("Gym Lift History")
if not gym_lift_df.empty:
    display_gym_df = gym_lift_df.copy()
    display_gym_df['Date'] = display_gym_df['Date'].dt.date 
    st.dataframe(display_gym_df.sort_values(by=["Date", "Exercise Name", "Set Number"], ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)
else:
    st.write("No gym lift entries yet.")

# --- Weight Progress Visualization (Body Weight) ---
st.subheader("Weight Progress (Body Weight)")
if not body_weight_df.empty and "Body Weight (lbs)" in body_weight_df.columns and body_weight_df["Body Weight (lbs)"].dropna().any():
    body_weight_data_2025 = body_weight_df[
        (body_weight_df["Date"].dt.year == 2025) &
        (body_weight_df["Body Weight (lbs)"] > 0)
    ]
    if not body_weight_data_2025.empty:
        chart = alt.Chart(body_weight_data_2025).mark_line(point=True).encode(
            x=alt.X('Date:T', title='Date'),
            y=alt.Y('Body Weight (lbs):Q', title='Body Weight (lbs)', scale=alt.Scale(domain=[130, 180]))
        ).properties(
            title="Body Weight Progress (2025)"
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("No body weight data for 2025 to display in graph.")
else:
    st.write("No body weight data to display in graph.")

# --- Gym Lift Progress Visualization ---
st.subheader("Gym Lift Progress")

if not gym_lift_df.empty:
    unique_exercises = sorted(gym_lift_df["Exercise Name"].dropna().unique())
    
    if unique_exercises:
        selected_exercise_viz = st.selectbox(
            "Select an Exercise to view progress:", 
            unique_exercises, 
            key="viz_exercise_select"
        )
        
        exercise_data = gym_lift_df[gym_lift_df["Exercise Name"] == selected_exercise_viz].copy()
        
        if not exercise_data.empty:
            exercise_data["Set Volume"] = exercise_data["Reps"] * exercise_data["Weight (lbs)"]
            
            # Corrected line: use exercise_data for groupby
            daily_volume = exercise_data.groupby(exercise_data['Date'].dt.date).agg(
                Total_Daily_Volume=('Set Volume', 'sum')
            ).reset_index()
            daily_volume['Date'] = pd.to_datetime(daily_volume['Date']) 
            
            chart = alt.Chart(daily_volume).mark_line(point={
                "size": 100,  # Make dots larger
                "opacity": 1 # Ensure dots are fully visible
            }, strokeWidth=3).encode( # Make lines bolder
                x=alt.X('Date:T', title='Date', axis=alt.Axis(format="%Y-%m-%d")), # Format X-axis to show only date
                y=alt.Y('Total_Daily_Volume:Q', title=f'Total Volume (lbs)'),
                tooltip=[alt.Tooltip('Date:T', format="%Y-%m-%d"), 'Total_Daily_Volume:Q']
            ).properties(
                title=f'Daily Total Volume for {selected_exercise_viz}'
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write(f"No data to display for {selected_exercise_viz}.")
    else:
        st.write("No exercises recorded yet to display progress. Add some gym lift entries!")
else:
    st.write("No gym lift entries yet to display progress.")