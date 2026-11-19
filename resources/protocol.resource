*** Settings ***
Documentation     Capture a procedure, then assert on the decoded messages.
Library           LteLib
Library           ProtocolLib

*** Keywords ***
Capture A Successful Attach
    [Arguments]    ${name}=attach
    [Documentation]    Provision, capture S1 during an attach plus a ping, return the capture file.
    Start Capture
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}
    Ping Through Tunnel    ${IMSI}
    ${capture}=    Stop Capture    ${name}
    RETURN    ${capture}

Capture A Rejected Attach
    [Arguments]    ${imsi}    ${name}=reject
    Start Capture
    Attach UE    ${imsi}    expect_failure=True
    ${capture}=    Stop Capture    ${name}
    RETURN    ${capture}
