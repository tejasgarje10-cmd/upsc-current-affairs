import feedparser
import json
import os
import re
from datetime import datetime
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Comprehensive Multi-Domain UPSC Feed Registry
RSS_FEEDS = [
    # PIB & Government Updates
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1",
    
    # International Relations & Geopolitics
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://indianexpress.com/section/world/feed/",
    
    # National Polity & Governance
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://indianexpress.com/section/india/feed/",
    
    # Economy & Business
    "https://www.thehindu.com/business/Economy/feeder/default.rss",
    "https://indianexpress.com/section/business/feed/",
    
    # Science, Environment & Security
    "https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss",
    "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
    "https://indianexpress.com/section/lifestyle/science/feed/"
]

SYSTEM_PROMPT = """
You are a senior UPSC Civil Services Examination (CSE) syllabus architect and evaluator.
Analyze the following news item and generate a high-yield current affairs module.

Evaluate relevance for GS-1, GS-2, GS-3, or GS-4 across:
- Geopolitics, Bilateral Relations, Multilateral Bodies (UN, G20, BRICS, SCO, ASEAN)
- Constitutional Provisions, Bills, SC Judgments, Electoral Reforms, Governance
- Macroeconomics, RBI Policies, Trade Agreements, Infrastructure, DPI
- Environment, Climate Change, Biodiversity, Renewable Energy, Pollution
- Science & Technology, Space (ISRO), Defense Exercises, Cybersecurity
- Indian Society, Social Justice, Schemes, Heritage, Tribal Welfare, Ethics

Return ONLY a valid JSON object:
{
  "relevant": true,
  "title": "Clear, concept-driven title suitable for Mains/Prelims notes",
  "paper": "GS-1" | "GS-2" | "GS-3" | "GS-4",
  "topic": "Micro-topic (e.g. Indo-Pacific Security, Monetary Policy, Biodiversity, Public Probity)",
  "prelims_pointers": [
    "Key factual point (statutory/constitutional provision, nodal agency, report, treaty)",
    "Core objective, index, or scientific/economic principle involved"
  ],
  "mains_perspective": {
    "context": "1-2 sentence core analytical summary",
    "key_arguments": "Structural challenges, critical policy benefits, or geopolitical impact",
    "way_forward": "Actionable policy solutions, committee/ARC/international best practices"
  }
}

If the news is purely local crime, sports, celebrity gossip, or routine local politics, return strictly:
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
    """Extract thumbnail/image URL from RSS media extensions or HTML description."""
    # 1. Check media_content or media_thumbnail
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if media.get('medium') == 'image' or media.get('type', '').startswith('image/'):
                return media.get('url')
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url')
    
    # 2. Extract <img> src from summary HTML using regex
    summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if img_match:
        return img_match.group(1)
        
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

    print("Fetching comprehensive UPSC news from RSS feeds...")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Parsing {feed_url}: {len(feed.entries)} items found.")
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
                    item_data["image"] = image_url or "[https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60)"
                    processed_items.append(item_data)
        except Exception as err:
            print(f"Error parsing feed {feed_url}: {err}")

    # Fallback multi-domain payload covering GS-1, GS-2, GS-3, GS-4 if feeds are dry
    if len(processed_items) < 6:
        print("Injecting comprehensive multi-paper fallback suite...")
        processed_items = [
            {
                "title": "Geopolitics of the West Asian Corridor & India's Strategic Interests",
                "paper": "GS-2",
                "topic": "International Relations & Geopolitics",
                "date": today_str,
                "image": "[https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60)",
                "prelims_pointers": [
                    "India-Middle East-Europe Economic Corridor (IMEC) aims to enhance trade connectivity across Eurasia.",
                    "Chabahar Port provides strategic sea-land access to Central Asian markets bypassing regional bottlenecks."
                ],
                "mains_perspective": {
                    "context": "Navigating complex multilateral alignments amidst regional conflicts in West Asia.",
                    "key_arguments": "Securing energy supply chains, safeguarding Indian diaspora interests, and balancing multi-alignment strategies.",
                    "way_forward": "Strengthen bilateral security frameworks and operationalize regional maritime safety initiatives."
                }
            },
            {
                "title": "UNCLOS & Maritime Security Architecture in the Indo-Pacific",
                "paper": "GS-2",
                "topic": "Bilateral & Global Groupings",
                "date": today_str,
                "image": "[https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&auto=format&fit=crop&q=60)",
                "prelims_pointers": [
                    "UNCLOS defines Exclusive Economic Zones (EEZ) extending up to 200 nautical miles from baseline.",
                    "SAGAR (Security and Growth for All in the Region) represents India's maritime doctrine."
                ],
                "mains_perspective": {
                    "context": "Ensuring freedom of navigation and rules-based international maritime order.",
                    "key_arguments": "Addressing non-traditional security threats including illegal fishing, piracy, and sea lane disruptions.",
                    "way_forward": "Deepen Quad maritime domain awareness and enhance joint naval patrol protocols."
                }
            },
            {
                "title": "Preservation of Coastal Fortresses & Maratha Heritage Architecture",
                "paper": "GS-1",
                "topic": "Indian Art, Culture & Heritage",
                "date": today_str,
                "image": "[https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=800&auto=format&fit=crop&q=60)",
                "prelims_pointers": [
                    "Maratha Military Landscapes were nominated for UNESCO World Heritage site recognition.",
                    "Archaeological Survey of India (ASI) acts as statutory custodian under AMASR Act 1958."
                ],
                "mains_perspective": {
                    "context": "Strategic conservation of 17th-century coastal, sea, and hill fort structures across Maharashtra.",
                    "key_arguments": "Promoting sustainable eco-tourism while preventing structural degradation from coastal weathering.",
                    "way_forward": "Adopt scientific stone preservation methods and community-led heritage management."
                }
            },
            {
                "title": "Digital Public Infrastructure & Sovereign AI Compute Stack",
                "paper": "GS-3",
                "topic": "Digital Tech & Tech Governance",
                "date": today_str,
                "image": "[https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=60)",
                "prelims_pointers": [
                    "India Stack includes open API layers like UPI, Aadhaar, and DigiLocker.",
                    "MeitY leads the IndiaAI Mission to build GPU-compute infrastructure for domestic AI models."
                ],
                "mains_perspective": {
                    "context": "Scaling DPI beyond financial technologies into healthcare diagnostics and precision agriculture.",
                    "key_arguments": "Reduces dependency on global tech monopolies while securing national data sovereignty.",
                    "way_forward": "Establish robust data privacy audits and expand high-speed optical fiber into rural panchayats."
                }
            },
            {
                "title": "Climate Resilience in Agriculture & Micro-Irrigation Adoption",
                "paper": "GS-3",
                "topic": "Agriculture & Biodiversity",
                "date": today_str,
                "image": "[https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&auto=format&fit=crop&q=60)",
                "prelims_pointers": [
                    "Per Drop More Crop (PDMC) scheme focuses on drip and sprinkler irrigation efficiency.",
                    "National Mission for Sustainable Agriculture (NMSA) promotes climate-resilient farming techniques."
                ],
                "mains_perspective": {
                    "context": "Mitigating climate risks, soil degradation, and groundwater depletion in rainfed farming zones.",
                    "key_arguments": "Enhancing crop diversification, promoting millets (Shree Anna), and scaling carbon-sequestration in soil.",
                    "way_forward": "Empower Farmer Producer Organizations (FPOs) with solar pump technology and micro-credit."
                }
            },
            {
                "title": "Ethical Governance, Probity & Whistleblower Protection in Administration",
                "paper": "GS-4",
                "topic": "Public Service Ethics & Probity",
                "date": today_str,
                "image": "[https://images.unsplash.com/photo-1450133064473-71024230f91b?w=800&auto=format&fit=crop&q=60](https://images.unsplash.com/photo-1450133064473-71024230f91b?w=800&auto=format&fit=crop&q=60)",
                "prelims_pointers": [
                    "Central Vigilance Commission (CVC) functions as an independent statutory vigilance body.",
                    "2nd Administrative Reforms Commission (ARC) Report 4 focuses specifically on Ethics in Governance."
                ],
                "mains_perspective": {
                    "context": "Reinforcing institutional accountability, integrity, and transparency in public service delivery.",
                    "key_arguments": "Preventing administrative discretionary abuse and protecting honest civil service officers.",
                    "way_forward": "Implement mandatory e-procurement portals, proactive RTI disclosures, and value-based civil services training."
                }
            }
        ]

    # Combine existing items with fresh items for historical archiving
    output_filename = "current_affairs.json"
    existing_items = []
    if os.path.exists(output_filename):
        try:
            with open(output_filename, "r", encoding="utf-8") as f:
                existing_items = json.load(f)
        except Exception:
            existing_items = []

    combined_items = processed_items + existing_items
    
    # Deduplicate by title
    unique_items = []
    final_titles = set()
    for item in combined_items:
        t = item.get("title", "").lower()
        if t not in final_titles:
            final_titles.add(t)
            unique_items.append(item)

    # Retain top 60 items for historical archives
    unique_items = unique_items[:60]

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(unique_items, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved {len(unique_items)} items to {output_filename}.")

if __name__ == "__main__":
    main()
