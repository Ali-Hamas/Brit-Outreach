"use client";
import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

export default function Chat({ code, user }: { code: string; user: string }) {
  const [msgs, setMsgs] = useState<{ user: string; text: string; time: string }[]>([]);
  const [text, setText] = useState("");
  const [groupMode, setGroupMode] = useState(true);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const s = io({ query: { code, user } });
    socketRef.current = s;
    s.on("history", (h) => setMsgs(h));
    s.on("chat:message", (m) => setMsgs((prev) => [...prev, m]));
    return () => { s.disconnect(); };
  }, [code, user]);

  const send = () => {
    if (!text.trim()) return;
    socketRef.current?.emit("chat:message", { text, room: code, user });
    setText("");
  };

  return (
    <div className="flex flex-col h-[520px] border rounded-lg bg-white">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50 rounded-t-lg">
        <span className="font-medium text-sm">Communication</span>
        <div className="flex gap-2 text-xs">
          <button onClick={() => setGroupMode(true)} className={`px-2 py-1 rounded ${groupMode ? "bg-slate-900 text-white" : "bg-white border"}`}>Group Chat</button>
          <button onClick={() => setGroupMode(false)} className={`px-2 py-1 rounded ${!groupMode ? "bg-slate-900 text-white" : "bg-white border"}`}>Chat</button>
          <span className="ml-2 text-slate-500 hidden md:inline">Room: {code} • {user}</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-slate-50">
        {msgs.length === 0 && <p className="text-xs text-slate-400">No messages yet. Start the conversation.</p>}
        {msgs.map((m, i) => (
          <div key={i} className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${m.user === user ? "bg-blue-600 text-white ml-auto" : "bg-white border"}`}>
            <div className="text-[11px] opacity-60">{m.user} • {new Date(m.time).toLocaleTimeString()}</div>
            <div>{m.text}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2 p-2 border-t">
        <input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder={groupMode ? "Message group..." : "Message..."} className="flex-1 border rounded px-3 py-2 text-sm" />
        <button onClick={send} className="bg-blue-600 text-white px-4 py-2 rounded text-sm">Send</button>
      </div>
      <p className="text-[11px] text-slate-400 px-3 pb-2">Easiest Socket.IO chat — no paid service, EU-hostable. Group chat is room-wide; DM will route via same room with @mention filter (extend later).</p>
    </div>
  );
}
