import asyncio
import json
import logging
import os
from typing import List, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from src.job_manager import JobManager, JobConfig, AntiBanConfig

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(name)-14s │ %(levelname)-7s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Server")

# ── Globals ──
job_manager = JobManager()
connected_clients: Set[WebSocket] = set()


async def broadcast(message: dict):
    """Send a message to all connected WebSocket clients."""
    dead = set()
    payload = json.dumps(message)
    for ws in connected_clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    connected_clients.difference_update(dead)


@asynccontextmanager
async def lifespan(app: FastAPI):
    job_manager.set_broadcast(broadcast)
    logger.info("🚀 Instagram Creator PRO Server started")
    yield
    if job_manager.state.running:
        await job_manager.stop_job()
    logger.info("🛑 Server shutting down")


app = FastAPI(title="Instagram Creator PRO", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──
class AntiBanRequest(BaseModel):
    typing_speed: str = "medium"
    tab_cooldown_min: int = 5
    tab_cooldown_max: int = 15
    random_delays: bool = True
    debug_screenshots: bool = False
    max_retries: int = 2


class StartJobRequest(BaseModel):
    phone_numbers: List[str]
    concurrent_tabs: int = 5
    session_limit: int = 100
    headless: bool = False
    enable_warming: bool = True
    anti_ban: AntiBanRequest = AntiBanRequest()


class OTPSubmitRequest(BaseModel):
    activation_id: str
    otp: str


# ── REST Endpoints ──
@app.post("/api/start")
async def start_job(req: StartJobRequest):
    try:
        # Clean phone numbers
        phones = [p.strip() for p in req.phone_numbers if p.strip()]
        if not phones:
            return JSONResponse(status_code=400, content={"error": "No phone numbers provided"})

        config = JobConfig(
            phone_numbers=phones,
            concurrent_tabs=min(req.concurrent_tabs, 100),
            session_limit=min(req.session_limit, 100),
            headless=req.headless,
            enable_warming=req.enable_warming,
            anti_ban=AntiBanConfig(
                typing_speed=req.anti_ban.typing_speed,
                tab_cooldown_min=req.anti_ban.tab_cooldown_min,
                tab_cooldown_max=req.anti_ban.tab_cooldown_max,
                random_delays=req.anti_ban.random_delays,
                debug_screenshots=req.anti_ban.debug_screenshots,
                max_retries=req.anti_ban.max_retries,
            ),
        )
        await job_manager.start_job(config)
        return {"status": "started", "job_id": job_manager.state.job_id, "total": len(phones)}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post("/api/stop")
async def stop_job():
    await job_manager.stop_job()
    return {"status": "stopped"}


@app.post("/api/tab/{tab_id}/ban")
async def ban_tab(tab_id: int):
    success = await job_manager.ban_tab(tab_id)
    if success:
        return {"status": "banned", "tab_id": tab_id}
    return JSONResponse(status_code=404, content={"error": f"Tab {tab_id} not found"})


@app.get("/api/status")
async def get_status():
    return job_manager.get_state_snapshot()


@app.post("/api/otp")
async def submit_otp(req: OTPSubmitRequest):
    success = job_manager.submit_otp(req.activation_id, req.otp)
    if success:
        return {"status": "ok"}
    return JSONResponse(status_code=404, content={"error": "No pending OTP request for this ID"})


@app.post("/api/upload-phones")
async def upload_phones(file: UploadFile = File(...)):
    """Upload a .txt file with one phone number per line."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {"phones": lines, "count": len(lines)}


@app.get("/api/accounts")
async def get_accounts():
    """Get all created accounts."""
    return {"accounts": job_manager.state.created_accounts}


@app.get("/api/download-csv")
async def download_csv():
    """Download accounts.csv file."""
    csv_path = "accounts.csv"
    if os.path.exists(csv_path):
        return FileResponse(csv_path, media_type="text/csv", filename="accounts.csv")
    return JSONResponse(status_code=404, content={"error": "No accounts file found"})


# ── WebSocket ──
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    logger.info(f"🔌 WebSocket client connected (total: {len(connected_clients)})")

    try:
        # Send current state on connect
        await ws.send_text(json.dumps({
            "event": "INIT",
            **job_manager.get_state_snapshot()
        }))

        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                event = msg.get("event", "")

                if event == "SUBMIT_OTP":
                    act_id = msg.get("activation_id", "")
                    otp = msg.get("otp", "")
                    if act_id and otp:
                        job_manager.submit_otp(act_id, otp)

                elif event == "PING":
                    await ws.send_text(json.dumps({"event": "PONG"}))

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(ws)
        logger.info(f"🔌 WebSocket client disconnected (total: {len(connected_clients)})")


# ── Serve Frontend (production) ──
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React SPA — all non-API routes go to index.html."""
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
