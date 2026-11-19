# Day 5 kit: CI and Maintainability

Module 10, Python + Robot Framework. This kit continues the Day 4 regression suite and adds
everything Day 5 needs: **evidence on failure, tag-based runs, parallel runs, a CI pipeline with a
gate, and the tools that keep a growing suite alive.**

It runs on any machine with Python 3.8+. The lab is **simulated** (`libraries/day2_lte.py`), so no
Open5GS, no eNodeB and no root are needed. On the real VM only the interface layer changes
(see "Pointing it at the real lab").

## 1. Set up (2 minutes)

```bash
git clone https://github.com/arpit376/day5_ci_maintanability.git
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run.sh check          # must end with READY
./run.sh unit           # 11 plain-Python checks of the gate and the lint tool
```

Every `./run.sh <mode>` is a plain command; the README shows the real command in each section.

## 2. What is in the kit

| Folder / file | What it is | Module |
| --- | --- | --- |
| `suites/01..07` | The Day 4 regression suite, now tagged for CI (`smoke`, `functional`, `kpi`, `REQ-*`) | 5.2 |
| `suites/08_soak.robot` | 300-cycle soak, tag `long` (weekly) | 5.2 |
| `suites/09_quarantine.robot` | A flaky test with tag `quarantine`, a ticket and an owner | 5.4 |
| `suites/parallel/` | Attach tests that are safe to run in parallel | 5.2 |
| `libraries/EvidenceLib.py` | `Collect Evidence`: per-test evidence folder + log link | 5.1 |
| `listeners/Notifier.py` | Listener API v3: failures to a log file and an optional webhook | 5.1 |
| `libraries/SharedHss.py` | A shared subscriber claim, to *show* a parallel conflict | 5.2 |
| `resources/parallel.resource` | `Get Worker IMSI`, `Run With Core Lock` (PabotLib) | 5.2 |
| `data/pool.dat` | PabotLib value sets: one IMSI per worker | 5.2 |
| `ci/local_pipeline.sh` | The six stages on your machine | 5.3 |
| `ci/gate.py` | Reads `output.xml`, prints a summary, sets the exit code | 5.3 |
| `ci/run_smoke.sh`, `ci/run_nightly.sh` | The commands CI calls | 5.3 |
| `Jenkinsfile`, `.github/workflows/regression.yml` | The same pipeline for Jenkins and GitHub Actions | 5.3 |
| `libraries/capture_view.py` | Turns a capture into a Wireshark-style HTML page (packet list, details, hex, display filter) | 4.3 / 5.1 |
| `tools/lint_suite.py` | Suite lint: docs, REQ tag, type tag, no `Sleep`, no hard-coded IMSI/IP | 5.4 |
| `tools/flaky_report.py` | Finds tests that both pass and fail across runs | 5.4 |
| `tools/trace_matrix.py` | Requirement-to-result matrix (from Day 4) | 5.4 |
| `demos/` | `evidence_demo`, `failure_messages`, `parallel_conflict`, `lint_bad` | all |
| `exercises/` | `EXERCISES.md` and `my_pipeline_tests.robot` (with TODOs) | all |
| `env/lab01.py`, `lab02.py` | The data layer: one variable file per lab | 5.4 |

## 3. Module 5.1: Reports that get acted on

```bash
./run.sh evidence     # a failing test; teardown collects evidence
./run.sh messages     # weak versus actionable failure message
./run.sh notify       # the Notifier listener writes results/notifications.log
```

- Open `results/evidence_demo/log.html`: the failing test has a link to its evidence folder
  `results/evidence_demo/evidence/<test>_<time>/` with `lab.log`, `capture.json`, `versions.txt`
  and `result.txt`. Folders are named by test and time. The passing test has none.
- Keep evidence for passes too: `robot ... --variable EVIDENCE_ALWAYS:True`.
- How it is wired: `resources/network.resource` defines `Collect Artefacts`, which every suite already
  uses as **Test Teardown**. It now calls `Collect Evidence` (`libraries/EvidenceLib.py`). A teardown
  runs even when the test failed, which is why evidence belongs there.
- The listener is enabled with `--listener listeners/Notifier.py:results/notifications.log`. Set
  `NOTIFY_WEBHOOK=https://...` to also POST failures as JSON to a chat tool. Quarantined failures are
  logged but never sent.

Rule: **a failure without evidence is a rerun.**

### The capture viewer (Wireshark-style page)

Every capture taken with `Stop Capture`, and every evidence folder of a failed test, now also gets an
`.html` page. Open it in any browser: packet list, packet details tree, hex bytes and a display filter.

```bash
python libraries/capture_view.py demos/captures/nas_order.capture.json      # simulated capture
python libraries/capture_view.py /tmp/attach.pcap -o attach.html            # real pcap, needs tshark
```
Open `demos/captures/nas_order.html` and `unknown_imsi.html` right away. Try the filters
`nas-eps`, `nas == 0x44`, `emm.cause == 8`, `info contains "Reject"`, `imsi == ...`; click a detail line such as
"Message Type" and the byte is highlighted in the hex pane; Up/Down arrows move between packets.
Simulated captures use generated addresses and bytes (the status bar says so). The real-pcap path
decodes with tshark and has not been run on a real pcap in this kit; it is a teaching viewer, not Wireshark.

## 4. Module 5.2: Smoke, full, parallel

```bash
./run.sh smoke       # robot --include smoke  --outputdir results/smoke suites
./run.sh full        # robot --exclude long   --outputdir results/full  suites
./run.sh long        # robot --include long   --outputdir results/long  suites
```

| Tag | Contains | Runs when |
| --- | --- | --- |
| `smoke` | attach, detach, default bearer: the five-minute set | every commit |
| `functional` | all procedure suites | nightly |
| `kpi` | attach rate, throughput, latency, sweep | nightly or weekly |
| `long` | 300-cycle soak | weekly or release |
| `quarantine` | known flaky tests | run, not gated |

Parallel, in three steps (needs `robotframework-pabot`):

```bash
./run.sh seq         # the parallel suite in one process: passes
./run.sh conflict    # pabot --processes 2 --testlevelsplit on tests that SHARE one IMSI: fails
./run.sh parallel    # pabot ... --pabotlib --resourcefile data/pool.dat: passes
PROCESSES=4 ./run.sh parallel
```

The conflict is the "shared IMSI" row of the slide: `SharedHss` stands in for a real subscriber
database. The fix is the "unique IMSI range" idea: `Get Worker IMSI` takes one value set per worker
from `data/pool.dat` (PabotLib). `Run With Core Lock` shows the lock for a core that cannot be shared.
In this kit each Pabot worker has its own simulated lab, so the claim file is the only shared thing.
On the real VM the other three conflicts appear as well:

| Conflict | Fix |
| --- | --- |
| shared ports | one network namespace per worker (`namespace` in `pool.dat`) |
| shared IMSI | unique IMSI range per worker (done here) |
| shared core | lock it, or isolate it |
| shared capture | filter or split the pcap per worker |

Start with 2 processes on the lab VM; 4 may be too many.

## 5. Module 5.3: The pipeline

```bash
./ci/local_pipeline.sh commit     # Provision, Smoke, (Full skipped), Publish, Archive, Gate
./ci/local_pipeline.sh nightly    # smoke + full without the long tests
./ci/local_pipeline.sh weekly     # smoke + full including long

LAB_FAULT=no_ip ./ci/local_pipeline.sh nightly      # break the build on purpose
LAB_SEED=1      ./ci/local_pipeline.sh nightly      # quarantined test fails, build stays green
```

Stages: **1 Provision, 2 Smoke, 3 Full, 4 Publish, 5 Archive, 6 Gate.**
Publish and Archive always run, even after a failure. Only the Gate sets the exit code, so a red
build keeps its evidence. A failed smoke stage skips Full. Results: `results/report/report.html`,
`results/summary.md`, `results/archive/run-<mode>-<time>.tar.gz`.

`ci/gate.py results/report/output.xml [--min-pass-rate 100]` exits 0 (passed), 1 (failed) or
2 (no usable result: an empty or missing run never passes). Quarantined tests are listed but not counted.

**Jenkins:** `Jenkinsfile`. Agent label `lte-lab`, nightly `cron`, `post { always { robot ...; archiveArtifacts ... } }`.
Needs the Robot Framework plugin for the `robot` step.
**GitHub Actions:** `.github/workflows/regression.yml`. `push` runs smoke, `schedule` runs the nightly
full run (`if: github.event_name == 'schedule'`), `if: always()` uploads `results/`. Needs a
self-hosted runner labelled `lte-lab`.

> The two CI files use exactly the commands `local_pipeline.sh` runs, and those are tested. The files
> themselves are **not** tested on a real Jenkins or GitHub runner in this kit (the YAML is syntax-checked).
> Expect to adjust labels, credentials and plugin versions for your server.

## 6. Module 5.4: Keeping a growing suite alive

```bash
./run.sh lint            # the suites are clean
./run.sh lintdemo        # what lint catches: DOC, REQ, TYPE, SLEEP, DATA
./run.sh quarantine      # the flaky test, seed 42
LAB_SEED=1 ./run.sh quarantine      # same seed = same failure, every time
./run.sh flaky 6         # 6 runs, seeds 1..6, then the flaky report
./run.sh trace results/full/output.xml
```

- **Four layers:** tests (`suites/`), resource keywords (`resources/`), libraries (`libraries/`),
  data (`env/`, `data/`). A new lab needs a new `env/labNN.py`, not new tests.
- **Seeds:** `LAB_SEED` makes the simulated random behaviour repeatable. The flaky test fails on
  seeds 1 to 3 and passes on seed 4. A failure you can repeat is a bug report; one you cannot is a rerun.
  `versions.txt` in the evidence folder records the seed.
- **Quarantine, do not delete:** add the `quarantine` tag, put ticket, owner and deadline in the
  documentation, review weekly. It still runs; the gate ignores it.
- **Flaky causes:** timing (wait on state, not sleep), shared state (reset in setup), contention
  (isolate or lock), real intermittent defect (capture, raise a defect).

## 7. Exercises

`exercises/EXERCISES.md` has the steps for each module. `./run.sh mine` runs your file
`exercises/my_pipeline_tests.robot` (five TODOs; one test fails on purpose).

## 8. Pointing it at the real lab (5G SA later)

Replace only the interface layer:
1. `libraries/day2_lte.py`: the simulated lab; the real version drives Open5GS, the eNodeB and UEs.
2. `env/lab01.py`: copy to `env/lab02.py`, set hosts, IMSI, thresholds.
3. `libraries/capture_backend.py`: the tshark path for real pcaps (already present from Day 4).
4. `EvidenceLib._write_versions`: add the Open5GS / OAI / tshark versions.

Suites, resources, CI files, gate, lint and flaky tools stay as they are.
For 5G SA: same keywords and the same CI, with NGAP and 5G NAS captures
(registration and PDU session follow the pattern of attach and default bearer).

## 9. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `No module named pabot.__main__` | run `pabot ...` or `python -m pabot.pabot ...` |
| `pabot: command not found` | `pip install robotframework-pabot` |
| `./run.sh conflict` passes | the tests did not overlap; rerun, or use `PROCESSES=2` |
| `./run.sh parallel` finds no value set | `data/pool.dat` needs as many sets as `--processes` |
| `ci/gate.py` exits 2 | the stage before it produced no `output.xml` |
| `No keyword with name 'x    y'` | two or more spaces between a keyword and its arguments |
| the `robot` step is unknown in Jenkins | install the Robot Framework plugin |

## 10. Trainer notes

- Timing: 5.1 about 35 min, 5.2 lab 55, 5.3 lab 70, 5.4 about 50.
- Run `./run.sh conflict` live first: the failure message names the cause, which is the point of 5.1 and 5.2.
- `LAB_SEED=1 ./ci/local_pipeline.sh nightly` shows quarantine well: a red test, a green build.
- `LAB_FAULT=no_ip ./ci/local_pipeline.sh nightly` shows the "always publish" rule.
- Lint, gate and flaky report are plain Python on `robot.api`: good material for "what else could you build".
