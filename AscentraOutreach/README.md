# Ascentra Global - Outreach System

## Quick Start (3 steps)

### Step 1: Setup Campaigns
```powershell
cd "M:\Brit Outreach System\backend"
python ../AscentraOutreach/setup.py
```

### Step 2: Start Backend
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Start Frontend
```powershell
cd ../frontend
npm run dev
```

Open: **http://localhost:3000**

---

## What You Get

| Campaign | What It Does | Daily Limit |
|----------|-------------|-------------|
| AI Consultancy | Sell AI strategy | 100 emails |
| TalentBridge | Find remote engineers | 100 emails |
| Biometric Sign Up | Passwordless login (free) | 100 emails |
| Sentrivault | NHS cybersecurity (£990) | 100 emails |

**All emails sent from:** info@ascentraconsulting.co.uk

---

## How To Use

1. Go to **Campaigns** tab
2. Click **Upload CSV** to add leads
3. Click **Launch** to send emails
4. Check **Prospects** tab to see results

---

## Files

| File | What It Does |
|------|-------------|
| `config/campaigns.json` | All campaign settings |
| `setup.py` | One-click setup |
| `templates/` | Email templates |

---

## Need Help?

Just run: `python setup.py` — it does everything automatically.
