import feedparser
import json
import os
from google import genai

# Configure Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is missing.")

client = genai.Client(api_key=api_key)

RSS_FEEDS = [
    "https://pib.gov.in/rss/RssMain.aspx?ModId=6",                  # PIB Press Releases
    "https://www.thehindu.com/news/national/feeder/default.rss",    # The Hindu National
    "https://indianexpress.com/section/india/feed/"                 # Indian Express
]

SYSTEM_PROMPT = """
You are an expert UPSC Civil Services Examination (CSE) strategist and evaluator.
Analyze the following news item for its relevance to the UPSC CSE General Studies (GS-1, GS-2, GS-3, GS-4) and optional syllabi.

If the news item is NOT relevant to UPSC preparation (e.g., routine political commentary, sports updates, crime news), return strictly:
{"relevant": false}

If it IS relevant, return ONLY a valid JSON object matching this exact structure:
{
  "relevant": true,
  "title": "Concise issue-based title suitable for Mains/Prelims notes",
  "paper": "GS-1" | "GS-2" | "GS-3" | "GS-4",
  "topic": "Specific micro-topic (e.g., Digital Public Infrastructure, FLFPR, Land Reforms, Purva Mimamsa, Monetary Policy, Biodiversity)",
  "prelims_pointers": [
    "Key factual point (e.g., statutory/constitutional provision, nodal agency, report name)",
    "Core objective, index, or scientific principle involved"
  ],
  "mains_perspective": {
    "context": "1-2 sentence core summary of the underlying issue",
    "key_arguments": "Analytical takeaways, structural bottlenecks, or socio-economic impacts",
    "way_forward": "Actionable solutions, ARC/Committee recommendations, or policy measures"
  }
}
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
    prompt = f"{SYSTEM_PROMPT}\n\nNews Title: {title}\nSummary/Content: {summary}"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
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
        for entry in feed.entries[:8]:
            title = getattr(entry, 'title', '').strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
            item_data = process_feed_item(title, summary)

            if item_data:
                item_data.pop("relevant", None)
                processed_items.append(item_data)

    output_filename = "current_affairs.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(processed_items, f, indent=2, ensure_ascii=False)

    print(f"Done! Successfully generated {len(processed_items)} items.")

if __name__ == "__main__":
    main()
