# Intent: .idd/modules/engine/INTENT.md
# Layer: Examples (Non-CRUD Actions)

Feature: Execute Non-CRUD Action Commands
  Actions are non-standard operations inferred from path segments
  like /activate, /send, /refund. They use the path segment as the verb.

  Background:
    Given a test API server is running with an action-rich fixture

  @wip
  Scenario: Execute a simple action
    When the user runs "happi testapi user activate 123"
    Then the exit code is 0
    And the output contains "✓" and "Activated"

  @wip
  Scenario: Execute an action with body params
    When the user runs "happi testapi invoice send 456 --email alice@example.com"
    Then the exit code is 0
    And the output contains "✓" and "Sent"

  @wip
  Scenario: Action with no path param
    When the user runs "happi testapi report generate --format pdf"
    Then the exit code is 0
    And the output contains "✓"
