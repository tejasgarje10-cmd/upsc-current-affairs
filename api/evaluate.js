import { GoogleGenAI } from '@google/genai';

export default async function handler(req, res) {
  // Support both POST (manual frontend calls) and GET (Vercel automatic daily Cron triggers)
  if (req.method !== 'POST' && req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY is not configured on Vercel.' });
    }

    const ai = new GoogleGenAI({ apiKey });
    const modelName = 'gemini-2.0-flash';

    const action = req.body?.action || (req.method === 'GET' ? 'generateDailyBatch' : null);
    const { searchTerm, question, paper, markerType, imageBase64, mimeType } = req.body || {};

    // 1. Bulk Daily Current Affairs Synthesis (Triggered automatically by Cron or manually)
    if (action === 'generateDailyBatch' || req.method === 'GET') {
      const prompt = `You are a senior UPSC Civil Services examination expert and current affairs director at a premier Delhi institute. 
      Generate a comprehensive batch of exactly 8 distinct, high-yield current affairs articles covering recent national policy changes, international relations, economic shifts, scientific breakthroughs, and governance issues spanning GS-1, GS-2, GS-3, and GS-4.
      Return ONLY a valid JSON array (no markdown code blocks, no backticks) matching this exact schema:
      [
        {
          "title": "Precise UPSC-grade title",
          "paper": "GS-2",
          "date": "2026-10",
          "topic": "Polity & Federalism",
          "static_linkage": "Constitutional Framework & Evolution",
          "prelims_pointers": ["Point 1 with factual detail", "Point 2 with reference", "Point 3"],
          "mains_perspective": {
            "context": "Comprehensive analytical context background for civil services mains.",
            "key_arguments": "Multi-dimensional arguments covering social, economic, political angles.",
            "way_forward": "Actionable administrative and policy recommendations."
          },
          "image": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=60"
        }
      ]`;

      const response = await ai.models.generateContent({
        model: modelName,
        contents: prompt
      });

      let rawText = response.text.trim();
      if (rawText.startsWith('```json')) rawText = rawText.replace(/^```json/, '').replace(/```$/, '').trim();
      else if (rawText.startsWith('```')) rawText = rawText.replace(/^```/, '').replace(/```$/, '').trim();

      const parsed = JSON.parse(rawText);
      
      // If it's a Vercel cron job trigger (GET request), return a clean success confirmation
      if (req.method === 'GET') {
        return res.status(200).json({ success: true, message: "Daily current affairs batch successfully generated via cron.", count: parsed.length });
      }

      return res.status(200).json({ articles: parsed });
    }

    // 2. Handle Single Dynamic Wiki Article Generation
    if (action === 'generateWikiArticle') {
      if (!searchTerm) return res.status(400).json({ error: 'Search term is required.' });

      const prompt = `You are a senior UPSC Civil Services examination expert. Synthesize a comprehensive, Wikipedia-grade study article for the topic: "${searchTerm}".
      Return ONLY a valid JSON object (no markdown code blocks, no backticks) matching this exact schema:
      {
        "article": {
          "title": "Precise UPSC-grade title",
          "paper": "GS-2",
          "date": "2026-10",
          "topic": "Polity & Federalism",
          "static_linkage": "Constitutional Framework & Evolution",
          "prelims_pointers": ["Point 1", "Point 2", "Point 3"],
          "mains_perspective": {
            "context": "Comprehensive analytical context background.",
            "key_arguments": "Multi-dimensional arguments.",
            "way_forward": "Actionable recommendations."
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

    // 3. Handle AI Vision Answer Sheet Grading
    if (imageBase64) {
      if (!question) return res.status(400).json({ error: 'Question prompt is required for evaluation.' });

      const imagePart = {
        inlineData: {
          data: imageBase64,
          mimeType: mimeType || 'image/jpeg'
        }
      };

      const evalPrompt = `You are an expert UPSC Civil Services Mains Evaluator at a premier Delhi institute. 
      Examine this handwritten student answer sheet for:
      - Paper: ${paper || 'GS-2'}
      - Marker Type: ${markerType || '15-Marker (250 Words)'}
      - Question: "${question}"

      Provide rigorous, structured feedback:
      1. Structure & Introduction
      2. Body Content & Multidimensional Arguments
      3. Handwriting & Presentation Legibility
      4. Scope for Improvement & Model Keywords
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
