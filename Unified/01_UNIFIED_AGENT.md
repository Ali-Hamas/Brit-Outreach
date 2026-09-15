# Unified Campaigns — Agent Skill Config

Configures the **dedicated Hermes Agent** for four campaigns under Ascentra Global Ltd. Covers four functional skills with campaign-aware routing.

---

## Campaign Parameters

| Campaign | Description | Outreach Email (unified across all campaigns) | Lead Category (single MCP profile) | Geo |
|----------|-------------|-----------------------------------------------|------------------------------------|-----|
| **1 — AI Consultancy** | AI & Business Transformation consulting | info@ascentraconsulting.co.uk | `mcp_ascentra_main` / `cat_ai_consultancy` | UK/US |
| **2 — TalentBridge** | AI & tech talent provision + remote recruitment | info@ascentraconsulting.co.uk | `mcp_ascentra_main` / `cat_talentbridge` | UK/US |
| **3 — Biometric Sign Up** | Biometric-only sign-up tech (unique ID single device; email/pass for multi-device; safe code; GDPR) | info@ascentraconsulting.co.uk | `mcp_ascentra_main` / `cat_biometric_signup` | EU & UK |
| **4 — Sentrivault** | **Vendor-First + Enterprise Licensing** — biometric auth + encrypted vault (Vendor Starter £2k→£990 launch + £29/user/mo, Team £5k→£2.9k + £9/user, Business £8k + £14/user, Enterprise £12-15k + £19/user, annual upfront, 14-day POC, 30-day guarantee) — targets NHS vendors first | info@ascentraconsulting.co.uk | `mcp_ascentra_main` / `cat_sentravault` | EU & UK |

## Human-in-the-Loop (MANDATORY)

1. **Meetings:** Agent **books the meeting itself via the MCP CRM calendar** (single `mcp_ascentra_main`, using `info@ascentraconsulting.co.uk`). **Event title prefix:** `[Campaign] Company — Contact` + lead category in description. Syed **attends** and confirms status inside CRM.
2. **Confirmations:** When a client agrees/confirms anything, the agent MUST NOT confirm. Notify Syed with the exact agreement; set stage "Awaiting Syed Confirmation" — Syed confirms status inside CRM.

## Multi-Channel Cadence (Email -> 48h -> Cold Call)
- **Step 1:** Cold email sent from `info@ascentraconsulting.co.uk`.
- **Step 2:** Cadence monitor checks every cycle. If no response after **48 hours (2 days)**, Hermes activates **Voice Caller** (`skills/voice_caller/SKILL.md`) to place an outbound phone call via Twilio + OpenAI Realtime.
- **Hook:** Voice caller references the exact email sent: *"Hi [Name], this is Alex calling from Ascentra Global regarding the note we emailed you a couple days back from info@ascentraconsulting.co.uk..."*

## Sprint Goals — FAST-CASH MODE (all via unified email info@ascentraconsulting.co.uk)

- **TalentBridge (PRIORITY):** 5 new clients in 2 months — 200/d via `info@ascentraconsulting.co.uk`
- **AI Consultancy:** 5 new clients in 2 months — 100/d via `info@ascentraconsulting.co.uk`
- **Biometric Sign Up:** 25 demo-requesting orgs by 29 Oct 2026 — 50/d via `info@ascentraconsulting.co.uk`
- **Sentrivault (VENDOR-FIRST):** 3 paid licenses in 4 months (16 weeks) — 50/d via `info@ascentraconsulting.co.uk` (70% vendors / 30% enterprise)

---

## Skills (functional, campaign-aware)

### Skill 1: Prospect Research (`skills/prospect_research/SKILL.md`)
Finds decision-maker and their email (fallback to company dedicated email, never generic); detects campaign signals, scores fit, logs to correct lead category (single MCP profile).
See `skills/prospect_research/SKILL.md`.

### Skill 2: Outreach Writer (`skills/outreach_writer/SKILL.md`)
Sends via **CRM mass mailing (unified info@ascentraconsulting.co.uk)** to **decision-maker email**; books meetings via MCP CRM calendar.
See `skills/outreach_writer/SKILL.md`.

### Skill 3: Voice Caller (`skills/voice_caller/SKILL.md`)
Orchestrates outbound phone calls via Voice Agent when prospect has not replied to email after 48 hours. Warm follow-up referencing sent email, handles objections, and closes for meeting.
See `skills/voice_caller/SKILL.md`.

### Skill 4: Pipeline Manager (`skills/pipeline_manager/SKILL.md`)
Tracks pipeline with campaign-specific gates and "Awaiting Syed Confirmation" state, segregated by lead category (single MCP profile).
See `skills/pipeline_manager/SKILL.md`.

### Skill 5: Onboarding Manager (`skills/onboarding_manager/SKILL.md`)
Campaign-specific onboarding workflows (4 tracks); starts only after Syed confirms.
See `skills/onboarding_manager/SKILL.md`.

---

## Cron Schedules

See `cron/` for the YAML to drop into Hermes (`daily_prospects.yaml`, `daily_outreach.yaml`, `daily_voice_cadence.yaml`, `weekly_followup.yaml`, `weekly_onboarding.yaml`, `monthly_report.yaml`).
