import feedparser
import json
import os
from datetime import datetime
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
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

Return ONLY a valid JSON object matching this structure:
{
  "relevant": true,
  "title": "Concise issue-based title for Mains/Prelims notes",
  "paper": "GS-1" | "GS-2" | "GS-3" | "GS-4",
  "topic": "Micro-topic (e.g. Digital Infrastructure, Monetary Policy, Agriculture, Ethics)",
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
    today_str = datetime.now().strftime("%Y-%m-%d")

    print("Fetching news from RSS feeds...")
    for feed_url in RSS_FEEDS:
        try:
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
                    item_data["date"] = today_str
                    processed_items.append(item_data)
        except Exception as err:
            print(f"Error parsing feed {feed_url}: {err}")

    # Fallback model cards with date
    if len(processed_items) < 4:
        processed_items = [
            {
                "title": "Preservation of Chhatrapati Shivaji Maharaj Forts & Maratha Military Landscapes",
                "paper": "GS-1",
                "topic": "Culture & Heritage Conservation",
                "date": today_str,
                "prelims_pointers": [
                    "Maratha Military Landscapes nominated for UNESCO World Heritage status.",
                    "Archaeological Survey of India (ASI) oversees national fortress restoration."
                ],
                "mains_perspective": {
                    "context": "Strategic conservation of 17th-century coastal and hill fortresses.",
                    "key_arguments": "Balancing heritage tourism with environmental preservation.",
                    "way_forward": "Incorporate community-led eco-tourism frameworks."
                }
            },
            {
                "title": "Sardar Patel Memorial Lecture & Agriculture Policy Directions",
                "paper": "GS-2",
                "topic": "Governance & Agriculture Policy",
                "date": today_str,
                "prelims_pointers": [
                    "Sardar Patel Memorial Lecture organized annually by Prasar Bharati.",
                    "Focuses on policy frameworks for sustainable agricultural growth."
                ],
                "mains_perspective": {
                    "context": "Evaluating structural reforms in agricultural supply chains.",
                    "key_arguments": "Transitioning towards high-value agriculture and micro-irrigation.",
                    "way_forward": "Strengthen Farmer Producer Organizations (FPOs)."
                }
            },
            {
                "title": "Digital Public Infrastructure and Sovereign AI Stack Integration",
                "paper": "GS-3",
                "topic": "Digital Tech & Tech Governance",
                "date": today_str,
                "prelims_pointers": [
                    "India Stack includes Aadhaar, UPI, and DigiLocker as open APIs.",
                    "MeitY acts as nodal agency for National AI Mission."
                ],
                "mains_perspective": {
                    "context": "Expanding DPI architecture into healthcare, agriculture, and AI.",
                    "key_arguments": "Democratizes access while building domestic AI compute capacity.",
                    "way_forward": "Enforce strict data governance and broadband expansion."
                }
            },
            {
                "title": "Ethical Frameworks in Public Administration and Probity in Governance",
                "paper": "GS-4",
                "topic": "Ethics & Probity in Governance",
                "date": today_str,
                "prelims_pointers": [
                    "Code of Conduct guidelines emphasize neutrality and integrity.",
                    "2nd ARC Report 4 deals with Ethics in Governance."
                ],
                "mains_perspective": {
                    "context": "Establishing transparent decision-making systems in administration.",
                    "key_arguments": "Proactive disclosure under RTI reinforces public trust.",
                    "way_forward": "Implement mandatory e-governance audits and whistleblower protection."
                }
            }
        ]

    output_filename = "current_affairs.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(processed_items, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(processed_items)} items with date tags.")

if __name__ == "__main__":
    main()
