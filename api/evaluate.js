import { GoogleGenAI } from '@google/genai';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { question, paper, markerType, imageBase64, mimeType } = req.body;
    
    // Uses Vercel's secure server environment variable
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

    const prompt = `Act as a strict UPSC Civil Services Mains examiner. Evaluate the provided handwritten answer photo for ${paper} (${markerType}).
    Question: "${question}"

    Provide your evaluation in clean HTML format:
    1. Overall Score out of 10 with a brief examiner verdict.
    2. Handwriting & Presentation Review (spacing, structure, margins, headings).
    3. Content & Breadth (dimensional coverage, committee reports, keywords used vs missing).
    4. Scope for Improvement & Model Conclusion suggestion.`;

    const contents = [
      { text: prompt },
      { inlineData: { mimeType: mimeType || 'image/jpeg', data: imageBase64 } }
    ];

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: contents,
    });

    return res.status(200).json({ feedback: response.text });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Failed to evaluate answer.' });
  }
}
