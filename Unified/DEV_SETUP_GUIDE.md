# DEV SETUP GUIDE — Unified Hermes Agent (Ascentra Global Ltd)
> Single folder to run 4 campaigns. Give this file + the whole `unified_campaigns/` folder to dev.

---

## 1. Overview

**One Hermes agent, one MCP CRM profile, four campaigns under Ascentra Global Ltd:**

| # | Campaign | Lead Category (MCP) | Outreach Email (SMTP in MCP) | Purpose |
|---|----------|---------------------|------------------------------|---------|
| 1 | AI Consultancy | `cat_ai_consultancy` | `info@ascentraconsulting.co.uk` | AI & Business Transformation |
| 2 | TalentBridge | `cat_talentbridge` | `info@ascentraconsulting.co.uk` | Talent provision (1.6-9k/mo) + recruitment (10%) |
| 3 | Biometric Sign Up | `cat_biometric_signup` | `info@ascentraconsulting.co.uk` | Biometric-only sign-up tech (free early-access) |
| 4 | Sentrivault | `cat_sentravault` | `info@ascentraconsulting.co.uk` | **Vendor-First + Enterprise:** Vendor Starter £990 launch (was £2k) + £29/user, Team £2.9k→£5k + £9/user, Business £8k + £14/user, Enterprise £12-15k + £19/user per mo |

- **Single Unified Email:** `info@ascentraconsulting.co.uk` across all 4 campaigns.
- **Single sending channel:** **All mail via MCP CRM mass mailing (unified SMTP)**.
- **Cadence Integration:** Leads not responding after 48h are automatically called via Voice Agent.
- **Single calendar:** **MCP CRM calendar** inside `mcp_ascentra_main`. Agent books there.
- **Human-in-the-loop:** Agent **books** via MCP calendar, **Syed attends** and **confirms status inside CRM**. Agent never confirms a client agreement.

---

## 2. Prerequisites

- VPS with Docker (for Hermes), or local Windows/Linux with Python 3.10+ (`uv` will manage env)
- MCP CRM access (admin) to create profile/categories and verify SMTP domains
- Calendar access inside MCP CRM (enabled for `mcp_ascentra_main`)
- Model API key (OpenAI `GPT-4o` recommended, or Anthropic/Claude)

---

## 3. MCP CRM Setup (Do This First)

1. **Create/Use Profile:** `mcp_ascentra_main` (single profile for all 4 campaigns).
2. **Create Lead Categories** inside that profile:
   - `cat_ai_consultancy`
   - `cat_talentbridge` (use field `Line A / Line B` for TalentBridge sub-type if needed)
   - `cat_biometric_signup`
   - `cat_sentravault`
3. **Verify Email Domain (SMTP) in the profile:**
   - `info@ascentraconsulting.co.uk` (Single unified SMTP for all 4 categories)
   - Ensure SPF/DKIM/DMARC pass, domain is warmed (as provided).
4. **Enable Calendar** inside `mcp_ascentra_main` connected to `info@ascentraconsulting.co.uk` (so agent can book calendar events).

---

## 4. Hermes Installation & Directory Structure

After CRM is ready, install Hermes to use this folder as source:

```powershell
# Windows (PowerShell) - installs Hermes CLI (hermes)
irm https://nousresearch.com/hermes/install.ps1 | iex
# hermes manages its own env via uv, needs Python 3.10+
```

**Hermes workspace location:**
- Windows: `%LOCALAPPDATA%\hermes\`
- Linux/macOS: `~/.hermes/`

**Deploy this folder's contents:**

```
unified_campaigns/
├── DEV_SETUP_GUIDE.md              # this file
├── 00_UNIFIED_PROFILE.md           # full memory for agent
├── 01_UNIFIED_AGENT.md             # skill config overview
├── ASCENTRA_GROUP_PROFILE.md       # group business profile
├── SENTRAVAULT_ENTERPRISE_PROFILE.md # Sentrivault enterprise tiers
├── memory/
│   ├── unified_profile.md          # copy of 00 (agent loads this)
│   ├── ascentra_group_profile.md
│   └── pipeline.md                 # unified pipeline, segmented by cat_*
├── skills/
│   ├── prospect_research/SKILL.md  # finds decision-maker + direct email, fallback to company dedicated email, never generic
│   ├── outreach_writer/SKILL.md    # sends via CRM SMTP to decision-maker email, books via MCP calendar
│   ├── pipeline_manager/SKILL.md   # 11-stage pipeline, segregated by lead category
│   └── onboarding_manager/SKILL.md # 4 onboarding tracks (TalentBridge A/B etc.)
└── cron/
    ├── daily_prospects.yaml        # 8/day fast-cash split: 4 TalentBridge, 2 AI Consultancy, 1 Biometric, 1 Sentrivault
    ├── daily_outreach.yaml         # fast-cash sends: TalentBridge 200/d, AI 100/d, Biometric+Sentrivault 50 each (shared support@ cap 100/d)
    ├── weekly_followup.yaml
    ├── weekly_onboarding.yaml
    └── monthly_report.yaml
```

**Copy to Hermes workspace:**

```powershell
# PowerShell — adjust paths
$src="C:\Users\DELL\Desktop\unified_campaigns"
$dst="$env:LOCALAPPDATA\hermes"
Copy-Item "$src\skills" "$dst\skills" -Recurse -Force
Copy-Item "$src\memory" "$dst\memory" -Recurse -Force
Copy-Item "$src\cron" "$dst\cron" -Recurse -Force
```

---

## 5. Model & Cron Configuration

```bash
hermes model   # pick OpenAI GPT-4o (recommended)
hermes config  # paste API key
hermes cron list
# cron YAMLs in cron/ are auto-loaded; fast-cash mode already set (TalentBridge 200/d)
```

**Verify:**
```bash
hermes
# In chat: "Read the file at %LOCALAPPDATA%\hermes\memory\unified_profile.md"
# Then: "Research 2 prospects for TalentBridge as a test"
```

---

## 6. Critical Rules (Agent Must Follow)

1. **Recipients:** Send **only to decision-maker direct email**. If not found after search, fallback to **company dedicated email** (e.g., `contact@company.com` from website). **Never** `info@/support@/admin@`.
   - Prospect research finds this: `skills/prospect_research/SKILL.md:11-24`
2. **From Email:** Use the **dedicated SMTP per lead category** (table in section 1) — all via **MCP CRM mass mailing**, single channel.
3. **Calendar Booking:** Agent **books itself via MCP CRM calendar** (`mcp_ascentra_main`) with title prefix `[AI Consultancy]` / `[TalentBridge]` / `[Biometric Sign Up]` / `[Sentrivault]` + company — contact. Description must have lead category + To email + CRM lead link. (`skills/outreach_writer/SKILL.md:5-6`, `skills/pipeline_manager/SKILL.md`)
4. **Human-in-the-loop:** Agent **never confirms** a client agreement. Sets stage `Awaiting Syed Confirmation` — Syed confirms status inside CRM. Syed attends every meeting.

---

## 7. Pipeline Stages (All 4 Campaigns)

`Research` → `Outreach` → `Engaged` → `Qualified` → `Meeting/Demo Booked via Calendar` → `Meeting Held` → `Agreed → AWAITING Syed Confirmation` → `Confirmed` → `Won` → `Onboarded` → `Lost`
- Tracked in `memory/pipeline.md` segmented by `cat_*` under single `mcp_ascentra_main`.
- Sentrivault (Vendor-First): `POCs 0/6-8 (≥4 vendors)` → `Licenses Won 0/3` (Vendor Starter £990→£2k + £29/user / Team £2.9k→£5k + £9/user / Business £8k + £14/user / Enterprise £12-15k + £19/user).

---

## 8. Testing Checklist (Run Before Going Live)

- [ ] MCP profile `mcp_ascentra_main` exists with 4 `cat_*` categories
- [ ] All 3 SMTP domains verified and test mail from each succeeds via CRM mass mailing
- [ ] MCP calendar shows test event with prefix `[TalentBridge] Test Co — Jane Doe`
- [ ] Hermes loads `memory/unified_profile.md` without error
- [ ] Test prospect research: finds decision-maker direct email (not generic)
- [ ] Test outreach: sends via correct From email per category, logged to correct `cat_*`
- [ ] Test booking: agent creates calendar event via MCP CRM calendar, Syed can see it and confirm status inside CRM

---

## 9. Troubleshooting

- **Mail goes to spam:** Domains already warmed — check SPF/DKIM, keep Biometric+Sentrivault capped at 100/d total on `support@` (fast-cash rule).
- **Agent sends to generic:** Check `prospect_research` output has `To Email: decision-maker or company dedicated` — if generic, research failed, fix prospect step.
- **Calendar not booking:** Ensure MCP calendar is enabled for `mcp_ascentra_main` and agent has write access to it.
- **Wrong category:** Agent must read `00_UNIFIED_PROFILE.md` table — single profile, category decides From email.

---

## 10. What Not to Do

- Do NOT create separate CRM profiles per campaign (single `mcp_ascentra_main` only).
- Do NOT create a second mailer channel (all via CRM SMTP).
- Do NOT send to `info@/support@/admin@`.
- Do NOT let agent confirm a client agreement — only Syed confirms inside CRM.

---

*Folder ready to deploy. All files use UTF-8. For Sentrivault tier details, see `SENTRAVAULT_ENTERPRISE_PROFILE.md`.*
