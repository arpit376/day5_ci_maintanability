#!/usr/bin/env bash
# Run the six pipeline stages on THIS machine, the way Jenkins or GitHub Actions would (module 5.3).
#   ./ci/local_pipeline.sh commit     smoke only                      (every commit)
#   ./ci/local_pipeline.sh nightly    smoke + full (no long)          (nightly)
#   ./ci/local_pipeline.sh weekly     smoke + full incl. long         (weekly / release)
# Stages: 1 Provision  2 Smoke  3 Full  4 Publish  5 Archive  6 Gate
# Publish and Archive ALWAYS run, even after a failure: a red build must keep its evidence.
# Only the Gate sets the exit code.
cd "$(dirname "$0")/.." || exit 1
MODE="${1:-commit}"
PY="${PYTHON:-python3}"
RUN="$PY -m robot -A lab.args --listener listeners/Notifier.py:results/notifications.log"
rm -rf results/smoke results/full results/report results/archive results/notifications.log
mkdir -p results

stage() { echo; echo "=== STAGE $1 ==============================================="; }

stage "1 Provision"
$PY check_setup.py || { echo "Provision failed: the lab is not ready"; exit 1; }

SMOKE_RC=0; FULL_RC=0; LAST=smoke
stage "2 Smoke"
$RUN --include smoke --outputdir results/smoke suites; SMOKE_RC=$?

stage "3 Full"
if [ "$MODE" = "commit" ]; then
  echo "skipped: mode '$MODE' runs smoke only"
elif [ "$SMOKE_RC" -ne 0 ]; then
  echo "skipped: smoke failed, no point running the full suite on a broken build"
else
  if [ "$MODE" = "weekly" ]; then
    $RUN --outputdir results/full suites; FULL_RC=$?
  else
    $RUN --exclude long --outputdir results/full suites; FULL_RC=$?
  fi
  LAST=full
fi

stage "4 Publish"
mkdir -p results/report
$PY -m robot.rebot --outputdir results/report --output output.xml --xunit xunit.xml \
    --name "LTE regression ($MODE)" "results/$LAST/output.xml" >/dev/null
echo "Report: results/report/report.html   Log: results/report/log.html"

stage "5 Archive"
mkdir -p results/archive
STAMP=$(date +%Y%m%d-%H%M%S)
tar --exclude='results/archive' -czf "results/archive/run-$MODE-$STAMP.tar.gz" results
echo "Archived: results/archive/run-$MODE-$STAMP.tar.gz"

stage "6 Gate"
$PY ci/gate.py results/report/output.xml --summary results/summary.md
GATE_RC=$?
echo; echo "Pipeline '$MODE': smoke rc=$SMOKE_RC, full rc=$FULL_RC, gate rc=$GATE_RC"
[ -f results/notifications.log ] && { echo "--- notifications.log"; cat results/notifications.log; }
exit $GATE_RC
