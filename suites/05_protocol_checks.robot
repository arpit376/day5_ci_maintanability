*** Settings ***
Documentation     Verification at the protocol level (module 4.3): decode, then assert.
Library           LteLib
Library           ProtocolLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Resource          ../resources/protocol.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
NAS Messages Appear In The Specified Order
    [Documentation]    Attach Request, Authentication, Security Mode, Attach Accept, Attach Complete.
    [Tags]    functional    protocol    REQ-PROTO-01
    ${cap}=    Capture A Successful Attach    nas_order
    NAS Messages Should Appear In Order    ${cap}    Attach Request    Authentication Request
    ...    Security Mode Command    Attach Accept    Attach Complete

Security Mode Completes Before Attach Accept
    [Documentation]    NAS security must be active before the network accepts the attach.
    [Tags]    functional    protocol    REQ-PROTO-02
    ${cap}=    Capture A Successful Attach    security
    NAS Messages Should Appear In Order    ${cap}    Security Mode Complete    Attach Accept

E-RAB ID Matches The EPS Bearer ID
    [Documentation]    The S1AP E-RAB ID equals the NAS EPS bearer ID.
    [Tags]    functional    protocol    REQ-PROTO-03
    ${cap}=    Capture A Successful Attach    erab
    E-RAB ID Should Match Bearer ID    ${cap}

Tunnel IDs Are Consistent And A Ping Is In The Tunnel
    [Documentation]    User plane built as the control plane said it would be.
    [Tags]    functional    protocol    userplane    REQ-PROTO-04
    ${cap}=    Capture A Successful Attach    gtpu
    Tunnel IDs Should Be Consistent    ${cap}
    GTP-U Should Contain Ping    ${cap}

Rejected Attach Creates No Bearer Setup
    [Documentation]    Negative, at message level: right cause, no context setup.
    [Tags]    functional    protocol    negative    REQ-PROTO-05
    ${cap}=    Capture A Rejected Attach    ${UNKNOWN_IMSI}    unknown_imsi
    NAS Messages Should Appear In Order    ${cap}    Attach Request    Attach Reject
    Reject Cause In Capture Should Be    ${cap}    ${EMM_CAUSE_UNKNOWN_IMSI}
    S1AP Message Should Not Appear    ${cap}    InitialContextSetupRequest
