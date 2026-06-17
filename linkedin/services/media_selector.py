import os
import json
import random
import logging

logger = logging.getLogger(__name__)

MEDIA_LIBRARY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "media_library"))
TAGS_FILE = os.path.join(MEDIA_LIBRARY_PATH, "tags.json")

def select_media_for_post(topic_pillar: str) -> str | None:
    """
    Selects an image from the media library that matches the topic pillar based on labels.
    Returns the absolute path to the image, or None if no match is found.
    """
    if not os.path.exists(TAGS_FILE):
        logger.warning(f"Media library tags file not found at {TAGS_FILE}")
        return None

    try:
        with open(TAGS_FILE, "r", encoding="utf-8") as f:
            tags_db = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load media tags: {e}")
        return None

    topic_lower = topic_pillar.lower()
    matches = []

    for filename, labels in tags_db.items():
        # Check if any label is in the topic, or if the topic is in the label
        for label in labels:
            label_lower = label.lower()
            if label_lower in topic_lower or topic_lower in label_lower:
                image_path = os.path.join(MEDIA_LIBRARY_PATH, filename)
                if os.path.exists(image_path):
                    matches.append(image_path)
                break  # No need to check other labels for this file

    if matches:
        selected = random.choice(matches)
        logger.info(f"Selected media '{selected}' for topic '{topic_pillar}'")
        return selected

    logger.info(f"No matching media found for topic '{topic_pillar}'")
    return None
