import os
import logging

logger = logging.getLogger("PhoneTracker")

USED_PHONES_FILE = "used_phones.txt"


class PhoneTracker:
    """
    Tracks which phone numbers have already been used across job runs.
    Persists to used_phones.txt — one number per line.
    """

    def __init__(self, filepath: str = USED_PHONES_FILE):
        self.filepath = filepath
        self._used: set = self._load()

    def _load(self) -> set:
        if not os.path.exists(self.filepath):
            return set()
        with open(self.filepath, "r") as f:
            return {line.strip() for line in f if line.strip()}

    def is_used(self, phone: str) -> bool:
        return phone.strip() in self._used

    def mark_used(self, phone: str):
        """Call this after a number is successfully used."""
        phone = phone.strip()
        if phone and phone not in self._used:
            self._used.add(phone)
            with open(self.filepath, "a") as f:
                f.write(phone + "\n")
            logger.info(f"📝 Marked used: {phone}  (total used: {len(self._used)})")

    def filter_fresh(self, phones: list) -> list:
        """Return only numbers not yet used. Logs how many were skipped."""
        fresh = [p for p in phones if not self.is_used(p.strip())]
        skipped = len(phones) - len(fresh)
        if skipped > 0:
            logger.warning(
                f"⏭️  Skipped {skipped} already-used number(s). "
                f"{len(fresh)} fresh number(s) remaining."
            )
        else:
            logger.info(f"✅ All {len(fresh)} numbers are fresh (unused).")
        return fresh

    def stats(self) -> dict:
        return {"used_total": len(self._used)}
