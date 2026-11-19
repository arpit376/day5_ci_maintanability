*** Settings ***
Documentation     Attach tests written to be safe in parallel (module 5.2):
...               each test takes its own IMSI, never a fixed one.
Library           LteLib
Library           SharedHss
Resource          ../../resources/network.resource
Resource          ../../resources/procedures.resource
Resource          ../../resources/parallel.resource
Variables         ../../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Finish Parallel Test

*** Test Cases ***
Worker Attach A
    [Documentation]    Attach with a worker-specific IMSI and hold it briefly.
    [Tags]    functional    parallel    REQ-PAR-01
    ${imsi}=    Get Worker IMSI
    Set Test Variable    ${WORKER_IMSI}    ${imsi}
    Claim Subscriber    ${imsi}
    Provision Subscriber    ${imsi}    ${KEY}    ${OPC}
    ${r}=    Attach And Verify IP    ${imsi}
    Hold Subscriber
    Detach UE    ${imsi}

Worker Attach B
    [Documentation]    Same as A, a second test that can run at the same moment.
    [Tags]    functional    parallel    REQ-PAR-01
    ${imsi}=    Get Worker IMSI
    Set Test Variable    ${WORKER_IMSI}    ${imsi}
    Claim Subscriber    ${imsi}
    Provision Subscriber    ${imsi}    ${KEY}    ${OPC}
    ${r}=    Attach And Verify IP    ${imsi}
    Hold Subscriber
    Detach UE    ${imsi}

Worker Attach C
    [Documentation]    A third parallel attach.
    [Tags]    functional    parallel    REQ-PAR-01
    ${imsi}=    Get Worker IMSI
    Set Test Variable    ${WORKER_IMSI}    ${imsi}
    Claim Subscriber    ${imsi}
    Provision Subscriber    ${imsi}    ${KEY}    ${OPC}
    ${r}=    Attach And Verify IP    ${imsi}
    Hold Subscriber
    Detach UE    ${imsi}

Worker Attach D
    [Documentation]    A fourth parallel attach.
    [Tags]    functional    parallel    REQ-PAR-01
    ${imsi}=    Get Worker IMSI
    Set Test Variable    ${WORKER_IMSI}    ${imsi}
    Claim Subscriber    ${imsi}
    Provision Subscriber    ${imsi}    ${KEY}    ${OPC}
    ${r}=    Attach And Verify IP    ${imsi}
    Hold Subscriber
    Detach UE    ${imsi}

*** Keywords ***
Hold Subscriber
    [Documentation]    Keep the subscriber busy for a moment so parallel tests really overlap.
    ...                This is a stand-in for a real traffic test; it is the only wait in the kit.
    Sleep    1s

Finish Parallel Test
    ${imsi}=    Get Variable Value    ${WORKER_IMSI}    ${NONE}
    IF    $imsi is not None
        Release Subscriber    ${imsi}
    END
    Release Worker IMSI
    Collect Artefacts
