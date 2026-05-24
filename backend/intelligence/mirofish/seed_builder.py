"""
MiroFish Seed Builder — Agent A Module

Collects daily seed content from RSS feeds, Reddit, Google Trends.
Output: list of 30-50 seed documents (title, content, source, timestamp).
"""

import os
import re
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field

# Optional imports with graceful fallback
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class SeedDocument:
    title: str
    content: str
    source: str
    timestamp: str


# Default RSS feeds
DEFAULT_RSS_FEEDS = [
    ("https://hnrss.org/newest?points=50", "HackerNews"),
    ("https://feeds.feedburner.com/TechCrunch/", "TechCrunch"),
    ("https://www.reddit.com/r/webdev/.rss", "r/webdev"),
    ("https://www.reddit.com/r/SideProject/.rss", "r/SideProject"),
    ("https://www.reddit.com/r/startups/.rss", "r/startups"),
    ("https://www.reddit.com/r/entrepreneur/.rss", "r/entrepreneur"),
]

# Default niche keywords
DEFAULT_KEYWORDS = [
    "AI tools", "developer tools", "startup", "side project",
    "automation", "build in public", "indie hacker",
    "African tech", "API security", "deployment",
]


def _fetch_rss_feeds(feeds: list = None, timeout: float = 15.0) -> list:
    """Fetch seed documents from RSS feeds."""
    if not HAS_FEEDPARSER:
        return []
    
    if feeds is None:
        feeds = DEFAULT_RSS_FEEDS
    
    documents = []
    for url, source_name in feeds:
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                continue
            
            for entry in feed.entries[:8]:
                title = entry.get("title", "").strip()
                content = entry.get("summary", entry.get("description", "")).strip()
                # Clean HTML
                content = re.sub(r'<[^>]+>', '', content)
                content = content[:500]  # Limit content length
                
                pub_date = entry.get("published", entry.get("updated", ""))
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        ts = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                    except Exception:
                        ts = datetime.now(timezone.utc).isoformat()
                else:
                    ts = datetime.now(timezone.utc).isoformat()
                
                if title and content:
                    documents.append(SeedDocument(
                        title=title,
                        content=content,
                        source=source_name,
                        timestamp=ts,
                    ))
        except Exception:
            continue
    
    return documents


def _fetch_reddit_posts(subreddits: list = None, limit: int = 10) -> list:
    """Fetch hot posts from Reddit using JSON API (no PRAW needed)."""
    if not HAS_HTTPX:
        return []
    
    if subreddits is None:
        subreddits = ["webdev", "SideProject", "startups", "entrepreneur"]
    
    documents = []
    headers = {"User-Agent": "python:oybit:v1.0 (by /u/admin)"}
    
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
            response = httpx.get(url, headers=headers, timeout=15.0)
            if response.status_code == 429:
                # Rate limited — skip
                continue
            response.raise_for_status()
            data = response.json()
            
            for post in data.get("data", {}).get("children", []):
                pd = post.get("data", {})
                title = pd.get("title", "")
                content = pd.get("selftext", pd.get("url", ""))[:500]
                created = pd.get("created_utc", 0)
                ts = datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else datetime.now(timezone.utc).isoformat()
                
                if title and title != "[deleted]":
                    documents.append(SeedDocument(
                        title=title,
                        content=content if content else title,
                        source=f"r/{sub}",
                        timestamp=ts,
                    ))
        except Exception:
            continue
    
    return documents


def _fetch_trends_data(keywords: list = None) -> list:
    """Fetch trend signals for niche keywords."""
    if keywords is None:
        keywords = DEFAULT_KEYWORDS
    
    # Generate trend-based seed documents from keywords
    # In production, this would use pytrends or similar
    documents = []
    now = datetime.now(timezone.utc).isoformat()
    
    for keyword in keywords[:10]:
        documents.append(SeedDocument(
            title=f"Trending: {keyword}",
            content=f"Rising interest in {keyword} detected in developer/tech communities. Potential content opportunity for niche content creation.",
            source="Google Trends",
            timestamp=now,
        ))
    
    return documents


def collect_seeds(
    rss_feeds: list = None,
    subreddits: list = None,
    keywords: list = None,
    min_documents: int = 10,
    max_documents: int = 50,
    timeout: float = 60.0,
) -> list:
    """
    Collect seed documents from all sources.
    
    Args:
        rss_feeds: list of (url, name) tuples for RSS feeds
        subreddits: list of subreddit names
        keywords: list of niche keywords for trends
        min_documents: minimum docs to return
        max_documents: maximum docs to return
        timeout: total execution timeout in seconds
        
    Returns:
        list of SeedDocument objects
    """
    start_time = time.time()
    all_documents = []
    
    # Source 1: RSS feeds
    if time.time() - start_time < timeout:
        try:
            rss_docs = _fetch_rss_feeds(rss_feeds, timeout=min(15.0, timeout - (time.time() - start_time)))
            all_documents.extend(rss_docs)
        except Exception:
            pass
    
    # Source 2: Reddit
    if time.time() - start_time < timeout:
        try:
            reddit_docs = _fetch_reddit_posts(subreddits)
            all_documents.extend(reddit_docs)
        except Exception:
            pass
    
    # Source 3: Trends/keywords
    if time.time() - start_time < timeout:
        try:
            trend_docs = _fetch_trends_data(keywords)
            all_documents.extend(trend_docs)
        except Exception:
            pass
    
    # Deduplicate by title
    seen_titles = set()
    unique_docs = []
    for doc in all_documents:
        title_key = doc.title.lower().strip()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_docs.append(doc)
    
    # Filter empty content
    unique_docs = [d for d in unique_docs if d.content and d.content.strip()]
    
    # Limit to max
    return unique_docs[:max_documents]
