# Import libraries
import logging
import streamlit as st
import google.generativeai as genai

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- API Configuration ---
def configure_genai(api_key):
    try:
        genai.configure(api_key=api_key)
        # --- Model Availability Check (Crucial Fix) ---
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        logger.info(f"Available Gemini models: {available_models}")
        if not available_models:  # Check if any models are available
            raise Exception("No Gemini models with 'generateContent' support are available.")
        
        logger.info("Gemini API connection and model check successful.")
        return available_models  # Return available models

    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        st.error(f"Failed to configure Gemini API: {str(e)}.  Check your API key and ensure the Gemini API is enabled in your Google Cloud project.")
        st.stop()