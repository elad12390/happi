# Intent: .idd/modules/config/INTENT.md
# Layer: Examples (Profile Management)

Feature: API Profile Management
  Users configure API profiles with base URL, auth, and spec location.
  Profiles are stored in ~/.happi/config.yaml.

  @wip
  Scenario: Configure a new API profile
    Given no config file exists
    When the user runs "happi configure petstore" with input:
      | prompt   | answer                                         |
      | Base URL | https://petstore3.swagger.io/api/v3             |
      | Auth     | api-key                                        |
      | Header   | X-API-Key                                      |
      | Value    | special-key                                    |
    Then a config file is created at "~/.happi/config.yaml"
    And the config contains a profile named "petstore"
    And the profile has base URL "https://petstore3.swagger.io/api/v3"

  @wip
  Scenario: Multiple profiles supported
    Given a config with profiles "petstore" and "dummyjson"
    When the user runs "happi petstore pet list"
    Then the command uses the petstore profile
    When the user runs "happi dummyjson products list"
    Then the command uses the dummyjson profile

  @wip
  Scenario: Override file in cwd is loaded
    Given a config with profile "myapi"
    And a file ".happi.yaml" exists in the current directory with relation overrides
    When the CLI loads configuration
    Then the override relations are applied
    And global config is not replaced

  @wip
  Scenario: Config created on first configure
    Given no config directory exists
    When the user runs "happi configure testapi" with valid input
    Then the directory "~/.happi/" is created
    And the config file is created

  @wip
  Scenario: Profile name is independent from spec title
    When the user runs "happi configure stripe-live --spec fixtures/stripe.yaml"
    Then the profile name is "stripe-live"
    And the profile command prefix is "happi stripe-live"

  @wip
  Scenario: Configure can skip auth and add it later
    When the user runs "happi configure petstore --spec fixtures/petstore.json"
    Then the profile is created without auth
    And documentation and explore commands are still usable
    And the user can later run "happi auth set petstore"

  @wip
  Scenario: Multiple servers choose a production-like HTTPS server automatically
    Given a spec with servers "https://api.example.com", "https://staging.example.com", and "http://localhost:3000"
    When the user runs "happi configure myapi --spec fixtures/multi-server.yaml"
    Then the configured base URL is "https://api.example.com"

  @wip
  Scenario: Explicit --server overrides automatic selection
    Given a spec with multiple servers
    When the user runs "happi configure myapi --spec fixtures/multi-server.yaml --server https://staging.example.com"
    Then the configured base URL is "https://staging.example.com"
