"""
Oybit — Trend Aggregator
Collects Google Trends + Reddit hot posts + RSS signals.
Lightweight trend collection — deep intelligence is Agent A's MiroFish.
"""
import os
import logging
from datetime import datetime

from backend.db.models import TrendSignal, get_session

logger = logging.getLogger(__name__)


def collect_rss_trends(keywords: list[str] = None) -> list[dict]:
    """Collect trends from RSS feeds."""
    import feedparser
    import requests
    from bs4 import BeautifulSoup
    
    def get_og_image(url):
        try:
            resp = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                meta = soup.find('meta', property='og:image')
                if meta and meta.get('content'):
                    return meta.get('content')
        except Exception:
            pass
        return ""

    feeds = [
        "https://techcrunch.com/feed/",
        "https://news.ycombinator.com/rss",
    ]

    signals = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:  # Process all entries
                link = entry.get("link", "")
                hero_image = get_og_image(link) if link else ""
                
                signals.append({
                    "source": "rss",
                    "topic": entry.get("title", ""),
                    "score": 1.0,
                    "raw_data": {
                        "url": link,
                        "summary": entry.get("summary", "")[:500],
                        "published": entry.get("published", ""),
                        "feed": feed_url,
                        "hero_image": hero_image
                    }
                })
        except Exception as e:
            logger.warning(f"Failed to parse RSS feed {feed_url}: {e}")
            continue

    return signals


def collect_google_trends(keywords: list[str] = None) -> list[dict]:
    """Collect signals from Google Trends."""
    if not keywords:
        keywords = ["AI tools", "startup", "developer", "SaaS", "indie hacker"]

    signals = []
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        for kw_batch in [keywords[i:i+5] for i in range(0, len(keywords), 5)]:
            try:
                pytrends.build_payload(kw_batch, timeframe="now 1-d")
                data = pytrends.interest_over_time()
                if not data.empty:
                    for kw in kw_batch:
                        if kw in data.columns:
                            score = float(data[kw].iloc[-1]) / 100.0
                            signals.append({
                                "source": "google_trends",
                                "topic": kw,
                                "score": score,
                                "raw_data": {"keyword": kw, "current_interest": score}
                            })
            except Exception as e:
                logger.warning(f"Google Trends error for {kw_batch}: {e}")
                continue
    except ImportError:
        logger.warning("pytrends not installed — skipping Google Trends")

    return signals


def save_signals(signals: list[dict], engine=None):
    """Save trend signals to database."""
    session = get_session(engine)
    try:
        for signal in signals:
            record = TrendSignal(
                source=signal.get("source", "unknown"),
                topic=signal.get("topic", ""),
                score=signal.get("score", 0.0),
                raw_data=signal.get("raw_data", {}),
                collected_at=datetime.utcnow()
            )
            session.add(record)
        session.commit()
        logger.info(f"Saved {len(signals)} trend signals")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_trend_collection(keywords: list[str] = None, engine=None) -> list[dict]:
    """Run full trend collection pipeline."""
    all_signals = []

    # RSS
    rss_signals = collect_rss_trends(keywords)
    all_signals.extend(rss_signals)
    logger.info(f"Collected {len(rss_signals)} RSS signals")

    # Google Trends
    gt_signals = collect_google_trends(keywords)
    all_signals.extend(gt_signals)
    logger.info(f"Collected {len(gt_signals)} Google Trends signals")

    # Save
    save_signals(all_signals, engine)

    return all_signals
