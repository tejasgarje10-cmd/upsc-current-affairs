import { GoogleGenAI } from '@google/genai';

const ai = new GoogleGenAI();

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { action, question, paper, markerType, imageBase64, mimeType, searchTerm } = req.body;

    // Handle Dynamic Wiki Article Generation
    if (action === 'generateWikiArticle') {
      if (!searchTerm) {
        return res.status(400).json({ error: 'Search term is required' });
      }

      const prompt = `Act as an elite UPSC civil services expert and master curriculum author. A student searched for the topic "${searchTerm}" in the NexusGS Wikipedia repository. 
      Generate a comprehensive, publication-grade study article for this exact topic tailored for UPSC Civil Services.
      
      Return ONLY valid raw JSON matching this exact structure, with no markdown code blocks or extra text:
      {
        "title": "A precise, professional title for ${searchTerm}",
        "paper": "GS-3",
        "topic": "Economy & Growth",
        "static_linkage": "Core constitutional article, statutory body, or theoretical framework",
        "date": "2026-10",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=60",
        "prelims_pointers": [
          "Key factual statement 1 with constitutional or institutional backing",
          "Key factual statement 2 with historical or committee precedent"
        ],
        "mains_perspective": {
          "context": "Socio-economic, geopolitical, or administrative context of ${searchTerm}",
          "key_arguments": "Multi-dimensional analysis exploring core arguments, challenges, and stakeholder impacts",
          "way_forward": "Actionable policy measures, administrative reforms, or committee recommendations"
        }
      }`;

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: prompt,
      });

      let text = response.text.trim();
      if (text.startsWith('```json')) {
        text = text.replace(/^```json/, '').replace(/```$/, '').trim();
      } else if (text.startsWith('```')) {
        text = text.replace(/^```/, '').replace(/```$/, '').trim();
      }

      const articleData = JSON.parse(text);
      return res.status(200).json({ article: articleData });
    }

    // Default Action: Handwritten Answer Evaluation (Vision Grader)
    if (!imageBase64 || !question) {
      return res.status(400).json({ error: 'Missing required image or question parameters.' });
    }

    const evaluationPrompt = `You are an expert UPSC civil services examiner. Evaluate this handwritten answer sheet for the following prompt:
    Question: "${question}"
    Paper: ${paper}
    Marker Type: ${markerType}
    
    Provide rigorous, constructive feedback following standard UPSC evaluation parameters (Introduction, Core Body structure, Multidimensional Analysis, Keywords/Committees used, and Conclusion/Way Forward), along with an estimated score out of 10 or 15.`;

    const imagePart = {
      inlineData: {
        data: imageBase64,
        mimeType: mimeType || 'image/jpeg'
      }
    };

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: [evaluationPrompt, imagePart]
    });

    return res.status(200).json({ feedback: response.text });

  } catch (err) {
    console.error('API Error:', err);
    return res.status(500).json({ error: err.message || 'Internal server error.' });
  }
}
