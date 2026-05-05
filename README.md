# 🚀 Instagram Account Creator PRO

A professional Instagram account automation tool with a real-time web dashboard. Features anti-ban protection, human-like behavior simulation, and concurrent multi-tab creation.

---

## 💎 Features

- **Web Dashboard** — Real-time job control, live tab status, OTP input via browser UI
- **Anti-Ban Engine** — Camoufox (patched Firefox) with randomized hardware fingerprints (Canvas, WebGL, Audio)
- **Human Behavior** — Ghost-Cursor for natural mouse paths, configurable typing speed (Fast → Paranoid)
- **Session Warming** — Browses Wikipedia/Google before signup to build browser trust
- **Concurrent Tabs** — Run up to 10 parallel signup sessions
- **Anti-Ban Presets** — Low / Medium / High / Paranoid protection levels
- **Manual OTP Input** — OTP prompt appears in dashboard when Instagram sends verification code

---

## 🛠️ Setup

### Requirements
- Python 3.10+
- Node.js 18+

### 1. Install Python dependencies
```bash
pip install -r requirements_pro.txt
python -m camoufox fetch
```

### 2. Install frontend dependencies
```bash
cd frontend
npm install
cd ..
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings (optional — defaults work out of the box)
```

---

## ▶️ Run

```bash
DEV_MODE=true python3 run.py
```

Opens:
- **Dashboard** → `http://localhost:5173`
- **API** → `http://localhost:8000`

---

## 📋 How to Use

1. Open `http://localhost:5173` in your browser
2. Enter phone numbers (one per line) in the **Phone Numbers** section
3. Set number of accounts and concurrent tabs
4. Choose an **Anti-Ban** preset (recommended: High or Paranoid)
5. Click **Start Job**
6. Watch live tab status — when OTP is requested, a prompt appears in the dashboard
7. Enter the OTP received on the phone → account is created
8. Accounts are saved to `accounts.csv`

---

## 📁 Project Structure

```
├── run.py                  # Entry point (starts backend + frontend)
├── src/
│   ├── server.py           # FastAPI backend + WebSocket
│   ├── job_manager.py      # Job orchestration & concurrency
│   ├── pro_creator.py      # Instagram signup automation
│   ├── providers/
│   │   ├── sms/            # SMS providers (Manual, SMS-Activate)
│   │   └── proxy/          # Proxy management
│   └── utils/
│       ├── human.py        # Human-like delays & mouse movement
│       └── pro_browser.py  # Camoufox browser launcher
├── frontend/               # React + TailwindCSS dashboard
├── requirements_pro.txt
└── .env.example
```

---

## ⚠️ Disclaimer
For educational and research purposes only. Ensure compliance with local laws and platform terms of service.
