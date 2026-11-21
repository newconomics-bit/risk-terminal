"""
Modul fetcher untuk berita geopolitik.
Membaca RSS feed dari sumber publik dan memfilter berdasarkan keyword
dari config/settings.yaml.
Setiap event memiliki risk_weight tertinggi dari keyword yang cocok.
"""

import logging
import os
from datetime import datetime, timezone, timedelta

import feedparser
import yaml

from src.utils.io import load_json

logger = logging.getLogger(__name__)

# Zona waktu Indonesia (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))

# Sumber RSS yang digunakan (public, legal, stabil)
RSS_FEEDS = [
    {
        "name": "BBC News",
        "url": "http://feeds.bbci.co.uk/news/rss.xml",
    },
    {
        "name": "Reuters",
        "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    },
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
    },
    {
        "name": "AP News",
        "url": "https://rsshub.app/apnews/topics/business",
    },
]


def _load_config():
    """
    Memuat konfigurasi dari config/settings.yaml.
    """
    config_path = "config/settings.yaml"
    if not os.path.exists(config_path):
        # Fallback jika konfigurasi belum dibuat
        logger.warning("File konfigurasi %s tidak ditemukan.", config_path)
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_keyword_weights():
    """
    Mengambil keyword dan risk weight dari konfigurasi.
    """
    config = _load_config()
    geopolitics = config.get("geopolitics", {})
    keywords = geopolitics.get("keywords", [])

    # Default weights sesuai PRD FR-04
    default_weights = {
        "red sea": 30,
        "suez": 25,
        "malacca": 25,
        "south china sea": 30,
        "tariff": 20,
        "sanction": 25,
        "export control": 25,
        "brics": 10,
        "de-dollarization": 10,
        "supply chain": 20,
    }

    # Gunakan default weights; bisa ditimpa oleh konfigurasi jika ada.
    weights = {}
    for keyword in keywords:
        weights[keyword] = default_weights.get(keyword, 10)

    return weights


def _match_keywords(text, keywords):
    """
    Mencocokkan keyword dalam teks (case-insensitive).
    Mengembalikan list keyword yang cocok.
    """
    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    return matched


def _fetch_feed(feed_url, feed_name):
    """
    Membaca satu RSS feed dan mengembalikan list event.
    """
    events = []
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            logger.warning(
                "Feed %s (%s) memiliki masalah parsing.", feed_name, feed_url
            )

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")

            # Parse waktu publikasi
            published = entry.get("published", "")
            published_at = None
            if published:
                try:
                    # feedparser menyediakan parsed time
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        published_at = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        published_at = published
                except Exception:
                    published_at = published

            # Gabungkan title dan summary untuk matching keyword
            summary = entry.get("summary", "")
            body_text = f"{title} {summary}"

            events.append({
                "title": title,
                "link": link,
                "source": feed_name,
                "published_at": published_at,
                "body_text": body_text,
            })

    except Exception as e:
        logger.warning(
            "Gagal fetch RSS feed %s (%s): %s", feed_name, feed_url, e
        )

    return events


def fetch_news():
    """
    Mengambil berita dari RSS feed dan memfilter berdasarkan keyword geopolitik.
    Mengembalikan dictionary dengan events, keyword_counts, dan top_tags.
    """
    keywords = _get_keyword_weights()
    keyword_list = list(keywords.keys())

    all_events = []
    for feed in RSS_FEEDS:
        events = _fetch_feed(feed["url"], feed["name"])
        all_events.extend(events)

    # Filter dan hitung risk weight
    filtered_events = []
    keyword_counts = {}
    tag_risk_scores = []

    for event in all_events:
        matched = _match_keywords(event["body_text"], keyword_list)
        if not matched:
            continue

        # Ambil risk weight tertinggi dari keyword yang cocok
        max_weight = max(keywords[k] for k in matched)

        # Buat tags sederhana dari matched keywords
        tags = [k.replace(" ", "_") for k in matched]

        filtered_events.append({
            "title": event["title"],
            "link": event["link"],
            "source": event["source"],
            "published_at": event["published_at"],
            "tags": tags,
            "risk_weight": max_weight,
            "matched_keywords": matched,
        })

        # Hitung keyword counts
        for k in matched:
            keyword_counts[k] = keyword_counts.get(k, 0) + 1

        # Kumpulkan untuk top tags
        tag_risk_scores.extend([(t, max_weight) for t in tags])

    # Top tags: urutkan berdasarkan frekuensi, kemudian risk weight
    tag_freq = {}
    for tag, weight in tag_risk_scores:
        tag_freq[tag] = tag_freq.get(tag, 0) + weight

    top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)
    top_tags = [tag for tag, _ in top_tags[:10]]

    result = {
        "events": filtered_events,
        "keyword_counts": keyword_counts,
        "top_tags": top_tags,
    }

    logger.info(
        "Berita geopolitik: %d event terfilter dari %d total.",
        len(filtered_events),
        len(all_events),
    )

    return result