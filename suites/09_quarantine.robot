*** Settings ***
Documentation     Quarantined tests (module 5.4). They still RUN, so the history and the signal
...               are kept, but the CI gate ignores their result (tag: quarantine).
...               Policy: every test here has a ticket, an owner and a deadline in its documentation.
Library           LteLib
Resource          ../resources/network.resource
Resource          ../resources/procedures.resource
Variables         ../env/lab01.py
Suite Setup       Start Network
Suite Teardown    Stop Network
Test Setup        Reset UE State
Test Teardown     Quarantine Teardown

*** Test Cases ***
Five UEs Attach On A Noisy Cell
    [Documentation]    FLAKY: attaches 5 UEs while the cell rejects ~15 % of attaches at random.
    ...                Ticket: LTE-1234   Owner: alice   Fix or remove by: next Friday's review.
    ...                Reproduce a failure: LAB_SEED=<seed from versions.txt> ./run.sh quarantine
    [Tags]    functional    quarantine    REQ-ATTACH-04
    Inject Fault    flaky
    ${imsis}=    Provision Subscribers    count=5
    ${results}=    Attach UEs    ${imsis}    timeout=60s
    FOR    ${r}    IN    @{results}
        Should Be Equal    ${r.status}    ATTACHED
        ...    msg=UE ${r.imsi} was ${r.status}, cause ${r.cause}. Intermittent: see ticket LTE-1234.
    END

*** Keywords ***
Quarantine Teardown
    Inject Fault    none
    Collect Artefacts
