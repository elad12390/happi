# Intent: .idd/modules/display/INTENT.md
# Layer: Examples (Hint System)

Feature: Contextual Action Hints
  After every output, the CLI suggests natural next commands using ↳.
  Hints are context-aware and hidden in non-interactive mode.

  Background:
    Given a test API server is running with the Petstore fixture
    And the terminal is interactive (TTY)

  Scenario: Hints after create suggest show and update
    When the user runs "happi testapi pet create --name Buddy --status available"
    Then the output contains "↳" followed by "pet show _"
    And the output contains "↳" followed by "pet update _"

  Scenario: Hints after list suggest show with index
    When the user runs "happi testapi pet list"
    Then the output contains "↳" followed by "pet show"

  Scenario: No hints referencing deleted resource after delete
    When the user runs "happi testapi pet delete 1 --yes"
    Then the output does not contain "↳" followed by "pet show _"

  Scenario: Hints hidden in quiet mode
    When the user runs "happi testapi pet create --name Buddy --quiet"
    Then the output does not contain "↳"

  Scenario: Hints hidden in non-TTY mode
    Given the terminal is non-interactive (pipe)
    When the user runs "happi testapi pet create --name Buddy"
    Then the output does not contain "↳"
