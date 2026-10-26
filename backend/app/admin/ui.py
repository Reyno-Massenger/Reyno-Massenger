"""Minimal privacy-preserving HTML templates for Reyno Messenger Lite Admin Panel.

Strictly limited to:
1. Adding or removing user accounts (without exposing any user private data, chats, or activity).
2. Clearing server storage space (72h expired data or full storage wipe).
"""

ADMIN_CSS = """
:root {
  --bg: #0f172a;
  --surface: #1e293b;
  --surface-2: #0b1324;
  --border: #334155;
  --primary: #0088cc;
  --primary-hover: #0ea5e9;
  --danger: #ef4444;
  --danger-hover: #dc2626;
  --text: #f8fafc;
  --muted: #94a3b8;
  --success: #10b981;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.5;
}
.container {
  max-width: 820px;
  margin: 0 auto;
  padding: 32px 20px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 24px;
  margin-bottom: 28px;
  border-bottom: 1px solid var(--border);
}
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}
.brand img {
  width: 42px;
  height: 42px;
  border-radius: 10px;
}
.brand h1 {
  font-size: 20px;
  font-weight: 700;
}
.brand p {
  font-size: 12.5px;
  color: var(--muted);
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}
.card h2 {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 6px;
}
.card .subtitle {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 18px;
}
.privacy-banner {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #6ee7b7;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  margin-bottom: 24px;
}
.alert {
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13.5px;
  margin-bottom: 20px;
  font-weight: 500;
}
.alert-success {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.4);
  color: #6ee7b7;
}
.alert-error {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #fca5a5;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
  align-items: end;
}
@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
}
label {
  display: block;
  font-size: 12.5px;
  color: var(--muted);
  margin-bottom: 6px;
  font-weight: 600;
}
input[type="text"], input[type="password"] {
  width: 100%;
  padding: 11px 14px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface-2);
  color: var(--text);
  font-size: 14px;
  outline: none;
}
input[type="text"]:focus, input[type="password"]:focus {
  border-color: var(--primary);
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 11px 18px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s ease;
  color: #fff;
}
.btn-primary { background: var(--primary); }
.btn-primary:hover { background: var(--primary-hover); }
.btn-danger { background: var(--danger); }
.btn-danger:hover { background: var(--danger-hover); }
.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
}
.btn-outline:hover {
  border-color: var(--text);
  color: var(--text);
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}
.stat-box {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px;
}
.stat-box .label {
  font-size: 12px;
  color: var(--muted);
}
.stat-box .value {
  font-size: 20px;
  font-weight: 700;
  margin-top: 4px;
}
.actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.login-wrap {
  max-width: 400px;
  margin: 80px auto;
}
"""
