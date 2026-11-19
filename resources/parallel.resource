*** Settings ***
Documentation     Keywords that make a test safe to run in parallel (module 5.2).
...               The simulated lab is one process per worker, so the only thing the workers
...               really share here is the subscriber claim (SharedHss). Rule: every worker
...               gets its OWN subscriber range, taken from pool.dat when PabotLib is running.
Library           Collections
Library           SharedHss
Library           LteLib

*** Keywords ***
Get Worker IMSI
    [Documentation]    Return an IMSI that no other worker uses.
    ...    With Pabot + PabotLib: take a value set from data/pool.dat (one set per worker).
    ...    Without Pabot: return the default ${IMSI}.
    ${uri}=    Get Variable Value    ${PABOTLIBURI}    ${NONE}
    IF    $uri is None
        RETURN    ${IMSI}
    END
    Import Library    pabot.PabotLib
    ${set}=    Acquire Value Set
    ${imsi}=    Get Value From Set    imsi
    Set Test Variable    ${VALUE_SET}    ${set}
    RETURN    ${imsi}

Release Worker IMSI
    ${set}=    Get Variable Value    ${VALUE_SET}    ${NONE}
    IF    $set is not None
        Release Value Set
    END

Run With Core Lock
    [Documentation]    Run a keyword while holding a PabotLib lock: use when the core must be
    ...    reconfigured and cannot be shared. Without Pabot it simply runs the keyword.
    [Arguments]    ${keyword}    @{args}
    ${uri}=    Get Variable Value    ${PABOTLIBURI}    ${NONE}
    IF    $uri is None
        ${r}=    Run Keyword    ${keyword}    @{args}
        RETURN    ${r}
    END
    Import Library    pabot.PabotLib
    Acquire Lock    core
    TRY
        ${r}=    Run Keyword    ${keyword}    @{args}
    FINALLY
        Release Lock    core
    END
    RETURN    ${r}
