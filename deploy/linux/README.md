# Deploy (Linux VM)

This repo can run as 2 background services + optional Streamlit dashboard:

- `main_bot.py` (pipeline worker)
- `telegram_chatbot.py` (interactive Telegram bot)
- `dashboard/main_dashboard.py` (optional Streamlit dashboard)

## Recommended approach

Run bots on an always-on VM (Ubuntu). Dashboard can be:
- On the same VM (simple, one place), or
- Hosted separately (Streamlit Community / any web host) while bots stay on the VM.

## Quick setup (Ubuntu)

1) Install system deps:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

2) Clone repo:

```bash
git clone https://github.com/<YOU>/<REPO>.git
cd <REPO>
```

3) Create venv + install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4) Create `.env` on the VM (DO NOT COMMIT):

```bash
nano .env
```

Add at least:

- `TELEGRAM_TOKEN=...`
- `CHANNEL_ID=...`
- `ADMIN_USER_ID=624875667`
- `GROQ_API_KEY=...`
- plus Blogger/Dev.to/Facebook keys if you publish there.

5) Copy systemd unit files:

```bash
sudo cp deploy/linux/systemd/contentorbit-bot.service /etc/systemd/system/
sudo cp deploy/linux/systemd/contentorbit-chatbot.service /etc/systemd/system/
# optional dashboard
sudo cp deploy/linux/systemd/contentorbit-dashboard.service /etc/systemd/system/
```

6) Edit unit files to set the correct paths:

```bash
sudo nano /etc/systemd/system/contentorbit-bot.service
sudo nano /etc/systemd/system/contentorbit-chatbot.service
sudo nano /etc/systemd/system/contentorbit-dashboard.service
```

You must update:
- `WorkingDirectory=/opt/contentorbit` (or your actual repo path)
- `ExecStart=.../python ...` (your venv python path)

7) Start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now contentorbit-bot
sudo systemctl enable --now contentorbit-chatbot
# optional
sudo systemctl enable --now contentorbit-dashboard
```

8) Logs:

```bash
journalctl -u contentorbit-bot -f
journalctl -u contentorbit-chatbot -f
journalctl -u contentorbit-dashboard -f
```

## Public dashboard (no paid domain required)

You have two good options:

### Option A: Public via VM IP (HTTP)

This is the simplest when you don't own a domain.

- You will access the dashboard via the VM external IP.
- HTTPS via Let's Encrypt is not available without a domain.
- Keep the dashboard behind a password (`DASHBOARD_PASSWORD`).

**Recommended:** expose via Nginx on port 80 (so the URL is `http://<EXTERNAL_IP>/`) and keep Streamlit bound to localhost.

1) Install Nginx:

```bash
sudo apt-get update
sudo apt-get install -y nginx
```

2) Ensure Streamlit is running locally (systemd unit uses `:8501`):

```bash
sudo systemctl enable --now contentorbit-dashboard
```

3) Enable Nginx reverse proxy (IP-based):

```bash
sudo cp deploy/linux/nginx/contentorbit-dashboard.conf /etc/nginx/sites-available/contentorbit-dashboard
sudo ln -s /etc/nginx/sites-available/contentorbit-dashboard /etc/nginx/sites-enabled/contentorbit-dashboard
sudo nginx -t
sudo systemctl restart nginx
```

4) Google Cloud Firewall rules:

- Allow inbound `tcp:80` to the VM.
- Do NOT expose `8501` publicly (keep it only for localhost).

Open the dashboard at:

- `http://<EXTERNAL_IP>/`

### Option B: Free subdomain + HTTPS (DuckDNS)

If you want HTTPS without buying a domain, use a free DNS provider like DuckDNS.

High level:
- Create a free subdomain like `yourname.duckdns.org`.
- Point it to your VM external IP.
- Set `server_name yourname.duckdns.org;` in the Nginx config.
- Run certbot to issue HTTPS.

### Option C: Public on a domain with HTTPS

If you have a domain/subdomain:

1) Install Nginx + certbot:

```bash
sudo apt-get update
sudo apt-get install -y nginx
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

1) Put Streamlit on port 8501 (already done in the systemd unit):

- Ensure the service is running:

```bash
sudo systemctl enable --now contentorbit-dashboard
sudo systemctl status contentorbit-dashboard
```

2) Add Nginx reverse-proxy config:

```bash
sudo cp deploy/linux/nginx/contentorbit-dashboard.conf /etc/nginx/sites-available/contentorbit-dashboard
sudo nano /etc/nginx/sites-available/contentorbit-dashboard
```

Replace `server_name _;` with your domain.

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/contentorbit-dashboard /etc/nginx/sites-enabled/contentorbit-dashboard
sudo nginx -t
sudo systemctl restart nginx
```

3) Get HTTPS certificate:

```bash
sudo certbot --nginx -d example.com
```

4) Google Cloud Firewall rules:

- Allow inbound `tcp:80` and `tcp:443` to the VM.
- Do NOT expose `8501` publicly (keep it only for localhost).

## Important security note

- Keep the dashboard behind a password (`DASHBOARD_PASSWORD` in `.env`).
- If any tokens were ever shared publicly, rotate them.

## Security notes

- Never commit `.env`.
- Keep `data/config.json` untracked (repo already ignores it). Use env vars.
- If you shared tokens publicly, rotate them.
