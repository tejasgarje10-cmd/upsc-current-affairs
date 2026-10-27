import feedparser
import json
import os
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is missing.")

client = genai.Client(api_key=api_key)

RSS_FEEDS = [
    "https://pib.gov.in/rss/RssMain.aspx?ModId=6",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://indianexpress.com/section/india/feed/",
    "https://indianexpress.com/section/business/feed/"
]

SYSTEM_PROMPT = """
You are an expert UPSC Civil Services Examination (CSE) mentor.
Analyze the following news item and generate a structured current affairs analysis suitable for UPSC GS-1, GS-2, GS-3, or GS-4.

Always classify national news, governance, international relations, economy, environment, science, or public policy as relevant (relevant: true).

Return ONLY a valid JSON object matching this structure:
{
  "relevant": true,
  "title": "Concise issue-based title for Mains/Prelims notes",
  "paper": "GS-1" | "GS-2" | "GS-3" | "GS-4",
  "topic": "Micro-topic (e.g. Digital Infrastructure, Monetary Policy, Agriculture, International Relations)",
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

def process_feed_item(title: str, summary: str):
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

    print("Fetching news from RSS feeds...")
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            title = getattr(entry, 'title', '').strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            summary = getattr(entry, 'summary', getattr(entry, 'description', title))
            item_data = process_feed_item(title, summary)

            if item_data and item_data.get("title"):
                item_data.pop("relevant", None)
                processed_items.append(item_data)

    print(f"Total processed items: {len(processed_items)}")

    output_filename = "current_affairs.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(processed_items, f, indent=2, ensure_ascii=False)

    print("Successfully written to current_affairs.json")

if __name__ == "__main__":
    main()
