"use client";
import { useEffect, useState } from "react";
import { io, Socket } from "socket.io-client";

type Task = { id: string; title: string; status: "todo" | "pending" | "done"; assignee?: string };

export default function Kanban({ code, socketRef }: { code: string; socketRef: any }) {
  const [tasks, setTasks] = useState<Task[]>([
    { id: "1", title: "Setup project repo", status: "todo" },
    { id: "2", title: "Design review", status: "pending" },
  ]);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    const s: Socket = socketRef?.current;
    if (!s) return;
    s.emit("kanban:get", { code });
    s.on("kanban:state", (t: Task[]) => { if (t.length) setTasks(t); });
    return () => { s.off("kanban:state"); };
  }, [code, socketRef]);

  const sync = (next: Task[]) => {
    setTasks(next);
    socketRef?.current?.emit("kanban:set", { code, tasks: next });
  };

  const add = () => {
    if (!newTitle.trim()) return;
    sync([...tasks, { id: Date.now().toString(), title: newTitle, status: "todo" }]);
    setNewTitle("");
  };
  const move = (id: string, status: Task["status"]) => sync(tasks.map(t => t.id === id ? { ...t, status } : t));

  const cols: Task["status"][] = ["todo", "pending", "done"];
  return (
    <div className="border rounded-lg bg-white p-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-sm">Project Management — Simple Kanban</h3>
        <div className="flex gap-2">
          <input value={newTitle} onChange={e=>setNewTitle(e.target.value)} placeholder="New task" className="border rounded px-2 py-1 text-sm w-48" />
          <button onClick={add} className="bg-slate-900 text-white px-3 py-1 rounded text-sm">Add</button>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {cols.map(col => (
          <div key={col} className="bg-slate-50 rounded p-2 min-h-[280px]">
            <div className="text-xs font-semibold uppercase tracking-wide mb-2 text-slate-600">{col === "todo" ? "To Do" : col === "pending" ? "Pending" : "Done"}</div>
            <div className="space-y-2">
              {tasks.filter(t=>t.status===col).map(t=>(
                <div key={t.id} className="bg-white border rounded p-2 text-sm">
                  <div>{t.title}</div>
                  <div className="flex gap-1 mt-2">
                    {cols.filter(c=>c!==col).map(c=>(
                      <button key={c} onClick={()=>move(t.id,c)} className="text-[11px] border rounded px-2 py-1 bg-white">→ {c}</button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
