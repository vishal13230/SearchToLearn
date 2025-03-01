# Import the libraries
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import validators
import time
import requests
from bs4 import BeautifulSoup
import logging
import json
from googletrans import Translator
from PIL import Image  # VISION INTEGRATION:  Import PIL for image handling
import io  # VISION INTEGRATION: For handling image bytes

# Import modules
from roadmap import scrape_roadmap_sh
from level_names import get_level_names
from api_configration import configure_genai
from translate import translate_text, LANGUAGES
from prompt_and_response import verify_url, validate_api_key, validate_skill_input, InvalidInputError, generate_learning_path, parse_response

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Streamlit UI ---
def main():
    st.set_page_config(page_title="Resource Rover", page_icon="🚀", layout="wide")
    
    # --- Session State ---
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = None
    if 'skill' not in st.session_state:
        st.session_state.skill = ""
    if 'level_names' not in st.session_state:
        st.session_state.level_names = None
    if 'roadmap_data' not in st.session_state:
        st.session_state.roadmap_data = None
    if 'available_models' not in st.session_state:
        st.session_state.available_models = [] # Initialize
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = None
    # VISION INTEGRATION: Add session state for image-related data
    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None
    if 'identified_skill' not in st.session_state:
        st.session_state.identified_skill = None


    # --- CSS Styling ---
    lang_selector_css = """
        <style>
        .language-selector { position: absolute; top: 0.75rem; right: 1rem; z-index: 1000; max-width: 180px; }
        .stSelectbox > div > div > div { background-color: white; font-size: 0.9em; padding: 4px 8px; }
        .lang-dropdown { border-left: 3px solid #FF9933; border-right: 3px solid #138808; background-color: #FFFFFF; }
        .stApp { background: linear-gradient(to bottom right, #f0f2f6, #dcdde1); }
        .sidebar .sidebar-content { background-color: #e8eaf6; }
        h1, h2, h3 { font-family: 'Product Sans', sans-serif; }
        h1 { color: #311b92; font-size: 3em; font-weight: 700; }
        h2 { color: #4527a0; font-size: 2.5em; font-weight: 600; }
        h3 { color: #5e35b1; font-size: 2em; font-weight: 500; }
        .explanation-text { background-color: #ede7f6; padding: 15px; border-radius: 8px; border-left: 5px solid #5e35b1; font-size: 1.1em; line-height: 1.5; }
        .resource-card { background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .resource-card a { color: #4527a0; text-decoration: none; font-weight: 600; }
        .resource-card a:hover { text-decoration: underline; }
        .time-estimate { background-color: #f3e8ff; padding: 8px 15px; border-radius: 20px; border: 1px dashed #9333ea; display: inline-block; margin: 10px 0; font-style: italic; color: #6b21a8; }
        .stButton>button { background-color: #5e35b1; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; transition: all 0.3s ease; }
        .stButton>button:hover { background-color: #4527a0; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .stTextInput>div>div>input { color: #1F2937; border-color: #ddd; border-radius: 8px; padding: 12px 15px; }
        .stSelectbox>div>div>div { background-color: white; border-color: #ddd; border-radius: 8px; }
        .stExpander { border-color: #ddd; border-radius: 8px; overflow: hidden; }
        .stExpanderHeader { font-weight: bold; color: #4527a0; background-color: #f3e8ff; padding: 15px; }
        .stAlert { border-radius: 8px; }
        .stAlert.success { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
        .stAlert.warning { background-color: #fff3cd; color: #856404; border-color: #ffeeba; }
        .stAlert.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
        .app-header { position: relative; padding-bottom: 5px; }
        .app-header::after { content: ""; position: absolute; left: 0; bottom: 0; height: 4px; width: 100%; background: linear-gradient(to right, #FF9933 33%, #FFFFFF 33%, #FFFFFF 66%, #138808 66%); }
        .tips-section { background-color: #e0e7ff; padding: 15px; border-radius: 8px; margin-top: 20px; }
        .tips-section h3 { color: #311b92; }
        .tips-section ul { list-style-type: disc; margin-left: 20px; }
        .tips-section li { margin-bottom: 5px; }
        </style>
        """
    st.markdown(lang_selector_css, unsafe_allow_html=True)

    # Language selector
    lang_container = st.container()
    with lang_container:
        st.markdown('<div class="language-selector">', unsafe_allow_html=True)
        selected_lang = st.selectbox(
            "भाषा / மொழி / Language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=list(LANGUAGES.keys()).index(st.session_state.language),
            key="lang_select",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            if st.session_state.generated_content:
                st.experimental_rerun()

    # App Titles and Description
    app_titles = {
        'en': "Resource Rover 🚀",
        'hi': "संसाधन रोवर 🚀",
        'ta': "ரிசோர்ஸ் ரோவர் 🚀",
        'te': "రిసోర్స్ రోవర్ 🚀",
        'kn': "ರಿಸೋರ್ಸ್ ರೋವರ್ 🚀",
        'ml': "റിസോഴ്സ് റോവർ 🚀",
        'bn': "রিসোর্স রোভার 🚀",
        'gu': "રિસોર્સ રોવર 🚀",
        'mr': "रिसोर्स रोव्हर 🚀",
        'pa': "ਰਿਸੋਰਸ ਰੋਵਰ 🚀",
        'or': "ରିସୋର୍ସ ରୋଭର 🚀",
    }
    app_descriptions = {
        'en': "Discover the best learning resources for any skill! Enter a skill and let Resource Rover find your path to mastery.",
        'hi': "किसी भी कौशल के लिए सर्वोत्तम शिक्षण संसाधन खोजें! एक कौशल दर्ज करें और रिसोर्स रोवर को आपकी महारत का मार्ग खोजने दें।",
        'ta': "எந்த திறனுக்கும் சிறந்த கற்றல் ஆதாரங்களைக் கண்டறியுங்கள்! ஒரு திறனை உள்ளிட்டு, ரிசோர்ஸ் ரோவர் உங்கள் தேர்ச்சிப் பாதையைக் கண்டுபிடிக்கட்டும்.",
    }
    current_title = app_titles.get(st.session_state.language, app_titles['en'])
    current_description = app_descriptions.get(st.session_state.language, app_descriptions['en'])

    st.markdown(f'<div class="app-header"><h1>{current_title}</h1></div>', unsafe_allow_html=True)
    st.markdown(current_description)

    # --- Sidebar ---
    with st.sidebar:
        sidebar_title = translate_text("Configuration", st.session_state.language)
        st.header(sidebar_title)

        api_key_label = translate_text("Enter Google API Key:", st.session_state.language)
        api_key = st.text_input(api_key_label, type="password", placeholder="sk-...")
        if api_key:
            try:
                api_key = validate_api_key(api_key)
                st.session_state.available_models = configure_genai(api_key)  # Configure and get models
            except ValueError as e:
                st.error(translate_text(str(e), st.session_state.language))
                st.stop()
            except Exception as e: # Catch configuration errors
                st.error(translate_text(str(e), st.session_state.language))
                st.stop()


        get_key_text = translate_text("[Get Google API Key](https://ai.google.dev/)", st.session_state.language)
        st.markdown(get_key_text)

        model_settings_text = translate_text("Model Settings", st.session_state.language)
        st.subheader(model_settings_text)
        
        model_choice_label = translate_text("Choose a Model:", st.session_state.language)

        # --- Model Selection (Handles initial state and updates) ---
        if st.session_state.available_models: # Only show if models are available
             # Select default, or the first available model
            default_model = st.session_state.selected_model if st.session_state.selected_model in st.session_state.available_models else st.session_state.available_models[0]
            model_choice = st.selectbox(model_choice_label, st.session_state.available_models, index=st.session_state.available_models.index(default_model))
            st.session_state.selected_model = model_choice # Store the selected model
        else:
            st.selectbox(model_choice_label, ["No models available"], disabled=True) # Disable if no models available

        advanced_params_label = translate_text("Advanced Parameters", st.session_state.language)
        with st.expander(advanced_params_label):
            temperature = st.slider(translate_text("Temperature:", st.session_state.language), min_value=0.0, max_value=1.0, value=0.7, step=0.05)
            top_p = st.slider("Top P:", min_value=0.0, max_value=1.0, value=0.9, step=0.05, help="Controls diversity via nucleus sampling")
            top_k = st.slider("Top K:", min_value=1, max_value=50, value=40, step=1, help="Controls diversity by limiting to top k tokens")
            max_output_tokens = st.slider("Max Output Tokens:", min_value=1000, max_value=8000, value=4096, step=250,help="Maximum length of generated response")

        st.subheader("Advanced Options")
        if st.checkbox("Show Advanced Options"):
            enable_debug = st.checkbox("Enable Debug Mode", help="Displays additional information for troubleshooting")
            rate_limit = st.slider("Rate Limit (requests/min)", min_value=1, max_value=60, value=20,help="Limit API requests to avoid quota issues")

    # --- Main Content Columns ---
    col1, col2 = st.columns([3, 1])

    with col1:
        # VISION INTEGRATION: Image Upload Section
        st.subheader("Identify Skill from Image")
        uploaded_file = st.file_uploader("Upload an image of a skill", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.session_state.uploaded_image = image  # Store the PIL Image
            st.image(image, caption="Uploaded Image", width=250)

            if st.button("Identify Skill from Image"):
                if 'gemini-pro-vision' not in st.session_state.available_models:
                    st.error("Gemini Pro Vision model is not available. Please check your API key and configuration.")
                else:
                    with st.spinner("Analyzing image..."):
                        try:
                            # Convert PIL Image to bytes
                            img_byte_arr = io.BytesIO()
                            image.save(img_byte_arr, format=image.format)
                            img_byte_arr = img_byte_arr.getvalue()

                            vision_model = genai.GenerativeModel('gemini-pro-vision')
                            response = vision_model.generate_content(
                                ["Identify the primary skill depicted in this image. Be specific.  Return the skill as a single phrase.", img_byte_arr]
                            )
                            identified_skill = response.text.strip()
                            st.session_state.identified_skill = identified_skill  # Store for later use
                            st.success(f"Identified Skill: {identified_skill}")

                        except Exception as e:
                            st.error(f"Error analyzing image: {e}")

        # --- Skill Input (Modified) ---
        # Use identified skill if available, otherwise, use text input
        skill_input_label = "Enter the skill (or use identified skill above):"
        if st.session_state.identified_skill:
             skill = st.text_input(skill_input_label, value=st.session_state.identified_skill)
        else:
             skill = st.text_input(skill_input_label, placeholder="e.g., Python Programming, Data Analysis, Watercolor Painting")


        examples = ["Data Science", "Digital Marketing", "Guitar", "Spanish Language", "Machine Learning"]
        st.markdown("**Try examples:** " + " • ".join([f"[{ex}](#{ex.lower().replace(' ', '-')})" for ex in examples]))

        # --- Generate Learning Path (remains largely the same) ---
        if st.button("Generate Learning Path"):
            if not api_key:
                st.warning("Please enter your Google API Key in the sidebar first.")
                return
            if not st.session_state.available_models:
                st.warning("No Gemini models are available. Please check your API key and configuration.")
                return
            try:
                skill = validate_skill_input(skill)
                # No need to call configure_genai here, it's done in the sidebar
                level_names, _ = get_level_names(skill)
                basic_level, intermediate_level, advanced_level = level_names

                with st.spinner(f"Generating your personalized learning path for {skill}..."):
                    progress_bar = st.progress(0)
                    progress_bar.progress(10)
                    start_time = time.time()

                    response = generate_learning_path(skill, st.session_state.selected_model, temperature, top_p, top_k, max_output_tokens)  # Use selected model
                    progress_bar.progress(70)
                    roadmap_data = scrape_roadmap_sh(skill)
                    progress_bar.progress(90)
                    end_time = time.time()
                    progress_bar.progress(100)

                    if response:
                        sections = parse_response(response, level_names)
                        st.markdown(f"""
                        ## Learning Path for {skill}
                        
                        This personalized learning path will take you from beginner to expert level.
                        """)
                        for level in [basic_level, intermediate_level, advanced_level]:
                            if level in sections:
                                with st.expander(f"**{level} Level**", expanded=(level == basic_level)):
                                    if sections[level]['explanation']:
                                        st.markdown("<div class='explanation-text'>" + sections[level]['explanation'] + "</div>", unsafe_allow_html=True)
                                    if sections[level]['estimated_time']:
                                        st.markdown(f"<div class='time-estimate'>⏱️ **Time Estimate:** {sections[level]['estimated_time']}</div>", unsafe_allow_html=True)
                                    if sections[level]["resources"]:
                                        st.markdown("### 📚 Recommended Resources")
                                        for resource in sections[level]["resources"]:
                                            url_status = "✅ Link verified" if verify_url(resource['url']) else "⚠️ Link may be unstable"
                                            st.markdown(f"""
                                            <div class='resource-card'>
                                                <strong>{resource['type']}</strong>: <a href="{resource['url']}" target="_blank">{resource['name']}</a>
                                                <p>{resource['description']}</p>
                                                <small>{url_status}</small>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    else:
                                        st.warning("No resources were found for this level. Please try regenerating.")
                            else:
                                st.error(f"Could not generate content for {level} level. Please try again.")
                        if roadmap_data:
                            with st.expander("Industry Roadmap", expanded=False):
                                st.markdown(roadmap_data)

                        with col2:
                            st.success(f"✨ Generated in {end_time - start_time:.2f} seconds!")
                            st.balloons()
                            st.markdown("### 💾 Save Your Path")
                            markdown_content = f"# Learning Path for {skill}\n\n"
                            for level in [basic_level, intermediate_level, advanced_level]:
                                if level in sections:
                                    markdown_content += f"## {level}\n\n"
                                    markdown_content += f"### Explanation\n{sections[level]['explanation']}\n\n"
                                    markdown_content += f"### Estimated Time\n{sections[level]['estimated_time']}\n\n"
                                    markdown_content += "### Resources\n"
                                    for resource in sections[level]["resources"]:
                                        
                                        markdown_content += f"- **{resource['type']}**: [{resource['name']}]({resource['url']}) - {resource['description']}\n"
                                    markdown_content += "\n"
                            st.download_button(
                                label="Download as Markdown",
                                data=markdown_content,
                                file_name=f"{skill.lower().replace(' ', '_')}_learning_path.md",
                                mime="text/markdown",
                            )
                    else:
                        st.error("Failed to generate content. Please check your API key and try again.")
            except InvalidInputError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                logger.exception("Unexpected error")

        # VISION INTEGRATION: Visual Feedback Section
        st.subheader("Get Visual Feedback")
        if st.session_state.identified_skill or skill:
            feedback_skill = st.session_state.identified_skill if st.session_state.identified_skill else skill
            st.write(f"Upload an image related to: **{feedback_skill}**")
            feedback_file = st.file_uploader("Upload image for feedback", type=["jpg", "jpeg", "png"], key="feedback_uploader")

            if feedback_file is not None:
                feedback_image = Image.open(feedback_file)
                st.image(feedback_image, caption="Uploaded Image for Feedback", width=250)

                if st.button("Get Feedback"):
                    if 'gemini-pro-vision' not in st.session_state.available_models:
                        st.error("Gemini Pro Vision model is not available.")
                    else:
                        with st.spinner("Generating feedback..."):
                            try:
                                # Convert PIL Image to bytes
                                img_byte_arr = io.BytesIO()
                                feedback_image.save(img_byte_arr, format=feedback_image.format)
                                img_byte_arr = img_byte_arr.getvalue()

                                vision_model = genai.GenerativeModel('gemini-pro-vision')
                                response = vision_model.generate_content(
                                    [f"Provide brief, constructive feedback on this image related to {feedback_skill}. Assume the user is a beginner.", img_byte_arr]
                                )
                                st.write(response.text)

                            except Exception as e:
                                st.error(f"Error generating feedback: {e}")
        else:
            st.info("Please identify or enter a skill first to get feedback.")

    # --- Feedback and Tips ---
    with col2:
        st.subheader("Feedback")
        feedback = st.text_area("How can we improve?", max_chars=500)
        if st.button("Submit Feedback"):
            if feedback.strip():
                st.success("Thank you for your feedback!")
                st.session_state['feedback'] = ""  # Clear feedback
            else:
                st.warning("Please enter your feedback before submitting.")

        st.markdown("<div class='tips-section'>", unsafe_allow_html=True)
        st.markdown("### 💡 Tips")
        st.markdown("""
            <ul>
                <li>Be specific with your skill (e.g., "Conversational French" instead of "French").</li>
                <li>Try related skills for broader results.</li>
                <li>Higher temperature: more varied resources (but potentially less reliable).</li>
                <li>Lower temperature: more focused and reliable resources.</li>
            </ul>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    load_dotenv()
    main()