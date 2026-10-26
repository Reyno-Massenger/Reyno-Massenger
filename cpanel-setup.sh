#!/usr/bin/env bash
set -euo pipefail
echo "=== Reyno Messenger Lite - cPanel / shared hosting ==="
echo "1) cPanel > Setup Python App > Create: Python 3.11, root = this folder/backend, startup file = passenger_wsgi.py, entry = application"
read -rp "Admin username [admin]: " ADMIN_USER || true; ADMIN_USER=${ADMIN_USER:-admin}
read -rsp "Admin password (min 8): " ADMIN_PASS; echo
python3 -m venv venv 2>/dev/null || virtualenv venv
venv/bin/pip install -q -r backend/requirements.txt || pip install -q -r backend/requirements.txt
SECRET=$(python3 -c "import secrets;print(secrets.token_hex(32))"); JWT=$(python3 -c "import secrets;print(secrets.token_hex(32))")
cat > backend/.env <<EOF
DATABASE_URL=sqlite:///$PWD/backend/reyno_lite.db
SECRET_KEY=$SECRET
JWT_SECRET_KEY=$JWT
ADMIN_USERNAME=$ADMIN_USER
ADMIN_PASSWORD=$ADMIN_PASS
UPLOAD_FOLDER=$PWD/backend/uploads
EOF
mkdir -p backend/uploads tmp; touch tmp/restart.txt
echo "2) SSL: cPanel > SSL/TLS > Let's Encrypt (free) > Issue for your domain, then Force HTTPS Redirect = ON"
echo "3) Cron: cPanel > Cron Jobs > hourly: $PWD/venv/bin/python $PWD/backend/scripts/retention_maintenance.py"
echo "DONE. Open your domain. Admin panel: /admin"
