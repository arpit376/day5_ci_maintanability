#!/usr/bin/env bash
# What CI runs on every commit (module 5.2/5.3). Exit code = number of failed tests.
cd "$(dirname "$0")/.." || exit 1
exec python3 -m robot -A lab.args --include smoke --outputdir results/smoke \
     --listener listeners/Notifier.py:results/notifications.log suites
