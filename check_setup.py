"""Check that the lab can run:  python check_setup.py"""
import importlib
import sys

ok = True
print(f"Python {sys.version.split()[0]}")
if sys.version_info < (3, 8):
    print("  FAIL: Python 3.8 or newer is needed"); ok = False
for mod, pip in (("robot", "robotframework"), ("pabot", "robotframework-pabot")):
    try:
        m = importlib.import_module(mod)
        print(f"  ok   {pip} {getattr(m, '__version__', '')}")
        if mod == "robot" and int(m.__version__.split(".")[0]) < 6:
            print("  FAIL: Robot Framework 6 or newer is needed (Test Tags, RETURN)"); ok = False
    except ImportError:
        if mod == "pabot":
            print(f"  warn {pip} is missing (only needed for parallel runs):  pip install {pip}")
        else:
            print(f"  FAIL {pip} is missing:  pip install {pip}"); ok = False
import shutil
for tool in ("tshark", "iperf3"):
    print(f"  {'ok  ' if shutil.which(tool) else 'info'} {tool} {'found' if shutil.which(tool) else 'not found (not needed: this kit simulates it; needed on the real VM)'}")
print("READY" if ok else "NOT READY: fix the lines marked FAIL")
sys.exit(0 if ok else 1)
