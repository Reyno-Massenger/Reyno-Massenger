#!/usr/bin/env bash
# Free SSL certificate for a bare IP address (no domain) — like 3x-ui panels.
# Tries: 1) Let's Encrypt IP certificate via acme.sh (free, trusted, ~6-day
# short-lived cert, auto-renewed) 2) self-signed fallback (free, always works).
set -uo pipefail
IP="${1:-$(curl -s --max-time 8 https://api.ipify.org || hostname -I | awk '{print $1}')}"
[ -n "$IP" ] || { echo "Could not detect IP. Usage: bash scripts/ip-ssl.sh 1.2.3.4"; exit 1; }
CERT_DIR="${CERT_DIR:-/etc/reyno-ssl}"; sudo mkdir -p "$CERT_DIR"
echo "==> Getting a FREE certificate for IP: $IP"
if ! command -v acme.sh >/dev/null 2>&1 && [ ! -x "$HOME/.acme.sh/acme.sh" ]; then
  curl -s https://get.acme.sh | sh -s email="admin@$IP" >/dev/null 2>&1 || true
fi
ACME="$HOME/.acme.sh/acme.sh"; [ -x "$ACME" ] || ACME="$(command -v acme.sh || true)"
if [ -n "${ACME:-}" ]; then
  sudo systemctl stop nginx 2>/dev/null || true
  "$ACME" --issue --standalone -d "$IP" --server letsencrypt \
      --certificate-profile shortlived --days 6 2>/dev/null \
   || "$ACME" --issue --standalone -d "$IP" --server letsencrypt 2>/dev/null || true
  "$ACME" --install-cert -d "$IP" --key-file "$CERT_DIR/privkey.pem" \
      --fullchain-file "$CERT_DIR/fullchain.pem" \
      --reloadcmd "sudo systemctl reload nginx || true" 2>/dev/null || true
  sudo systemctl start nginx 2>/dev/null || true
fi
if [ ! -s "$CERT_DIR/fullchain.pem" ]; then
  echo "==> Trusted IP cert unavailable right now. Creating a FREE self-signed cert."
  echo "    https://$IP WILL work — visitors tap 'Advanced -> Continue' once."
  sudo openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
    -keyout "$CERT_DIR/privkey.pem" -out "$CERT_DIR/fullchain.pem" \
    -subj "/CN=$IP" -addext "subjectAltName=IP:$IP" >/dev/null 2>&1
fi
sudo chmod 600 "$CERT_DIR/privkey.pem" || true
echo "==> Ready: $CERT_DIR/fullchain.pem (auto-renew cron installed by acme.sh)"
