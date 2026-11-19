#!/usr/bin/env python3
"""CI gate (module 5.3): read output.xml, print a summary, set the exit code.

    python ci/gate.py results/report/output.xml [--min-pass-rate 100] [--summary results/summary.md]

* Tests tagged 'quarantine' are shown but do NOT count towards the gate (module 5.4).
* Exit code 0 = gate passed, 1 = gate failed, 2 = no usable output.xml.
* Writes a Markdown summary; if GITHUB_STEP_SUMMARY is set, appends it there too.
"""
import argparse
import os
import sys

from robot.api import ExecutionResult, ResultVisitor


class Collect(ResultVisitor):
    def __init__(self):
        self.rows = []

    def visit_test(self, test):
        self.rows.append({"name": test.name, "longname": test.longname, "status": test.status,
                          "message": test.message, "tags": [str(t) for t in test.tags],
                          "elapsed": test.elapsedtime / 1000.0})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output", nargs="?", default="results/report/output.xml")
    ap.add_argument("--min-pass-rate", type=float, default=100.0,
                    help="percent of gated tests that must pass (default 100)")
    ap.add_argument("--summary", default=None, help="write a Markdown summary here")
    a = ap.parse_args()

    if not os.path.exists(a.output):
        print(f"GATE ERROR: {a.output} not found. Did the test stage run?")
        return 2
    try:
        collect = Collect()
        ExecutionResult(a.output).visit(collect)
    except Exception as exc:
        print(f"GATE ERROR: cannot read {a.output}: {exc}")
        return 2
    rows = collect.rows
    if not rows:
        print("GATE ERROR: no tests in the result. An empty run must not pass.")
        return 2

    gated = [r for r in rows if "quarantine" not in r["tags"]]
    quarantined = [r for r in rows if "quarantine" in r["tags"]]
    failed = [r for r in gated if r["status"] == "FAIL"]
    passed = [r for r in gated if r["status"] == "PASS"]
    rate = 100.0 * len(passed) / len(gated) if gated else 0.0
    ok = rate >= a.min_pass_rate and not (a.min_pass_rate >= 100 and failed)

    lines = [f"## Regression gate: {'PASSED' if ok else 'FAILED'}", "",
             f"- Gated tests: {len(gated)}  (passed {len(passed)}, failed {len(failed)})",
             f"- Pass rate: {rate:.1f} %  (required {a.min_pass_rate:.1f} %)",
             f"- Quarantined (not gated): {len(quarantined)}"
             + (f"  ({sum(1 for r in quarantined if r['status'] == 'FAIL')} failing)" if quarantined else ""), ""]
    if failed:
        lines += ["### Failed tests", "", "| Test | Message |", "| --- | --- |"]
        lines += [f"| {r['longname']} | {r['message'].replace('|', '/')[:200]} |" for r in failed]
        lines.append("")
    if quarantined:
        lines += ["### Quarantined tests (run, but do not fail the build)", "", "| Test | Status |", "| --- | --- |"]
        lines += [f"| {r['longname']} | {r['status']} |" for r in quarantined]
        lines.append("")
    text = "\n".join(lines)
    print(text)

    for path in (a.summary, os.environ.get("GITHUB_STEP_SUMMARY")):
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "a" if path == os.environ.get("GITHUB_STEP_SUMMARY") else "w") as f:
                f.write(text + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
