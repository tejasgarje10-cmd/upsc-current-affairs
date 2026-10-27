import feedparser
import json
import os
from datetime import datetime
from google import genai
from google.genai import types

# 1. Initialize Gemini API Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing GEMINI_API_KEY environment variable.")

client = genai.Client(api_key=api_key)

# 2. Production RSS Feed Registry
RSS_FEEDS = [
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1",          # PIB Releases
    "https://www.thehindu.com/news/national/feeder/default.rss",        # The Hindu National
    "https://www.thehindu.com/business/Economy/feeder/default.rss",    # The Hindu Economy
    "https://indianexpress.com/section/india/feed/",                   # Indian Express National
    "https://indianexpress.com/section/business/feed/"                 # Indian Express Economy
]

SYSTEM_PROMPT = """
You are a senior UPSC Civil Services Examination (CSE) evaluator and mentor.
Analyze the provided news item and determine its strategic value for General Studies (GS-1, GS-2, GS-3, GS-4) or key optionals (e.g., Economics, Public Administration, Agriculture, Philosophy).

Filtering Rule:
- Ignore routine political speeches, crime, local mishaps, entertainment, or sports.
- Retain structural policy updates, statutory decisions, economic indicators, supreme court judgments, environmental initiatives, and diplomatic developments.

If the news is RELEVANT, return strictly a JSON object:
{
  "relevant": true,
  "title": "Clear, concept-driven title suitable for UPSC answer-writing",
  "paper": "GS-1" | "GS-2" | "GS-3" | "GS-4",
  "topic": "Specific syllabus tag (e.g. Constitutional Bodies, Digital Economy, Biodiversity, Public Ethics)",
  "prelims_pointers": [
    "Statutory/constitutional basis, nodal ministry, or report name",
    "Core objective, data point, or scientific principle involved"
  ],
  "mains_perspective": {
    "context": "1-2 sentence core analytical takeaway",
    "key_arguments": "Structural challenges, critical policy benefits, or socio-economic impacts",
    "way_forward": "Actionable policy solutions, committee/ARC recommendations"
  }
}

If NOT relevant, return strictly:
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

def process_feed_item(title: str, summary: str):
    prompt = f"News Title: {title}\nSummary/Content: {summary}"
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
        print(f"Skipping '{title}' due to error: {e}")
        return None

def main():
    processed_items = []
    seen_titles = set()

    print("Executing full-fledged RSS feed processing...")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Parsing feed: {feed_url} ({len(feed.entries)} entries found)")
            for entry in feed.entries[:12]:
                title = getattr(entry, 'title', '').strip()
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                summary = getattr(entry, 'summary', getattr(entry, 'description', title))
                item_data = process_feed_item(title, summary)

                if item_data and item_data.get("title"):
                    item_data.pop("relevant", None)
                    item_data["date"] = datetime.now().strftime("%Y-%m-%d")
                    processed_items.append(item_data)
        except Exception as err:
            print(f"Feed error ({feed_url}): {err}")

    output_filename = "current_affairs.json"
    
    # Merge new items into existing history (prevents overwriting past days)
    existing_items = []
    if os.path.exists(output_filename):
        try:
            with open(output_filename, "r", encoding="utf-8") as f:
                existing_items = json.load(f)
        except Exception:
            existing_items = []

    combined_items = processed_items + existing_items
    
    # Deduplicate combined list by title
    unique_items = []
    final_titles = set()
    for item in combined_items:
        t = item.get("title", "").lower()
        if t not in final_titles:
            final_titles.add(t)
            unique_items.append(item)

    # Keep latest 50 entries
    unique_items = unique_items[:50]

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(unique_items, f, indent=2, ensure_ascii=False)

    print(f"Success! Updated {output_filename} with {len(unique_items)} total items.")

if __name__ == "__main__":
    main()
