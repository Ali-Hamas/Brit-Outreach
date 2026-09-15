# Pipeline Manager Skill — Unified Campaigns

Track pipeline for **four campaigns**, segregated by lead category (single MCP profile).

## Stages (all campaigns)

1. Research - company identified (with decision-maker email or company dedicated email)
2. Outreach - first message sent to decision-maker / company dedicated email (never generic)
3. Engaged - replied, conversation started
4. Qualified - service line confirmed, scope/timeline/budget
5. **Meeting/Demo Booked via Calendar** (agent books via MCP CRM calendar, Syed attends and confirms status in CRM)
6. Meeting/Demo Held - Syed delivered, status confirmed in CRM
7. **Agreed - client confirmed intent → AWAITING Syed Confirmation** (agent does NOT confirm — Syed confirms status in CRM)
8. Confirmed - Syed confirmed in CRM
 9. Won - contract/early-access/pilot/license signed → **Agent creates all onboarding docs + sends invoice from CRM template** (see `outreach_writer/SKILL.md` Post-Meeting rule)
10. Onboarded - onboarding workflow complete (docs + invoice sent, provisioned)
11. Lost - declined (record reason + revisit date)

## Human-in-the-Loop (MANDATORY)
- Stage 5: prospect asks for meeting/demo → **agent books via the MCP CRM calendar** (single profile `mcp_ascentra_main`, using the campaign's dedicated From email). **Calendar event title:** `[Campaign] Company — Contact` (e.g., `[TalentBridge] Acme Ltd — Jane Doe, CTO`). Description: lead category + To email + CRM link. Syed attends and confirms status inside CRM.
- Stage 7: client agrees/confirms anything → do NOT confirm. Notify Syed with exact agreement; set stage to "Awaiting Syed Confirmation" — Syed confirms status inside CRM.

## Campaign Goals & lead category (single MCP profile)s

| Campaign | lead category (single MCP profile) | Target |
|----------|-------------|--------|
| AI Consultancy | `mcp_ascentra_main / cat_ai_consultancy` | 5 new clients in 2 months |
| TalentBridge | `mcp_ascentra_main / cat_talentbridge` | 5 new clients in 2 months |
| Biometric Sign Up | `mcp_ascentra_main / cat_biometric_signup` | 25 demo-requesting orgs by 29 Oct 2026 |
| Sentrivault (Vendor-First) | `mcp_ascentra_main / cat_sentravault` | 3 paid licenses in 4 months (Vendor Starter £990→£2k / Team £5k→£2.9k + per-user subs; 14-day POC) — 6-8 POCs (≥4 vendors), ACV = setup + annual sub |

## Pipeline File Format (memory/pipeline.md)

```
# Unified Pipeline — [Date]

## Summary by CRM
- mcp_ascentra_main / cat_ai_consultancy: Prospects X | Engaged X | Meeting(Syed) X | Awaiting Confirm X | Won X/5
- mcp_ascentra_main / cat_talentbridge: Prospects X | Engaged X | Meeting(Syed) X | Awaiting Confirm X | Won X/5 | Onboarded X
  - TalentBridge: Line A Lease MRR pipeline GBP X | Won MRR GBP X | Line B pipeline GBP X
- mcp_ascentra_main / cat_biometric_signup: Prospects X | Demo Requests X/25 | Demos Held X | Early-Access Joined X | Pilots X
- mcp_ascentra_main / cat_sentravault (Vendor-First): Prospects X | POCs X/6-8 | Demos Held X | Licenses Won X/3 | ACV Pipeline GBP X | Won ACV GBP X | Vendors vs Enterprise split X/Y

## Active Prospects

### [Company Name] | Campaign: [1-4] | CRM: [crm_*]
- **Stage:** [stage]
- **Contact:** [name, title]
- **Scope:** [role / assignment / tech]
- **Value:** [£ or MRR / % / pilot]
- **Outreach Email:** [syedislam@... / lease@... / support@...]
- **Next Action:** [step]
- **Deadline:** [date]
```

## Weekly Review Prompt
Review pipeline and provide per lead category (single MCP profile):
1. Sprint progress vs target
2. Meetings pending Syed; agreements awaiting Syed confirmation
3. Prospects needing follow-up (no contact 7+ days)
4. Deals at risk / matched-but-not-signed
5. Recommended actions this week to hit targets
