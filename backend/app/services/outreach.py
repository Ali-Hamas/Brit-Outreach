import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from jinja2 import Template
import redis

from app.db.models import Prospect, Campaign, SMTPConfig, OutreachActivity, ProspectStatus
from app.core.config import settings

class SMTPRouter:
    """Routes emails through business SMTP servers with rate-limiting using Redis or in-memory fallback"""

    def __init__(self):
        try:
            self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False
            self.in_memory_counts = {}

    def check_and_increment_daily_limit(self, smtp_config: SMTPConfig) -> Tuple[bool, int]:
        """Verify daily sending limit for the specific SMTP config and increment count if valid"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"smtp:{smtp_config.id}:count:{today}"

        if self.use_redis:
            current = int(self.redis_client.get(key) or 0)
            if current >= smtp_config.daily_limit:
                return False, current
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 86400)
            pipe.execute()
            return True, current + 1
        else:
            current = self.in_memory_counts.get(key, 0)
            if current >= smtp_config.daily_limit:
                return False, current
            self.in_memory_counts[key] = current + 1
            return True, current + 1

    def send_email(
        self,
        smtp_config: SMTPConfig,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        tracking_id: str
    ) -> bool:
        """Send personalized email via configured business SMTP"""
        can_send, count = self.check_and_increment_daily_limit(smtp_config)
        if not can_send:
            print(f"[SMTPRouter] Daily send limit ({smtp_config.daily_limit}) reached for SMTP: {smtp_config.name}")
            return False

        # Inject 1x1 open tracking pixel
        tracking_pixel = f'<img src="{settings.BASE_TRACKING_URL}/api/v1/tracking/{tracking_id}/open" width="1" height="1" style="display:none;" />'
        full_html = body_html + tracking_pixel

        # Inject click tracking links
        full_html = self._add_click_tracking(full_html, tracking_id)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{smtp_config.from_name} <{smtp_config.from_email}>"
        msg['To'] = to_email

        msg.attach(MIMEText(body_text or "", 'plain'))
        msg.attach(MIMEText(full_html, 'html'))

        # Send email via real SMTP
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=10) as server:
                server.starttls(context=context)
                server.login(smtp_config.username, smtp_config.password)
                server.sendmail(smtp_config.from_email, to_email, msg.as_string())
            print(f"[SMTPRouter] Sent email to {to_email} via {smtp_config.from_email}. Tracking ID: {tracking_id}")
            return True
        except Exception as e:
            print(f"[SMTPRouter Error] Failed sending to {to_email}: {e}")
            return False

    def _add_click_tracking(self, html: str, tracking_id: str) -> str:
        """Rewrite standard HTML href links with tracking endpoint redirect"""
        def replace_link(match):
            original_url = match.group(1)
            # Skip replacing tracking URLs themselves
            if "/tracking/" in original_url:
                return match.group(0)
            tracked_url = f"{settings.BASE_TRACKING_URL}/api/v1/tracking/{tracking_id}/click?url={original_url}"
            return f'href="{tracked_url}"'

        return re.sub(r'href="(https?://[^"]+)"', replace_link, html)


class PersonalizationEngine:
    """Renders personalized templates using prospect attributes"""

    @staticmethod
    def personalize(template_str: str, prospect: Prospect, extra_vars: Optional[Dict[str, Any]] = None) -> str:
        if not template_str:
            return ""

        context = {
            "first_name": prospect.first_name or "there",
            "last_name": prospect.last_name or "",
            "full_name": f"{prospect.first_name or ''} {prospect.last_name or ''}".strip() or "there",
            "title": prospect.title or "",
            "company": prospect.company or "your company",
            "industry": prospect.industry or "your industry",
            "location": prospect.location or "",
            "website": prospect.website or "",
            "email": prospect.email
        }
        if extra_vars:
            context.update(extra_vars)

        try:
            template = Template(template_str)
            return template.render(**context)
        except Exception as e:
            print(f"[Personalization Error] Failed rendering template: {e}")
            return template_str
