*** Settings ***
Documentation     Weak versus actionable failure messages (module 5.1, slide "A failure message
...               that helps"). Both tests fail on purpose. Compare the two messages in log.html,
...               then rewrite two of YOUR OWN failure messages in the second form.
Library           LteLib
Resource          ../resources/network.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
Weak Failure Message
    [Documentation]    Fails with a message nobody can act on.
    [Tags]    demo
    ${r}=    Attach UE    ${UNKNOWN_IMSI}    expect_failure=True
    Should Be Equal    ${r.status}    ATTACHED

Actionable Failure Message
    [Documentation]    Same failure, a message that names the problem and the next step.
    [Tags]    demo
    ${r}=    Attach UE    ${UNKNOWN_IMSI}    expect_failure=True
    Should Be Equal    ${r.status}    ATTACHED
    ...    msg=UE ${UNKNOWN_IMSI} was ${r.status} with EMM cause ${r.cause} (8 = IMSI unknown in HSS). Next: check the HSS subscription, then open the attach capture.    values=${FALSE}
