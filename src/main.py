import asyncio
import logging
import os
import sys
import random
import string
import signal
from datetime import datetime
from dotenv import load_dotenv

from src.providers.sms.sms_activate import SmsActivateProvider
from src.providers.sms.mock_provider import MockSMSProvider
from src.utils.pro_browser import BrowserManager
from src.pro_creator import ProInstagramCreator
from src.utils.storage import AccountStorage

# Load Environment Variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(name)-14s │ %(levelname)-7s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Main")

# ── Configuration ──
MAX_TABS = int(os.getenv("MAX_CONCURRENT_TABS", 5))
ACCOUNTS_TO_CREATE = int(os.getenv("ACCOUNTS_TO_CREATE", 10))
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
ENABLE_WARMING = os.getenv("SESSION_WARMING", "true").lower() == "true"


def generate_username():
    return "pro_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choices(chars, k=14))


def generate_fullname():
    first_names = ["Alex", "Sam", "Jordan", "Casey", "Riley", "Morgan",
                   "Taylor", "Quinn", "Avery", "Blake", "Drew", "Emery",
                   "Reese", "Skyler", "Jamie", "Logan", "Parker", "Rowan"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson",
                  "Thomas", "Jackson", "White", "Harris", "Martin", "Clark"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════╗
║           📸 INSTAGRAM ACCOUNT CREATOR PRO 📸           ║
║                    v2.0 — Multi-Tab                     ║
╠══════════════════════════════════════════════════════════╣
║  Engine    : Camoufox (Patched Firefox)                 ║
║  Behavior  : Humanized typing + cursor                  ║
║  Mode      : {mode:<43s} ║
║  Tabs      : {tabs:<43s} ║
║  Accounts  : {accounts:<43s} ║
╚══════════════════════════════════════════════════════════╝
"""
    mode = "HEADLESS" if HEADLESS else "HEADED (visible)"
    print(banner.format(
        mode=mode,
        tabs=str(MAX_TABS) + " concurrent",
        accounts=str(ACCOUNTS_TO_CREATE) + " to create",
    ))


def print_live_stats(creator: ProInstagramCreator, total: int):
    """Print compact live status of all tabs."""
    statuses = creator.get_all_statuses()
    stats = creator.stats

    # Build status line
    parts = []
    for tab_id in sorted(statuses.keys()):
        status = statuses[tab_id]
        parts.append(f"Tab-{tab_id}: {status}")

    status_line = " │ ".join(parts) if parts else "Starting..."

    progress = stats['success'] + stats['failed']
    print(f"\r  📊 [{progress}/{total}] ✅{stats['success']} ❌{stats['failed']} "
          f"🔄{stats['in_progress']}  │  {status_line}     ", end="", flush=True)


async def tab_worker(
    worker_id: int,
    browser: BrowserManager,
    creator: ProInstagramCreator,
    queue: asyncio.Queue,
    storage: AccountStorage,
    results: list,
):
    """
    Worker that processes accounts from the queue.
    Each iteration opens a NEW TAB, registers, then closes the tab.
    """
    while True:
        try:
            task = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        tab_id = worker_id
        page = None

        try:
            # Open a new tab
            page = await browser.new_tab()
            logger.info(f"[Tab-{tab_id}] 🆕 Starting registration for: {task['username']}")

            # Run registration
            success = await creator.register(page, tab_id, task)

            if success:
                task["phone"] = "mock"  # Will be real number in production
                task["proxy_server"] = "Direct"
                storage.save_account(task)
                results.append({"username": task["username"], "status": "success"})
            else:
                results.append({"username": task["username"], "status": "failed"})

        except Exception as e:
            logger.error(f"[Tab-{tab_id}] 💥 Worker error: {e}")
            results.append({"username": task.get("username", "?"), "status": "error"})

        finally:
            # Always close the tab
            if page:
                await browser.close_tab(page)
            queue.task_done()

            # Small cooldown between accounts on same tab
            if not queue.empty():
                cooldown = random.uniform(5, 15)
                logger.info(f"[Tab-{tab_id}] ⏸️  Cooldown {cooldown:.0f}s before next account...")
                await asyncio.sleep(cooldown)


async def main():
    print_banner()
    start_time = datetime.now()

    # ── 1. Initialize SMS Provider ──
    sms_api_key = os.getenv("SMS_ACTIVATE_API_KEY")
    if sms_api_key and sms_api_key != "your_key_here":
        logger.info("🔑 Using SMS-Activate provider (REAL)")
        sms_provider = SmsActivateProvider(sms_api_key)
    else:
        logger.info("🧪 Using Mock SMS provider (DEMO MODE)")
        sms_provider = MockSMSProvider()

    # ── 2. Initialize Components ──
    storage = AccountStorage("accounts.csv")
    creator = ProInstagramCreator(sms_provider, enable_warming=ENABLE_WARMING)

    # ── 3. Build Task Queue ──
    queue = asyncio.Queue()
    for i in range(ACCOUNTS_TO_CREATE):
        queue.put_nowait({
            "username": generate_username(),
            "password": generate_password(),
            "full_name": generate_fullname(),
        })

    logger.info(f"📋 {ACCOUNTS_TO_CREATE} accounts queued, launching {MAX_TABS} tabs...")
    print()

    # ── 4. Launch Browser + Workers ──
    results = []

    async with BrowserManager(headless=HEADLESS, humanize=True) as browser:
        # Create concurrent tab workers
        # Each worker processes accounts from the shared queue
        workers = []
        for i in range(min(MAX_TABS, ACCOUNTS_TO_CREATE)):
            worker = asyncio.create_task(
                tab_worker(i + 1, browser, creator, queue, storage, results)
            )
            workers.append(worker)
            # Stagger tab launches by 2-3s to avoid all hitting Instagram at once
            await asyncio.sleep(random.uniform(2, 3))

        # Wait for all workers to finish
        await asyncio.gather(*workers, return_exceptions=True)

    # ── 5. Final Report ──
    elapsed = (datetime.now() - start_time).total_seconds()
    stats = creator.stats

    duration_str = f"{elapsed:.0f}s ({elapsed/60:.1f}m)"

    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                    📊 FINAL REPORT                     ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  ✅ Successful  : {stats['success']:<38} ║")
    print(f"║  ❌ Failed      : {stats['failed']:<38} ║")
    print(f"║  ⏱️  Duration    : {duration_str:<38} ║")
    print(f"║  📁 Saved to    : {'accounts.csv':<38} ║")
    print("╚══════════════════════════════════════════════════════════╝")

    if stats['success'] > 0:
        logger.info(f"🎉 {stats['success']} accounts saved to accounts.csv")
    else:
        logger.warning("⚠️  No accounts were created successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user. Shutting down...")
        sys.exit(0)
