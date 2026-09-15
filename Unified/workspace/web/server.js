// Custom server: Next.js + Socket.IO (easiest chat, no paid service)
const { createServer } = require("http");
const { parse } = require("url");
const next = require("next");
const { Server } = require("socket.io");

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev, dir: "./" });
const handle = app.getRequestHandler();

// In-memory store (replace with Postgres/Redis on VPS)
const messagesByRoom = new Map(); // room -> [{user, text, time}]
const tasksByEngagement = new Map(); // engagementCode -> tasks
const timeByEngagement = new Map(); // engagementCode -> [{user, taskId, start, end}]

function getRoomMessages(room) {
  if (!messagesByRoom.has(room)) messagesByRoom.set(room, []);
  return messagesByRoom.get(room);
}

app.prepare().then(() => {
  const server = createServer((req, res) => {
    const parsedUrl = parse(req.url, true);
    handle(req, res, parsedUrl);
  });

  const io = new Server(server, { cors: { origin: "*" } });

  io.on("connection", (socket) => {
    const { code, user } = socket.handshake.query;
    const room = code ? String(code) : "lobby";
    socket.join(room);
    // send history
    socket.emit("history", getRoomMessages(room));

    socket.on("chat:message", ({ text, room: r, user: u }) => {
      const targetRoom = r || room;
      const msg = { user: u || user || "Guest", text, time: new Date().toISOString() };
      getRoomMessages(targetRoom).push(msg);
      // keep last 500
      if (getRoomMessages(targetRoom).length > 500) getRoomMessages(targetRoom).shift();
      io.to(targetRoom).emit("chat:message", msg);
    });

    // Kanban sync
    socket.on("kanban:get", ({ code: c }) => {
      const k = c || room;
      socket.emit("kanban:state", tasksByEngagement.get(k) || []);
    });
    socket.on("kanban:set", ({ code: c, tasks }) => {
      const k = c || room;
      tasksByEngagement.set(k, tasks);
      io.to(k).emit("kanban:state", tasks);
    });

    // Time tracking
    socket.on("time:get", ({ code: c }) => {
      const k = c || room;
      socket.emit("time:state", timeByEngagement.get(k) || []);
    });
    socket.on("time:add", ({ code: c, entry }) => {
      const k = c || room;
      const arr = timeByEngagement.get(k) || [];
      arr.push(entry);
      timeByEngagement.set(k, arr);
      io.to(k).emit("time:state", arr);
    });
  });

  const port = process.env.PORT || 3000;
  server.listen(port, () => console.log(`> Ready on http://localhost:${port} (Socket.IO enabled)`));
});
