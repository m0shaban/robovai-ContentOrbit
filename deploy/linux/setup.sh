#!/bin/bash

# ContentOrbit VM Setup Script
# Usage: ./deploy/linux/setup.sh

echo "🚀 Starting Setup..."

# 1. System Updates & Dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git nginx

# 2. Certbot (SSL) Support
echo "🔒 Installing Certbot..."
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# 3. Python Environment
echo "🐍 Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Systemd Services Setup
echo "⚙️  Configuring services..."
# Adjust paths in service files to current directory
CURRENT_DIR=$(pwd)
sudo sed -i "s|/opt/contentorbit|$CURRENT_DIR|g" deploy/linux/systemd/*.service

sudo cp deploy/linux/systemd/contentorbit-bot.service /etc/systemd/system/
sudo cp deploy/linux/systemd/contentorbit-chatbot.service /etc/systemd/system/
sudo cp deploy/linux/systemd/contentorbit-dashboard.service /etc/systemd/system/

# 5. Nginx Setup
echo "bw  Configuring Nginx..."
sudo cp deploy/linux/nginx/contentorbit-dashboard.conf /etc/nginx/sites-available/contentorbit-dashboard
# Remove default if exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi
# Link new config if not linked
if [ ! -f /etc/nginx/sites-enabled/contentorbit-dashboard ]; then
    sudo ln -s /etc/nginx/sites-available/contentorbit-dashboard /etc/nginx/sites-enabled/contentorbit-dashboard
fi
sudo nginx -t
sudo systemctl restart nginx

# 6. Env File
if [ ! -f .env ]; then
    echo "⚠️  Creating empty .env file..."
    touch .env
    echo "ADMIN_USER_ID=624875667" >> .env
    echo "TELEGRAM_TOKEN=" >> .env
    echo "# Add your other keys here" >> .env
fi

sudo systemctl daemon-reload

echo "✅ Setup Complete!"
echo "-----------------------------------------------------"
echo "Next Steps:"
echo "1. Edit your secrets:  nano .env"
echo "2. Start services:"
echo "   sudo systemctl enable --now contentorbit-bot contentorbit-chatbot contentorbit-dashboard"
echo "-----------------------------------------------------"
