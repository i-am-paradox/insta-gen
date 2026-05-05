import asyncio
import random
import string
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field

from src.providers.sms.manual_provider import ManualOTPProvider
from src.utils.pro_browser import BrowserManager
from src.pro_creator import ProInstagramCreator
from src.utils.storage import AccountStorage

logger = logging.getLogger("JobManager")


@dataclass
class TabInfo:
    tab_id: int
    phone: str = ""
    username: str = ""
    status: str = "IDLE"
    activation_id: str = ""


@dataclass
class AntiBanConfig:
    typing_speed: str = "medium"        # fast / medium / slow / paranoid
    tab_cooldown_min: int = 5
    tab_cooldown_max: int = 15
    random_delays: bool = True
    debug_screenshots: bool = False
    max_retries: int = 2


@dataclass
class JobConfig:
    phone_numbers: List[str]
    concurrent_tabs: int = 5
    session_limit: int = 100
    headless: bool = False
    enable_warming: bool = True
    anti_ban: AntiBanConfig = field(default_factory=AntiBanConfig)


@dataclass
class JobState:
    job_id: str = ""
    running: bool = False
    total: int = 0
    success: int = 0
    failed: int = 0
    in_progress: int = 0
    tabs: Dict[int, TabInfo] = field(default_factory=dict)
    created_accounts: List[Dict] = field(default_factory=list)
    start_time: Optional[datetime] = None


class JobManager:
    """
    Orchestrates Instagram account creation jobs.
    Bridges the web UI (FastAPI) with the Playwright automation engine.
    """

    def __init__(self):
        self.state = JobState()
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._sms_provider: Optional[ManualOTPProvider] = None
        self._broadcast: Optional[Callable[[dict], Awaitable[None]]] = None

    def set_broadcast(self, fn: Callable[[dict], Awaitable[None]]):
        """Register a function that broadcasts messages to all connected WebSocket clients."""
        self._broadcast = fn

    async def _emit(self, event: str, data: dict = None):
        if self._broadcast:
            await self._broadcast({"event": event, **(data or {})})

    @staticmethod
    def _generate_username() -> str:
        return "pro_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    @staticmethod
    def _generate_password() -> str:
        chars = string.ascii_letters + string.digits + "!@#$"
        return ''.join(random.choices(chars, k=14))

    @staticmethod
    def _generate_fullname() -> str:
        first_names = ["Alex", "Sam", "Jordan", "Casey", "Riley", "Morgan",
                       "Taylor", "Quinn", "Avery", "Blake", "Drew", "Emery",
                       "Reese", "Skyler", "Jamie", "Logan", "Parker", "Rowan"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                      "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson",
                      "Thomas", "Jackson", "White", "Harris", "Martin", "Clark"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def submit_otp(self, activation_id: str, otp: str) -> bool:
        """Forward OTP from UI to the ManualOTPProvider."""
        if self._sms_provider:
            return self._sms_provider.submit_otp(activation_id, otp)
        return False

    def get_state_snapshot(self) -> dict:
        """Return current job state as a serializable dict."""
        return {
            "job_id": self.state.job_id,
            "running": self.state.running,
            "total": self.state.total,
            "success": self.state.success,
            "failed": self.state.failed,
            "in_progress": self.state.in_progress,
            "tabs": {
                tid: {
                    "tab_id": t.tab_id,
                    "phone": t.phone,
                    "username": t.username,
                    "status": t.status,
                    "activation_id": t.activation_id,
                }
                for tid, t in self.state.tabs.items()
            },
            "created_accounts": self.state.created_accounts,
            "elapsed": (datetime.now() - self.state.start_time).total_seconds()
            if self.state.start_time else 0,
        }

    async def start_job(self, config: JobConfig):
        """Start a new account creation job."""
        if self.state.running:
            raise Exception("A job is already running")

        # Reset state
        self._stop_event.clear()
        self.state = JobState(
            job_id=f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            running=True,
            total=min(len(config.phone_numbers), config.session_limit),
            start_time=datetime.now(),
        )

        # Trim phone list to session limit
        phones = config.phone_numbers[:config.session_limit]

        # Create ManualOTPProvider
        self._sms_provider = ManualOTPProvider(phones)
        self._sms_provider.set_otp_request_callback(self._on_otp_needed)

        # Launch job in background
        self._task = asyncio.create_task(self._run_job(config, phones))
        await self._emit("JOB_STARTED", {"job_id": self.state.job_id, "total": self.state.total})

    async def stop_job(self):
        """Signal the job to stop."""
        self._stop_event.set()
        self.state.running = False
        await self._emit("JOB_STOPPED", {})

    async def _on_otp_needed(self, activation_id: str, phone: str, tab_id_str: str):
        """Callback from ManualOTPProvider when OTP is needed."""
        # Update tab card status to OTP_WAIT so UI shows the waiting state
        try:
            tab_id = int(tab_id_str)
            if tab_id in self.state.tabs:
                self.state.tabs[tab_id].status = "OTP_WAIT"
                self.state.tabs[tab_id].activation_id = activation_id
                await self._emit("TAB_STATUS", {
                    "tab_id": tab_id,
                    **self._tab_dict(self.state.tabs[tab_id]),
                })
        except (ValueError, KeyError):
            pass
        await self._emit("OTP_NEEDED", {
            "activation_id": activation_id,
            "phone": phone,
        })

    async def _run_job(self, config: JobConfig, phones: List[str]):
        """Main job loop — launches browser and workers."""
        storage = AccountStorage("accounts.csv")
        creator = ProInstagramCreator(
            self._sms_provider,
            enable_warming=config.enable_warming,
            anti_ban={
                "typing_speed": config.anti_ban.typing_speed,
                "random_delays": config.anti_ban.random_delays,
                "debug_screenshots": config.anti_ban.debug_screenshots,
                "max_retries": config.anti_ban.max_retries,
            },
        )

        # Build task queue
        queue = asyncio.Queue()
        for i, phone in enumerate(phones):
            queue.put_nowait({
                "username": self._generate_username(),
                "password": self._generate_password(),
                "full_name": self._generate_fullname(),
                "phone_override": phone,
            })

        concurrent = min(config.concurrent_tabs, len(phones))
        logger.info(f"📋 {len(phones)} accounts queued, {concurrent} concurrent tabs")

        try:
            async with BrowserManager(headless=config.headless, humanize=True) as browser:
                workers = []
                for i in range(concurrent):
                    if self._stop_event.is_set():
                        break
                    worker = asyncio.create_task(
                        self._tab_worker(i + 1, browser, creator, queue, storage, config)
                    )
                    workers.append(worker)
                    await asyncio.sleep(random.uniform(2, 3))

                await asyncio.gather(*workers, return_exceptions=True)

        except Exception as e:
            logger.error(f"💥 Job error: {e}")
        finally:
            self.state.running = False
            elapsed = (datetime.now() - self.state.start_time).total_seconds() if self.state.start_time else 0
            await self._emit("JOB_COMPLETE", {
                "success": self.state.success,
                "failed": self.state.failed,
                "elapsed": elapsed,
            })

    async def _tab_worker(
        self,
        worker_id: int,
        browser: BrowserManager,
        creator: ProInstagramCreator,
        queue: asyncio.Queue,
        storage: AccountStorage,
        config: Optional[JobConfig] = None,
    ):
        """Worker that processes accounts from the queue."""
        while not self._stop_event.is_set():
            try:
                task = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            tab_id = worker_id
            page = None
            tab_info = TabInfo(
                tab_id=tab_id,
                phone=task.get("phone_override", ""),
                username=task["username"],
                status="STARTING",
            )
            self.state.tabs[tab_id] = tab_info
            self.state.in_progress += 1

            try:
                page = await browser.new_tab()
                tab_info.status = "REGISTERING"
                await self._emit("TAB_STATUS", {"tab_id": tab_id, **self._tab_dict(tab_info)})

                logger.info(f"[Tab-{tab_id}] 🆕 Starting: {task['username']} / {task.get('phone_override', '')}")

                success = await creator.register(page, tab_id, task)

                if success:
                    tab_info.status = "SUCCESS"
                    self.state.success += 1
                    account_record = {
                        "username": task["username"],
                        "password": task["password"],
                        "full_name": task["full_name"],
                        "phone": task.get("phone_override", ""),
                        "status": "success",
                    }
                    task["phone"] = task.get("phone_override", "")
                    task["proxy_server"] = "Direct"
                    storage.save_account(task)
                    self.state.created_accounts.append(account_record)
                    await self._emit("ACCOUNT_CREATED", account_record)
                else:
                    tab_info.status = "FAILED"
                    self.state.failed += 1

                await self._emit("TAB_STATUS", {"tab_id": tab_id, **self._tab_dict(tab_info)})

            except Exception as e:
                tab_info.status = "ERROR"
                self.state.failed += 1
                logger.error(f"[Tab-{tab_id}] 💥 Worker error: {e}")
                await self._emit("TAB_STATUS", {"tab_id": tab_id, **self._tab_dict(tab_info)})
            finally:
                self.state.in_progress = max(0, self.state.in_progress - 1)
                if page:
                    await browser.close_tab(page)
                queue.task_done()

                if not queue.empty() and not self._stop_event.is_set():
                    cd_min = config.anti_ban.tab_cooldown_min if config else 5
                    cd_max = config.anti_ban.tab_cooldown_max if config else 15
                    cooldown = random.uniform(cd_min, cd_max)
                    tab_info.status = "COOLDOWN"
                    await self._emit("TAB_STATUS", {"tab_id": tab_id, **self._tab_dict(tab_info)})
                    await asyncio.sleep(cooldown)

    @staticmethod
    def _tab_dict(tab: TabInfo) -> dict:
        return {
            "phone": tab.phone,
            "username": tab.username,
            "status": tab.status,
            "activation_id": tab.activation_id,
        }
