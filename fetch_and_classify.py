import feedparser
import json
import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is missing.")

client = genai.Client(api_key=api_key)

# Working RSS feeds for UPSC-relevant news
RSS_FEEDS = [
    "https://pib.gov.in/rss/RssMain.aspx?ModId=6",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://indianexpress.com/section/india/feed/"
]

SYSTEM_PROMPT = """
You are an expert UPSC Civil Services Examination (CSE) strategist.
Evaluate if this news item is relevant to UPSC General Studies (GS-1, GS-2, GS-3, GS-4) or key optional subjects (e.g. Economics, Polity, Philosophy, Agriculture).

If relevant, return ONLY a raw JSON object matching this schema:
{
  "relevant": true,
  "title": "Concise issue-based title for Mains/Prelims notes",
  "paper": "GS-1" | "GS-2" | "GS-3" | "GS-4",
  "topic": "Micro-topic (e.g., Digital Public Infrastructure, Monetary Policy, Agriculture, Polity)",
  "prelims_pointers": [
    "Key factual point (statutory/constitutional provision, nodal agency, report)",
    "Core objective, index, or principle involved"
  ],
  "mains_perspective": {
    "context": "1-2 sentence core summary of the underlying issue",
    "key_arguments": "Analytical takeaways or policy implications",
    "way_forward": "Actionable solutions or committee recommendations"
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
        for entry in feed.entries[:15]:
            title = getattr(entry, 'title', '').strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            # Extract content from multiple fallback fields
            summary = ""
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description
            elif hasattr(entry, 'content'):
                summary = entry.content[0].value
            
            if not summary:
                summary = title

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
