# --- agents/pod_monitor.py ---
import requests


def is_runpod_live(runpod_url: str) -> bool:
    try:
        r = requests.get(runpod_url, timeout=3)
        return r.status_code == 200
    except Exception:
        return False
