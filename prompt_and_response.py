# Import libraries
import re
import logging
import requests
import validators
import streamlit as st
import google.generativeai as genai

# Import modules
from level_names import get_level_names

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---
class InvalidInputError(Exception):
    """Custom exception for invalid user inputs."""
    pass

# --- Input Validation ---
def validate_skill_input(skill):
    if not skill or len(skill.strip()) < 3:
        raise InvalidInputError("Please enter a valid skill (at least 3 characters).")
    return skill.strip()

def validate_api_key(api_key):
    if not api_key:
        raise ValueError("An API key is required. Please enter it in the sidebar.")
    pattern = re.compile(r'^[A-Za-z0-9_\-]{30,}$')  # Basic check for API key format
    if not pattern.match(api_key):
        raise ValueError("The API key format appears to be incorrect.")
    return api_key

# --- URL Verification ---
def verify_url(url):
    if not validators.url(url):
        return False
    try:
        response = requests.head(url, timeout=5, allow_redirects=True) # Allow redirects
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False

# --- Gemini Interaction ---
def generate_learning_path(skill, model_choice, temperature, top_p, top_k, max_output_tokens):
    level_names, prompt_suffix = get_level_names(skill)
    basic_level, intermediate_level, advanced_level = level_names

    prompt = f"""
    Create a highly structured and detailed learning path for the skill: '{skill}'. Organize the path into three distinct levels: {basic_level}, {intermediate_level}, and {advanced_level}.
    
    For each level, include:
    
    1.  **Comprehensive Explanation**:
        *   **{basic_level}**: A basic paragraph (5-7 sentences)
        *   **{intermediate_level}**: A detailed paragraph (15-20 sentences)
        *   **{advanced_level}**: A comprehensive explanation (20-40 sentences)
            
    2.  **Curated Resources**:
        *   Provide 4-6 *best* online resources.  Prioritize *free* resources.
        *   Include variety:
            *   ▶️ **YouTube Videos/Courses**
            *   📝 **Blogs/Articles**
            *   📚 **Documentation/Tutorials**
            *   💻 **Practice Exercises/Projects**
            *   📖 **Books (Free/Paid)**
            *   🧪 **Interactive Tools**
        *   **Format EXACTLY as**:  `[Emoji] [Type]: [Name] ([URL]) - [1-2 sentence description]`
            *   Ensure all URLs are **valid, complete and working**
            
    3. **Estimated Time Commitment**:
        *   Provide specific time ranges
        *   Break down time between theory and practice
        
    **Markdown Formatting**:
    ### {basic_level}
    - **Explanation:** [Extended detailed explanation]
    - **Estimated Time:** [Specific time range with weekly commitment]
    - **Resources:**
        [Emoji] [Type]: [Name] ([URL]) - [Description]
        
    ### {intermediate_level}
    - **Explanation:** [Extended detailed explanation]
    - **Estimated Time:** [Specific time range with weekly commitment]
    - **Resources:**
        [Emoji] [Type]: [Name] ([URL]) - [Description]
        
    ### {advanced_level}
    - **Explanation:** [Extended detailed explanation]
    - **Estimated Time:** [Specific time range with weekly commitment]
    - **Resources:**
        [Emoji] [Type]: [Name] ([URL]) - [Description]
    """

    prompt += prompt_suffix

    try:
        model = genai.GenerativeModel(model_choice)  # Use the selected model
        generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text
    except genai.APIError as e:
        logger.error(f"Gemini API Error: {str(e)}")
        error_message = str(e)
        if "404" in error_message and "not found" in error_message:
          st.error(f"Gemini API Error: The selected model '{model_choice}' was not found.  Please select a valid model from the dropdown.")
        else:
          st.error(f"Gemini API Error: {error_message}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
        return None


# --- Response Parsing ---
def parse_response(response_text, level_names):
    basic_level, intermediate_level, advanced_level = level_names
    levels = [basic_level, intermediate_level, advanced_level]
    sections = {}
    current_level = None

    lines = response_text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if re.match(r'^#{1,3}\s+', line):
            heading_text = re.sub(r'^#{1,3}\s+', '', line).strip()
            for level in levels:
                if level.lower() in heading_text.lower():
                    current_level = level
                    sections[current_level] = []
                    break
        elif current_level:
            sections[current_level].append(line)

    if not sections and any(level in response_text for level in levels):
        for level in levels:
            if level in response_text:
                split_text = response_text.split(level, 1)
                if len(split_text) > 1:
                    sections[level] = split_text[1].split(next((l for l in levels if l != level and l in split_text[1]), ""))[0].split('\n')

    structured_sections = {}

    for level, content in sections.items():
        structured_sections[level] = {"explanation": "", "estimated_time": "", "resources": []}
        content_text = '\n'.join(content)

        explanation_patterns = [
            r'(?:Explanation|EXPLANATION):\s*(.*?)(?:Estimated Time|ESTIMATED TIME|Resources|RESOURCES)',
            r'\*\*Explanation:\*\*\s*(.*?)(?:\*\*Estimated Time|\*\*Resources)',
            r'- Explanation:\s*(.*?)(?:- Estimated Time|- Resources)',
            r'- \*\*Explanation:\*\*\s*(.*?)(?:- \*\*Estimated Time|- \*\*Resources)'
        ]

        for pattern in explanation_patterns:
            explanation_match = re.search(pattern, content_text, re.DOTALL)
            if explanation_match:
                structured_sections[level]["explanation"] = explanation_match.group(1).strip()
                break

        time_patterns = [
            r'(?:Estimated Time|ESTIMATED TIME):\s*(.*?)(?:Resources|RESOURCES)',
            r'\*\*Estimated Time:\*\*\s*(.*?)(?:\*\*Resources)',
            r'- Estimated Time:\s*(.*?)(?:- Resources)',
            r'- \*\*Estimated Time:\*\*\s*(.*?)(?:- \*\*Resources)'
        ]

        for pattern in time_patterns:
            time_match = re.search(pattern, content_text, re.DOTALL)
            if time_match:
                structured_sections[level]["estimated_time"] = time_match.group(1).strip()
                break

        resource_section = None
        resource_patterns = [
            r'(?:Resources|RESOURCES):(.*?)(?:###|$)',
            r'\*\*Resources:\*\*(.*?)(?:###|$)',
            r'- Resources:(.*?)(?:###|$)',
            r'- \*\*Resources:\*\*(.*?)(?:###|$)'
        ]

        for pattern in resource_patterns:
            resource_match = re.search(pattern, content_text, re.DOTALL)
            if resource_match:
                resource_section = resource_match.group(1).strip()
                break

        if resource_section:
            resource_lines = resource_section.split('\n')
            for line in resource_lines:
                if not line.strip():
                    continue

                url_match = re.search(r'\((https?://[^\s\)]+)\)', line)
                if not url_match:
                    continue

                url = url_match.group(1).strip()

                is_valid_url = verify_url(url)
                if not is_valid_url:
                    if not url.startswith(('http://', 'https://')):
                        fixed_url = 'https://' + url
                        if verify_url(fixed_url):
                            url = fixed_url
                            is_valid_url = True

                if is_valid_url:
                    parts = line.split(':', 1)
                    if len(parts) < 2:
                        continue

                    emoji_and_type = parts[0].strip()
                    rest = parts[1].strip()

                    type_match = re.search(r'([A-Za-z\s/]+)', emoji_and_type)
                    resource_type = type_match.group(1).strip() if type_match else "Resource"
                    name_match = re.search(r'([^(]+)', rest)
                    resource_name = name_match.group(1).strip() if name_match else "Unnamed Resource"
                    description_match = re.search(r'\)\s*-\s*(.+)$', rest)
                    description = description_match.group(1).strip() if description_match else ""

                    structured_sections[level]["resources"].append({
                        "type": resource_type,
                        "name": resource_name,
                        "url": url,
                        "description": description
                    })
        
        # Add logging for missing fields
        if not structured_sections[level]["explanation"]:
            logger.warning(f"Missing explanation for level '{level}' during parsing.")
        if not structured_sections[level]["estimated_time"]:
            logger.warning(f"Missing estimated time for level '{level}' during parsing.")
        if not structured_sections[level]["resources"]:
            logger.warning(f"Missing resources for level '{level}' during parsing.")

    for level in structured_sections:
        explanation = structured_sections[level]["explanation"]
        explanation = re.sub(r'\s+', ' ', explanation)
        explanation = re.sub(r'\*\*|\*', '', explanation)
        structured_sections[level]["explanation"] = explanation.strip()

    return structured_sections