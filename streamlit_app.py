import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()
# GEMININ API / other llm keys 
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get Gemini response
def get_gemini_response(input_prompt, image):
    #model = genai.GenerativeModel('gemini-pro-vision')
    model = genai.GenerativeModel('gemini-1.5-flash')  # Newer, faster model
    response = model.generate_content([input_prompt, image[0]])  
    return response.text

# Function to process uploaded image
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [{
            "mime_type": uploaded_file.type,
            "data": bytes_data
        }]
        return image_parts
    else:
        raise FileNotFoundError("No File uploaded")


st.set_page_config(page_title="CalMeal APP")
st.header("Know Your Food!!!")

uploaded_file = st.file_uploader("Choose your meal image..", type=["jpg", "jpeg", "png"])
image = None

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_container_width=True)


submit = st.button("Tell me about the total calories.")


if submit:
    if uploaded_file is not None:
        image_data = input_image_setup(uploaded_file)  
        input_prompt = """
        You are an expert nutritionist. Analyze the food items from the image and estimate total calories.
        Also, provide a breakdown in this format:
        1. Item 1 - number of calories
        2. Item 2 - number of calories
        ----
        ----
        Additionally:
        - Mention if the food is healthy or not.Special mention for kids if it is complete meal to help them in growth.Add healthy or unhealthy emojis to represent it better.
        - Provide the percentage of protein, carbs, fat, fiber, sugar, and other important nutrients including vitamins.
        - Suggest veg food addition or replacement to balance any unhealthy intake.
        """
        response = get_gemini_response(input_prompt, image_data)
        st.header("Following are the nutrion deails of given meal in image:")
        st.write(response)
    else:
        st.error("Please upload an image before submitting.")
