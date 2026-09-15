import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class ProspectStatus(str, enum.Enum):
    NEW = "new"
    SCORED = "scored"
    CONTACTED = "contacted"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    QUALIFIED = "qualified"
    MEETING_BOOKED = "meeting_booked"
    NOT_INTERESTED = "not_interested"

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    smtp_configs = relationship("SMTPConfig", back_populates="business", cascade="all, delete-orphan")
    target_markets = relationship("TargetMarket", back_populates="business", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="business", cascade="all, delete-orphan")
    prospects = relationship("Prospect", back_populates="business", cascade="all, delete-orphan")


class SMTPConfig(Base):
    __tablename__ = "smtp_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "BritSync Sales"
    host = Column(String, nullable=False)
    port = Column(Integer, default=587)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    from_email = Column(String, nullable=False)
    from_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    daily_limit = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="smtp_configs")
    campaigns = relationship("Campaign", back_populates="smtp_config")


class TargetMarket(Base):
    __tablename__ = "target_markets"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)
    filters = Column(JSON, nullable=False, default={})  # {industries, company_size, titles, locations, tech}
    exclusion_filters = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="target_markets")
    campaigns = relationship("Campaign", back_populates="target_market")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    smtp_config_id = Column(String, ForeignKey("smtp_configs.id"), nullable=False)
    target_market_id = Column(String, ForeignKey("target_markets.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    sequence_config = Column(JSON, nullable=False, default={})  # Steps, delays, template subjects & bodies
    settings = Column(JSON, nullable=True, default={"max_leads_per_day": 50, "score_threshold": 60})
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="campaigns")
    smtp_config = relationship("SMTPConfig", back_populates="campaigns")
    target_market = relationship("TargetMarket", back_populates="campaigns")
    prospects = relationship("Prospect", back_populates="campaign")
    activities = relationship("OutreachActivity", back_populates="campaign")
    replies = relationship("Reply", back_populates="campaign")


class Prospect(Base):
    __tablename__ = "prospects"
    __table_args__ = (UniqueConstraint("business_id", "email", name="uq_business_prospect_email"),)

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)

    email = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    company_size = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    location = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    raw_data = Column(JSON, nullable=True, default={})
    score = Column(Integer, default=0)
    score_breakdown = Column(JSON, nullable=True, default={})
    status = Column(SQLEnum(ProspectStatus), default=ProspectStatus.NEW)

    last_contacted_at = Column(DateTime, nullable=True)
    contact_count = Column(Integer, default=0)
    last_email_subject = Column(String, nullable=True)

    email_opens = Column(Integer, default=0)
    email_clicks = Column(Integer, default=0)
    replied_at = Column(DateTime, nullable=True)

    source = Column(String, nullable=True)  # apollo, linkedin, manual, csv
    source_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="prospects")
    campaign = relationship("Campaign", back_populates="prospects")
    activities = relationship("OutreachActivity", back_populates="prospect", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="prospect", cascade="all, delete-orphan")


class OutreachActivity(Base):
    __tablename__ = "outreach_activities"

    id = Column(String, primary_key=True, default=generate_uuid)
    prospect_id = Column(String, ForeignKey("prospects.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    step_number = Column(Integer, nullable=False, default=1)
    email_subject = Column(String, nullable=False)
    email_body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    tracking_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="sent")  # sent, opened, clicked, replied, bounced

    prospect = relationship("Prospect", back_populates="activities")
    campaign = relationship("Campaign", back_populates="activities")


class Reply(Base):
    __tablename__ = "replies"

    id = Column(String, primary_key=True, default=generate_uuid)
    prospect_id = Column(String, ForeignKey("prospects.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    activity_id = Column(String, ForeignKey("outreach_activities.id"), nullable=True)
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    sentiment = Column(String, nullable=True)  # positive, neutral, negative, unsubscribe, out_of_office
    ai_summary = Column(Text, nullable=True)
    requires_followup = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    received_at = Column(DateTime, default=datetime.utcnow)

    prospect = relationship("Prospect", back_populates="replies")
    campaign = relationship("Campaign", back_populates="replies")
