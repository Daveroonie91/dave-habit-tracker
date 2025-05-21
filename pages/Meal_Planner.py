import streamlit as st
import json # For parsing JSON response from LLM
import google.generativeai as genai # NEW: Import the Gemini API library
import asyncio # New: For async operations if needed later

# Set page config for collapsible sidebar and page title
st.set_page_config(
    page_title="Meal Planner", # Updated page title
    initial_sidebar_state="collapsed"
)

st.title("🍽️ Meal Planner")

st.write("Let's generate some meal ideas for you!")

# --- Meal Generation Form ---
dietary_preferences = st.text_input("Dietary preferences (e.g., vegetarian, gluten-free, low-carb):")
ingredients_available = st.text_area("Ingredients you have on hand (comma-separated):")
meal_type = st.selectbox("Type of meal", ["Breakfast", "Lunch", "Dinner", "Snack"])
num_suggestions = st.slider("Number of suggestions", 1, 5, 2)

# Configure Gemini API with the key from Streamlit Secrets
# This assumes you will add gemini_api_key="YOUR_KEY" to your Streamlit Cloud secrets
try:
    API_KEY = st.secrets["gemini_api_key"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("Gemini API key not found in Streamlit Secrets. Please add it to your app's secrets.")
    st.stop() # Stop execution if API key is missing

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

def generate_meal_ideas(preferences, ingredients, meal_type, count):
    prompt = f"""Generate {count} meal ideas.
    Dietary Preferences: {preferences if preferences else 'None'}\n
    Ingredients Available: {ingredients if ingredients else 'Any'}\n
    Meal Type: {meal_type}\n

    For each meal idea, provide:\n
    - Meal Name\n
    - A short description\n
    - Key ingredients\n
    - Simple instructions (3-4 steps)\n

    Format the output as a JSON array of objects, where each object has 'mealName', 'description', 'keyIngredients' (array of strings), and 'instructions' (array of strings).\n
    Ensure the output is valid JSON and only the JSON.
    """

    # It's good practice to send an empty chat history for new prompts,
    # or manage chat history if you want conversational turns.
    # For a single prompt, you often just pass the prompt directly.
    chatHistory = [] # Keep this if you plan to implement chat turns
    
    try:
        # Use generate_content directly. The API call is synchronous.
        response = model.generate_content(prompt)
        
        # Access the text from the response
        json_string = response.text
        
        # Attempt to parse the JSON
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON response from AI. Error: {e}")
        st.code(f"AI response: {response.text}", language="json") # Show raw response for debugging
        return None
    except Exception as e:
        st.error(f"An error occurred while calling the AI: {e}")
        return None

if st.button("Generate Meal Ideas"):
    with st.spinner("Generating delicious ideas..."):
        # Call the synchronous function directly
        meal_ideas = generate_meal_ideas(dietary_preferences, ingredients_available, meal_type, num_suggestions)
        
        if meal_ideas:
            st.subheader("Your Meal Ideas:")
            for i, meal in enumerate(meal_ideas):
                st.markdown(f"### {i+1}. {meal.get('mealName', 'N/A')}")
                st.write(f"**Description:** {meal.get('description', 'N/A')}")
                st.write("**Key Ingredients:**")
                st.markdown("- " + "\n- ".join(meal.get('keyIngredients', ['N/A'])) if meal.get('keyIngredients') else 'N/A') # Handle empty lists
                st.write("**Instructions:**")
                st.markdown("- " + "\n- ".join(meal.get('instructions', ['N/A'])) if meal.get('instructions') else 'N/A') # Handle empty lists
                st.markdown("---")
        else:
            st.warning("No meal ideas could be generated. Please check the prompt or try again.")