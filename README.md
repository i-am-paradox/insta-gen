<div align="center">

# Instagram Creator PRO

**Professional Instagram account automation with a real-time web dashboard.**  
Anti-ban engine · Concurrent tabs · Manual OTP · Phone number tracking

---

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Node](https://img.shields.io/badge/Node.js-18%2B-green?style=flat-square&logo=node.js)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-Educational-orange?style=flat-square)

</div>

---

## Overview

Instagram Creator PRO automates the Instagram account registration process through a clean web dashboard. It uses a patched Firefox browser (Camoufox) with randomized hardware fingerprints, human-like mouse and keyboard behavior, and a session warming strategy to reduce detection risk.

All controls — start, stop, OTP input, live status — are accessible from a single browser dashboard at `http://localhost:5173`.

---

## Features

| Feature | Description |
|---|---|
| **Web Dashboard** | Real-time tab cards, job controls, live logs via WebSocket |
| **Anti-Detect Browser** | Camoufox (patched Firefox) with randomized Canvas, WebGL, Audio, and font fingerprints |
| **Human Behavior Engine** | Ghost-Cursor non-linear mouse paths, configurable typing cadence |
| **Session Warming** | Pre-browses trusted sites (Wikipedia, Google) before signup to build browser trust |
| **Concurrent Tabs** | Run 1–100 parallel signup sessions simultaneously |
| **Anti-Ban Presets** | Four protection levels: Low / Medium / High / Paranoid |
| **Manual OTP Input** | OTP prompt appears in the dashboard when Instagram sends a verification code |
| **Phone Number Tracking** | Used numbers are recorded in `used_phones.txt` and never reused across jobs |
| **Cross-Platform** | Works on Windows, macOS, and Linux |

---

## Requirements

Before setup, make sure you have the following installed:

| Software | Version | Download |
|---|---|---|
| Python | 3.10 or higher | [python.org](https://www.python.org/downloads/) |
| Node.js | 18 or higher | [nodejs.org](https://nodejs.org/) |

> **Windows users:** During Python installation, check **"Add Python to PATH"**.

---

## Installation

### 🍎 macOS / Linux

```bash
# Step 1 — Install everything (run once)
bash setup.sh

# Step 2 — Start the tool
bash start.sh
```

### 🪟 Windows

```
Step 1 — Double-click setup.bat    (run once)
Step 2 — Double-click start.bat
```

> If Windows shows a security warning, click **"More info" → "Run anyway"**.

After starting, the dashboard opens automatically at **http://localhost:5173**

---

## Usage

### 1. Enter Phone Numbers
Paste phone numbers into the **Phone Numbers** box — one per line, or comma-separated.  
You can also click **Upload .txt** to load a file directly.

```
+919876543210
+919876543211
+919876543212
```

### 2. Configure Settings
- **Concurrent Tabs** — How many accounts to create in parallel (1–100)
- **Session Limit** — Maximum accounts per job run
- **Anti-Ban Preset** — Choose your protection level:

| Preset | Speed | Protection |
|---|---|---|
| Low | Fastest | Minimal |
| Medium | Fast | Moderate |
| High | Balanced | Strong ✅ Recommended |
| Paranoid | Slow | Maximum |

### 3. Start the Job
Click **Start** and watch the live tab cards update in real-time.

### 4. Enter OTP
When Instagram sends a verification code to the phone number, a prompt will automatically appear in the dashboard. Enter the code and click **Confirm**.

### 5. Done
Successfully created accounts are saved to **`accounts.csv`** in the project folder.

---

## Phone Number Tracking

The tool automatically tracks which numbers have already been used:

- After each successful account creation, the phone number is saved to `used_phones.txt`
- On the next job run, already-used numbers are **automatically skipped**
- You will see a log message like:  
  `⏭️ Skipped 12 already-used numbers. 38 fresh numbers remaining.`

This means you can safely paste all 50–100 numbers every time — the tool handles deduplication for you.

---

## Configuration (Optional)

Copy `.env.example` to `.env` and edit as needed:

```env
SMS_ACTIVATE_API_KEY=your_key_here    # For automatic SMS (optional)
PROXY_LIST_PATH=proxies.txt           # Path to proxy list (optional)
MAX_CONCURRENT_WORKERS=10             # Default concurrent tabs
```

> The tool works without any `.env` changes. Manual OTP mode is the default.

---

## Project Structure

```
├── setup.sh / setup.bat      ← One-time setup (Mac/Linux or Windows)
├── start.sh / start.bat      ← Start the tool
├── run.py                    ← Application entry point
├── requirements_pro.txt      ← Python dependencies
├── .env.example              ← Environment config template
│
├── src/
│   ├── server.py             ← FastAPI backend + WebSocket server
│   ├── job_manager.py        ← Job orchestration & concurrent tab management
│   ├── pro_creator.py        ← Instagram signup automation logic
│   ├── providers/
│   │   ├── sms/              ← SMS providers (Manual, SMS-Activate)
│   │   └── proxy/            ← Proxy management
│   └── utils/
│       ├── human.py          ← Human-like delays & mouse movement
│       ├── pro_browser.py    ← Camoufox browser launcher
│       ├── phone_tracker.py  ← Used phone number persistence
│       └── storage.py        ← accounts.csv writer
│
└── frontend/                 ← React + TailwindCSS dashboard (Vite)
```

---

## Troubleshooting

**`python` not found on Windows**  
→ Re-install Python and check "Add Python to PATH"

**`npm` not found**  
→ Install Node.js from nodejs.org and restart your terminal

**Camoufox download fails**  
→ Run manually: `python -m camoufox fetch` (requires internet)

**Browser closes immediately after phone number entry**  
→ This is normal — the script is waiting for Instagram to load the OTP page (up to 20 seconds)

**OTP modal not appearing in dashboard**  
→ Ensure your browser is connected (green "Connected" indicator in top-right)

---

## Disclaimer

This tool is intended for **educational and research purposes only**.  
Use responsibly and ensure your activities comply with applicable local laws and the platform's Terms of Service.
