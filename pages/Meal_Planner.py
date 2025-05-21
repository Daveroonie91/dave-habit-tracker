import streamlit as st
import json # For parsing JSON response from LLM

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

# Placeholder for API Key - Canvas will inject this at runtime
API_KEY = "" # Leave this empty. Canvas will provide it.

async def generate_meal_ideas(preferences, ingredients, meal_type, count):
    prompt = f"""Generate {count} meal ideas.
    Dietary Preferences: {preferences if preferences else 'None'}
    Ingredients Available: {ingredients if ingredients else 'Any'}
    Meal Type: {meal_type}

    For each meal idea, provide:
    - Meal Name
    - A short description
    - Key ingredients
    - Simple instructions (3-4 steps)

    Format the output as a JSON array of objects, where each object has 'mealName', 'description', 'keyIngredients' (array of strings), and 'instructions' (array of strings).
    """

    chatHistory = []
    chatHistory.push({ "role": "user", "parts": [{ "text": prompt }] })

    payload = {
        "contents": chatHistory,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "mealName": { "type": "STRING" },
                        "description": { "type": "STRING" },
                        "keyIngredients": {
                            "type": "ARRAY",
                            "items": { "type": "STRING" }
                        },
                        "instructions": {
                            "type": "ARRAY",
                            "items": { "type": "STRING" }
                        }
                    },
                    "propertyOrdering": ["mealName", "description", "keyIngredients", "instructions"]
                }
            }
        }
    }

    # IMPORTANT: The API endpoint for text generation is gemini-2.0-flash
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    try:
        response = await st.experimental_singleton.fetch(
            api_url,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(payload)
        )
        result = await response.json()

        if result and result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            json_string = result["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(json_string)
        else:
            st.error("Failed to get a valid response from the AI. Please try again.")
            return None
    except Exception as e:
        st.error(f"An error occurred while calling the AI: {e}")
        return None

if st.button("Generate Meal Ideas"):
    with st.spinner("Generating delicious ideas..."):
        # Streamlit's `st.experimental_singleton.run_async` requires the async function to be awaited
        meal_ideas = st.experimental_singleton.run_async(
            generate_meal_ideas(dietary_preferences, ingredients_available, meal_type, num_suggestions)
        )
        
        if meal_ideas:
            st.subheader("Your Meal Ideas:")
            for i, meal in enumerate(meal_ideas):
                st.markdown(f"### {i+1}. {meal.get('mealName', 'N/A')}")
                st.write(f"**Description:** {meal.get('description', 'N/A')}")
                st.write("**Key Ingredients:**")
                st.markdown("- " + "\n- ".join(meal.get('keyIngredients', ['N/A'])))
                st.write("**Instructions:**")
                st.markdown("- " + "\n- ".join(meal.get('instructions', ['N/A'])))
                st.markdown("---")
        else:
            st.write("No meal ideas could be generated.")

