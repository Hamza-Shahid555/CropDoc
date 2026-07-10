"use client";

import { useState } from "react";
import DiseaseDetector from "@/components/DiseaseDetector";
import ChatWidget from "@/components/ChatWidget";
import { PredictResult } from "@/lib/api";

export default function Home() {
  const [result, setResult] = useState<PredictResult | null>(null);

  return (
    <main className="page">
      <header className="top">
        <h1>🌿 CropDoc</h1>
      </header>

      <div className="layout">
        <DiseaseDetector onDetected={setResult} />
        <ChatWidget detectedDisease={result?.class_name ?? null} />
      </div>
    </main>
  );
}
