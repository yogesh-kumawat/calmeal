import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import pandas as pd
import re
import plotly.graph_objects as go
import plotly.express as px

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Function to get Gemini response
def get_gemini_response(input_prompt, image):
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

# Function to parse nutrition percentages from response
def extract_nutrition_percentages(response_text):
    # Look for patterns like "Protein: 20%" or "Carbs: 45%"
    nutrients = {
        'Protein': 0,
        'Carbs': 0,
        'Fat': 0,
        'Fiber': 0,
        'Sugar': 0
    }
    
    for nutrient in nutrients.keys():
        pattern = f"{nutrient}:?\s*(\d+)%"
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            nutrients[nutrient] = int(match.group(1))
    
    # If no matches found, set default values to ensure chart displays
    if nutrients['Protein'] == 0 and nutrients['Carbs'] == 0 and nutrients['Fat'] == 0:
        nutrients['Protein'] = 33
        nutrients['Carbs'] = 34
        nutrients['Fat'] = 33
    
    # Make sure percentages add up to 100% for main macros (protein, carbs, fat)
    total = nutrients['Protein'] + nutrients['Carbs'] + nutrients['Fat']
    if total > 0:  # Avoid division by zero
        nutrients['Protein'] = round(nutrients['Protein'] * 100 / total)
        nutrients['Carbs'] = round(nutrients['Carbs'] * 100 / total)
        nutrients['Fat'] = round(nutrients['Fat'] * 100 / total)
    
    return nutrients

# Function to extract calorie information
def extract_calories(response_text):
    items = []
    calories = []
    
    # Extract items and their calories
    lines = response_text.split('\n')
    for line in lines:
        # Look for patterns like "1. Rice - 150 calories" or "Rice - 150 calories"
        match = re.search(r'\d+\.\s*(.*?)\s*-\s*(\d+)\s*calories', line, re.IGNORECASE)
        if match:
            items.append(match.group(1).strip())
            calories.append(int(match.group(2)))
    
    # If no items found, add default data to ensure chart displays
    if not items:
        items = ["Sample Item"]
        calories = [500]
    
    return items, calories

# Create a pie chart for macronutrients
def create_macros_chart(nutrients):
    labels = ['Protein', 'Carbs', 'Fat']
    values = [nutrients['Protein'], nutrients['Carbs'], nutrients['Fat']]
    
    fig = px.pie(
        values=values, 
        names=labels,
        color_discrete_sequence=px.colors.sequential.Viridis,
        title="Macronutrient Distribution"
    )
    fig.update_traces(textinfo='percent+label', textfont_size=14)
    fig.update_layout(
        height=400,
        width=600,
        legend=dict(font=dict(size=14)),
        title=dict(font=dict(size=18))
    )
    return fig

# Create a bar chart for calories by item
def create_calories_chart(items, calories):
    fig = px.bar(
        x=items, 
        y=calories,
        title="Calories by Food Item",
        labels={'x': 'Food Item', 'y': 'Calories'},
        color=calories,
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig.update_layout(
        height=400,
        width=600,
        xaxis=dict(tickfont=dict(size=14)),
        yaxis=dict(tickfont=dict(size=14)),
        title=dict(font=dict(size=18))
    )
    return fig

# Custom CSS
def apply_custom_styling():
    st.markdown("""
    <style>
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #2c3e50;
        font-weight: 700;
        padding-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .sub-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #34495e;
        font-weight: 600;
        padding-top: 0.8rem;
        margin-bottom: 1rem;
    }
    .logo-container {
        display: flex;
        align-items: center;
    }
    .logo-text {
        color: #27ae60;
        margin-left: 15px;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .insight-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #27ae60;
    }
    .assessment-healthy {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .assessment-unhealthy {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stButton>button {
        background-color: #27ae60;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #219653;
    }
    .nutrition-table {
        width: 100%;
        text-align: left;
    }
    .nutrition-table th {
        background-color: #e9f7ef;
    }
    .nutrition-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .suggestions {
        background-color: #e9f7ef;
        padding: 15px;
        border-radius: 10px;
        margin-top: 20px;
    }
    .footer {
        text-align: center;
        color: #7f8c8d;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #ecf0f1;
    }
    .chart-container {
        margin-top: 20px;
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    /* Make tabs larger and more visible */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f3f5;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding: 10px 16px;
        font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #27ae60 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="CalMeal - Know Your Food",
    page_icon="🥗",
    layout="wide"
)

# Apply custom styling
apply_custom_styling()

# Create columns for logo and header
col1, col2 = st.columns([1, 5])

with col1:
    # Placeholder for logo - replace with your actual logo path
    st.image("https://wadhwanifoundation.org/wp-content/uploads/2023/10/Wadhwani-Foundation-Logo.png", width=80)

with col2:
    st.markdown('<div class="logo-text">CalMeal</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">Know Your Food</h1>', unsafe_allow_html=True)

# App description
st.markdown("""
<div style="margin-bottom: 30px;">
    Upload a photo of your meal to get nutritional analysis, calorie count, and personalized recommendations.
</div>
""", unsafe_allow_html=True)

# Create columns for image upload
uploaded_file = st.file_uploader("Choose your meal image...", type=["jpg", "jpeg", "png"])

# Display image
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Your meal", use_container_width=True, width=400)
    
    # Analysis button
    submit = st.button("Analyze Nutrition 🔍")
    
    if submit:
        with st.spinner("Analyzing your meal..."):
            try:
                image_data = input_image_setup(uploaded_file)
                input_prompt = """
                You are an expert nutritionist. Analyze the food items from the image and estimate total calories.
                Also, provide a breakdown in this format:
                1. Item 1 - number of calories
                2. Item 2 - number of calories
                
                Additionally:
                - Mention if the food is healthy or not. Special mention for kids if it is complete meal to help them in growth.
                - Provide the percentage of protein, carbs, fat, fiber, sugar, and other important nutrients including vitamins.
                - Suggest veg food addition or replacement to balance any unhealthy intake.
                
                IMPORTANT: Please include specific percentages for macronutrients. For example: Protein: 25%, Carbs: 50%, Fat: 25%, etc.
                """
                response = get_gemini_response(input_prompt, image_data)
                
                # Extract nutrition percentages for visualization
                nutrients = extract_nutrition_percentages(response)
                items, calories = extract_calories(response)
                
                # Display analysis results
                st.markdown('<h2 class="sub-header">Nutrition Analysis</h2>', unsafe_allow_html=True)
                
                # Check if the meal is healthy or unhealthy
                health_class = "assessment-healthy" if "healthy" in response.lower() else "assessment-unhealthy"
                st.markdown(f'<div class="{health_class}">{response.split(".")[0]}.</div>', unsafe_allow_html=True)
                
                # Display charts in single column layout for better visibility
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("Macronutrient Distribution")
                macros_chart = create_macros_chart(nutrients)
                st.plotly_chart(macros_chart, use_container_width=True)
                
                st.subheader("Calories by Food Item")
                calories_chart = create_calories_chart(items, calories)
                st.plotly_chart(calories_chart, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Create tabs for detailed information
                tab1, tab2, tab3 = st.tabs(["Detailed Analysis", "Nutritional Breakdown", "Recommendations"])
                
                with tab1:
                    st.markdown(response)
                
                with tab2:
                    if items and calories:
                        # Create a DataFrame for the nutritional breakdown
                        df = pd.DataFrame({
                            'Food Item': items,
                            'Calories': calories
                        })
                        st.dataframe(df, use_container_width=True)
                        
                        # Display total calories
                        st.metric("Total Calories", f"{sum(calories)} kcal")
                    else:
                        st.info("Couldn't extract detailed calorie information from the analysis.")
                
                with tab3:
                    # Extract recommendations section
                    recommendations = ""
                    if "suggest" in response.lower():
                        recommendations_section = response.lower().split("suggest")[1]
                        recommendations = "Suggest" + recommendations_section
                    
                    if recommendations:
                        st.markdown('<div class="suggestions">' + recommendations + '</div>', unsafe_allow_html=True)
                    else:
                        st.info("No specific recommendations found in the analysis.")
            
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
else:
    st.info("👆 Upload an image of your meal to get started!")

# Add footer
st.markdown('<div class="footer">CalMeal - Your personal nutrition assistant © 2025</div>', unsafe_allow_html=True)