*** Settings ***
Library           LteLib

*** Test Cases ***
No Docs No Tags
    Sleep    5s
    Provision Subscriber    001010123456001    00112233445566778899aabbccddeeff    63bfa50ee6523365ff14c1f45f88737d
    Log    connect to 10.0.1.10

Has Tags But No Requirement
    [Documentation]    Tagged, but with no REQ tag.
    [Tags]    functional
    Log    ok
