*** Settings ***
Documentation     DEMO of a parallel conflict (module 5.2): every test claims the SAME fixed IMSI.
...               Sequential run: all pass. With pabot --testlevelsplit: the first overlap fails.
...               Fix: suites/parallel/10_parallel_attach.robot (a worker-specific IMSI).
Library           LteLib
Library           SharedHss
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Run Keywords    Release Subscriber    ${IMSI}    AND    Collect Artefacts

*** Test Cases ***
Conflict Attach A
    [Documentation]    Uses the fixed IMSI from the variable file: shared by all tests.
    [Tags]    demo    parallel-conflict
    Claim Subscriber    ${IMSI}
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    Sleep    1s
    Detach UE    ${IMSI}

Conflict Attach B
    [Documentation]    Uses the fixed IMSI from the variable file: shared by all tests.
    [Tags]    demo    parallel-conflict
    Claim Subscriber    ${IMSI}
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    Sleep    1s
    Detach UE    ${IMSI}

Conflict Attach C
    [Documentation]    Uses the fixed IMSI from the variable file: shared by all tests.
    [Tags]    demo    parallel-conflict
    Claim Subscriber    ${IMSI}
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    Sleep    1s
    Detach UE    ${IMSI}

Conflict Attach D
    [Documentation]    Uses the fixed IMSI from the variable file: shared by all tests.
    [Tags]    demo    parallel-conflict
    Claim Subscriber    ${IMSI}
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    Sleep    1s
    Detach UE    ${IMSI}
