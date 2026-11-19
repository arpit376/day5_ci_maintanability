*** Settings ***
Documentation     Start, stop and reset the lab network.
Library           LteLib
Library           EvidenceLib

*** Keywords ***
Start Network
    Start Core Network
    Start eNodeB    ${ENB_CONFIG}

Stop Network
    Stop Network Elements

Reset UE State
    Clear UE State

Collect Artefacts
    [Documentation]    Test teardown (module 5.1). A failed test gets its own evidence folder;
    ...                set ${EVIDENCE_ALWAYS}=True to keep evidence for passes too.
    Save Artefacts    ${OUTPUT DIR}/artefacts
    Collect Evidence
