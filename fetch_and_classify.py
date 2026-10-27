import feedparser
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

RSS_FEEDS = [
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://www.thehindu.com/business/Economy/feeder/default.rss",
    "https://indianexpress.com/section/india/feed/",
    "https://indianexpress.com/section/world/feed/",
    "https://indianexpress.com/section/business/feed/",
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"
]

SYSTEM_PROMPT = """
You are an expert UPSC Civil Services Examination (CSE) mentor.
Analyze the following news item and generate a structured current affairs analysis suitable for UPSC GS-1, GS-2, GS-3, or GS-4.

Classify national news, governance, international relations, geopolitics, economy, environment, science, or public policy as relevant (relevant: true).

Return ONLY a valid JSON object:
{
  "relevant": true,
  "title": "Concise issue-based title for Mains/Prelims notes",
  "paper": "GS-1" | "GS-2" | "GS-3" | "GS-4",
  "topic": "Micro-topic (e.g. Geopolitics, Digital Infrastructure, Monetary Policy, Agriculture, Ethics)",
  "image_keyword": "2-3 English search words for relevant news image (e.g., 'red sea ship', 'parliament india', 'isro rocket', 'indian rupee', 'solar panel')",
  "prelims_pointers": [
    "Key factual point (statutory/constitutional provision, nodal ministry, report)",
    "Core objective or scientific/economic principle involved"
  ],
  "mains_perspective": {
    "context": "1-2 sentence core summary of the issue",
    "key_arguments": "Analytical takeaways or socio-economic impacts",
    "way_forward": "Actionable solutions or policy recommendations"
  }
}

If the news is purely local crime, routine political commentary, or sports, return strictly:
{"relevant": false}
"""

def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def extract_image_url(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if media.get('medium') == 'image' or media.get('type', '').startswith('image/'):
                return media.get('url')
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url')
    
    summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if img_match:
        return img_match.group(1)
    return None

def fetch_wikimedia_image(query: str):
    """Fetch relevant news thumbnail dynamically from Wikimedia Commons OSINT database."""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"[https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=](https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=){encoded_query}&gsrnamespace=6&prop=imageinfo&iiprop=url&iiurlwidth=600&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'UPSC-CurrentAffairs-Bot/1.0 (contact@upsc-portal.com)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                imageinfo = page_data.get('imageinfo', [])
                if imageinfo and 'thumburl' in imageinfo[0]:
                    return imageinfo[0]['thumburl']
    except Exception as e:
        print(f"Wikimedia API query failed for '{query}': {e}")
    return None

def process_feed_item(title: str, summary: str):
    if not client:
        return None
    prompt = f"News Title: {title}\nContent: {summary}"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )
        cleaned_text = clean_json_text(response.text)
        data = json.loads(cleaned_text)
        return data if data.get("relevant") else None
    except Exception as e:
        print(f"Error processing item '{title}': {e}")
        return None

def main():
    processed_items = []
    seen_titles = set()
    today_str = datetime.now().strftime("%Y-%m-%d")

    print("Fetching news from RSS feeds...")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                title = getattr(entry, 'title', '').strip()
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                summary = getattr(entry, 'summary', getattr(entry, 'description', title))
                image_url = extract_image_url(entry)
                item_data = process_feed_item(title, summary)

                if item_data and item_data.get("title"):
                    item_data.pop("relevant", None)
                    item_data["date"] = today_str
                    
                    # Search dynamic OSINT image if RSS didn't include one
                    kw = item_data.pop("image_keyword", item_data.get("topic", "india"))
                    if not image_url:
                        image_url = fetch_wikimedia_image(kw)

                    item_data["image"] = image_url or "[https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60)"
                    processed_items.append(item_data)
        except Exception as err:
            print(f"Error parsing feed {feed_url}: {err}")

    output_filename = "current_affairs.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(processed_items, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(processed_items)} items with dynamic OSINT images.")

if __name__ == "__main__":
    main()
