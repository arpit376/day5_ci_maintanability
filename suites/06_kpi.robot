*** Settings ***
Documentation     KPIs need statistics: many cycles, median and p95, thresholds from data (module 4.4).
Library           LteLib
Library           KpiLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Resource          ../resources/kpi.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
Attach Success Rate And Setup Time
    [Documentation]    40 attach cycles: success rate and p95 setup time.
    [Tags]    kpi    REQ-KPI-01
    ${kpi}=    Run Attach Cycles    40    ${IMSI}
    Log    ${kpi}[successes]/${kpi}[attempts] = ${kpi}[success_rate] %, median ${kpi}[median_ms] ms, p95 ${kpi}[p95_ms] ms    console=True
    Save KPI Summary    ${OUTPUT DIR}/kpi_attach.json    ${kpi}
    Attach KPIs Should Meet Thresholds    ${kpi}

Downlink Throughput After Warm-up
    [Documentation]    Mean over 10 s with the first 2 s (TCP ramp-up) excluded.
    [Tags]    kpi    REQ-KPI-02
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    ${mbps}=    Measure Throughput    DL    duration=10s    warmup=2s
    Log    DL ${mbps} Mbit/s    console=True
    Throughput Should Be At Least    ${mbps}    ${DL_MIN_MBPS}

Latency Of Many Pings
    [Documentation]    30 pings through the tunnel: p95 latency within the threshold.
    [Tags]    kpi    REQ-KPI-03
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    ${lat}=    Measure Latency    ${IMSI}    count=30
    Log    mean ${lat}[mean_ms] ms, p95 ${lat}[p95_ms] ms    console=True
    Latency Should Meet Threshold    ${lat}
