# 🚀 Instagram Creator PRO

Professional Instagram account automation with a real-time web dashboard.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Web Dashboard** | Live tab status, start/stop controls, real-time logs |
| **Anti-Ban Engine** | Camoufox (patched Firefox) — randomized Canvas, WebGL, Audio fingerprints |
| **Human Behavior** | Ghost-Cursor mouse paths + configurable typing speed (Fast → Paranoid) |
| **Session Warming** | Pre-browses Wikipedia/Google to build browser trust before signup |
| **Concurrent Tabs** | Up to 10 parallel signup sessions |
| **Anti-Ban Presets** | Low / Medium / High / Paranoid — one click to configure |
| **Manual OTP** | OTP prompt appears in dashboard UI when Instagram sends verification code |

---

## ⚙️ Requirements

- **Python** 3.10 or higher → [python.org](https://python.org)
- **Node.js** 18 or higher → [nodejs.org](https://nodejs.org)

---

## 🚀 Quick Start

### Step 1 — Setup (run once)
```bash
bash setup.sh
```
This automatically installs all Python packages, downloads the Camoufox browser, and installs frontend dependencies.

### Step 2 — Start
```bash
bash start.sh
```

Then open **http://localhost:5173** in your browser.

---

## 📋 How to Use

1. **Open** `http://localhost:5173`
2. **Enter phone numbers** (one per line) in the Phone Numbers box
3. **Set** number of accounts to create and concurrent tabs
4. **Choose Anti-Ban preset** — recommended: **High** or **Paranoid**
5. **Click Start Job**
6. Watch live tab cards update in real-time
7. When Instagram sends OTP → a prompt appears in the dashboard → enter the code
8. ✅ Accounts saved automatically to `accounts.csv`

---

## 📁 Structure

```
├── setup.sh              ← Run once to install everything
├── start.sh              ← Run to start the tool
├── run.py                ← Backend entry point
├── requirements_pro.txt  ← Python dependencies
├── .env.example          ← Config template
├── src/
│   ├── server.py         ← FastAPI + WebSocket backend
│   ├── job_manager.py    ← Job & tab orchestration
│   ├── pro_creator.py    ← Instagram signup automation
│   ├── providers/sms/    ← SMS providers (Manual / SMS-Activate)
│   └── utils/            ← Human engine, browser, storage
└── frontend/             ← React + TailwindCSS dashboard
```

---

## ⚠️ Disclaimer
For educational and research purposes only. Use responsibly and in compliance with applicable laws and platform terms of service.
