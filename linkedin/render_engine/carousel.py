import os
import re
import json
import time
import logging
import random
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TMP_DIR = os.path.join(BASE_DIR, "data", "tmp")
TEMPLATES_DIR = os.path.join(BASE_DIR, "data", "templates")
STATE_FILE = os.path.join(BASE_DIR, "data", "theme_state.json")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Create empty stubs if they don't exist
for f in ["light_themes.html", "dark_themes.html"]:
    path = os.path.join(TEMPLATES_DIR, f)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as file:
            file.write("<!-- PASTE YOUR RAW HTML THEMES HERE -->\n")

def parse_template_file(file_name: str) -> dict:
    """
    Reads a raw HTML file containing multiple templates and extracts fonts, CSS, and individual template wrappers.
    """
    path = os.path.join(TEMPLATES_DIR, file_name)
    if not os.path.exists(path):
        return None
        
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract all Google Fonts links
    fonts = "".join(re.findall(r'<link[^>]*href=["\']https://fonts.googleapis.com[^>]*>', content))
    
    # Extract CSS
    css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL | re.IGNORECASE)
    css = css_match.group(1) if css_match else ""
    
    # Force body to be exactly 1080x1080 for Playwright
    css = "body { width: 1080px !important; height: 1080px !important; margin: 0; padding: 0; overflow: hidden; }\n" + css
    
    # Extract template wrappers
    # The user's code uses <div class="template-wrap"> for each slide
    parts = content.split('<div class="template-wrap">')
    
    if len(parts) < 2:
        return None  # No templates found
        
    templates = []
    for part in parts[1:]:
        # Remove anything after the closing </div> of the wrap if there are extra tags
        # A simple way is to just take it as is, since it will be injected into <body>
        # We append the opening div that was consumed by split()
        clean_part = '<div class="template-wrap">' + part
        templates.append(clean_part)
        
    return {
        "fonts": fonts,
        "css": css,
        "templates": templates
    }


def get_next_theme_type() -> str:
    """Reads state to alternate between light and dark."""
    state = {"last_theme": "dark"} # Default so first post is light
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except:
            pass
            
    next_theme = "light" if state.get("last_theme") == "dark" else "dark"
    
    # Save the new state
    with open(STATE_FILE, "w") as f:
        json.dump({"last_theme": next_theme}, f)
        
    return next_theme


def render_carousel(content_text: str) -> list[str]:
    """
    Renders text into a series of slide images using Playwright and returns the paths.
    Alternates between parsed light and dark themes.
    """
    slides_text = [t.strip() for t in content_text.split('\n\n') if t.strip()]
    if not slides_text:
        return []

    slides_text = slides_text[:10]
    media_paths = []
    
    theme_type = get_next_theme_type()
    logger.info(f"Carousel alternating theme engine selected: {theme_type.upper()}")
    
    file_name = f"{theme_type}_themes.html"
    parsed_data = parse_template_file(file_name)
    
    # Fallback to hardcoded aesthetic if external templates aren't loaded or are empty
    if not parsed_data or not parsed_data["templates"]:
        logger.warning(f"No templates found in {file_name}. Falling back to default.")
        return fallback_render(slides_text)

    # Pick one random template from the 15 available in that file
    selected_body = random.choice(parsed_data["templates"])

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1080})
            
            for i, slide_text in enumerate(slides_text):
                # Safely escape HTML
                safe_text = slide_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                
                import re
                
                # Replace whatever text is inside <div class="content">...</div> with the actual slide text
                body_content = re.sub(
                    r'(<div[^>]*class="[^"]*\bcontent\b[^"]*"[^>]*>).*?(</div>)', 
                    rf'\1{safe_text}\2', 
                    selected_body, 
                    flags=re.DOTALL
                )
                
                # Try replacing explicit placeholders if they exist
                body_content = body_content.replace("{slide_content}", safe_text)\
                                           .replace("{slide_num}", f"{i+1:02d}")\
                                           .replace("{total_slides}", f"{len(slides_text):02d}")
                
                rendered_html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    {parsed_data['fonts']}
                    <style>{parsed_data['css']}</style>
                </head>
                <body>
                    {body_content}
                </body>
                </html>
                """
                
                page.set_content(rendered_html)
                page.wait_for_load_state("networkidle")
                
                out_path = os.path.join(TMP_DIR, f"slide_{int(time.time())}_{i}.png")
                page.screenshot(path=out_path)
                media_paths.append(out_path)
                
            browser.close()
    except Exception as e:
        logger.error(f"Failed to generate carousel using Playwright: {e}")
        return []

    return media_paths


def fallback_render(slides_text: list) -> list:
    """Basic fallback if the user hasn't pasted their HTML themes yet."""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                margin: 0; padding: 0; width: 1080px; height: 1080px;
                background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
                color: #ffffff; font-family: 'Segoe UI', sans-serif;
                display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
                box-sizing: border-box; padding: 80px;
            }
            .content { font-size: 56px; line-height: 1.4; font-weight: 600; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
            .footer { position: absolute; bottom: 80px; font-size: 32px; color: #8892b0; font-weight: 400; }
        </style>
    </head>
    <body>
        <div class="content">{slide_content}</div>
        <div class="footer">{slide_num} / {total_slides}</div>
    </body>
    </html>
    """
    media_paths = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1080})
            for i, slide_text in enumerate(slides_text):
                safe_text = slide_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                rendered_html = html_template.replace("{slide_content}", safe_text).replace("{slide_num}", str(i+1)).replace("{total_slides}", str(len(slides_text)))
                page.set_content(rendered_html)
                out_path = os.path.join(TMP_DIR, f"slide_{int(time.time())}_{i}.png")
                page.screenshot(path=out_path)
                media_paths.append(out_path)
            browser.close()
    except Exception as e:
        logger.error(f"Fallback carousel generation failed: {e}")
    return media_paths
