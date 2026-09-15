# Hermes Agent Setup Guide

## What is Hermes?

Hermes is an AI agent that automates your outreach. It can:
- Research prospects
- Send personalized emails
- Manage your pipeline
- Run on autopilot

---

## Step 1: Get API Keys

### OpenAI API Key (Required)

1. Go to: https://platform.openai.com/api-keys
2. Sign up / Login
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. **Save it somewhere safe**

### Cost
- GPT-4o: ~$2.50 per 1M input tokens
- For outreach: ~$5-10/month

---

## Step 2: Install Hermes on VPS

```bash
# Connect to your VPS
ssh root@your-ip

# Install uv (Hermes dependency manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Hermes
curl -LsSf https://nousresearch.com/hermes/install.sh | sh

# Verify installation
hermes --version
```

---

## Step 3: Configure Hermes

```bash
# Start Hermes
hermes

# Select model (when prompted)
hermes model
# Choose: OpenAI GPT-4o

# Configure API key
hermes config
# Paste your OpenAI API key when prompted
```

---

## Step 4: Copy Campaign Files

```bash
# Create Hermes directories
mkdir -p ~/.hermes/skills
mkdir -p ~/.hermes/memory
mkdir -p ~/.hermes/cron

# Copy your campaign files
cp /var/www/outreach/Unified/00_UNIFIED_PROFILE.md ~/.hermes/memory/
cp /var/www/outreach/Unified/ASCENTRA_GROUP_PROFILE.md ~/.hermes/memory/
cp /var/www/outreach/Unified/SENTRAVAULT_ENTERPRISE_PROFILE.md ~/.hermes/memory/

# Copy skills
cp -r /var/www/outreach/Unified/skills/* ~/.hermes/skills/

# Copy cron jobs
cp /var/www/outreach/Unified/cron/* ~/.hermes/cron/
```

---

## Step 5: Test Hermes

```bash
# Start Hermes
hermes

# Test commands:
"Read the memory file at ~/.hermes/memory/unified_profile.md"
"Research 2 prospects for TalentBridge"
"Draft a cold email for AI Consultancy"
```

---

## Step 6: Setup Hermes as Background Service

```bash
# Create systemd service
cat > /etc/systemd/system/hermes.service << 'EOF'
[Unit]
Description=Hermes AI Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=/var/www/outreach
ExecStart=/root/.local/bin/hermes daemon
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl enable hermes
systemctl start hermes

# Check status
systemctl status hermes

# View logs
journalctl -u hermes -f
```

---

## Step 7: Configure Hermes Cron Jobs

Hermes runs tasks automatically. Configure in `~/.hermes/cron/`:

| File | What It Does |
|------|-------------|
| `daily_prospects.txt` | Research new leads daily |
| `daily_outreach.txt` | Send emails daily |
| `weekly_review.txt` | Review pipeline weekly |

### Edit Cron Jobs

```bash
# View current jobs
hermes cron list

# Add a job
hermes cron add "Research 10 prospects for TalentBridge every day at 9am"

# Remove a job
hermes cron remove JOB_ID
```

---

## Step 8: Connect Hermes to Backend

Hermes needs to talk to your backend API. Edit the memory file:

```bash
nano ~/.hermes/memory/unified_profile.md
```

Add this at the end:

```
API Configuration:
- Backend URL: http://localhost:8000
- API Token: (leave empty for now)
```

---

## Step 9: Monitor Hermes

### Check if Hermes is running

```bash
systemctl status hermes
```

### View Hermes logs

```bash
journalctl -u hermes -f
```

### Restart Hermes

```bash
systemctl restart hermes
```

### Stop Hermes

```bash
systemctl stop hermes
```

---

## Quick Commands

| Command | What It Does |
|---------|-------------|
| `hermes` | Start interactive chat |
| `hermes daemon` | Run as background service |
| `hermes model` | Change AI model |
| `hermes config` | Configure settings |
| `hermes cron list` | View scheduled tasks |
| `systemctl status hermes` | Check if running |
| `journalctl -u hermes -f` | View live logs |

---

## Troubleshooting

### "hermes: command not found"
```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

### "API key not configured"
```bash
hermes config
# Paste your OpenAI API key
```

### "Hermes not sending emails"
```bash
# Check backend is running
systemctl status outreach

# Test API
curl http://localhost:8000/docs
```

### "Hermes stopped working"
```bash
# Restart
systemctl restart hermes

# Check logs for errors
journalctl -u hermes -n 50
```

---

## Summary

| Step | Command |
|------|---------|
| 1. Get API key | https://platform.openai.com/api-keys |
| 2. Install | `curl -LsSf https://nousresearch.com/hermes/install.sh \| sh` |
| 3. Configure | `hermes model` + `hermes config` |
| 4. Copy files | `cp` campaign files to `~/.hermes/` |
| 5. Test | `hermes` |
| 6. Start service | `systemctl enable hermes` |

**Done! Hermes is now automating your outreach.**
