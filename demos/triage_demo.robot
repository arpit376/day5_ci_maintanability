*** Settings ***
Documentation     THREE RED RESULTS FOR TRIAGE (module 4.2). They fail on purpose.
...               Classify each as PRODUCT defect, TEST defect or ENVIRONMENT before debugging.
...               Answers are in the README (trainer section).
Library           LteLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Run Keywords    Inject Fault    none    AND    Collect Artefacts

*** Test Cases ***
Red Result A
    [Documentation]    Attach and check the IP.
    [Tags]    demo-fail    triage
    Inject Fault    no_ip
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}

Red Result B
    [Documentation]    Attach the UE and check it is attached.
    [Tags]    demo-fail    triage
    ${r}=    Attach UE    ${IMSI}    expect_failure=True
    Should Be Equal    ${r.status}    ATTACHED

Red Result C
    [Documentation]    Attach and check the IP.
    [Tags]    demo-fail    triage
    Inject Fault    core_down
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}    timeout=5s
