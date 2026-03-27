Feature: Global flags must not be consumed as positional arguments
  When a user passes --json, --output, --yes, --quiet, or --yaml after
  the verb, those flags must be stripped before splitting into positional
  args vs extras. Otherwise they get mistakenly used as path parameter values.

  Background:
    Given a test API server is running with the Petstore fixture

  @wip
  Scenario: --json after show is not consumed as the pet ID
    When the user runs "happi testapi pets show 1 --json"
    Then the exit code is 0
    And the output is valid JSON
    And the output does not contain "not found"

  @wip
  Scenario: --output table after show is not consumed as the pet ID
    When the user runs "happi testapi pets show 1 --output table"
    Then the exit code is 0
    And the output contains "Buddy"
    And the output does not contain "not found"

  @wip
  Scenario: --yes after delete is not consumed as the pet ID
    When the user runs "happi testapi pets delete 3 --yes"
    Then the exit code is 0

  @wip
  Scenario: --quiet after list suppresses hints not breaks the call
    When the user runs "happi testapi pets list --quiet"
    Then the exit code is 0
