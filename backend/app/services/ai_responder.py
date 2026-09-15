import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.db.models import Prospect, Reply, ProspectStatus, SMTPConfig, Campaign
from app.services.outreach import SMTPRouter
from app.services.crm import CRMSync
from app.core.config import settings

class AIConversationResponder:
    """AI Agent that autonomously chats with replying prospects to answer questions and book appointments in BritCRM"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.api_key = openai_api_key or getattr(settings, "OPENAI_API_KEY", None)
        self.crm_sync = CRMSync()

    def generate_ai_reply(self, prospect: Prospect, prospect_reply: str, campaign_context: Optional[str] = None) -> Dict[str, Any]:
        """Use LLM / Rule-based engine to generate a conversational reply and check if an appointment should be booked"""

        system_prompt = f"""
You are an expert AI Sales Assistant representing {prospect.company or 'our company'}.
Your objective is to have a natural, helpful email conversation with the prospect ({prospect.first_name or 'there'}) and book an appointment with them.

Prospect Info:
- Name: {prospect.first_name} {prospect.last_name}
- Title: {prospect.title}
- Company: {prospect.company}

Latest Message from Prospect:
"{prospect_reply}"

Instructions:
1. Be polite, professional, concise, and conversational.
2. If they ask a question or express interest, answer helpfully and suggest 2 convenient time slots for a brief 15-minute call (e.g. Tomorrow at 2:00 PM or Thursday at 10:00 AM).
3. If they specify a time slot or agree to a meeting (e.g., "Thursday at 2pm works"), confirm the booking enthusiastically.
4. Output your response in valid JSON format with keys:
   - "email_body": The conversational text to reply to the prospect.
   - "should_book_appointment": true/false
   - "proposed_time_iso": ISO timestamp if time was agreed upon (or null)
   - "meeting_title": Title of meeting if booking (e.g., "Discovery Call with {prospect.first_name}")
"""

        # If OpenAI API Key is provided, call OpenAI Chat API
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prospect_reply}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7
                }
                res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=15)
                res.raise_for_status()
                content = res.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            except Exception as e:
                print(f"[AI Responder Error] OpenAI API call failed: {e}. Falling back to default assistant.")

        # Fallback intelligent assistant response generator
        reply_lower = prospect_reply.lower()

        # Check if prospect confirmed a time or expressed clear interest
        if any(w in reply_lower for w in ["yes", "sure", "sounds good", "works for me", "schedule", "book", "tomorrow", "thursday", "friday", "monday", "tuesday", "wednesday", "pm", "am", "time"]):
            proposed_time = datetime.utcnow() + timedelta(days=1, hours=4)
            return {
                "email_body": f"Hi {prospect.first_name or 'there'},\n\nFantastic! I've reserved a 15-minute discovery call for us. I'll send over the calendar invitation right away.\n\nLooking forward to speaking!\n\nBest regards,\nOutreach Team",
                "should_book_appointment": True,
                "proposed_time_iso": proposed_time.isoformat(),
                "meeting_title": f"Discovery Meeting - {prospect.first_name or 'Lead'} ({prospect.company or 'Prospect'})"
            }
        else:
            return {
                "email_body": f"Hi {prospect.first_name or 'there'},\n\nThank you for getting back to me! Would you be open to a quick 10-minute introductory call this week?\n\nHow does tomorrow at 2:00 PM EST or Thursday at 10:00 AM EST work for you?\n\nBest regards,\nOutreach Team",
                "should_book_appointment": False,
                "proposed_time_iso": None,
                "meeting_title": None
            }

    def process_and_auto_chat(self, prospect: Prospect, prospect_reply: str, smtp_config: SMTPConfig) -> Dict[str, Any]:
        """Handle incoming reply: generate AI chat response, email prospect back, and book appointment in BritCRM if confirmed"""

        # 1. Generate AI conversational response
        ai_res = self.generate_ai_reply(prospect, prospect_reply)

        email_body = ai_res["email_body"]
        should_book = ai_res.get("should_book_appointment", False)
        meeting_title = ai_res.get("meeting_title", f"Call with {prospect.first_name}")

        # 2. Send email reply back to prospect via business SMTP
        smtp_router = SMTPRouter()
        subject = f"Re: {prospect.last_email_subject or 'Outreach'}"
        tracking_id = f"ai-chat-{prospect.id[:8]}"

        formatted_html = "<p>" + email_body.replace("\n", "<br>") + "</p>"
        sent = smtp_router.send_email(
            smtp_config=smtp_config,
            to_email=prospect.email,
            subject=subject,
            body_html=formatted_html,
            body_text=email_body,
            tracking_id=tracking_id
        )

        # 3. If appointment confirmed, book directly in BritCRM and notify CEO!
        crm_result = None
        if should_book:
            start_time = datetime.utcnow() + timedelta(days=1)
            if ai_res.get("proposed_time_iso"):
                try:
                    start_time = datetime.fromisoformat(ai_res["proposed_time_iso"])
                except Exception:
                    pass

            crm_result = self.crm_sync.book_appointment_in_crm(
                prospect=prospect,
                title=meeting_title,
                start_time=start_time,
                notes=f"Automatically booked by AI Conversation Assistant after email reply: '{prospect_reply}'"
            )
            prospect.status = ProspectStatus.MEETING_BOOKED
        else:
            prospect.status = ProspectStatus.REPLIED

        self.crm_sync.sync_prospect(prospect)

        return {
            "email_sent_to_prospect": sent,
            "ai_chat_response": email_body,
            "appointment_booked_in_britcrm": should_book,
            "britcrm_result": crm_result
        }
