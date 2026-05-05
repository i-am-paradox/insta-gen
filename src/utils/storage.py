import csv
import os
from typing import Dict

class AccountStorage:
    def __init__(self, file_path: str = "accounts.csv"):
        self.file_path = file_path
        self._init_file()

    def _init_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["username", "password", "full_name", "phone", "proxy"])

    def save_account(self, account_data: Dict[str, str]):
        with open(self.file_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                account_data.get("username"),
                account_data.get("password"),
                account_data.get("full_name"),
                account_data.get("phone"),
                account_data.get("proxy_server")
            ])
