# Import libraries
import logging
import requests
from bs4 import BeautifulSoup

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Roadmap.sh Scraping ---
def scrape_roadmap_sh(skill):
    try:
        skill_urls = [
            skill.lower().replace(" ", "-"),
            skill.lower().replace(" ", ""),
            skill.lower().split()[0] if " " in skill.lower() else skill.lower()
        ]

        for skill_url in skill_urls:
            url = f"https://roadmap.sh/{skill_url}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                roadmap_div = (
                    soup.find('div', class_='roadmap-container') or
                    soup.find('div', {'id': 'roadmap-content'}) or
                    soup.find('main')
                )

                if roadmap_div:
                    roadmap_items = []
                    selectors = [
                        ('li', {'class': 'node'}),
                        ('div', {'class': 'roadmap-group'}),
                        ('section', {'class': 'roadmap-section'})
                    ]

                    for tag, attrs in selectors:
                        items = roadmap_div.find_all(tag, attrs)
                        if items:
                            for item in items:
                                title_elem = item.find(['h2', 'h3', 'h4', 'strong'])
                                desc_elem = item.find(['p', 'span'])

                                title = title_elem.text.strip() if title_elem else ''
                                description = desc_elem.text.strip() if desc_elem else ''

                                if title:
                                    roadmap_items.append(f"- **{title}**: {description}")

                    if roadmap_items:
                        markdown_output = f"### Roadmap.sh Roadmap for {skill}:\n\n"
                        markdown_output += "\n".join(roadmap_items) + "\n"
                        markdown_output += f"\n[View Full Roadmap on roadmap.sh]({url})\n"
                        return markdown_output
                return f"Found a roadmap page for {skill} on roadmap.sh. [View it here]({url})"
        return f"Could not find a dedicated roadmap for '{skill}' on roadmap.sh. Try checking [their main page](https://roadmap.sh)."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching roadmap from roadmap.sh: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"An error occurred while scraping roadmap.sh: {str(e)}")
        return None