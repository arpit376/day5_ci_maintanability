*** Settings ***
Documentation     KPI assertions. Thresholds come from the variable file.
Library           KpiLib

*** Keywords ***
Attach KPIs Should Meet Thresholds
    [Arguments]    ${kpi}
    Should Be True    ${kpi}[success_rate] >= ${ATTACH_RATE_MIN}
    ...    msg=Attach success rate ${kpi}[success_rate] % is below ${ATTACH_RATE_MIN} % (${kpi}[successes]/${kpi}[attempts]).
    Should Be True    ${kpi}[p95_ms] <= ${SETUP_P95_MAX_MS}
    ...    msg=Attach setup p95 ${kpi}[p95_ms] ms is above ${SETUP_P95_MAX_MS} ms (median ${kpi}[median_ms] ms).

Throughput Should Be At Least
    [Arguments]    ${mbps}    ${minimum}    ${label}=DL
    Should Be True    ${mbps} >= ${minimum}
    ...    msg=${label} throughput ${mbps} Mbit/s is below ${minimum} Mbit/s.

Latency Should Meet Threshold
    [Arguments]    ${lat}
    Should Be True    ${lat}[p95_ms] <= ${LAT_P95_MAX_MS}
    ...    msg=Latency p95 ${lat}[p95_ms] ms is above ${LAT_P95_MAX_MS} ms (mean ${lat}[mean_ms] ms).
