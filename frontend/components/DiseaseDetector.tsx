"use client";

import { useRef, useState } from "react";
import { predictDisease, PredictResult } from "@/lib/api";

export default function DiseaseDetector({
  onDetected,
}: {
  onDetected: (result: PredictResult | null) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(f: File | undefined) {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
    onDetected(null);
  }

  async function analyse() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const r = await predictDisease(file);
      setResult(r);
      onDetected(r);
    } catch (e: any) {
      setError(e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>Detect Disease</h2>

      <div className="dropzone" onClick={() => inputRef.current?.click()}>
        {preview ? (
          <img src={preview} alt="preview" style={{ maxWidth: "100%", maxHeight: 220, borderRadius: 8 }} />
        ) : (
          <span>Click to choose a leaf photo (JPG or PNG)</span>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      <div style={{ marginTop: 12 }}>
        <button className="primary" disabled={!file || loading} onClick={analyse}>
          {loading ? "Analysing..." : "Analyse"}
        </button>
      </div>

      {error && <div className="error-text">{error}</div>}

      {result && (
        <div style={{ marginTop: 20 }}>
          <div className="result-header">
            <strong>{result.disease_name}</strong>
            <span className={`badge ${result.is_healthy ? "healthy" : "sick"}`}>
              {result.is_healthy ? "Healthy" : "Disease detected"}
            </span>
          </div>
          <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 10 }}>
            Confidence: {result.confidence}% &middot; Crop: {result.affected_crop}
          </div>

          <div className="gradcam-grid">
            <figure>
              <img src={`data:image/png;base64,${result.original_image}`} alt="original" />
              <figcaption>Original</figcaption>
            </figure>
            <figure>
              <img src={`data:image/png;base64,${result.heatmap_image}`} alt="heatmap" />
              <figcaption>Heat Map</figcaption>
            </figure>
            <figure>
              <img src={`data:image/png;base64,${result.overlay_image}`} alt="overlay" />
              <figcaption>Overlay</figcaption>
            </figure>
          </div>

          {result.symptoms && (
            <>
              <strong>Symptoms</strong>
              <p style={{ fontSize: 14 }}>{result.symptoms}</p>
            </>
          )}

          {result.precautionary_measures && (
            <>
              <strong>Recommended actions</strong>
              <ul className="measures">
                {result.precautionary_measures.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
