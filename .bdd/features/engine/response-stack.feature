# Intent: .idd/modules/engine/INTENT.md
# Layer: Examples (Response Stack)

Feature: Response Stack for Interactive Sessions
  The response stack lets users reference previous results with _ syntax.
  It is interactive-only and disabled in non-TTY mode.

  Background:
    Given a test API server is running with the Petstore fixture
    And the terminal is interactive (TTY)

  Scenario: _ resolves to the last created resource ID
    When the user runs "happi testapi pet create --name Buddy --status available"
    And the created pet has id "42"
    And the user runs "happi testapi pet show _"
    Then the second command resolves to "happi testapi pet show 42"
    And the exit code is 0

  Scenario: _1 resolves to the previous result
    When the user runs "happi testapi pet create --name Buddy" with result id "42"
    And the user runs "happi testapi pet create --name Rex" with result id "43"
    And the user runs "happi testapi pet show _1"
    Then the third command resolves to "happi testapi pet show 42"

  Scenario: _.field resolves to a specific field
    When the user runs "happi testapi pet show 1" returning name "Buddy"
    And the user runs with argument "_.name"
    Then the argument resolves to "Buddy"

  Scenario: _ after list produces an error
    When the user runs "happi testapi pet list" returning 5 items
    And the user runs "happi testapi pet show _"
    Then the exit code is non-zero
    And the error message contains "list"
    And the error message suggests using "_[0].id"

  Scenario: Stack has maximum 20 entries
    When the user runs 25 sequential create commands
    And the user runs "happi testapi stack"
    Then the stack shows exactly 20 entries

  Scenario: Stack is disabled in non-interactive mode
    Given the terminal is non-interactive (pipe)
    When the user runs "happi testapi pet create --name Buddy" with result id "42"
    And the user runs "happi testapi pet show _"
    Then the exit code is non-zero
    And the error message contains "interactive"

  Scenario: Stack command shows entries
    When the user runs "happi testapi pet create --name Buddy" with result id "42"
    And the user runs "happi testapi pet show 42"
    And the user runs "happi testapi stack"
    Then the output shows 2 stack entries
    And each entry shows source command and timestamp

  Scenario: Stack is isolated per API
    When the user runs "happi stripe customers create --email a@example.com" with result id "cus_123"
    And the user runs "happi github repos list"
    And the user runs "happi stripe customers show _"
    Then the command resolves to the Stripe customer created earlier

  Scenario: Session ends remove stack state but not history
    When the user runs "happi stripe customers create --email a@example.com" with result id "cus_123"
    And the process exits
    And a new process starts
    And the user runs "happi stripe customers show _"
    Then the command fails with "No previous result in this session"
    And "happi stripe history" still shows the earlier create command
