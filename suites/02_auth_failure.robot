*** Settings ***
Documentation     Negative tests: the rejection must be the right one (module 4.2).
Library           LteLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
Attach With Wrong Key Is Rejected
    [Documentation]    A wrong key must fail authentication with the expected cause.
    [Tags]    negative    auth    REQ-AUTH-01
    Provision Subscriber    ${IMSI}    ${WRONG_KEY}    ${OPC}
    ${r}=    Attach UE    ${IMSI}    expect_failure=True
    Should Be Equal    ${r.status}    REJECTED
    Should Be Equal As Integers    ${r.cause}    ${EMM_CAUSE_MAC_FAILURE}
    Bearer Should Not Exist    ${IMSI}

Attach With Unknown IMSI Is Rejected
    [Documentation]    A subscriber missing from the HSS must be rejected with EMM cause 8.
    [Tags]    negative    auth    REQ-AUTH-02
    ${r}=    Attach UE    ${UNKNOWN_IMSI}    expect_failure=True
    Should Be Equal    ${r.status}    REJECTED
    Should Be Equal As Integers    ${r.cause}    ${EMM_CAUSE_UNKNOWN_IMSI}
    Bearer Should Not Exist    ${UNKNOWN_IMSI}

Network Recovers After A Rejected Attach
    [Documentation]    A valid attach right after a reject must still work.
    [Tags]    negative    auth    REQ-AUTH-03
    Attach UE    ${UNKNOWN_IMSI}    expect_failure=True
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
