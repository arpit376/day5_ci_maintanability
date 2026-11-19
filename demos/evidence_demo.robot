*** Settings ***
Documentation     Evidence for a failing test (module 5.1). The test breaks the lab on purpose
...               (no IP is allocated). Run it, then open results/evidence_demo/evidence/<test>_<time>/.
...               Expected: lab.log, capture.json, versions.txt, result.txt and a link in log.html.
Library           LteLib
Library           ProtocolLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Evidence Demo Teardown

*** Test Cases ***
Attach Fails Without An IP Address
    [Documentation]    Fails on purpose: LAB_FAULT=no_ip. The teardown must still collect evidence.
    [Tags]    demo
    Inject Fault    no_ip
    Start Capture
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}

Passing Test Keeps No Evidence By Default
    [Documentation]    A passing test gets no evidence folder unless ${EVIDENCE_ALWAYS}=True.
    [Tags]    demo
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}

*** Keywords ***
Evidence Demo Teardown
    Inject Fault    none
    Collect Artefacts
