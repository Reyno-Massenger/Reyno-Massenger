<div align="center">

<img src="assets/icons/reyno_logo.png" alt="Reyno Messenger Lite" width="420">

# 💬 Reyno Messenger Lite

### A free, private, lightweight messenger you host yourself — even without a domain

[![License](https://img.shields.io/badge/license-free%20to%20use-brightgreen)](#-license)
[![Python](https://img.shields.io/badge/backend-Flask%20%2B%20SQLite-blue)](backend/)
[![Deploy](https://img.shields.io/badge/deploy-VPS%20%7C%20cPanel-success)](#-install--choose-your-easy-way)
[![SSL](https://img.shields.io/badge/SSL-free%20(domain%2C%20IP%20or%20none)-orange)](#-ssl--three-free-choices)
[![Retention](https://img.shields.io/badge/auto--delete-every%2072h-red)](#-privacy-by-design)

**English** · [🇮🇷 فارسی — پایین همین صفحه](#-نسخه-فارسی)

[🚀 Install](#-install--choose-your-easy-way) · [📱 How to use](#-how-to-use-plain-language) · [🆚 Lite vs Full](#-lite-vs-full) · [❓ Help](#-troubleshooting-for-humans)

</div>

---

## 🌟 What is this, in plain words?

Reyno Messenger Lite is a chat website (like a small, private WhatsApp/Telegram)
that runs on **your own** server or hosting. You own it, you control it, and:

- 👤 People sign up with only a **username + password** — no phone number, no email
- 🕐 **Photos, videos & voice files delete themselves after 72 hours** — your chats and messages always stay
- 🆓 Everything is **completely free**: the software, the SSL lock, the hosting guides
- 🇮🇷 It works **with or without HTTPS**, and even on a **national-only network**,
  because it never needs to contact any outside service
- 🚫 No ads, no tracking, no company reading your chats

> **Who is it for?** Families, friends, small teams and communities in Iran and
> anywhere else who want a simple private messenger without giving their phone
> number to anyone.

---

## ✨ What it can do

| | |
|---|---|
| 💬 Text chats (one-to-one) | 👥 Groups & 📢 channels (create, add members, make admins) |
| 📷 Photos | 🎬 Videos **under 10 MB** |
| 🎤 Voice messages | 😀 Stickers & reactions ❤️ |
| 📍 Static location (a pin on a map) | ✏️ **Edit messages** — the edit shows for both sides |
| 🗑️ Delete a message **for yourself** | 🗂️ Archive chats, 📌 pin, 🔕 mute |
| 🔍 Search people by `@username`, groups & channels | 🟢 See who is online |
| 🚫 Block annoying users | 🎨 Light & dark themes |

> ⚠️ **By design, Lite can NOT delete a message for everyone.**
> Once you send it, the other side keeps their copy —
> you can only remove it from your own screen (and you can always **edit** it).
> “Delete for everyone” is a Full-version feature.

---

## 🚀 Install — choose your easy way

> 🧭 **You do NOT need to be a programmer.** Pick the row that describes you and
> follow it step by step. Every way below is free.

| You have… | Follow this | Time | Terminal needed? |
|---|---|---|---|
| A Linux VPS (Ubuntu) + a domain | [Way A](#way-a--vps-with-a-domain) | ~5 min | One copy-paste |
| A Linux VPS, **no domain** (just an IP like `185.2.3.4`) | [Way B](#way-b--vps-with-only-an-ip-address-no-domain) | ~5 min | One copy-paste |
| A Linux VPS, want it **as simple as possible** (plain HTTP) | [Way C](#way-c--vps-plain-http-no-ssl-at-all) | ~5 min | One copy-paste |
| cPanel shared hosting, you **like** the terminal | [`cpanel-setup.sh`](cpanel-setup.sh) | ~5 min | Yes |
| cPanel shared hosting, you **hate** terminals 🖱️ | [📖 Manual cPanel guide (click-only)](docs/CPANEL_MANUAL.md) | ~15 min | **Never** |

### Way A — VPS with a domain

1. Point your domain's **A record** to your server's IP (your domain provider shows you how; it is one small form).
2. Connect to your server and paste this one line:

```bash
git clone YOUR-REPO-URL reyno-lite && cd reyno-lite && bash install.sh
```

3. Choose **1**, type your domain, pick an admin username/password — the script does everything else, including the **free SSL lock** 🔒.

### Way B — VPS with only an IP address (no domain)

Just like panels such as **3x-ui**: you don't need to buy a domain at all.

```bash
git clone YOUR-REPO-URL reyno-lite && cd reyno-lite && bash install.sh
```

Choose **2**. The installer automatically gets a **free SSL certificate for your
IP address** ([`scripts/ip-ssl.sh`](scripts/ip-ssl.sh): a trusted Let's Encrypt
IP certificate that renews itself; if that is unavailable it creates a free
self-signed one — your site still opens at `https://YOUR-IP`, visitors may tap
“Advanced → Continue” once). Then just open:

```
https://YOUR-SERVER-IP/
```

### Way C — VPS, plain HTTP, no SSL at all

```bash
git clone YOUR-REPO-URL reyno-lite && cd reyno-lite && bash install.sh
```

Choose **3**. Done. Open `http://YOUR-SERVER-IP/`.

This mode exists on purpose: **if the internet ever becomes national-only**,
certificate websites abroad may be unreachable — your messenger keeps working
because it needs nothing from outside. (On your own private network the risk of
plain HTTP is small; on the open internet, Way A or B is safer.)

### 🖱️ cPanel without any terminal

Follow the friendly click-by-click guide: **[docs/CPANEL_MANUAL.md](docs/CPANEL_MANUAL.md)**
— upload a ZIP, press a few buttons, done. Full deployment details, SSL and
troubleshooting also live in **[docs/DEPLOY.md](docs/DEPLOY.md)**.

---

## 🔒 SSL — three free choices

| Choice | Address people open | Cost | Good to know |
|---|---|---|---|
| Domain + Let's Encrypt | `https://chat.example.com` | Free | Most trusted; renews itself |
| **IP certificate** (like 3x-ui) | `https://185.2.3.4` | Free | No domain needed; short-lived cert renews itself automatically |
| No SSL (HTTP) | `http://185.2.3.4` | Free | Works on national-only/LAN networks; chats are not encrypted on the wire |

**Honest note:** Reyno Lite encrypts stored messages on the server disk and
strips GPS/photo metadata, but it is **not** end-to-end encrypted like Signal.
HTTPS protects chats while they travel; the server owner could, in theory,
access stored data. For most communities this is fine — please don't oversell it.

---

## 📱 How to use (plain language)

1. Open your site and tap **Create account**. Pick a username (like `sara_2026`) and a password. That's it — no phone, no email, no profile photo.
2. To find a friend, type their `@username` in the search box at the top.
3. Tap their name → write a message → send. 📷 button sends a photo/video, 🎤 sends a voice message, 📍 sends your location pin.
4. Made a typo? **Edit** fixes it for both sides. Want it gone from *your* screen? **Delete for me**. (It stays on the other side — see the note above.)
5. The **ℹ️ button** opens group settings: add members, make someone an admin, archive the chat, or block a person.
6. Remember: **photos, videos and voice files disappear by themselves after 72 hours** (the message stays, marked “media expired”). Save any important *files* elsewhere — your text chats never vanish!

**Admin page:** open `YOUR-SITE/admin` and log in with the admin name/password
from installation. It can only do three things — **add a user, remove a user,
free up storage**. It cannot read anyone's messages.

---

## 🆚 Lite vs Full

| Feature | Lite (this, free) | Full Reyno |
|---|:---:|:---:|
| Text, photo, video (<10 MB), voice, stickers | ✅ | ✅ |
| Groups & channels, admins | ✅ | ✅ |
| Edit messages (visible to both sides) | ✅ | ✅ |
| **Delete for yourself** | ✅ | ✅ |
| **Delete for everyone** | ❌ | ✅ |
| Archive chats | ✅ | ✅ |
| Search `@ID` / groups / channels, online status, block users | ✅ | ✅ |
| Works on plain HTTP (national network ready) | ✅ | ✅ |
| Old photos/videos/voice files auto-removed after 72h (messages stay) | ✅ | ✅ |
| Phone-number sign-up, profiles/avatars/bio | ❌ | ✅ |
| Notifications, GIFs, documents, polls, secret chats | ❌ | ✅ |
| Ghost mode, 2FA, folders, scheduled/view-once messages | ❌ | ✅ |
| Price | **Free** | — |

---

## 🛟 Troubleshooting for humans

| Problem | Try this first |
|---|---|
| Site won't open | Is the address exactly right — `http://` vs `https://`? Try the other one. |
| “Video too large” | Videos must be **under 10 MB** — trim it or lower the quality. |
| I deleted a message but my friend still sees it | That's Lite by design — deletion is only for your own screen. Use **Edit** if you need to change what they see. |
| A photo/video older than 3 days won't open | That's the 72-hour media cleanup working as promised 🕐 — the message itself stays; only the file is removed. Chats and texts are never auto-deleted. |
| Forgot the admin password (VPS) | Edit `backend/.env`, change `ADMIN_PASSWORD`, restart: `sudo systemctl restart reyno` |
| Still stuck? | 📖 [docs/DEPLOY.md](docs/DEPLOY.md) · 🖱️ [docs/CPANEL_MANUAL.md](docs/CPANEL_MANUAL.md) · open a GitHub issue (never share your passwords!) |

---

## 📄 License

Free to use, copy and modify for your own community. The Reyno name and logo
belong to the Reyno project.

---
---

<div dir="rtl">

# 🇮🇷 نسخه فارسی

## رینو مسنجر لایت چیه؟ (به زبان خیلی ساده)

«رینو مسنجر لایت» یه پیام‌رسان کوچیک و خصوصیه (مثل واتس‌اپ یا تلگرام کوچولو) که روی سرور یا هاستِ **خودت** نصب می‌شه. یعنی صاحبش خودتی و:

- 👤 ثبت‌نام فقط با **نام کاربری و رمز عبور**ه — نه شماره موبایل می‌خواد، نه ایمیل
- 🕐 **عکس‌ها، فیلم‌ها و ویس‌ها بعد از ۷۲ ساعت خودبه‌خود پاک می‌شن** — ولی چت‌ها و پیام‌هات همیشه می‌مونن
- 🆓 **کاملاً رایگانه** — خود برنامه، قفل امنیتی (SSL) و همه آموزش‌ها
- 🇮🇷 **بدون HTTPS هم کار می‌کنه**؛ حتی اگه اینترنت «ملی» بشه، چون به هیچ سایت خارجی‌ای نیاز نداره
- 🚫 بدون تبلیغ، بدون ردیابی، بدون اینکه شرکتی چت‌هاتو بخونه

**به درد کی می‌خوره؟** خانواده‌ها، دوستا، تیم‌های کوچیک و هر جمعی که یه پیام‌رسان ساده و خصوصی می‌خوان، بدون اینکه شماره موبایلشون رو به کسی بدن.

## چی‌کارا می‌تونه بکنه؟

| | |
|---|---|
| 💬 چت دونفره | 👥 ساخت گروه و 📢 کانال، اضافه‌کردن عضو و ادمین‌کردن |
| 📷 فرستادن عکس | 🎬 فرستادن فیلم **زیر ۱۰ مگابایت** |
| 🎤 پیام صوتی (ویس) | 😀 استیکر و ری‌اکشن ❤️ |
| 📍 فرستادن لوکیشن ثابت (یه نقطه روی نقشه) | ✏️ **ویرایش پیام** — ویرایش برای هر دو طرف دیده می‌شه |
| 🗑️ حذف پیام **فقط برای خودت** | 🗂️ آرشیو کردن چت، 📌 پین‌کردن، 🔕 بی‌صدا کردن |
| 🔍 پیدا کردن آدما با `@آیدی`، گروه و کانال | 🟢 دیدن اینکه کی آنلاینه |
| 🚫 بلاک‌کردن مزاحما | 🎨 تم روشن و تاریک |

> ⚠️ **توجه، این یه تصمیم عمدیه:** نسخه لایت **«حذف برای همه» نداره**.
> وقتی پیامی رو فرستادی، طرف مقابل نسخش رو داره؛
> تو فقط می‌تونی از صفحه **خودت** پاکش کنی (و همیشه می‌تونی **ویرایشش** کنی).
> «حذف برای طرف مقابل» مال نسخه کامل (Full) هست.

## نصب — راهی که به تو می‌خوره رو انتخاب کن

> 🧭 **لازم نیست برنامه‌نویس باشی.** از جدول زیر ردیف خودت رو پیدا کن و قدم‌به‌قدم برو جلو. همه راه‌ها رایگانن.

| تو چی داری؟ | این راه رو برو | چقدر طول می‌کشه؟ | ترمینال (صفحه سیاه) لازمه؟ |
|---|---|---|---|
| سرور لینوکسی (VPS) + دامنه | راه ۱ | حدود ۵ دقیقه | فقط یه کپی‌پیست |
| سرور لینوکسی، **بدون دامنه** (فقط یه آی‌پی مثل `185.2.3.4`) | راه ۲ | حدود ۵ دقیقه | فقط یه کپی‌پیست |
| سرور لینوکسی، **ساده‌ترین حالت** (بدون SSL، فقط HTTP) | راه ۳ | حدود ۵ دقیقه | فقط یه کپی‌پیست |
| هاست اشتراکی cPanel و با ترمینال مشکلی نداری | فایل `cpanel-setup.sh` | حدود ۵ دقیقه | بله |
| هاست اشتراکی cPanel و از ترمینال خوشت نمیاد 🖱️ | [📖 آموزش تصویری cPanel بدون ترمینال](docs/CPANEL_MANUAL.md) | حدود ۱۵ دقیقه | **اصلاً** |

### راه ۱ — سرور + دامنه

۱. توی سایتی که دامنه رو ازش خریدی، دامنه رو به آی‌پی سرورت وصل کن (رکورد A — خود سایت فروشنده راهنماییش کرده، یه فرم کوچیکه).

۲. به سرور وصل شو و این یه خط رو پیست کن:

```bash
git clone YOUR-REPO-URL reyno-lite && cd reyno-lite && bash install.sh
```

۳. گزینه **۱** رو بزن، دامنه‌ت رو بنویس، یه نام کاربری و رمز برای مدیر انتخاب کن — بقیه‌ش رو خود اسکریپت انجام می‌ده، حتی گرفتن **قفل امنیتی رایگان (SSL)** رو 🔒.

### راه ۲ — سرور بدون دامنه، فقط با آی‌پی (مثل پنل 3x-ui)

لازم نیست دامنه بخری! این دستور رو بزن و گزینه **۲** رو انتخاب کن:

```bash
git clone YOUR-REPO-URL reyno-lite && cd reyno-lite && bash install.sh
```

نصب‌کننده خودش برای آی‌پی سرورت **گواهی SSL رایگان** می‌گیره (مثل 3x-ui؛ خودش هم تمدید می‌شه). بعد فقط این آدرس رو باز کن:

```
https://آی‌پی-سرور-تو/
```

### راه ۳ — ساده‌ترین حالت: بدون SSL (فقط HTTP)

همون دستور بالا رو بزن و این بار گزینه **۳** رو انتخاب کن. تموم شد! آدرس سایتت می‌شه:

```
http://آی‌پی-سرور-تو/
```

این حالت رو عمداً گذاشتیم: **اگه یه روز اینترنت ملی شد**، سایت‌های خارجیِ صادرکننده گواهی ممکنه در دسترس نباشن — ولی پیام‌رسان تو به هیچ‌چیز خارجی‌ای نیاز نداره و به کارش ادامه می‌ده. (توی شبکه خصوصی خودت خطر HTTP کمه؛ ولی روی اینترنت باز، راه ۱ یا ۲ امن‌ترن.)

### 🖱️ هاست cPanel بدون حتی یه دونه دستور

آموزش قدم‌به‌قدم و کلیکی رو اینجا بخون: **[docs/CPANEL_MANUAL.md](docs/CPANEL_MANUAL.md)** — یه فایل زیپ آپلود می‌کنی، چند تا دکمه می‌زنی، تموم. جزئیات کامل نصب و رفع اشکال هم توی **[docs/DEPLOY.md](docs/DEPLOY.md)** هست.

## قفل امنیتی (SSL) — سه انتخاب رایگان

| انتخاب | آدرسی که مردم باز می‌کنن | هزینه | نکته |
|---|---|---|---|
| دامنه + Let's Encrypt | `https://chat.example.com` | رایگان | مطمئن‌ترین؛ خودش تمدید می‌شه |
| **گواهی برای آی‌پی** (مثل 3x-ui) | `https://185.2.3.4` | رایگان | دامنه نمی‌خواد؛ خودش تمدید می‌شه |
| بدون SSL (فقط HTTP) | `http://185.2.3.4` | رایگان | روی اینترنت ملی و شبکه داخلی کار می‌کنه؛ ولی چت‌ها توی مسیر رمزنگاری نمی‌شن |

**یه توضیح صادقانه:** نسخه لایت پیام‌های ذخیره‌شده روی دیسک سرور رو رمزنگاری می‌کنه و اطلاعات GPS عکس‌ها رو پاک می‌کنه، اما مثل سیگنال «رمزنگاری سرتاسری» نیست. یعنی HTTPS چت‌ها رو توی مسیر امن می‌کنه، ولی صاحب سرور از نظر فنی می‌تونه به داده‌های ذخیره‌شده دسترسی داشته باشه. برای بیشتر جمع‌ها این کافیه — فقط خواهشاً به کاربراتون قولِ بیشتر از این ندین.

## روش استفاده (به زبان ساده)

۱. سایت رو باز کن و **«ساخت حساب»** رو بزن. یه نام کاربری (مثل `sara_2026`) و یه رمز انتخاب کن. همین! نه موبایل، نه ایمیل، نه عکس پروفایل.

۲. برای پیدا کردن دوستت، بالای صفحه `@نام‌کاربری` اون رو توی کادر جست‌وجو بنویس.

۳. روی اسمش بزن ← پیام بنویس ← بفرست. با دکمه 📷 عکس و فیلم، با 🎤 ویس و با 📍 لوکیشن می‌فرستی.

۴. اشتباه تایپی داشتی؟ **ویرایش** کن؛ برای هر دو طرف درست می‌شه. می‌خوای فقط از صفحه **خودت** پاک بشه؟ **«حذف برای من»** رو بزن. (روی صفحه طرف مقابل می‌مونه — دلیلش رو بالاتر گفتیم.)

۵. دکمه **ℹ️** تنظیمات گروه رو باز می‌کنه: اضافه‌کردن عضو، ادمین‌کردن، آرشیو کردن چت یا بلاک‌کردن یه نفر.

۶. یادت نره: **عکس‌ها، فیلم‌ها و ویس‌ها بعد از ۷۲ ساعت خودشون پاک می‌شن** (خود پیام می‌مونه و روش می‌نویسه «رسانه منقضی شده»). پس **فایل‌های** مهم رو یه جای دیگه نگه دار — چت‌ها و متن‌هات هیچ‌وقت خودبه‌خود پاک نمی‌شن!

**صفحه مدیر:** آدرس `آدرس-سایتت/admin` رو باز کن و با نام کاربری و رمز مدیری که موقع نصب انتخاب کردی وارد شو. این صفحه فقط سه تا کار می‌تونه بکنه: **اضافه‌کردن کاربر، حذف کاربر و خالی‌کردن فضای سرور**. به هیچ وجه نمی‌تونه پیام‌های کسی رو بخونه.

## مقایسه نسخه لایت و کامل

| امکان | لایت (همین، رایگان) | نسخه کامل |
|---|:---:|:---:|
| پیام متنی، عکس، فیلم زیر ۱۰ مگ، ویس، استیکر | ✅ | ✅ |
| گروه و کانال و ادمین | ✅ | ✅ |
| ویرایش پیام (برای هر دو طرف) | ✅ | ✅ |
| **حذف فقط برای خودت** | ✅ | ✅ |
| **حذف برای طرف مقابل** | ❌ | ✅ |
| آرشیو کردن چت | ✅ | ✅ |
| جست‌وجو با آیدی، گروه و کانال؛ دیدن آنلاین‌ها؛ بلاک | ✅ | ✅ |
| کار کردن با HTTP ساده (آماده برای اینترنت ملی) | ✅ | ✅ |
| ثبت‌نام با شماره موبایل، پروفایل و عکس و بیو | ❌ | ✅ |
| نوتیفیکیشن، گیف، فایل و سند، نظرسنجی، چت محرمانه | ❌ | ✅ |
| حالت روح، رمز دو مرحله‌ای، پوشه‌بندی، پیام زمان‌دار و یک‌بارمصرف | ❌ | ✅ |
| قیمت | **رایگان** | — |

## اگه یه جا گیر کردی 😟

| مشکل | اول اینو امتحان کن |
|---|---|
| سایت باز نمی‌شه | آدرس رو دقیق چک کن — اولش `http://` هست یا `https://`؟ اون یکی رو هم امتحان کن. |
| می‌گه «فیلم خیلی بزرگه» | فیلم باید **زیر ۱۰ مگابایت** باشه — کوتاهش کن یا کیفیتش رو بیار پایین. |
| پیام رو پاک کردم ولی دوستم هنوز می‌بینتش | طبیعیه! توی نسخه لایت حذف فقط برای صفحه خودته. اگه می‌خوای اون چیزی که می‌بینه عوض بشه، از **ویرایش** استفاده کن. |
| عکس یا فیلم قدیمی‌تر از ۳ روز باز نمی‌شه | این همون پاک‌سازی خودکار ۷۲ ساعته‌ست 🕐 — فقط فایل پاک شده، خود پیام سر جاشه. چت و متن هیچ‌وقت خودکار پاک نمی‌شن. |
| رمز مدیر رو یادم رفته (سرور) | فایل `backend/.env` رو باز کن، `ADMIN_PASSWORD` رو عوض کن و این دستور رو بزن: `sudo systemctl restart reyno` |
| باز هم نشد؟ | 📖 [docs/DEPLOY.md](docs/DEPLOY.md) · 🖱️ [docs/CPANEL_MANUAL.md](docs/CPANEL_MANUAL.md) · یا توی گیت‌هاب Issue باز کن (هیچ‌وقت رمزت رو برای کسی نفرست!) |

## مجوز

استفاده، کپی و تغییرش برای جمع خودت آزاده. اسم و لوگوی «رینو» متعلق به پروژه رینو هستن.

</div>
