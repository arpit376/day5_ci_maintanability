"""Notifier: a Robot Framework listener (API v3) that reports failures (module 5.1).

Run:   robot --listener listeners/Notifier.py:results/notifications.log suites/
The argument after the colon is the log file (default: notifications.log).

Set NOTIFY_WEBHOOK to a URL to also POST each failure as JSON, for a chat tool or tracker
that accepts incoming webhooks. Webhook errors never fail the run.
"""
import json
import os
import time
import urllib.request


class Notifier:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, logfile="notifications.log"):
        self.logfile = logfile
        self.failed = []
        self.total = 0
        folder = os.path.dirname(logfile)
        if folder:
            os.makedirs(folder, exist_ok=True)

    def end_test(self, data, result):
        self.total += 1
        if result.status == "FAIL":
            quarantined = "quarantine" in [str(t) for t in result.tags]
            self.failed.append(data.name)
            kind = "QUARANTINED" if quarantined else "FAIL"
            self._notify(f"[{kind}] {data.longname}: {result.message}", quarantined)

    def close(self):
        self._write(f"[DONE] {self.total} tests, {len(self.failed)} failed")

    # ---- output ---------------------------------------------------------------
    def _write(self, line):
        with open(self.logfile, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")

    def _notify(self, text, quarantined):
        self._write(text)
        url = os.environ.get("NOTIFY_WEBHOOK")
        if url and not quarantined:
            try:
                body = json.dumps({"text": text}).encode()
                req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5)
            except Exception as exc:      # a broken chat must not break the test run
                self._write(f"[WARN] webhook failed: {exc}")
