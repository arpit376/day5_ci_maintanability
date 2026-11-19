*** Settings ***
Documentation     Day 5 exercise file. Work through the TODO comments (see exercises/EXERCISES.md).
...               Run:  ./run.sh mine      Lint:  python tools/lint_suite.py exercises
Library           LteLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Resource          ../resources/parallel.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Collect Artefacts

*** Test Cases ***
My Attach Test With A Weak Message
    [Documentation]    TODO 1 (5.1): rewrite the msg= so it names the problem AND the next step.
    [Tags]    functional    REQ-ATTACH-01
    Provision Default Subscriber
    ${r}=    Attach UE    ${IMSI}
    Should Be Equal    ${r.status}    ATTACHED    msg=Attach failed

My Unknown IMSI Test With A Weak Message
    [Documentation]    TODO 2 (5.1): this must FAIL on purpose. Give it a message of the form
    ...                "UE <imsi> rejected, EMM cause <n> (<meaning>). Next: <what to check>".
    [Tags]    negative    REQ-AUTH-02
    ${r}=    Attach UE    ${UNKNOWN_IMSI}    expect_failure=True
    Should Be Equal    ${r.status}    ATTACHED    msg=Expected 1 got 0

My Attach Test That Is Not Parallel Safe
    [Documentation]    TODO 3 (5.2): replace the fixed ${IMSI} with Get Worker IMSI, and release it.
    ...                Then run  ./run.sh parallel  with PROCESSES=2 and PROCESSES=4.
    [Tags]    functional    parallel    REQ-PAR-01
    Provision Default Subscriber
    Attach And Verify IP    ${IMSI}

My Flaky Test
    [Documentation]    TODO 4 (5.4): this test is intermittent (LAB_FAULT=flaky). Add the quarantine tag,
    ...                a ticket and an owner to the documentation, and check that ci/gate.py ignores it.
    [Tags]    functional    REQ-ATTACH-04
    Inject Fault    flaky
    ${imsis}=    Provision Subscribers    count=8
    ${results}=    Attach UEs    ${imsis}
    FOR    ${r}    IN    @{results}
        Should Be Equal    ${r.status}    ATTACHED    msg=UE ${r.imsi} was ${r.status}
    END
    [Teardown]    Run Keywords    Inject Fault    none    AND    Collect Artefacts

My Test With Smells
    [Documentation]    TODO 5 (5.4): run  python tools/lint_suite.py exercises  and fix every finding.
    [Tags]    functional
    Sleep    2s
    Provision Subscriber    001010123456001    00112233445566778899aabbccddeeff    63bfa50ee6523365ff14c1f45f88737d
    Attach UE    001010123456001
