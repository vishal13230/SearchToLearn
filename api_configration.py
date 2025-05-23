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
        target_model = "models/gemini-1.5-flash-latest"
        available_models = []
        try:
            model = genai.get_model(target_model)
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(target_model)
                logger.info(f"Using specified Gemini model: {target_model}")
            else:
                 raise Exception(f"Specified model {target_model} does not support 'generateContent'.")
        except Exception as e:
            logger.error(f"Failed to get or check specified model {target_model}: {str(e)}")
            raise Exception(f"Failed to get or check specified model {target_model}: {str(e)}")

        if not available_models:
             raise Exception(f"Specified model {target_model} is not available or supported.")

        logger.info("Gemini API connection and model check successful.")
        return available_models

    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        st.error(f"Failed to configure Gemini API: {str(e)}.  Check your API key and ensure the Gemini API is enabled in your Google Cloud project.")
        st.stop()