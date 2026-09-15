"use client";
import { useState } from "react";

export default function VideoRoom({ code }: { code: string }) {
  const [joined, setJoined] = useState(false);
  // Jitsi self-hosted embed — free, EU VPS. Replace YOUR_JITSI_DOMAIN after you deploy Jitsi on VPS.
  const jitsiDomain = process.env.NEXT_PUBLIC_JITSI_DOMAIN || "meet.jit.si";
  const room = `TalentBridge-${code}`;
  const src = `https://${jitsiDomain}/${room}#config.prejoinConfig.enabled=false`;
  return (
    <div className="border rounded-lg bg-white p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-sm">Video Meeting — with transcription & minutes (free self-hosted)</h3>
        <button onClick={()=>setJoined(!joined)} className={`px-3 py-1 rounded text-sm ${joined?"bg-red-600 text-white":"bg-blue-600 text-white"}`}>{joined?"Leave":"Join"}</button>
      </div>
      {!joined ? (
        <div className="bg-slate-50 rounded p-4 text-sm text-slate-600">
          <p>When you deploy on your EU VPS, set <code className="bg-white border px-1 rounded">NEXT_PUBLIC_JITSI_DOMAIN</code> to your Jitsi domain (e.g., <code>jitsi.yourdomain.eu</code>). Until then it uses <code>meet.jit.si</code> for testing.</p>
          <p className="mt-2"><b>Transcription pipeline (free, self-hosted):</b> Jibri records -> <code>faster-whisper</code> transcribes -> <code>Ollama (Llama 3.1)</code> generates minutes. Both run on same VPS (see <code>docker-compose.yml</code> commented services). No paid API.</p>
          <p className="mt-2 text-xs">Recording/transcript stored encrypted in MinIO (EU). Minutes auto-appear after meeting ends.</p>
        </div>
      ) : (
        <iframe allow="camera; microphone; display-capture" src={src} className="w-full h-[520px] rounded border" />
      )}
    </div>
  );
}
