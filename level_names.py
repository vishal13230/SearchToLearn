# --- Level Name Mapping ---
def get_level_names(skill):
    skill_lower = skill.lower()
    if any(keyword in skill_lower for keyword in ["coding", "programming", "python", "java", "javascript", "software", "web development", "data science"]):
        return ("Syntax & Basics", "Object-Oriented Programming", "Advanced Frameworks"), " (Levels: Syntax & Basics, Object-Oriented Programming, Advanced Frameworks)"
    elif any(keyword in skill_lower for keyword in ["music", "guitar", "piano", "singing", "violin"]):
        return ("Fundamentals", "Technique", "Performance"), " (Levels: Fundamentals, Technique, Performance)"
    elif any(keyword in skill_lower for keyword in ["art", "drawing", "painting", "sculpture", "design"]):
        return ("Sketching & Form", "Color Theory", "Advanced Techniques"), " (Levels: Sketching & Form, Color Theory, Advanced Techniques)"
    elif any(keyword in skill_lower for keyword in ["writing", "creative writing", "blogging", "journalism"]):
        return ("Grammar and Style", "Storytelling Techniques", "Publishing Strategies"), " (Levels: Grammar and Style, Storytelling Techniques, Publishing Strategies)"
    elif any(keyword in skill_lower for keyword in ["language", "spanish", "french", "german", "english"]):
        return ("Conversational Basics", "Fluency & Grammar", "Native-Level Proficiency"), " (Levels: Conversational Basics, Fluency & Grammar, Native-Level Proficiency)"
    else:
        return ("Foundation", "Core", "Mastery"), " (Levels: Foundation, Core, Mastery)"