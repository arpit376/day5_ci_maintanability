*** Settings ***
Documentation     Long-running stability tests (tag: long). Excluded from smoke and from the
...               normal full run; they run weekly or per release (module 5.2, tag strategy).
Library           LteLib
Library           KpiLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
Attach Detach Soak 300 Cycles
    [Documentation]    300 attach/detach cycles on one UE: no cycle may fail, no bearer may leak.
    [Tags]    long    stability    REQ-STAB-01
    ${kpi}=    Run Attach Cycles    300    ${IMSI}
    Should Be Equal As Integers    ${kpi}[successes]    ${kpi}[attempts]
    ...    msg=Soak: ${kpi}[successes]/${kpi}[attempts] attaches worked. Check the log for the first failing cycle.
    Bearer Should Not Exist    ${IMSI}
