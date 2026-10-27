export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY is not configured in Vercel environment settings.' });
    }

    const { action, question, paper, markerType, imageBase64, mimeType, searchTerm } = req.body;

    if (action === 'generateWikiArticle') {
      if (!searchTerm) {
        return res.status(400).json({ error: 'Search term is required' });
      }

      const prompt = `Act as an elite UPSC civil services expert. A student searched for "${searchTerm}" in the NexusGS Wikipedia repository. 
      Generate a comprehensive study article for this exact topic tailored for UPSC.
      
      Return ONLY valid raw JSON matching this exact structure, with no markdown code blocks or extra text:
      {
        "title": "A precise, professional title for ${searchTerm}",
        "paper": "GS-3",
        "topic": "Economy & Growth",
        "static_linkage": "Core constitutional article or statutory body",
        "date": "2026-10",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=60",
        "prelims_pointers": [
          "Key factual statement 1 with institutional backing",
          "Key factual statement 2 with committee precedent"
        ],
        "mains_perspective": {
          "context": "Socio-economic or administrative context of ${searchTerm}",
          "key_arguments": "Multi-dimensional analysis exploring core arguments and challenges",
          "way_forward": "Actionable policy measures or administrative recommendations"
        }
      }`;

      const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }]
        })
      });

      const geminiData = await geminiRes.json();
      if (!geminiRes.ok) {
        throw new Error(geminiData.error?.message || 'Failed to communicate with Gemini API');
      }

      let text = geminiData.candidates[0].content.parts[0].text.trim();
      if (text.startsWith('```json')) {
        text = text.replace(/^```json/, '').replace(/```$/, '').trim();
      } else if (text.startsWith('```')) {
        text = text.replace(/^```/, '').replace(/```$/, '').trim();
      }

      const articleData = JSON.parse(text);
      return res.status(200).json({ article: articleData });
    }

    if (!imageBase64 || !question) {
      return res.status(400).json({ error: 'Missing required image or question parameters.' });
    }

    const evaluationPrompt = `You are an expert UPSC examiner. Evaluate this handwritten answer for: "${question}" (Paper: ${paper}, Type: ${markerType}). Provide structured feedback and an estimated score.`;

    const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              { text: evaluationPrompt },
              { inline_data: { mime_type: mimeType || 'image/jpeg', data: imageBase64 } }
            ]
          }
        ]
      })
    });

    const geminiData = await geminiRes.json();
    if (!geminiRes.ok) {
      throw new Error(geminiData.error?.message || 'Failed to evaluate image');
    }

    const feedbackText = geminiData.candidates[0].content.parts[0].text;
    return res.status(200).json({ feedback: feedbackText });

  } catch (err) {
    console.error('API Error:', err);
    return res.status(500).json({ error: err.message || 'Internal server error during AI synthesis.' });
  }
}
