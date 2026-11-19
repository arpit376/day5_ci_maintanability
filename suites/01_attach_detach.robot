*** Settings ***
Documentation     Functional suite: attach and detach (module 4.2).
Library           LteLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
Attach With A Valid Subscriber
    [Documentation]    Precondition: core and eNodeB up, IMSI provisioned.
    ...                Stimulus: attach. Pass: Attach Complete and an IP in time.
    [Tags]    smoke    functional    attach    REQ-ATTACH-01
    Provision Default Subscriber
    ${result}=    Attach And Verify IP    ${IMSI}    timeout=30s
    Should Be True    ${result.setup_ms} < 30000

Detach Leaves No Bearer Behind
    [Documentation]    After detach the bearer must be gone (clean detach).
    [Tags]    smoke    functional    attach    REQ-ATTACH-02
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    Detach UE    ${IMSI}
    Bearer Should Not Exist    ${IMSI}

Attach Setup Time Is Recorded
    [Documentation]    Every attach reports a positive setup time.
    [Tags]    functional    attach    REQ-ATTACH-03
    Provision Default Subscriber
    ${result}=    Attach UE    ${IMSI}
    Should Be True    ${result.setup_ms} > 0
