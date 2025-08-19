# docker/healthcheck.py
import os, sys, urllib.request
port = os.getenv("PORT", os.getenv("API_PORT", "8000"))
url = f"http://127.0.0.1:{port}/health"
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
