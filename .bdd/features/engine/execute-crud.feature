# Intent: .idd/modules/engine/INTENT.md
# Layer: Examples (Command Execution)

Feature: Execute CRUD Commands Against Real APIs
  CRUD commands map to HTTP methods and produce appropriate display output.
  All tests run against a real local test server serving fixture specs.

  Background:
    Given a test API server is running with the Petstore fixture

  Scenario: List resources displays a table
    When the user runs "happi testapi pet list"
    Then the exit code is 0
    And the output contains a numbered table with "#" column
    And the output contains a row count footer

  Scenario: Show a resource displays a card
    When the user runs "happi testapi pet show 1"
    Then the exit code is 0
    And the output contains a card with the pet's name
    And the output contains humanized timestamps

  Scenario: Create a resource sends POST and shows success
    When the user runs "happi testapi pet create --name Buddy --status available"
    Then the exit code is 0
    And the output contains "✓" and "Created"
    And the output contains "Buddy"
    And the output contains hint "↳"

  Scenario: Update a resource sends PUT and shows success
    When the user runs "happi testapi pet update 1 --status sold"
    Then the exit code is 0
    And the output contains "✓" and "Updated"

  Scenario: Delete prompts for confirmation in interactive mode
    Given the terminal is interactive (TTY)
    When the user runs "happi testapi pet delete 1" with stdin "y"
    Then the output contains "⚠" and "Delete"
    And the exit code is 0

  Scenario: Delete with --yes skips confirmation
    When the user runs "happi testapi pet delete 1 --yes"
    Then the exit code is 0
    And the output does not contain "⚠"
    And the output contains "✓"

  Scenario: Delete in non-interactive mode without --yes fails
    Given the terminal is non-interactive (pipe)
    When the user runs "happi testapi pet delete 1"
    Then the exit code is non-zero
    And the output contains "Use --yes"

  Scenario: JSON output mode
    When the user runs "happi testapi pet show 1 --json"
    Then the output is valid JSON
    And the output does not contain "✓" or "↳"

  Scenario: Pipe mode defaults to JSON
    Given the terminal is non-interactive (pipe)
    When the user runs "happi testapi pet list"
    Then the output is valid JSON
