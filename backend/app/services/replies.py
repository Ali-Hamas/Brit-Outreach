import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from app.db.models import Prospect, Reply, ProspectStatus

class ReplyProcessor:
    """Processes inbound email replies and classifies intent & sentiment"""

    @staticmethod
    def clean_email_body(body: str) -> str:
        """Strip quoted history, automated headers, and signature noise"""
        if not body:
            return ""
        patterns = [
            r'On .* wrote:.*',
            r'From:.*',
            r'>.*',
            r'-----Original Message-----.*',
            r'Sent from my iPhone',
            r'Sent from my Android'
        ]
        cleaned = body
        for pattern in patterns:
            cleaned = re.split(pattern, cleaned, flags=re.IGNORECASE)[0]
        return cleaned.strip()

    @staticmethod
    def detect_sentiment(body: str) -> str:
        """Determine sentiment category: positive, neutral, negative, out_of_office, unsubscribe"""
        b_lower = body.lower()

        # Check Unsubscribe
        unsub_words = ['unsubscribe', 'remove me', 'opt out', 'stop emailing', 'take me off']
        if any(w in b_lower for w in unsub_words):
            return "unsubscribe"

        # Check Out Of Office
        ooo_words = ['out of office', 'ooo', 'automated response', 'auto-reply', 'on vacation', 'back in the office']
        if any(w in b_lower for w in ooo_words):
            return "out_of_office"

        # Check Positive Lead Intent
        pos_words = ['interested', 'yes', 'schedule', 'meeting', 'call', 'demo', 'book', 'talk next week', 'sounds good', 'send details']
        neg_words = ['not interested', 'no thanks', 'don\'t contact', 'pass', 'busy', 'spam']

        pos_score = sum(1 for w in pos_words if w in b_lower)
        neg_score = sum(1 for w in neg_words if w in b_lower)

        if pos_score > neg_score:
            return "positive"
        elif neg_score > pos_score:
            return "negative"

        return "neutral"

    def process_inbound_reply(
        self,
        prospect: Prospect,
        raw_body: str,
        subject: Optional[str] = None,
        activity_id: Optional[str] = None
    ) -> Reply:
        """Create a Reply object and update prospect status according to sentiment"""
        clean_content = self.clean_email_body(raw_body)
        sentiment = self.detect_sentiment(clean_content)

        requires_followup = sentiment in ["positive", "neutral"]

        reply = Reply(
            id=str(uuid.uuid4()),
            prospect_id=prospect.id,
            campaign_id=prospect.campaign_id,
            activity_id=activity_id,
            subject=subject,
            content=clean_content,
            sentiment=sentiment,
            requires_followup=requires_followup,
            processed=True,
            received_at=datetime.utcnow()
        )

        # Update prospect pipeline status based on sentiment
        prospect.replied_at = datetime.utcnow()
        if sentiment == "positive":
            prospect.status = ProspectStatus.QUALIFIED
        elif sentiment == "negative":
            prospect.status = ProspectStatus.NOT_INTERESTED
        elif sentiment == "unsubscribe":
            prospect.status = ProspectStatus.UNSUBSCRIBED
        else:
            prospect.status = ProspectStatus.REPLIED

        return reply
