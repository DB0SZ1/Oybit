import os

bots = [
    "facebook_page",
    "facebook_personal",
    "instagram_brand",
    "instagram_personal",
    "linkedin",
    "reddit",
    "telegram"
]

endpoints_to_add = """
@app.get("/api/analytics/overview")
def analytics_overview():
    return {"overview": {"total_posts": 0, "avg_engagement": 0, "accounts": {}}}

@app.get("/api/pipeline/posts")
def pipeline_posts(limit: int = 5):
    return {"posts": []}

@app.get("/api/scheduler")
def scheduler():
    return {"calendar": []}

@app.get("/api/replies")
def replies():
    return {"count": 0}

@app.get("/api/settings/workers")
def settings_workers():
    return {"workers": []}
"""

def patch():
    for bot in bots:
        filepath = os.path.join(bot, "main.py")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "analytics_overview" not in content:
                content = content.replace("def start_worker():", endpoints_to_add + "\ndef start_worker():")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                    
    print("Endpoints added.")

if __name__ == "__main__":
    patch()
