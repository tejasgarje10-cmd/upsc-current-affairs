import feedparser
import json
import os
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY missing.")

client = genai.Client(api_key=api_key) if api_key else None

RSS_FEEDS = [
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1",
    "https://indianexpress.com/section/india/feed/",
    "https://indianexpress.com/section/business/feed/",
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"
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
  "topic": "Micro-topic (e.g. Digital Infrastructure, Monetary Policy, Agriculture, Polity)",
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

    print("Fetching news from RSS feeds...")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Feed {feed_url} fetched {len(feed.entries)} entries.")
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
        except Exception as err:
            print(f"Error parsing feed {feed_url}: {err}")

    # Fallback sample data to guarantee non-empty JSON if RSS feeds or API fails
    if len(processed_items) == 0:
        print("No items generated from API. Injecting initial syllabus-aligned model cards...")
        processed_items = [
            {
                "title": "Digital Public Infrastructure and Sovereign AI Stack",
                "paper": "GS-3",
                "topic": "Digital Infrastructure & Tech Governance",
                "prelims_pointers": [
                    "India Stack includes Aadhaar, UPI, and DigiLocker as foundational open API layers.",
                    "Ministry of Electronics and IT (MeitY) serves as the nodal agency for National AI Mission implementation."
                ],
                "mains_perspective": {
                    "context": "Expanding DPI architecture beyond financial technology into healthcare, agriculture, and AI capabilities.",
                    "key_arguments": "Democratizes access to digital services while promoting domestic innovation and reducing dependence on proprietary global stacks.",
                    "way_forward": "Implement robust data protection frameworks and expand broadband connectivity across Tier-2 and rural sectors."
                }
            },
            {
                "title": "Sardar Patel Memorial Lecture & Agriculture Policy Directions",
                "paper": "GS-2",
                "topic": "Governance & Agriculture Policy",
                "prelims_pointers": [
                    "Sardar Patel Memorial Lecture is organized annually by All India Radio (Prasar Bharati).",
                    "Focuses on policy frameworks for sustainable agricultural growth and farmer welfare."
                ],
                "mains_perspective": {
                    "context": "Evaluating structural changes required in agricultural supply chains and price stabilization mechanisms.",
                    "key_arguments": "Need to transition towards high-value agriculture, micro-irrigation, and climate-resilient seed technologies.",
                    "way_forward": "Strengthen Farmer Producer Organizations (FPOs) and scale up modern storage infrastructure."
                }
            }
        ]

    print(f"Total processed items: {len(processed_items)}")

    output_filename = "current_affairs.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(processed_items, f, indent=2, ensure_ascii=False)

    print("Successfully written to current_affairs.json")

if __name__ == "__main__":
    main()
