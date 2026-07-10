const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface PredictResult {
  class_name: string;
  confidence: number;
  disease_name: string;
  affected_crop: string | null;
  is_healthy: boolean | null;
  symptoms: string | null;
  precautionary_measures: string[] | null;
  original_image: string;
  heatmap_image: string;
  overlay_image: string;
}

export async function predictDisease(file: File): Promise<PredictResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/predict`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Prediction failed (${res.status})`);
  }
  return res.json();
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export async function sendChatMessage(
  message: string,
  history: ChatMessage[],
  detectedDisease: string | null
): Promise<string> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, detected_disease: detectedDisease }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Chat failed (${res.status})`);
  }
  const data = await res.json();
  return data.reply;
}
