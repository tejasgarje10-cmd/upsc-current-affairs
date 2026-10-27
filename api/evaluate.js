const { GoogleGenAI } = require('@google/genai');

module.exports = async function handler(req, res) {
  // Enable CORS headers so your frontend can talk smoothly to the backend
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { question, paper, markerType, imageBase64, mimeType } = req.body;
    
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'Server configuration error: GEMINI_API_KEY is missing in Vercel Environment Variables.' });
    }

    const ai = new GoogleGenAI({ apiKey });

    const prompt = `Act as a strict UPSC Civil Services Mains examiner. Evaluate the provided handwritten answer photo for ${paper} (${markerType}).
    Question: "${question}"

    Provide your evaluation in clean HTML format:
    1. Overall Score out of 10 with a brief examiner verdict.
    2. Handwriting & Presentation Review (spacing, structure, margins, headings).
    3. Content & Breadth (dimensional coverage, committee reports, keywords used vs missing).
    4. Scope for Improvement & Model Conclusion suggestion.`;

    // Clean base64 string if data URL prefix exists
    let cleanBase64 = imageBase64;
    if (imageBase64 && imageBase64.includes(',')) {
      cleanBase64 = imageBase64.split(',')[1];
    }

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: [
        { text: prompt },
        { 
          inlineData: { 
            mimeType: mimeType || 'image/jpeg', 
            data: cleanBase64 
          } 
        }
      ],
    });

    return res.status(200).json({ feedback: response.text });
  } catch (error) {
    console.error("Gemini Vision Error:", error);
    return res.status(500).json({ error: error.message || 'Failed to evaluate answer.' });
  }
};
