import logging
from googletrans import Translator

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Translation Support ---
LANGUAGES = {
    'en': 'English',
    'hi': 'हिन्दी (Hindi)',
    'ta': 'தமிழ் (Tamil)',
    'te': 'తెలుగు (Telugu)',
    'kn': 'ಕನ್ನಡ (Kannada)',
    'ml': 'മലയാളം (Malayalam)',
    'bn': 'বাংলা (Bengali)',
    'gu': 'ગુજરાતી (Gujarati)',
    'mr': 'मराठी (Marathi)',
    'pa': 'ਪੰਜਾਬੀ (Punjabi)',
    'or': 'ଓଡ଼ିଆ (Odia)',
}

def get_translator():
    return Translator()

def translate_text(text, target_language, from_language='en'):
    if target_language == 'en' or not text:
        return text
    try:
        translator = get_translator()
        result = translator.translate(text, src=from_language, dest=target_language)
        return result.text
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text + " [Translation failed]"


def translate_content(content, target_language):
    if target_language == 'en':
        return content
        
    translated_content = {}
    for level, level_data in content.items():
        translated_content[level] = {
            "explanation": translate_text(level_data.get("explanation", ""), target_language),
            "estimated_time": translate_text(level_data.get("estimated_time", ""), target_language),
            "resources": []
        }

        for resource in level_data.get("resources", []):
            translated_resource = resource.copy()
            translated_resource["type"] = translate_text(resource.get("type", ""), target_language)
            translated_resource["name"] = translate_text(resource.get("name", ""), target_language)
            translated_resource["description"] = translate_text(resource.get("description", ""), target_language)
            translated_content[level]["resources"].append(translated_resource)

    return translated_content