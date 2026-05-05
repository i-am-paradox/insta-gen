"""
Instagram Account Creator PRO — One-click launcher.
Starts the FastAPI backend server. In development mode,
also starts the React frontend dev server.
"""
import subprocess
import sys
import os
import webbrowser
import time
import signal

PORT = int(os.getenv("SERVER_PORT", 8000))
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║           📸 INSTAGRAM CREATOR PRO — WEB UI 📸          ║
║                    v3.0 — Dashboard                     ║
╠══════════════════════════════════════════════════════════╣
║  Backend  : FastAPI + WebSocket                         ║
║  Frontend : React + TailwindCSS                         ║
║  URL      : http://localhost:{port:<27s}║
╚══════════════════════════════════════════════════════════╝
""".format(port=str(PORT)))

    frontend_proc = None

    if DEV_MODE:
        # Start React dev server in background
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        if os.path.isdir(frontend_dir):
            print("🔧 Starting React dev server...")
            frontend_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            url = f"http://localhost:{PORT}" if not DEV_MODE else "http://localhost:5173"
            webbrowser.open(url)

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

        # Start FastAPI server
        import uvicorn
        uvicorn.run(
            "src.server:app",
            host="0.0.0.0",
            port=PORT,
            reload=DEV_MODE,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        if frontend_proc:
            frontend_proc.terminate()


if __name__ == "__main__":
    main()
