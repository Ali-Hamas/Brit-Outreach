# TalentBridge Secure Workspace

**For:** `unified_campaigns` — granted on onboarding via shared code/link. Windows desktop only.

**3 Sections (as requested):**
1. **Communication** — Chat + Group Chat (Socket.IO, easiest free self-hosted, no paid service) + Video Meeting
2. **Project Management** — Simple Kanban: To Do / Pending / Done (no Jira bloat)
3. **Monitoring & Tracking** — Time tracking only (Start/Stop per task)

**Access:** On onboarding, generate a share code/link (e.g., `https://workspace.yourdomain.eu?code=A1B2C3`) and give it to employer + assigned engineers. No CRM sync.

**Video + Transcription/Minutes:** Jitsi Meet self-hosted on same EU VPS (free) + `Jibri` recording -> `faster-whisper` -> `Ollama (Llama 3.1)` generates minutes. Both `whisper` and `ollama` services are in `docker-compose.yml` (commented, uncomment when ready — all free, no API).

**Run locally (Windows):**
```powershell
cd unified_campaigns\workspace\web
npm install
npm run dev
# open http://localhost:3000?code=TEST
```

**Deploy to EU VPS:**
```bash
docker compose up -d
# set NEXT_PUBLIC_JITSI_DOMAIN=jitsi.yourdomain.eu in web/.env
```

**Desktop only:** Layout has `min-width: 1024px`, no mobile breakpoints.
