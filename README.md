# Brit Outreach System

Unified lead generation and outreach system for Ascentra Global businesses. Combines prospecting, lead scoring, website auditing, social listening, email outreach, and CRM management in one platform.

## Features

- **Multi-Business Support** — Isolated SMTP configs, campaigns, and prospect pools per business
- **Prospecting Engine** — Apollo.io integration for lead discovery with deduplication
- **Lead Scoring** — ICP-fit scoring (0-100) based on title, company size, industry, location, technology
- **Website Audit** — SSL, mobile-friendliness, PageSpeed, Core Web Vitals, tech stack detection
- **Social Listening** — Reddit search, Google Custom Search across platforms (LinkedIn, Twitter/X, forums)
- **AI Reply Drafting** — Groq-powered social comment/DM generation
- **Email Outreach** — Multi-step sequences with SMTP routing, rate limiting, open/click tracking
- **Reply Processing** — Sentiment detection, unsubscribe handling, out-of-office detection
- **CRM Integration** — Internal CRM with optional HubSpot sync

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
│  /api/v1/businesses | /smtp | /campaigns | /prospects | /social │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Prospecting  │      │   Scoring    │      │   Outreach   │
│   Engine     │─────▶│   Engine     │─────▶│   Engine     │
│              │      │              │      │              │
│ • Apollo.io  │      │ • ICP Fit    │      │ • SMTP Router│
│ • Google     │      │ • Title      │      │ • Sequences  │
│ • Reddit     │      │ • Industry   │      │ • Tracking   │
│ • Google CSE │      │ • Location   │      │ • Personalize│
└──────────────┘      └──────────────┘      └──────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    PostgreSQL     │
                    │   (CRM + Data)    │
                    └───────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis 6+

### Installation

```bash
# Clone and setup
cd "Brit Outreach System"
python -m venv .venv
.venv\Scripts\Activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install backend dependencies
cd backend
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `backend/.env`
2. Fill in your API keys and database credentials
3. Required for basic operation:
   - `POSTGRES_*` — Database connection
   - `APOLLO_API_KEY` — For lead prospecting
   - `GROQ_API_KEY` — For AI reply drafting

### Running

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: `http://localhost:8000/docs`

## API Endpoints

### Core Resources

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/businesses` | CRUD | Manage business profiles |
| `/api/v1/smtp` | CRUD | Configure SMTP servers per business |
| `/api/v1/target-markets` | CRUD | Define ICP filters |
| `/api/v1/campaigns` | CRUD | Create/manage outreach campaigns |
| `/api/v1/prospects` | CRUD | View/manage leads |
| `/api/v1/tracking/{id}/open` | GET | Email open tracking pixel |
| `/api/v1/tracking/{id}/click` | GET | Email click tracking redirect |

### Social Listening

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/social-listening/reddit/search` | POST | Search Reddit for leads |
| `/api/v1/social-listening/google/search` | POST | Google CSE cross-platform search |
| `/api/v1/social-listening/draft-reply` | POST | AI-draft reply for social posts |
| `/api/v1/social-listening/reddit/defaults` | GET | Get default subreddits/keywords |

## Environment Variables

See `.env.example` for full list. Key variables:

| Variable | Purpose | Required |
|----------|---------|----------|
| `POSTGRES_*` | Database connection | Yes |
| `APOLLO_API_KEY` | Lead prospecting | For prospecting |
| `GROQ_API_KEY` | AI reply drafting | For social listening |
| `REDDIT_CLIENT_ID/SECRET` | Reddit search | For Reddit listening |
| `GOOGLE_CUSTOM_SEARCH_API_KEY` | Google CSE search | For cross-platform search |
| `GOOGLE_PLACES_API_KEY` | Business search | For local business leads |

## Project Structure

```
backend/
├── app/
│   ├── api/                    # FastAPI route handlers
│   │   ├── businesses.py
│   │   ├── campaigns.py
│   │   ├── prospects.py
│   │   ├── social_listening.py # Reddit, Google CSE, AI replies
│   │   ├── tracking.py
│   │   └── ...
│   ├── core/
│   │   └── config.py           # Settings & env vars
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── session.py          # DB session
│   │   └── seed_data.py        # Default data
│   ├── services/
│   │   ├── lead_discovery/     # Prospecting, audit, social
│   │   │   ├── places.py       # Google Places search
│   │   │   ├── audit.py        # Website auditing
│   │   │   ├── scoring.py      # Lead scoring
│   │   │   ├── reddit_service.py
│   │   │   ├── google_cse_service.py
│   │   │   └── groq_service.py
│   │   ├── outreach.py         # SMTP routing, personalization
│   │   ├── scoring.py          # ICP-fit scoring
│   │   ├── replies.py          # Reply processing
│   │   └── prospecting.py      # Apollo integration
│   ├── workers/                # Celery tasks
│   └── main.py                 # App entrypoint
├── requirements.txt
└── Dockerfile
```

## Data Models

- **Business** — Company profile (name, domain)
- **SMTPConfig** — Email server settings per business
- **TargetMarket** — ICP definition (filters, exclusions)
- **Campaign** — Outreach campaign with sequence config
- **Prospect** — Lead with contact info, score, status
- **OutreachActivity** — Email send log with tracking
- **Reply** — Inbound reply with sentiment

## Campaign Workflow

1. Create Business → Configure SMTP → Define Target Market
2. Create Campaign with sequence steps and settings
3. System discovers leads from Apollo/sources
4. Leads scored against ICP criteria
5. Qualified leads enter outreach sequence
6. Emails sent via correct SMTP with tracking
7. Replies processed, sentiment detected
8. Follow-ups scheduled automatically

## License

Private — Ascentra Global Ltd.
