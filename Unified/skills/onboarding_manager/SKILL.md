# Onboarding Manager Skill — Unified Campaigns

Turn a **lead → client** conversion into a live engagement. When lead changes to client after meeting, agent **creates all onboarding documentation and sends invoice from CRM template** — no manual hand-off.

## Human-in-the-Loop (reminder)
Onboarding starts AFTER meeting when lead becomes client. Agent creates docs + invoice via CRM (see Post-Meeting rule in `outreach_writer/SKILL.md`). Syed confirms status/offer/pilot scope inside CRM where required.

---

## Track 1 — AI Consultancy (mcp_ascentra_main / cat_ai_consultancy)
1. Kickoff — confirm business goals, AI readiness, constraints
2. Discovery — assess current state, data, processes
3. Strategy — draft AI & Business Transformation roadmap (2-4 weeks)
4. Proposal — present Strategy Sprint / Project Engagement options
5. Execution Support — if retained, run implementation oversight
6. Mark Onboarded → monthly retainer check-ins

## Track 2 — TalentBridge (mcp_ascentra_main / cat_talentbridge)
**Line A — Talent Provision:**
1. Send TalentBridge profile (capabilities + proof) within 2 business days
2. Kickoff — confirm role, stack, ways of working, timezone
3. Spec sheet — one-page role brief
4. Shortlist — only after Syed confirms: share vetted engineer shortlist
5. Intro calls / Trial (1-2 week paid trial)
6. Contract — lease (monthly) or direct hire (10%)
7. Workspace — provision Dedicated Workspace
8. First 30 days — weekly check-ins → Mark Onboarded

**Line B — Recruitment Service:**
1. Recruitment brief — confirm roles, salary band, timeline
2. Search plan — agree sourcing channels
3. Source & screen — run outreach, screen candidates
4. Shortlist — present 2-4 vetted candidates per role with scorecards
5. Candidate presentation — **Syed confirms offer before it goes to candidate**
6. Placement & close — invoice per 10% or retainer → Mark Onboarded

## Track 3 — Biometric Sign Up (mcp_ascentra_main / cat_biometric_signup)
1. Provision early-access — set up org's Biometric Sign Up workspace/sandbox
2. Kickoff (Syed) — confirm use case, GDPR/eIDAS 2.0 needs
3. Pilot scope — agree small pilot (e.g., one app flow); **Syed confirms scope**
4. Biometric enrollment — device-scoped ID generation + email/pass setup for multi-device + safe code generation (safe code never stored plaintext, only salted hash)
5. Check-ins — weekly 30 days → Mark Won (Early-Access Joined / Pilot)

## Track 4 — Sentrivault Vendor-First + Enterprise (mcp_ascentra_main / cat_sentravault)
1. POC — provision 14-30 day POC (up to 25 users, EU cloud, Vendor Starter/Team/Business/Enterprise tier features incl. DSPT/DTAC evidence pack) — **Syed confirms POC scope**
2. Kickoff — confirm use case, vendor-NHS relationship + data classification + compliance needs (DSPT/DTAC/GDPR/NHS DSP/FCA/eIDAS 2.0, G-Cloud/NHS tender timeline)
3. Commercial — agree tier: Vendor Starter £2k→£990 launch + £29/user/mo (min 1) / Team £5k→£2.9k + £9/user/mo (min 10, 500GB) / Business £8k + £14/user/mo (min 25, 2TB) / Enterprise £12-15k + £19/user/mo (min 100, 10TB, private cloud/on-prem) — annual upfront (monthly +15%, 3x instalments for Vendor tiers), storage pool, DPA/SLA, 30-day audit-ready guarantee; issue order form; **Syed confirms**
4. Provision — EU cloud / private cloud / on-prem per tier; SSO + audit log + DSPT/DTAC pack enablement
5. Check-ins — weekly 30 days → Mark Won (license active) — for vendors, track NHS tender submission readiness as success metric

---

## Universal Post-Meeting → Client Step (applies to all 4 tracks)
When lead → client after meeting:
1. Create all required onboarding docs from CRM templates (NDA, Order Form/SOW, DPA/SLA, provision doc per track above)
2. Generate + send invoice from **CRM invoice template** (single MCP profile `mcp_ascentra_main`) — use correct setup + subscription amount, log invoice link/number to lead category
3. Then run the track-specific steps below (POC/provision/kickoff) and mark Onboarded

## Output
After each onboarding, append to `memory/pipeline.md` under the correct lead category section and notify Syed of:
- Org/client onboarded, date, value/lead category (single MCP profile) + invoice number/link
- Any risks / objections
- Upsell signal (e.g., TalentBridge Line A → Line B, Biometric → Sentrivault)

## Targets
- TalentBridge: every Won → Onboarded within 2 weeks to count toward 5-client goal
- Biometric Sign Up: every demo → early-access/pilot toward 25-org goal
