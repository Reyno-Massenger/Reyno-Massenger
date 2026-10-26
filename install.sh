#!/usr/bin/env bash
set -euo pipefail
echo "=== Reyno Messenger Lite — easy installer (Ubuntu/Debian) ==="
echo "How do you want people to open your site?"
echo "  1) I have a domain name        -> free trusted SSL (recommended)"
echo "  2) No domain — use server IP   -> free SSL for the IP (like 3x-ui)"
echo "  3) No SSL at all — plain HTTP  -> works everywhere, incl. Iran national network"
read -rp "Choose 1, 2 or 3 [3]: " MODE || true; MODE=${MODE:-3}
DOMAIN=""; IP=""
if [ "$MODE" = "1" ]; then read -rp "Your domain (e.g. chat.example.com): " DOMAIN; fi
if [ "$MODE" = "2" ]; then IP=$(curl -s --max-time 8 https://api.ipify.org || hostname -I | awk '{print $1}'); echo "Your server IP: $IP"; fi
read -rp "Admin username [admin]: " ADMIN_USER || true; ADMIN_USER=${ADMIN_USER:-admin}
read -rsp "Admin password (min 8 chars): " ADMIN_PASS; echo
[ ${#ADMIN_PASS} -ge 8 ] || { echo "Admin password too short"; exit 1; }
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip nginx certbot python3-certbot-nginx curl openssl >/dev/null
cd "$(dirname "$0")"
python3 -m venv .venv; .venv/bin/pip install -q -r backend/requirements.txt gunicorn
SECRET=$(python3 -c "import secrets;print(secrets.token_hex(32))"); JWT=$(python3 -c "import secrets;print(secrets.token_hex(32))")
# HTTP mode: cookies must NOT require HTTPS, and HTTPS is never forced.
if [ "$MODE" = "3" ]; then COOKIE=false; else COOKIE=true; fi
cat > backend/.env <<ENVEOF
DATABASE_URL=sqlite:///$PWD/backend/reyno_lite.db
SECRET_KEY=$SECRET
JWT_SECRET_KEY=$JWT
ADMIN_USERNAME=$ADMIN_USER
ADMIN_PASSWORD=$ADMIN_PASS
UPLOAD_FOLDER=$PWD/backend/uploads
SESSION_COOKIE_SECURE=$COOKIE
FORCE_HTTPS=false
ENVEOF
mkdir -p backend/uploads
cat > /tmp/reyno.service <<SVCEOF
[Unit]
Description=Reyno Messenger Lite
After=network.target
[Service]
WorkingDirectory=$PWD/backend
EnvironmentFile=$PWD/backend/.env
ExecStart=$PWD/.venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 run:app
Restart=always
User=$USER
[Install]
WantedBy=multi-user.target
SVCEOF
sudo cp /tmp/reyno.service /etc/systemd/system/reyno.service
sudo systemctl daemon-reload; sudo systemctl enable --now reyno
(crontab -l 2>/dev/null | grep -v retention_maintenance; echo "17 * * * * $PWD/.venv/bin/python $PWD/backend/scripts/retention_maintenance.py >> /tmp/reyno-retention.log 2>&1") | crontab -
SERVER_NAME=${DOMAIN:-_}
sudo tee /etc/nginx/sites-available/reyno >/dev/null <<NGXEOF
server { listen 80; server_name $SERVER_NAME; client_max_body_size 26m;
 location / { proxy_pass http://127.0.0.1:5000; proxy_set_header Host \$host; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto \$scheme; } }
NGXEOF
sudo ln -sf /etc/nginx/sites-available/reyno /etc/nginx/sites-enabled/reyno
sudo nginx -t && sudo systemctl reload nginx
URL="http://${IP:-YOUR_SERVER_IP}/"
if [ "$MODE" = "1" ]; then
  sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN" --redirect \
    && URL="https://$DOMAIN/" || echo "SSL failed (is DNS pointing here?) — site still works at http://$DOMAIN/"
elif [ "$MODE" = "2" ]; then
  bash scripts/ip-ssl.sh "$IP" || true
  if [ -s /etc/reyno-ssl/fullchain.pem ]; then
    sudo tee /etc/nginx/sites-available/reyno >/dev/null <<NGXEOF2
server { listen 80; server_name _; return 301 https://\$host\$request_uri; }
server { listen 443 ssl; server_name _; client_max_body_size 26m;
 ssl_certificate /etc/reyno-ssl/fullchain.pem; ssl_certificate_key /etc/reyno-ssl/privkey.pem;
 location / { proxy_pass http://127.0.0.1:5000; proxy_set_header Host \$host; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto https; } }
NGXEOF2
    sudo nginx -t && sudo systemctl reload nginx && URL="https://$IP/"
  fi
fi
echo; echo "DONE. Open: $URL   Admin panel: ${URL}admin"
[ "$MODE" = "3" ] && echo "HTTP mode: no SSL needed. It also keeps working if the internet becomes national-only."
