from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import Business, Campaign, Prospect, ProspectStatus
from app.db.session import get_db

router = APIRouter(prefix="/voice", tags=["Voice Calling & Cadence"])
logger = logging.getLogger(__name__)

VOICE_AGENT_DIR = Path(r"M:\Voice Agent")
VOICE_AGENT_DB = VOICE_AGENT_DIR / "data" / "voiceagent.sqlite"

CAMPAIGN_HOOKS = {
    "camp-ai-consultancy": {
        "name": "AI Consultancy — AI & Business Transformation",
        "hook": "AI strategy sprints, automated copilots, and end-to-end business transformation to reduce operational costs by up to 40%",
        "pitch": "Ascentra Global's enterprise AI practice helps UK and US organizations design and deploy high-ROI agentic workflows in 2 to 4 weeks.",
    },
    "camp-talentbridge": {
        "name": "TalentBridge — AI & Tech Talent Provision",
        "hook": "pre-vetted remote senior AI, full-stack, and DevOps engineers placed on lease in under 2 weeks, saving 60% compared to local hiring",
        "pitch": "We eliminate recruiter fees and hiring bottlenecks by providing certified engineering squads ready to deploy immediately.",
    },
    "camp-biometric": {
        "name": "Biometric Sign Up — Passwordless Technology",
        "hook": "passwordless biometric onboarding and identity verification with full GDPR and ISO 27001 compliance",
        "pitch": "Eliminates credential stuffing, phishing, and password reset overhead while boosting conversion rates.",
    },
    "camp-sentrivault": {
        "name": "Sentrivault — NHS & Enterprise Compliance Vault",
        "hook": "NHS DTAC and DSPT compliance pack with biometric zero-knowledge vault, ready to deploy in 30 days",
        "pitch": "Our 990 launch offer solves NHS DTAC and enterprise security audits in 30 days, preventing lost vendor contracts.",
    },
}


def get_voice_db_connection() -> sqlite3.Connection:
    if not VOICE_AGENT_DB.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Voice Agent database not found at {VOICE_AGENT_DB}. Run Voice Agent setup first.",
        )
    cx = sqlite3.connect(VOICE_AGENT_DB)
    cx.row_factory = sqlite3.Row
    return cx


# ---------- Pydantic Schemas ----------


class CadenceTriggerRequest(BaseModel):
    cadence_hours: float = 48.0
    dry_run: bool = False
    business_id: Optional[str] = "biz-ascentra"


class DirectColdCallRequest(BaseModel):
    prospect_ids: List[str]
    campaign_id: str
    business_id: Optional[str] = "biz-ascentra"
    scheduled_delay_seconds: int = 0


# ---------- Endpoints ----------


@router.get("/cadence/status")
def get_cadence_status(
    cadence_hours: float = 48.0,
    business_id: Optional[str] = "biz-ascentra",
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns real-time status of the Multi-Channel Cadence Funnel:
    - How many leads were emailed
    - How many replied
    - How many have NOT replied after X hours (and are eligible for voice calling)
    - How many cold calls are currently queued / in progress
    - How many discovery meetings have been booked
    """
    query = db.query(Prospect)
    if business_id:
        query = query.filter(Prospect.business_id == business_id)

    all_prospects = query.all()
    cutoff_time = datetime.utcnow() - timedelta(hours=cadence_hours)

    total_count = len(all_prospects)
    contacted_count = 0
    replied_count = 0
    unreplied_eligible_leads: List[Dict[str, Any]] = []
    meeting_booked_count = 0

    for p in all_prospects:
        status_val = p.status.value if hasattr(p.status, "value") else str(p.status)

        if status_val == "meeting_booked":
            meeting_booked_count += 1

        if status_val in ("contacted", "replied", "meeting_booked") or p.last_contacted_at is not None:
            contacted_count += 1

        if p.replied_at is not None or status_val == "replied":
            replied_count += 1
        elif status_val == "contacted" or (p.last_contacted_at is not None and status_val != "meeting_booked"):
            # Check if contacted >= cadence_hours ago and has phone
            if p.last_contacted_at and p.last_contacted_at <= cutoff_time:
                has_phone = bool(p.phone and len(p.phone.strip()) >= 7)
                unreplied_eligible_leads.append({
                    "id": p.id,
                    "name": f"{p.first_name or ''} {p.last_name or ''}".strip() or "Decision Maker",
                    "email": p.email,
                    "phone": p.phone or "Missing Phone",
                    "has_valid_phone": has_phone,
                    "company": p.company or "N/A",
                    "title": p.title or "N/A",
                    "campaign_id": p.campaign_id,
                    "last_contacted_at": p.last_contacted_at.isoformat() if p.last_contacted_at else None,
                    "hours_since_email": round((datetime.utcnow() - p.last_contacted_at).total_seconds() / 3600, 1) if p.last_contacted_at else None,
                })

    # Query Voice Agent database for active queue count
    calls_queued = 0
    calls_completed = 0
    try:
        with get_voice_db_connection() as cx:
            row_q = cx.execute("SELECT COUNT(*) AS c FROM outbound_jobs WHERE status IN ('queued', 'dialing', 'in_call')").fetchone()
            if row_q:
                calls_queued = row_q["c"]
            row_done = cx.execute("SELECT COUNT(*) AS c FROM outbound_jobs WHERE status = 'completed'").fetchone()
            if row_done:
                calls_completed = row_done["c"]
    except Exception as e:
        logger.warning("Could not read Voice Agent DB: %s", e)

    return {
        "business_id": business_id,
        "cadence_hours_configured": cadence_hours,
        "funnel": {
            "total_leads": total_count,
            "emails_dispatched": contacted_count,
            "inbound_replies": replied_count,
            "unreplied_leads": len(unreplied_eligible_leads),
            "unreplied_ready_for_call": len([l for l in unreplied_eligible_leads if l["has_valid_phone"]]),
            "calls_currently_queued": calls_queued,
            "calls_completed": calls_completed,
            "meetings_booked": meeting_booked_count,
        },
        "eligible_leads": unreplied_eligible_leads[:50],
    }


@router.post("/cadence/trigger")
def trigger_cadence_calling(
    req: CadenceTriggerRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Scans for all prospects who were emailed >= cadence_hours ago and have not replied.
    Automatically pushes them into the Voice Agent's cold calling queue referencing
    info@ascentraconsulting.co.uk and the specific campaign hook.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=req.cadence_hours)
    query = db.query(Prospect).filter(
        Prospect.business_id == req.business_id,
        Prospect.last_contacted_at <= cutoff_time,
        Prospect.replied_at.is_(None),
    )

    eligible_prospects = [
        p for p in query.all()
        if (p.phone and len(p.phone.strip()) >= 7) and (p.status.value if hasattr(p.status, "value") else str(p.status)) != "meeting_booked"
    ]

    if not eligible_prospects:
        return {
            "success": True,
            "message": f"No unreplied leads found matching criteria (emailed >= {req.cadence_hours}h ago with valid phone number).",
            "enqueued_count": 0,
            "leads": [],
        }

    enqueued = []
    skipped = []

    if req.dry_run:
        return {
            "success": True,
            "dry_run": True,
            "message": f"[DRY-RUN] Found {len(eligible_prospects)} leads eligible for cold call cadence.",
            "enqueued_count": len(eligible_prospects),
            "leads": [
                {
                    "name": f"{p.first_name} {p.last_name}",
                    "phone": p.phone,
                    "company": p.company,
                    "campaign": p.campaign_id,
                }
                for p in eligible_prospects
            ],
        }

    # Connect to Voice Agent SQLite
    try:
        with get_voice_db_connection() as cx:
            now_ts = int(time.time())

            for p in eligible_prospects:
                phone = p.phone.strip()
                full_name = f"{p.first_name or ''} {p.last_name or ''}".strip() or "Valued Decision Maker"
                company = p.company or "N/A"
                camp_id = p.campaign_id or "camp-ai-consultancy"

                camp_info = CAMPAIGN_HOOKS.get(camp_id, CAMPAIGN_HOOKS["camp-ai-consultancy"])
                campaign_name = camp_info["name"]
                campaign_hook = camp_info["hook"]

                # 1. Insert or get lead in voiceagent.sqlite
                lead_cur = cx.execute(
                    "SELECT id FROM leads WHERE restaurant_id = 1 AND phone = ?", (phone,)
                ).fetchone()

                qual_note = (
                    f"Outreach email sent {p.last_contacted_at} from info@ascentraconsulting.co.uk. "
                    f"No reply after {req.cadence_hours}h. 48-Hour Voice Cadence Follow-Up."
                )

                if lead_cur:
                    lead_id = lead_cur["id"]
                    cx.execute(
                        "UPDATE leads SET status = 'queued', qualification_notes = ?, updated_at = ? WHERE id = ?",
                        (qual_note, now_ts, lead_id),
                    )
                else:
                    cur = cx.execute(
                        """
                        INSERT INTO leads (
                            restaurant_id, name, phone, email, company_name, role,
                            service_interest, status, qualification_notes, created_at, updated_at
                        ) VALUES (1, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?)
                        """,
                        (full_name, phone, p.email, company, p.title or "", campaign_name, qual_note, now_ts, now_ts),
                    )
                    lead_id = cur.lastrowid

                # 2. Check if active job exists
                job_cur = cx.execute(
                    "SELECT id FROM outbound_jobs WHERE restaurant_id = 1 AND lead_id = ? AND status IN ('queued', 'dialing', 'in_call')",
                    (lead_id,),
                ).fetchone()

                if job_cur:
                    skipped.append({"id": p.id, "name": full_name, "reason": "Already queued"})
                    continue

                # 3. Enqueue job
                context = {
                    "prospect_id": p.id,
                    "company": company,
                    "decision_maker": full_name,
                    "title": p.title or "",
                    "email": p.email,
                    "campaign": campaign_name,
                    "email_sender": "info@ascentraconsulting.co.uk",
                    "last_email_subject": p.last_email_subject or "recent outreach",
                    "campaign_hook": campaign_hook,
                    "cadence_step": "48h_voice_followup",
                }

                cx.execute(
                    """
                    INSERT INTO outbound_jobs (
                        restaurant_id, job_type, lead_id, to_number, guest_name,
                        context_json, scheduled_at, status, attempts, source,
                        created_at, updated_at
                    ) VALUES (1, 'cold_call', ?, ?, ?, ?, ?, 'queued', 0, 'brit_cadence_48h', ?, ?)
                    """,
                    (lead_id, phone, full_name, json.dumps(context), now_ts, now_ts, now_ts),
                )
                enqueued.append({"id": p.id, "name": full_name, "phone": phone, "company": company})

            cx.commit()

        return {
            "success": True,
            "message": f"Successfully queued {len(enqueued)} unreplied leads for automated cold calling.",
            "enqueued_count": len(enqueued),
            "skipped_count": len(skipped),
            "enqueued_leads": enqueued,
        }
    except Exception as e:
        logger.error("Failed triggering voice cadence: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to queue cold calls: {e}")


@router.post("/direct-call")
def trigger_direct_cold_calling(
    req: DirectColdCallRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """DIRECT COLD CALLING MODE (No prior email required):
    Allows selecting a specific product (AI Consultancy, TalentBridge, Biometric Sign Up, or Sentrivault)
    and immediately enqueues the selected leads for direct outbound cold calls.
    """
    camp_info = CAMPAIGN_HOOKS.get(req.campaign_id)
    if not camp_info:
        # Fallback to campaign lookup by ID from campaigns table
        camp_obj = db.query(Campaign).filter(Campaign.id == req.campaign_id).first()
        if camp_obj:
            camp_info = {
                "name": camp_obj.name,
                "hook": f"our tailored solutions for {camp_obj.name}",
                "pitch": f"Ascentra Global provides market-leading solutions for {camp_obj.name}.",
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid campaign_id '{req.campaign_id}'. Choose one of: {list(CAMPAIGN_HOOKS.keys())}",
            )

    # Fetch selected prospects
    prospects = db.query(Prospect).filter(
        Prospect.id.in_(req.prospect_ids),
        Prospect.business_id == req.business_id,
    ).all()

    if not prospects:
        raise HTTPException(status_code=404, detail="No matching prospects found for given IDs.")

    enqueued = []
    missing_phone = []

    try:
        with get_voice_db_connection() as cx:
            now_ts = int(time.time())
            scheduled_ts = now_ts + max(0, req.scheduled_delay_seconds)

            for p in prospects:
                phone = (p.phone or "").strip()
                if not phone or len(phone) < 7:
                    missing_phone.append({"id": p.id, "name": f"{p.first_name} {p.last_name}", "email": p.email})
                    continue

                full_name = f"{p.first_name or ''} {p.last_name or ''}".strip() or "Decision Maker"
                company = p.company or "N/A"

                qual_note = (
                    f"Direct Cold Call initiated for product: '{camp_info['name']}'. "
                    f"Hook: {camp_info['hook']}."
                )

                # 1. Insert or update lead in voiceagent.sqlite
                lead_cur = cx.execute(
                    "SELECT id FROM leads WHERE restaurant_id = 1 AND phone = ?", (phone,)
                ).fetchone()

                if lead_cur:
                    lead_id = lead_cur["id"]
                    cx.execute(
                        "UPDATE leads SET status = 'queued', service_interest = ?, qualification_notes = ?, updated_at = ? WHERE id = ?",
                        (camp_info["name"], qual_note, now_ts, lead_id),
                    )
                else:
                    cur = cx.execute(
                        """
                        INSERT INTO leads (
                            restaurant_id, name, phone, email, company_name, role,
                            service_interest, status, qualification_notes, created_at, updated_at
                        ) VALUES (1, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?)
                        """,
                        (full_name, phone, p.email, company, p.title or "", camp_info["name"], qual_note, now_ts, now_ts),
                    )
                    lead_id = cur.lastrowid

                # 2. Enqueue outbound calling job
                context = {
                    "prospect_id": p.id,
                    "company": company,
                    "decision_maker": full_name,
                    "title": p.title or "",
                    "email": p.email,
                    "campaign": camp_info["name"],
                    "campaign_hook": camp_info["hook"],
                    "product_pitch": camp_info["pitch"],
                    "calling_mode": "direct_cold_call",
                }

                cx.execute(
                    """
                    INSERT INTO outbound_jobs (
                        restaurant_id, job_type, lead_id, to_number, guest_name,
                        context_json, scheduled_at, status, attempts, source,
                        created_at, updated_at
                    ) VALUES (1, 'cold_call', ?, ?, ?, ?, ?, 'queued', 0, 'direct_outreach_panel', ?, ?)
                    """,
                    (lead_id, phone, full_name, json.dumps(context), scheduled_ts, now_ts, now_ts),
                )

                # Update status in brit_outreach.db
                p.status = ProspectStatus.CONTACTED
                p.campaign_id = req.campaign_id
                enqueued.append({
                    "id": p.id,
                    "name": full_name,
                    "phone": phone,
                    "company": company,
                    "product": camp_info["name"],
                })

            cx.commit()
            db.commit()

        return {
            "success": True,
            "product_selected": camp_info["name"],
            "enqueued_count": len(enqueued),
            "missing_phone_count": len(missing_phone),
            "enqueued_leads": enqueued,
            "skipped_missing_phone": missing_phone,
        }
    except Exception as e:
        logger.error("Direct cold calling enqueue error: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed direct cold calling enqueue: {e}")


@router.get("/jobs")
def list_voice_jobs(limit: int = 50) -> Dict[str, Any]:
    """Returns recent outbound cold calling jobs and their live execution status."""
    try:
        with get_voice_db_connection() as cx:
            rows = cx.execute(
                """
                SELECT id, restaurant_id, job_type, lead_id, to_number, guest_name,
                       context_json, scheduled_at, status, attempts, source, created_at, updated_at
                FROM outbound_jobs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            jobs = []
            for r in rows:
                d = dict(r)
                try:
                    d["context"] = json.loads(d.get("context_json") or "{}")
                except Exception:
                    d["context"] = {}
                d.pop("context_json", None)
                jobs.append(d)

            return {
                "total": len(jobs),
                "jobs": jobs,
            }
    except Exception as e:
        logger.error("Error reading jobs: %s", e)
        return {"total": 0, "jobs": [], "error": str(e)}


@router.post("/sync-outcomes")
def sync_voice_outcomes(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Synchronizes call outcomes (qualified, meeting_booked, lost) from Voice Agent
    leads back into Brit Outreach prospects.
    """
    updated_count = 0
    try:
        with get_voice_db_connection() as cx:
            lead_rows = cx.execute("SELECT email, phone, status, qualification_notes FROM leads WHERE email IS NOT NULL").fetchall()

            for l in lead_rows:
                email = (l["email"] or "").strip().lower()
                status_v = l["status"]

                if not email:
                    continue

                prospect = db.query(Prospect).filter(Prospect.email == email).first()
                if prospect:
                    if status_v == "meeting_booked" and prospect.status != ProspectStatus.MEETING_BOOKED:
                        prospect.status = ProspectStatus.MEETING_BOOKED
                        updated_count += 1
                    elif status_v == "qualified" and prospect.status == ProspectStatus.NEW:
                        prospect.status = ProspectStatus.QUALIFIED
                        updated_count += 1

            db.commit()

        return {
            "success": True,
            "synced_prospects": updated_count,
        }
    except Exception as e:
        logger.error("Sync outcomes failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed syncing outcomes: {e}")
