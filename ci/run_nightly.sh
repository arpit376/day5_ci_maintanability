#!/usr/bin/env bash
# What CI runs nightly: the full regression without the long soak tests, in parallel.
# Quarantined tests run too; ci/gate.py ignores their result.
cd "$(dirname "$0")/.." || exit 1
python3 -m pabot.pabot --processes "${PROCESSES:-2}" --testlevelsplit \
     --pabotlib --resourcefile data/pool.dat \
     -A lab.args --exclude long --outputdir results/full suites
RC=$?
python3 ci/gate.py results/full/output.xml --summary results/summary.md
GATE=$?
echo "robot/pabot rc=$RC, gate rc=$GATE"
exit $GATE
