import { GoogleGenAI } from '@google/genai';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { action, searchTerm, question, paper, markerType, imageBase64, mimeType, isProUser } = req.body;

    // Optional Server-Side Pro Verification
    // If you want strict security, you can verify user subscription tokens here.
    // For now, we ensure the request structure is safe and valid.

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY is not configured on Vercel.' });
    }

    const ai = new GoogleGenAI({ apiKey });
    const modelName = 'gemini-2.0-flash';

    // 1. Handle Dynamic Wiki Article Generation
    if (action === 'generateWikiArticle') {
      if (!searchTerm) return res.status(400).json({ error: 'Search term is required.' });

      const prompt = `You are a senior UPSC Civil Services examination expert. Synthesize a comprehensive, Wikipedia-grade study article for the topic: "${searchTerm}".
      Return ONLY a valid JSON object (no markdown formatting blocks like \`\`\`json) matching this exact schema:
      {
        "article": {
          "title": "Precise UPSC-grade title",
          "paper": "GS-2",
          "date": "2026-10",
          "topic": "Polity & Federalism",
          "static_linkage": "Constitutional Framework & Evolution",
          "prelims_pointers": ["Point 1 with exact factual detail", "Point 2 with constitutional/economic article or data reference", "Point 3"],
          "mains_perspective": {
            "context": "Comprehensive analytical context background for civil services mains.",
            "key_arguments": "Multi-dimensional arguments covering social, economic, political, and administrative angles.",
            "way_forward": "Actionable administrative and policy recommendations."
          },
          "image": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60"
        }
      }`;

      const response = await ai.models.generateContent({
        model: modelName,
        contents: prompt
      });

      let rawText = response.text.trim();
      if (rawText.startsWith('```json')) rawText = rawText.replace(/^```json/, '').replace(/```$/, '').trim();
      else if (rawText.startsWith('```')) rawText = rawText.replace(/^```/, '').replace(/```$/, '').trim();

      const parsed = JSON.parse(rawText);
      return res.status(200).json(parsed);
    }

    // 2. Handle AI Vision Answer Sheet Grading
    if (imageBase64) {
      if (!question) return res.status(400).json({ error: 'Question prompt is required for evaluation.' });

      const imagePart = {
        inlineData: {
          data: imageBase64,
          mimeType: mimeType || 'image/jpeg'
        }
      };

      const evalPrompt = `You are an expert UPSC Civil Services Mains Evaluator at a premier Delhi institute. 
      Examine this handwritten student answer sheet for the following parameters:
      - Paper: ${paper || 'GS-2'}
      - Marker Type: ${markerType || '15-Marker (250 Words)'}
      - Question: "${question}"

      Provide rigorous, structured feedback:
      1. Structure & Introduction (Demand of the question addressed?)
      2. Body Content & Multidimensional Arguments (Political, Economic, Social, Ethical angles)
      3. Handwriting & Presentation Legibility
      4. Scope for Improvement & Model Keywords to Include
      5. Estimated Score out of 10 or 15.`;

      const response = await ai.models.generateContent({
        model: modelName,
        contents: [evalPrompt, imagePart]
      });

      return res.status(200).json({ feedback: response.text });
    }

    return res.status(400).json({ error: 'Invalid request payload.' });

  } catch (err) {
    console.error("Backend Evaluation Error:", err);
    return res.status(500).json({ error: err.message || 'Internal server error during AI generation.' });
  }
}
