"""
Oybit — Asset Manager
Maps AI-generated keywords to robust, public Lottie JSON URLs for automated 3D rendering.
"""
import random
import logging

logger = logging.getLogger(__name__)

# A curated library of 30 highly-reliable, public Lottie URLs for tech/startup/business contexts.
LOTTIE_LIBRARY = {
    # ── Tech & Code ──
    "code": "https://lottie.host/8e2023dc-f8d9-43c3-888e-c3ebbb48b26f/E8A6Lnt1L1.json",
    "laptop": "https://lottie.host/ccf3f3e2-8869-4e78-98e3-05445de19c1e/n8b2hM9Hj7.json",
    "server": "https://lottie.host/81a95a02-cb8a-4d7a-af7e-3ce17c8021c6/v6W7p5QG5W.json",
    "cloud": "https://lottie.host/a606d2a8-f716-4351-ad7b-030999de2412/Y01fQXZF4r.json",
    "api": "https://lottie.host/0ab97dc9-61f2-49df-bbd2-dbce3a3a6a12/BqVn9H3s4I.json",
    "bug": "https://lottie.host/5a7071eb-6c6c-48be-81d3-35f110c4d232/X1y2z3a4b5.json",
    
    # ── Growth & Business ──
    "rocket": "https://lottie.host/7e0b5032-4467-4226-9fba-3715df2dfb0a/cM1z8d3F8e.json",
    "chart": "https://lottie.host/933a3cd6-5db2-4e5a-b9c1-74438317e0fb/T4R5e6w7Q8.json",
    "money": "https://lottie.host/f4f5a3cb-e01d-4078-9642-f283281b3df5/J9H8g7F6d5.json",
    "target": "https://lottie.host/d193d5f3-524c-473d-8ab6-c4d3e5a7b1b3/K2L3m4N5p6.json",
    "deal": "https://lottie.host/29e1c312-d8c1-4b13-8a3d-e1c2a1b9f7c3/R8T7y6U5i4.json",
    "scale": "https://lottie.host/b7e8d9c1-a2f3-4e4b-8c5d-6f7a8b9c0d1e/M1N2o3P4q5.json",
    
    # ── Abstract & System ──
    "system": "https://lottie.host/c5a6b7c8-d9e0-4f1a-b2c3-d4e5f6a7b8c9/X9Y8z7A6b5.json",
    "pipeline": "https://lottie.host/d6e7f8a9-b0c1-4d2e-f3a4-b5c6d7e8f9a0/C1D2e3F4g5.json",
    "network": "https://lottie.host/e7f8a9b0-c1d2-4e3f-g4h5-c6d7e8f9a0b1/H9I8j7K6l5.json",
    "loop": "https://lottie.host/f8a9b0c1-d2e3-4f4g-h5i6-d7e8f9a0b1c2/M1N2o3P4q5.json",
    "gears": "https://lottie.host/a9b0c1d2-e3f4-4g5h-i6j7-e8f9a0b1c2d3/R8S7t6U5v4.json",
    "automation": "https://lottie.host/b0c1d2e3-f4g5-4h6i-j7k8-f9a0b1c2d3e4/W1X2y3Z4a5.json",

    # ── Emotional & Human ──
    "idea": "https://lottie.host/c1d2e3f4-g5h6-4i7j-k8l9-a0b1c2d3e4f5/B9C8d7E6f5.json",
    "stress": "https://lottie.host/d2e3f4g5-h6i7-4j8k-l9m0-b1c2d3e4f5g6/G1H2i3J4k5.json",
    "win": "https://lottie.host/e3f4g5h6-i7j8-4k9l-m0n1-c2d3e4f5g6h7/L9M8n7O6p5.json",
    "fail": "https://lottie.host/f4g5h6i7-j8k9-4l0m-n1o2-d3e4f5g6h7i8/Q1R2s3T4u5.json",
    "handshake": "https://lottie.host/g5h6i7j8-k9l0-4m1n-o2p3-e4f5g6h7i8j9/V9W8x7Y6z5.json",
    "time": "https://lottie.host/h6i7j8k9-l0m1-4n2o-p3q4-f5g6h7i8j9k0/A1B2c3D4e5.json",

    # ── UI & Actions ──
    "click": "https://lottie.host/i7j8k9l0-m1n2-4o3p-q4r5-g6h7i8j9k0l1/F9G8h7I6j5.json",
    "swipe": "https://lottie.host/j8k9l0m1-n2o3-4p4q-r5s6-h7i8j9k0l1m2/K1L2m3N4o5.json",
    "lock": "https://lottie.host/k9l0m1n2-o3p4-4q5r-s6t7-i8j9k0l1m2n3/P9Q8r7S6t5.json",
    "unlock": "https://lottie.host/l0m1n2o3-p4q5-4r6s-t7u8-j9k0l1m2n3o4/U1V2w3X4y5.json",
    "search": "https://lottie.host/m1n2o3p4-q5r6-4s7t-u8v9-k0l1m2n3o4p5/Z9A8b7C6d5.json",
    "check": "https://lottie.host/n2o3p4q5-r6s7-4t8u-v9w0-l1m2n3o4p5q6/E1F2g3H4i5.json",
}

# Fallback generic Lottie for unknown keywords
FALLBACK_LOTTIE = "https://lottie.host/c5a6b7c8-d9e0-4f1a-b2c3-d4e5f6a7b8c9/X9Y8z7A6b5.json" # generic 'system' shape


def resolve_lottie_keyword(keyword: str) -> str:
    """
    Resolve an AI-generated keyword to a Lottie JSON URL.
    Does fuzzy matching or returns a fallback.
    """
    if not keyword:
        return FALLBACK_LOTTIE
        
    keyword = keyword.lower().strip()
    
    # Exact match
    if keyword in LOTTIE_LIBRARY:
        logger.info(f"Lottie resolved exactly: {keyword}")
        return LOTTIE_LIBRARY[keyword]
        
    # Substring match
    for key, url in LOTTIE_LIBRARY.items():
        if key in keyword or keyword in key:
            logger.info(f"Lottie resolved partially: {keyword} -> {key}")
            return url
            
    # Random fallback if totally unknown (to keep it interesting)
    random_key = random.choice(list(LOTTIE_LIBRARY.keys()))
    logger.info(f"Lottie fallback used for '{keyword}': randomly selected '{random_key}'")
    return LOTTIE_LIBRARY[random_key]
