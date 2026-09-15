"use client";
import { useEffect, useState } from "react";

type Entry = { user: string; task: string; minutes: number; date: string };

export default function TimeTracker({ code, user, socketRef }: { code: string; user: string; socketRef: any }) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [task, setTask] = useState("");
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const s = socketRef?.current;
    if (!s) return;
    s.emit("time:get", { code });
    s.on("time:state", (e: Entry[]) => setEntries(e));
    return () => s.off("time:state");
  }, [code, socketRef]);

  useEffect(() => {
    if (active === null) return;
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - active)/60000)), 1000);
    return () => clearInterval(id);
  }, [active]);

  const start = () => { if (!task.trim()) return; setActive(Date.now()); setElapsed(0); };
  const stop = () => {
    if (active===null) return;
    const mins = Math.max(1, Math.round((Date.now()-active)/60000));
    const e: Entry = { user, task, minutes: mins || elapsed || 1, date: new Date().toISOString().slice(0,10) };
    const next = [...entries, e];
    setEntries(next);
    socketRef?.current?.emit("time:add", { code, entry: e });
    setActive(null); setElapsed(0);
  };

  return (
    <div className="border rounded-lg bg-white p-3">
      <h3 className="font-medium text-sm mb-2">Monitoring & Tracking — Time Tracking Only</h3>
      <div className="flex gap-2 mb-3">
        <input value={task} onChange={e=>setTask(e.target.value)} placeholder="Task name" className="border rounded px-2 py-1 text-sm flex-1" />
        {active===null ? <button onClick={start} className="bg-emerald-600 text-white px-4 py-1 rounded text-sm">Start</button> : <button onClick={stop} className="bg-red-600 text-white px-4 py-1 rounded text-sm">Stop ({elapsed}m)</button>}
      </div>
      <div className="text-xs">
        <div className="grid grid-cols-4 font-semibold border-b pb-1 mb-1"><span>User</span><span>Task</span><span>Minutes</span><span>Date</span></div>
        {entries.length===0 && <div className="text-slate-400 py-2">No entries yet.</div>}
        {entries.map((e,i)=><div key={i} className="grid grid-cols-4 py-1 border-b last:border-0"><span>{e.user}</span><span>{e.task}</span><span>{e.minutes}m</span><span>{e.date}</span></div>)}
      </div>
    </div>
  );
}
