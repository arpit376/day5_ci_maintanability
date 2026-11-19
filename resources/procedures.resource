*** Settings ***
Documentation     Reusable LTE procedures.
Library           LteLib

*** Keywords ***
Provision Default Subscriber
    Provision Subscriber    ${IMSI}    ${KEY}    ${OPC}

Attach And Verify IP
    [Arguments]    ${imsi}    ${timeout}=30s
    [Documentation]    Attach, check an IP was allocated, return the AttachResult.
    ${result}=    Attach UE    ${imsi}    ${timeout}
    Should Be Equal    ${result.status}    ATTACHED
    Should Not Be Empty    ${result.ip}    msg=UE ${imsi} attached but got no IP. Check the P-GW and the default bearer.
    RETURN    ${result}
