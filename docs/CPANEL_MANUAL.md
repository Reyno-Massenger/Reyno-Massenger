# Manual cPanel installation — no Terminal, no commands 🖱️

> **You never need to type a single command in this guide.** Everything is done by
> clicking buttons in cPanel. It takes about **10–15 minutes**. If your hosting plan
> hides any button mentioned here, send your host a support ticket saying:
> *“Please enable Python Selector / Setup Python App for my account.”*

---

## Before you start — what you need

| Thing | Where to get it | Cost |
|---|---|---|
| A cPanel hosting account with **Python** support | Your hosting company | You already have it |
| This project as a **ZIP file** | GitHub → green **Code** button → **Download ZIP** | Free |
| A domain or subdomain, e.g. `chat.yourdomain.com` | cPanel → **Subdomains** → Create | Free |

> 💡 No domain? On shared cPanel hosting you usually cannot use a bare IP.
> A free subdomain from your host works fine. On a VPS, use `install.sh` instead.

---

## Step 1 — Create a subdomain (2 minutes)

1. Log in to **cPanel**.
2. Open **Subdomains**.
3. Type `chat`, pick your domain, click **Create**.

## Step 2 — Upload the project (3 minutes)

1. Open **File Manager**.
2. Go into the folder of your subdomain (usually `public_html/chat` or a folder named after the subdomain).
3. Click **Upload** (top menu) and choose the ZIP file you downloaded.
4. Go back, click the ZIP file once, then click **Extract** at the top.
5. You should now see folders like `backend`, `docs`, `assets`. ✅

## Step 3 — Create the Python app (3 minutes)

1. Go back to the cPanel home page and open **Setup Python App**
   (on some hosts it is called **Python Selector** → **Applications**).
2. Click **Create Application**.
3. Fill the form:
   - **Python version:** pick the newest (3.11 or higher)
   - **Application root:** the folder from Step 2, e.g. `public_html/chat/backend`  ← the folder that contains `passenger_wsgi.py`
   - **Application URL:** your subdomain, e.g. `chat.yourdomain.com`
   - **Application startup file:** `passenger_wsgi.py`
   - **Application entry point:** `application`
4. Click **Create**.

## Step 4 — Install the required packages (2 minutes, still no Terminal!)

1. On the same **Setup Python App** page, find **Configuration files**.
2. Type `requirements.txt` in the box and click **Add**.
3. Click **Run Pip Install** → choose `requirements.txt` → **Run**.
4. Wait for the green success message. ✅

## Step 5 — Set your private settings (2 minutes)

Still on the same page, find **Environment variables** and add these, one by one
(click **Add variable** for each). Think of them as the app's control panel:

| Name | Value (example) | What it means, in plain words |
|---|---|---|
| `ADMIN_USERNAME` | `admin` | Username for the hidden admin page |
| `ADMIN_PASSWORD` | *(a long password only you know, min 8 chars)* | Password for the admin page — **never share it** |
| `SECRET_KEY` | *(press a password-generator site and paste 40+ random characters)* | A secret lock for messages stored on the server |
| `JWT_SECRET_KEY` | *(another different long random text)* | A secret lock for login sessions |
| `SESSION_COOKIE_SECURE` | `false` | Set to `true` only after HTTPS (Step 7) works |
| `FORCE_HTTPS` | `false` | Keep `false` so the site also works on plain HTTP |

Click **Save** at the top when finished.

## Step 6 — Start the app (30 seconds)

1. On the same page, click **Restart**.
2. Open `http://chat.yourdomain.com` in your browser.
3. You should see the **Reyno Messenger Lite** login screen. 🎉
4. The admin page is at `http://chat.yourdomain.com/admin`
   (it can only add/remove users and free up storage — nothing else).

> **First test:** create two accounts in two browser windows, search the other
> person's `@username`, and send a message. Photo/video/voice *files* are
> automatically removed after **72 hours** — chats and messages always stay.

## Step 7 — Free HTTPS lock 🔒 (optional, 2 minutes)

HTTPS makes the connection private. It is **recommended but not required** —
Reyno Lite works fully on plain HTTP too (important if the internet becomes
national-only).

**Option A — AutoSSL (most cPanel hosts):**
1. cPanel → **SSL/TLS Status** → tick your subdomain → **Run AutoSSL**.
2. Wait 2–5 minutes. Done — the certificate renews itself for free.

**Option B — Let's Encrypt in cPanel (if shown):**
1. cPanel → **Let's Encrypt™ SSL** → find your subdomain → **Issue**.
2. Keep the default options → **Issue**.

**After HTTPS works:**
1. Go back to **Setup Python App** → set `SESSION_COOKIE_SECURE` to `true` → **Save** → **Restart**.
2. *(Optional)* cPanel → **Domains** → turn **Force HTTPS Redirect** on.
   Skip this if you want HTTP to keep working as a fallback!

## Step 8 — Automatic cleanup every hour (2 minutes, clicking only)

This removes photo/video/voice *files* older than 72 hours even while you sleep (chats and messages are never deleted):

1. cPanel → **Cron Jobs**.
2. Under **Add New Cron Job**, choose **Once Per Hour** from the *Common Settings* dropdown.
3. In the **Command** box, paste the line shown on your **Setup Python App** page.
   It looks like this (your path will differ — copy it from that page's example):

   ```
   /home/YOURNAME/virtualenv/public_html/chat/backend/3.11/bin/python /home/YOURNAME/public_html/chat/backend/scripts/retention_maintenance.py
   ```

   > How to build this line without typing commands: on the **Setup Python App**
   > page cPanel shows your virtualenv path; copy it, add `/bin/python`, then a
   > space, then your project path + `/backend/scripts/retention_maintenance.py`.
4. Click **Add New Cron Job**. ✅

## If something goes wrong 😟

| What you see | What to do (still no Terminal) |
|---|---|
| White page / “Error 503” | Setup Python App → **Restart**. Wait 1 minute, refresh. |
| Still 503 after restart | Setup Python App page shows an error log link — open it and check the last lines; the usual cause is a missing environment variable from Step 5. |
| Packages failed to install | Repeat Step 4 and click **Run Pip Install** again. |
| Page opens but login fails | Make sure you clicked **Save** after Step 5, then **Restart**. |
| Photos won't upload | File Manager → check the `backend/uploads` folder exists; create it if not. |
| Everything worked, then broke after host changes | Setup Python App → **Restart** fixes most cases. |

Still stuck? Open an issue on GitHub and paste (a photo of) the error log —
**never** paste your `ADMIN_PASSWORD` or secret keys.
