*** Settings ***
Documentation     One test body, many rows: sweep bandwidth and UE count (module 4.4).
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
Test Tags         kpi    sweep    REQ-KPI-04
Test Template     Measure And Assert DL Throughput

*** Test Cases ***                  BW_MHZ    UES    MIN_DL
5 MHz, 1 UE                         5         1      ${DL_MIN_5}
10 MHz, 1 UE                        10        1      ${DL_MIN_10}
20 MHz, 2 UEs                       20        2      ${DL_MIN_20}

*** Keywords ***
Measure And Assert DL Throughput
    [Arguments]    ${bw_mhz}    ${ues}    ${min_dl}
    [Documentation]    Per-UE downlink throughput must reach the threshold for this row.
    ${prb}=    Set Cell Bandwidth    ${bw_mhz}
    ${imsis}=    Provision Subscribers    count=${ues}
    ${results}=    Attach UEs    ${imsis}
    FOR    ${r}    IN    @{results}
        Should Be Equal    ${r.status}    ATTACHED    msg=UE ${r.imsi} did not attach in the ${bw_mhz} MHz row.
    END
    ${mbps}=    Measure Throughput    DL    duration=10s    warmup=2s    ues=${ues}
    Log    ${bw_mhz} MHz (${prb} PRB), ${ues} UE(s): ${mbps} Mbit/s per UE    console=True
    Throughput Should Be At Least    ${mbps}    ${min_dl}    label=${bw_mhz} MHz x ${ues} UE
