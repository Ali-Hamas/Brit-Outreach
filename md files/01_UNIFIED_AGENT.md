# Unified Campaigns — Agent Skill Config

Configures the **dedicated Hermes Agent** for four campaigns under Ascentra Global Ltd. Covers four functional skills with campaign-aware routing.

---

## Campaign Parameters

| Campaign | Description | Outreach Email | CRM Profile | Geo |
|----------|-------------|----------------|-------------|-----|
| **1 — AI Consultancy** | AI & Business Transformation consulting | syedislam@ascentraconsulting.co.uk | `crm_ai_consultancy` | UK/US |
| **2 — TalentBridge** | AI & tech talent provision + remote recruitment | lease@talentbridge.it.com | `crm_talentbridge` | UK/US |
| **3 — Biometric Sign Up** | Biometric-only sign-up tech (unique ID single device; email/pass for multi-device; safe code; GDPR) | support@ascentraconsulting.co.uk | `crm_biometric_signup` | EU & UK |
| **4 — Sentrivault** | Cybersecurity product (biometric auth + encrypted storage) | support@ascentraconsulting.co.uk | `crm_sentravault` | EU & UK |

## Human-in-the-Loop (MANDATORY)

1. **Meetings:** When a prospect wants a meeting/demo, the agent MUST NOT book/confirm a time. Notify Syed (company, contact, trigger) — **Syed attends**.
2. **Confirmations:** When a client agrees/confirms anything, the agent MUST NOT confirm. Notify Syed with the exact agreement; set stage "Awaiting Syed Confirmation".

## Sprint Goals

- **AI Consultancy:** 5 new clients in 2 months
- **TalentBridge:** 5 new clients in 2 months (Line A + Line B; vast pool, send TalentBridge profile)
- **Biometric Sign Up:** 25 demo-requesting orgs by 29 Oct 2026 (EU & UK, ≥10 EU)
- **Sentrivault:** Finalised profile + investor traction for £500K pre-seed

---

## Skills (functional, campaign-aware)

### Skill 1: Prospect Research (`skills/prospect_research/SKILL.md`)
Detects campaign-specific signals, picks best-fit campaign (1-4), scores fit 1-5, drafts first-line hook, logs to correct CRM profile.
See `skills/prospect_research/SKILL.md`.

### Skill 2: Outreach Writer (`skills/outreach_writer/SKILL.md`)
Sends campaign-specific outreach using the correct outreach email and CRM profile; never books/confirms meetings.
See `skills/outreach_writer/SKILL.md`.

### Skill 3: Pipeline Manager (`skills/pipeline_manager/SKILL.md`)
Tracks pipeline with campaign-specific gates and "Awaiting Syed Confirmation" state, segregated by CRM profile.
See `skills/pipeline_manager/SKILL.md`.

### Skill 4: Onboarding Manager (`skills/onboarding_manager/SKILL.md`)
Campaign-specific onboarding workflows (4 tracks); starts only after Syed confirms.
See `skills/onboarding_manager/SKILL.md`.

---

## Cron Schedules

See `cron/` for the YAML to drop into Hermes (`daily_prospects.yaml`, `daily_outreach.yaml`, `weekly_followup.yaml`, `weekly_onboarding.yaml`, `monthly_report.yaml`).
