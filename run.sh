#!/usr/bin/env bash
# Shortcuts for the Day 5 lab.   ./run.sh <mode>     Every mode is a plain command (see README).
cd "$(dirname "$0")" || exit 1
PY="${PYTHON:-python3}"
R="$PY -m robot -A lab.args"
N="--listener listeners/Notifier.py:results/notifications.log"
case "${1:-help}" in
  check)      $PY check_setup.py ;;
  unit)       $PY -m unittest discover tests_py -v ;;
  lint)       $PY tools/lint_suite.py ${2:-suites} ;;
  lintdemo)   $PY tools/lint_suite.py demos/lint_bad.robot ;;
  # ---- 5.1 reports that get acted on
  evidence)   $R --outputdir results/evidence_demo demos/evidence_demo.robot ;;
  messages)   $R --outputdir results/messages demos/failure_messages.robot ;;
  notify)     rm -f results/notifications.log
              $R $N --outputdir results/notify demos/failure_messages.robot
              echo; echo "--- results/notifications.log"; cat results/notifications.log ;;
  # ---- 5.2 selection and parallel
  smoke)      $R --include smoke --outputdir results/smoke suites ;;
  full)       $R --exclude long --outputdir results/full suites ;;
  long)       $R --include long --outputdir results/long suites ;;
  seq)        rm -rf results/seq; $R --include parallel --outputdir results/seq suites/parallel ;;
  conflict)   rm -rf results/conflict /tmp/lte_lab_shared_hss
              $PY -m pabot.pabot --processes 2 --testlevelsplit -A lab.args --outputdir results/conflict demos/parallel_conflict.robot ;;
  parallel)   rm -rf results/parallel
              $PY -m pabot.pabot --processes "${PROCESSES:-2}" --testlevelsplit --pabotlib --resourcefile data/pool.dat \
                  -A lab.args --include parallel --outputdir results/parallel suites ;;
  # ---- 5.3 CI
  pipeline)   ./ci/local_pipeline.sh "${2:-commit}" ;;
  gate)       $PY ci/gate.py "${2:-results/full/output.xml}" ;;
  nightly)    ./ci/run_nightly.sh ;;
  # ---- 5.4 keeping it alive
  quarantine) $R --include quarantine --outputdir results/quarantine suites ;;
  flaky)      N_RUNS="${2:-6}"; rm -rf results/flaky
              for i in $(seq 1 "$N_RUNS"); do
                LAB_SEED=$i $R --include quarantine --outputdir "results/flaky/run_$i" suites >/dev/null 2>&1
                echo "run $i (LAB_SEED=$i) done"
              done
              $PY tools/flaky_report.py results/flaky/run_*/output.xml ;;
  trace)      $PY tools/trace_matrix.py ${2:-results/full/output.xml} ;;
  dryrun)     $R --dryrun --outputdir results/dryrun suites demos exercises ;;
  mine)       $R --outputdir results/mine exercises/my_pipeline_tests.robot ;;
  fault)      [ -n "$2" ] || { echo "Usage: ./run.sh fault <name>   (no_ip dup_ip bad_order erab_mismatch teid_mismatch low_tput high_latency flaky core_down)"; exit 1; }
              LAB_FAULT="$2" $R --outputdir "results/fault_$2" suites ;;
  *) cat <<USAGE
Usage: ./run.sh <mode>
  check | unit | lint [folder] | lintdemo
  5.1:  evidence | messages | notify
  5.2:  smoke | full | long | seq | conflict | parallel
  5.3:  pipeline [commit|nightly|weekly] | gate [output.xml] | nightly
  5.4:  quarantine | flaky [runs] | trace [output.xml] | dryrun | mine | fault <name>
USAGE
     exit 1 ;;
esac
