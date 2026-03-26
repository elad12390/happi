# Intent: .idd/modules/display/INTENT.md
# Layer: Examples (Error Output)

Feature: Human-Friendly Error Display
  Errors are rendered in 3 layers: what failed, how to fix it, and
  raw details via --debug. HTTP status codes are translated to human messages.

  Background:
    Given a test API server is running with the Petstore fixture

  Scenario: 422 validation error shows field problems
    When the user runs "happi testapi pet create" without required fields
    Then the exit code is non-zero
    And the output contains "✗" and "Couldn't create"
    And the output lists missing required fields
    And the output contains a suggestion command

  Scenario: 401 shows authentication hint
    Given the API requires authentication
    When the user runs "happi testapi pet list" without auth configured
    Then the output contains "✗" and "Authentication"
    And the output suggests "happi auth set" or "happi auth login"

  Scenario: 404 shows not found with search suggestion
    When the user runs "happi testapi pet show 99999"
    Then the output contains "✗" and "not found"
    And the output suggests "pet list"

  Scenario: 500 shows server error with debug hint
    Given the API returns a 500 error
    When the user runs the failing command
    Then the output contains "✗" and "Server error"
    And the output contains "Run with --debug"

  Scenario: --debug shows raw HTTP request and response
    When the user runs "happi testapi pet show 99999 --debug"
    Then the output contains the HTTP status line
    And the output contains response headers
    And the output contains the raw response body
