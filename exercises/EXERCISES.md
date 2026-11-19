# Day 5 exercises

Run everything from the kit folder. `./run.sh mine` runs `exercises/my_pipeline_tests.robot`.
Your copy is ignored by git (`exercises/my_*.robot`).

## 5.1 Reports that get acted on  (35 min)

1. `./run.sh evidence`, then open `results/evidence_demo/log.html`. Find the evidence link in the
   failing test and open `results/evidence_demo/evidence/<test>_<time>/`.
   - Which files are there? Which one would you open first for "no IP"?
   - Why does the passing test have no folder? How do you keep evidence for passes too?
     (`--variable EVIDENCE_ALWAYS:True`)
2. `./run.sh messages` and compare the two failing messages in `log.html`.
3. In `my_pipeline_tests.robot` fix **TODO 1 and TODO 2**.
4. `./run.sh notify`: read `results/notifications.log`. Read `listeners/Notifier.py`: where
   would you add a call to your chat tool?

## 5.2 Smoke, full, parallel  (55 min)

1. `./run.sh smoke` then `./run.sh full`. Compare the test counts and the run times.
2. `./run.sh seq` (parallel suite, one process: passes).
3. `./run.sh conflict`: four tests with the **same IMSI** on two workers. Read the failure message.
   Which of the four conflicts from slide "Resource conflicts" is this?
4. `./run.sh parallel`: the fixed suite. Look at `data/pool.dat` and
   `resources/parallel.resource` to see how each worker gets its own IMSI.
5. `PROCESSES=4 ./run.sh parallel`. What happens when there are more workers than value sets?
   (Add a fifth worker, or add sets to `pool.dat`.)
6. In `my_pipeline_tests.robot` fix **TODO 3**.

## 5.3 The pipeline  (70 min)

1. `./run.sh pipeline commit`: smoke only. Then `./run.sh pipeline nightly`.
2. Break the build: `LAB_FAULT=no_ip ./run.sh pipeline nightly`. Check:
   - Did the Full stage run? (No: smoke failed first.)
   - Did Publish and Archive still run? Open `results/report/report.html` and the `.tar.gz`.
   - Which stage set the exit code? (Only the Gate.)
3. Read `Jenkinsfile` and `.github/workflows/regression.yml`. Match each of the six stages to a
   Jenkins `stage` and a GitHub `step`. Which `if:`/`when:` chooses smoke versus nightly?
4. Open `ci/gate.py`. Change `--min-pass-rate` to 90 and rerun the gate. Is that a good idea?

## 5.4 Keeping it alive  (50 min)

1. `./run.sh lint` (clean). `./run.sh lintdemo` shows what lint catches. Fix **TODO 5**.
2. `./run.sh quarantine` several times, then `./run.sh flaky 6`. Which seeds fail? Reproduce one:
   `LAB_SEED=3 ./run.sh quarantine`. Same seed, same failure: that is how a flaky test becomes a bug report.
3. Fix **TODO 4** (quarantine tag). Run `./run.sh pipeline nightly`: the test runs, may fail, the gate ignores it.
4. `./run.sh trace results/full/output.xml`: which requirements have no test?
5. Layering check: to point the suite at a second lab you copy `env/lab01.py` to `env/lab02.py`
   and change `Variables`. Which files need no change? (All suites, resources and libraries.)

## Capstone (take-home)

Run `./run.sh pipeline nightly` from a clean checkout on your own VM, publish the report,
and add one NGAP / 5G NAS check following the pattern of `suites/05_protocol_checks.robot`.
