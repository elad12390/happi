# Intent: .idd/modules/http/INTENT.md
# Layer: Examples (Auth)

Feature: API Authentication
  Auth credentials are loaded from the API profile and applied
  to HTTP requests automatically.

  Background:
    Given a test API server is running that validates authentication

  Scenario: API key sent in header
    Given a profile with auth type "api-key", header "X-API-Key", value "test123"
    When the user runs a command against the test API
    Then the request includes header "X-API-Key" with value "test123"
    And the command succeeds

  Scenario: API key sent in query parameter
    Given a profile with auth type "api-key", query "api_key", value "test123"
    When the user runs a command against the test API
    Then the request URL includes query parameter "api_key=test123"
    And the command succeeds

  Scenario: Bearer token sent in Authorization header
    Given a profile with auth type "bearer", token "tok_abc123"
    When the user runs a command against the test API
    Then the request includes header "Authorization" with value "Bearer tok_abc123"
    And the command succeeds

  Scenario: No auth configured sends no auth header
    Given a profile with no auth configured
    When the user runs a command against the test API
    Then the request does not include an "Authorization" header
    And the request does not include an "X-API-Key" header

  Scenario: Missing auth explains how to configure it
    Given a profile with no auth configured
    And the API declares a bearer auth scheme
    When the user runs a protected command
    Then the output contains "Authentication required"
    And the output explains that the API expects a bearer token
    And the output suggests running "happi auth set" or "happi auth login"

  Scenario: Multiple auth schemes require explicit type
    Given the API declares auth schemes "api-key", "bearer", and "oauth2"
    When the user runs "happi auth login myapi"
    Then the command fails with an explanation of the available auth schemes
    And the output contains runnable commands with explicit "--type"

  Scenario: OAuth login opens browser by default
    Given the API declares OAuth2 authorization code flow
    When the user runs "happi auth login myapi --type oauth2"
    Then the login flow opens the browser automatically
    And the output explains the fallback manual mode if automatic login fails
