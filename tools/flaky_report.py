#!/usr/bin/env python3
"""Flaky report (module 5.4): a test that both passes and fails across runs is flaky.

    python tools/flaky_report.py results/flaky/run_*/output.xml

Needs several output.xml files of the SAME suite (nightly results, or ./run.sh flaky 6).
Prints pass/fail counts per test, flags mixed results, and shows the failing messages so you
can decide: timing, shared state, contention, or a real intermittent defect.
"""
import collections
import sys

from robot.api import ExecutionResult, ResultVisitor


class Collect(ResultVisitor):
    def __init__(self, store, run):
        self.store, self.run = store, run

    def visit_test(self, test):
        self.store[test.longname].append((self.run, test.status, test.message, [str(t) for t in test.tags]))


def main(paths):
    if not paths:
        print(__doc__)
        return 2
    store = collections.defaultdict(list)
    for p in paths:
        try:
            ExecutionResult(p).visit(Collect(store, p))
        except Exception as exc:
            print(f"skip {p}: {exc}")
    flaky = 0
    print(f"{'Test':58} {'runs':>4} {'pass':>4} {'fail':>4}  verdict")
    for name, rows in sorted(store.items()):
        ok = sum(1 for r in rows if r[1] == "PASS")
        bad = len(rows) - ok
        mixed = ok and bad
        flaky += 1 if mixed else 0
        quarantined = any("quarantine" in r[3] for r in rows)
        verdict = "FLAKY" if mixed else ("always fails" if bad else "stable")
        if mixed and quarantined:
            verdict += " (already quarantined)"
        elif mixed:
            verdict += "  -> quarantine it, open a ticket"
        print(f"{name[:58]:58} {len(rows):>4} {ok:>4} {bad:>4}  {verdict}")
    for name, rows in sorted(store.items()):
        msgs = collections.Counter(r[2] for r in rows if r[1] == "FAIL")
        if msgs and any(r[1] == "PASS" for r in rows):
            print(f"\nFailure messages for {name}:")
            for m, n in msgs.most_common(3):
                print(f"  {n}x  {m[:150]}")
    print(f"\n{flaky} flaky test(s) in {len(paths)} run(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
