*** Settings ***
Documentation     Default bearer, service request and tracking area update (module 4.2).
Library           LteLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
Default Bearer Is Active With An IP
    [Documentation]    After attach the default bearer is active and the UE has an IP.
    [Tags]    smoke    functional    bearer    REQ-BEARER-01
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    ${bearer}=    Bearer Should Exist    ${IMSI}
    Should Be Equal As Integers    ${bearer}[ebi]    5
    Should Not Be Empty    ${bearer}[ip]

Service Request Restores The Bearer After Idle
    [Documentation]    Idle, then downlink data: paging, and the bearer is restored.
    [Tags]    functional    idle    REQ-IDLE-01
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    Go Idle    ${IMSI}
    ${sr}=    Service Request    ${IMSI}    downlink_data=True
    Should Be Equal    ${sr}[status]    ACTIVE
    Should Be True    ${sr}[paging]
    Should Be True    ${sr}[bearer_restored]

Tracking Area Update Is Accepted
    [Documentation]    An attached UE sends a TAU and the network accepts it.
    [Tags]    functional    tau    REQ-TAU-01
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    ${tau}=    Tracking Area Update    ${IMSI}
    Should Be Equal    ${tau}[status]    TAU_ACCEPTED
