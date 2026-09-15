# Unified Campaigns — Hermes Agent

This is a **single Hermes Agent** instance managing **four campaigns under Ascentra Global Ltd**:

1. **AI Consultancy** — AI & Business Transformation
2. **TalentBridge** — Talent leasing + recruitment service
3. **Biometric Sign Up** — Biometric-only sign-up technology
4. **Sentrivault** — Cybersecurity product (biometric auth + encrypted vault) — **Vendor-First GTM (Sept 2026): NHS vendors & Gov suppliers for compliance**

All campaigns operate under the parent company Ascentra Global Ltd.

---

## Campaign Channels & Lead Categories (single MCP profile)

| Campaign | Outreach Email | Lead Category |
|----------|----------------|---------------|

| AI Consultancy | info@ascentraconsulting.co.uk | `mcp_ascentra_main / cat_ai_consultancy` |
| TalentBridge | info@ascentraconsulting.co.uk | `mcp_ascentra_main / cat_talentbridge` |
| Biometric Sign Up | info@ascentraconsulting.co.uk | `mcp_ascentra_main / cat_biometric_signup` |
| Sentrivault (Vendor-First) | info@ascentraconsulting.co.uk | `mcp_ascentra_main / cat_sentravault` |

> All 4 campaigns use the single email `info@ascentraconsulting.co.uk`. Multi-channel cadence automatically triggers Voice Agent cold calling 48 hours after email dispatch if no reply is received.


---

## Quick Setup

1. Drop `skills/` + `memory/` + `cron/` into the Hermes data dir (`%LOCALAPPDATA%\hermes` or `~/.hermes`)
2. Load `memory/unified_profile.md`
3. Declare active campaign in Hermes chat: `"work on talentbridge"` / `"run biometricsignup"` / `"work on sentravault"` / `"work on consultancy"`

---

## Human-in-the-Loop (MANDATORY)

- **Meetings:** agent never books/confirms. Notify Syed — Syed attends.
- **Confirmations:** agent never confirms any client agreement. Notify Syed; set "Awaiting Syed Confirmation".

*This is the only place a personal name appears.*

---

## Goals

- **AI Consultancy:** 5 new clients in 2 months
- **TalentBridge:** 5 new clients in 2 months
- **Biometric Sign Up:** 25 demo-requesting orgs across EU & UK by 29 Oct 2026
- **Sentrivault:** 3 paid licenses in 4 months (Vendor Starter £2k→£990 launch + Team £5k→£2.9k + per-user) — 6-8 POCs (≥4 vendors) — finalised vendor-first profile + traction for £500K pre-seed

---
