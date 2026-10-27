const { GoogleGenAI } = require('@google/genai');
const fs = require('fs');

// Automatically initialized using process.env.GEMINI_API_KEY
const ai = new GoogleGenAI();

async function generateSubtopicArticles(paper, subtopic) {
  console.log(`Generating Wikipedia consolidation modules for ${paper} - ${subtopic}...`);
  
  const prompt = `Act as an elite UPSC civil services mentor and expert examiner. Generate a JSON array of 5 highly detailed, rigorous study articles for ${paper} under the subtopic "${subtopic}". 
  Each object in the JSON array must strictly follow this exact structure:
  {
    "title": "Comprehensive article title tailored for UPSC Mains",
    "paper": "${paper}",
    "topic": "${subtopic}",
    "static_linkage": "Specific constitutional article, statutory body, or core economic/ethical concept",
    "date": "2026-10",
    "image": "https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=800&auto=format&fit=crop&q=60",
    "prelims_pointers": [
      "Precise factual point 1 with constitutional/statutory backing",
      "Precise factual point 2 with committee/index reference"
    ],
    "mains_perspective": {
      "context": "Socio-economic or geo-political context of the issue",
      "key_arguments": "Multi-dimensional analysis covering arguments for and against",
      "way_forward": "Actionable administrative, structural, or policy recommendations"
    }
  }
  Return ONLY valid raw JSON with no markdown formatting blocks or extra text.`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });

    let text = response.text.trim();
    // Clean up markdown block ticks if present
    if (text.startsWith('```json')) text = text.replace(/^```json/, '').replace(/```$/, '').trim();
    
    return JSON.parse(text);
  } catch (err) {
    console.error(`Error generating data for ${subtopic}:`, err);
    return [];
  }
}

async function buildFullWiki() {
  const syllabus = [
    { paper: 'GS-1', subtopic: 'Art & Culture' },
    { paper: 'GS-1', subtopic: 'Indian Society' },
    { paper: 'GS-2', subtopic: 'Polity & Federalism' },
    { paper: 'GS-2', subtopic: 'International Relations' },
    { paper: 'GS-3', subtopic: 'Economy & Growth' },
    { paper: 'GS-3', subtopic: 'Science & Tech' },
    { paper: 'GS-3', subtopic: 'Internal Security' },
    { paper: 'GS-4', subtopic: 'Ethics & Governance' }
  ];

  let masterWiki = [];
  for (const item of syllabus) {
    const articles = await generateSubtopicArticles(item.paper, item.subtopic);
    masterWiki.push(...articles);
    // Brief pause to respect API rate limits
    await new Promise(res => setTimeout(res, 2000));
  }

  fs.writeFileSync('./public/repository.json', JSON.stringify(masterWiki, null, 2));
  console.log(`Successfully generated and saved ${masterWiki.length} Wikipedia consolidation articles to public/repository.json!`);
}

buildFullWiki();
