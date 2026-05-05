# Technical Usage & Security Guide

## 1. Remote Kill-Switch Setup (Detailed)
This script includes a "License Manager" to protect your work. 

**Steps:**
1. Go to [gist.github.com](https://gist.github.com/).
2. Create a new secret gist named `status.txt`.
3. Content: `ACTIVE`
4. Click **Raw** and copy the URL.
5. Paste this URL into `src/main.py` in the `LICENSE_URL` variable.

**How to Kill:** 
Simply edit the gist and change `ACTIVE` to `OFF`. The script will immediately start showing fake connection errors and exit.

## 2. Code Protection (Obfuscation)
Before giving the code to the client, you **MUST** obfuscate it so they cannot find and delete the kill-switch.

**Recommended Tool:** [PyArmor](https://pyarmor.readthedocs.io/)
```bash
pip install pyarmor
pyarmor pack -e " --onefile" src/main.py
```
Give the resulting executable or obfuscated files in the `dist/` folder to the client.

## 3. Proxy Recommendations
For 100+ accounts/day, **do not use Datacenter proxies**.
- **Recommended:** 4G/5G Mobile Proxies or High-Quality Rotating Residential Proxies.
- **Format in proxies.txt:** `ip:port:user:pass` (one per line).

## 4. Troubleshooting
- **Chromium/Firefox Errors:** Ensure you ran `playwright install`.
- **SMS Timeout:** Check your SMS-Activate balance and ensure the `service='ig'` code is correct for your country.
- **License Error:** Ensure your `LICENSE_URL` is a "Raw" link (direct text, no HTML).
