# Complete VPS Deployment Guide

## What You're Deploying

| Component | What It Does |
|-----------|-------------|
| **Backend** | FastAPI server (API + email sending) |
| **Frontend** | React web app (user interface) |
| **Hermes Agent** | AI agent for automated outreach |
| **Database** | SQLite (no install needed) |

---

## Step 1: Buy a VPS

### Recommended Providers

| Provider | Cheapest Plan | Link |
|----------|--------------|------|
| **Hetzner** | €4.50/mo (2 vCPU, 4GB RAM) | hetzner.com |
| **Vultr** | $6/mo (1 vCPU, 1GB RAM) | vultr.com |
| **DigitalOcean** | $6/mo (1 vCPU, 1GB RAM) | digitalocean.com |

### What to Choose

- **OS:** Ubuntu 22.04 LTS
- **RAM:** 2GB minimum (4GB recommended)
- **Storage:** 25GB minimum
- **Location:** London or Frankfurt (for UK/EU)

### After Purchase

You'll get:
```
IP Address: 123.456.789.012
Username: root
Password: your_password
```

---

## Step 2: Connect to VPS

### On Windows (PowerShell)

```powershell
ssh root@123.456.789.012
```

Enter password when prompted.

---

## Step 3: Update System

```bash
apt update && apt upgrade -y
```

---

## Step 4: Install Required Software

```bash
# Install Python
apt install -y python3 python3-pip python3-venv

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Git
apt install -y git

# Verify installations
python3 --version
node --version
npm --version
```

---

## Step 5: Upload Your Code

### Option A: Using Git (Recommended)

```bash
# Create project folder
mkdir -p /var/www/outreach
cd /var/www/outreach

# Clone your repo (if you have one)
git clone https://github.com/yourusername/Brit-Outreach-System.git .

# OR upload files manually (see Option B)
```

### Option B: Upload Files Manually

On your Windows computer:

```powershell
# Using SCP (secure copy)
scp -r "M:\Brit Outreach System\*" root@123.456.789.012:/var/www/outreach/
```

---

## Step 6: Setup Backend

```bash
cd /var/www/outreach/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python -c "
import os
os.environ['DATABASE_URL'] = 'sqlite:///./brit_outreach.db'
from app.db.session import engine
from app.db.base import Base
from app.db.models import *
Base.metadata.create_all(bind=engine)
print('Database created!')
"

# Run setup script
cd /var/www/outreach
python backend/AscentraOutreach/setup.py
```

---

## Step 7: Setup Frontend

```bash
cd /var/www/outreach/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

---

## Step 8: Create Startup Script

```bash
cat > /var/www/outreach/start.sh << 'EOF'
#!/bin/bash
cd /var/www/outreach/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
cd /var/www/outreach/frontend
npm run preview -- --port 3000 &
echo "System started!"
echo "Backend: http://your-ip:8000"
echo "Frontend: http://your-ip:3000"
EOF

chmod +x /var/www/outreach/start.sh
```

---

## Step 9: Open Firewall Ports

```bash
# Allow HTTP and HTTPS
ufw allow 80
ufw allow 443
ufw allow 8000
ufw allow 3000
ufw enable
```

---

## Step 10: Start the System

```bash
cd /var/www/outreach
./start.sh
```

---

## Step 11: Access Your System

Open browser and go to:

```
http://123.456.789.012:3000
```

You should see the Ascentra Global outreach system!

---

## Step 12: Setup Hermes Agent (Optional)

Hermes is the AI agent that automates outreach. Follow these steps:

### Install Hermes

```bash
# Install uv (Hermes dependency manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Hermes
curl -LsSf https://nousresearch.com/hermes/install.sh | sh

# Verify
hermes --version
```

### Configure Hermes

```bash
# Create Hermes directory
mkdir -p ~/.hermes

# Copy campaign files
cp -r /var/www/outreach/Unified/skills ~/.hermes/
cp -r /var/www/outreach/Unified/memory ~/.hermes/
cp -r /var/www/outreach/Unified/cron ~/.hermes/

# Configure model
hermes model
# Select: OpenAI GPT-4o (recommended)

hermes config
# Paste your OpenAI API key
```

### Test Hermes

```bash
hermes

# In chat:
"Read the memory file at ~/.hermes/memory/unified_profile.md"
"Research 2 prospects for TalentBridge as a test"
```

---

## Step 12: Setup Auto-Start on Boot

```bash
# Create systemd service
cat > /etc/systemd/system/outreach.service << 'EOF'
[Unit]
Description=Outreach System
After=network.target

[Service]
Type=simple
WorkingDirectory=/var/www/outreach/backend
ExecStart=/var/www/outreach/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl enable outreach
systemctl start outreach

# Check status
systemctl status outreach
```

---

## Step 13: Setup Domain (Optional)

If you have a domain (e.g., outreach.ascentraconsulting.co.uk):

```bash
# Install Nginx
apt install -y nginx

# Configure Nginx
cat > /etc/nginx/sites-available/outreach << 'EOF'
server {
    listen 80;
    server_name outreach.ascentraconsulting.co.uk;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/outreach /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Restart Nginx
systemctl restart nginx
```

### Get Free SSL Certificate

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d outreach.ascentraconsulting.co.uk
```

---

## Quick Reference

| What | URL |
|------|-----|
| Frontend | http://your-ip:3000 |
| Backend API | http://your-ip:8000 |
| API Docs | http://your-ip:8000/docs |

---

## Troubleshooting

### System not starting?
```bash
# Check logs
journalctl -u outreach -f

# Restart
systemctl restart outreach
```

### Port already in use?
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it
kill -9 PID_NUMBER
```

### Can't connect from browser?
```bash
# Check firewall
ufw status

# Check if services are running
systemctl status outreach
```

---

## Summary

| Step | Command |
|------|---------|
| 1. Buy VPS | Ubuntu 22.04, 2GB RAM |
| 2. Connect | `ssh root@your-ip` |
| 3. Update | `apt update && apt upgrade -y` |
| 4. Install | Python, Node.js, Git |
| 5. Upload | `scp -r` or `git clone` |
| 6. Backend | `pip install -r requirements.txt` |
| 7. Frontend | `npm install && npm run build` |
| 8. Start | `./start.sh` |
| 9. Access | `http://your-ip:3000` |

**Done! Your outreach system is live.**
