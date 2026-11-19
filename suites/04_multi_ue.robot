*** Settings ***
Documentation     Several UEs at once (module 4.2). Start small: the VM is the first limit.
Library           LteLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Variables ***
${UE_COUNT}      10

*** Test Cases ***
Ten UEs Attach Concurrently
    [Documentation]    ${UE_COUNT} UEs attach together: all attach, all IPs unique.
    [Tags]    functional    capacity    REQ-CAP-01
    ${imsis}=    Provision Subscribers    count=${UE_COUNT}
    ${results}=    Attach UEs    ${imsis}    timeout=60s
    FOR    ${r}    IN    @{results}
        Should Be Equal    ${r.status}    ATTACHED
        ...    msg=UE ${r.imsi} was ${r.status}, cause ${r.cause}. Is the VM at its UE limit?
    END
    All IP Addresses Should Be Unique    ${results}
