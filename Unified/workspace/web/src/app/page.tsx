"use client";
import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";
import Chat from "@/components/Chat";
import Kanban from "@/components/Kanban";
import TimeTracker from "@/components/TimeTracker";
import VideoRoom from "@/components/VideoRoom";

export default function Page() {
  const [code, setCode] = useState("");
  const [user, setUser] = useState("");
  const [joined, setJoined] = useState(false);
  const [tab, setTab] = useState<"chat" | "project" | "tracking" | "video">("chat");
  const socketRef = useRef<any>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const c = params.get("code") || localStorage.getItem("tb_code") || "";
    const u = localStorage.getItem("tb_user") || "";
    if (c) setCode(c);
    if (u) setUser(u);
  }, []);

  const join = () => {
    if (!code.trim() || !user.trim()) return;
    localStorage.setItem("tb_code", code);
    localStorage.setItem("tb_user", user);
    // init socket for kanban/time sync
    const s = io({ query: { code, user } });
    socketRef.current = s;
    setJoined(true);
  };

  const generateLink = () => {
    const c = Math.random().toString(36).slice(2, 8).toUpperCase();
    setCode(c);
    navigator.clipboard?.writeText(`${window.location.origin}?code=${c}`);
    alert(`Share link copied: ${window.location.origin}?code=${c}\nGive this code to employer + engineers.`);
  };

  if (!joined) {
    return (
      <main className="max-w-3xl mx-auto p-8">
        <h1 className="text-2xl font-bold">TalentBridge Secure Workspace</h1>
        <p className="text-sm text-slate-600 mt-1">Employer ↔ Engineers — shared code/link access. Windows desktop only.</p>
        <div className="mt-6 border rounded-lg bg-white p-6 space-y-4">
          <div>
            <label className="text-sm font-medium">Shared Code / Link</label>
            <div className="flex gap-2 mt-1">
              <input value={code} onChange={e=>setCode(e.target.value)} placeholder="e.g. A1B2C3 or paste ?code=..." className="flex-1 border rounded px-3 py-2" />
              <button onClick={generateLink} className="border rounded px-3 py-2 text-sm">Generate Link</button>
            </div>
            <p className="text-xs text-slate-500 mt-1">On onboarding, generate a code and share it with the client + engineers. No CRM sync needed.</p>
          </div>
          <div>
            <label className="text-sm font-medium">Your display name</label>
            <input value={user} onChange={e=>setUser(e.target.value)} placeholder="e.g. Alex (Employer)" className="w-full border rounded px-3 py-2 mt-1" />
          </div>
          <button onClick={join} className="w-full bg-slate-900 text-white rounded py-2">Enter Workspace</button>
          <p className="text-xs text-slate-400">Self-hosted EU VPS, no paid tools. Chat= Socket.IO (easiest, free). Video= Jitsi self-hosted + faster-whisper + Ollama for minutes.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-[1400px] mx-auto p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">TalentBridge Workspace <span className="text-slate-500 font-normal text-sm">— Code: {code} • {user}</span></h1>
        <button onClick={()=>{localStorage.clear(); location.href="/";}} className="text-xs border rounded px-2 py-1">Leave</button>
      </div>
      <div className="flex gap-2 mt-3">
        {(["chat","project","tracking","video"] as const).map(t=>(
          <button key={t} onClick={()=>setTab(t)} className={`px-4 py-2 rounded text-sm capitalize ${tab===t?"bg-slate-900 text-white":"bg-white border"}`}>{t==="chat"?"Communication": t==="project"?"Project Management": t==="tracking"?"Monitoring & Tracking": "Video Meeting"}</button>
        ))}
      </div>
      <div className="mt-4">
        {tab==="chat" && <Chat code={code} user={user} />}
        {tab==="project" && <Kanban code={code} socketRef={socketRef} />}
        {tab==="tracking" && <TimeTracker code={code} user={user} socketRef={socketRef} />}
        {tab==="video" && <VideoRoom code={code} />}
      </div>
    </main>
  );
}
