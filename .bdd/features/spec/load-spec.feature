# Intent: .idd/modules/spec/INTENT.md
# Layer: Examples (Spec Loading)

Feature: Load OpenAPI Specifications
  The tool must load OpenAPI 3.x specs from local files, remote URLs, and LAP,
  resolve all $ref references, and handle errors gracefully.

  Scenario: Load Petstore spec from local YAML file
    Given a local copy of the Petstore OpenAPI spec at "fixtures/petstore.yaml"
    When the spec is loaded from "fixtures/petstore.yaml"
    Then the spec is parsed successfully
    And the spec title is "Swagger Petstore - OpenAPI 3.0"
    And the spec contains at least 3 resources

  Scenario: Load Petstore spec from remote URL
    When the spec is loaded from "https://petstore3.swagger.io/api/v3/openapi.json"
    Then the spec is parsed successfully
    And the spec title is "Swagger Petstore - OpenAPI 3.0"

  Scenario: Load GitHub API spec (massive, 900+ operations)
    Given a local copy of the GitHub OpenAPI spec at "fixtures/github.yaml"
    When the spec is loaded from "fixtures/github.yaml"
    Then the spec is parsed successfully
    And the spec contains at least 100 resources

  Scenario: Load Stripe spec (complex schemas, polymorphic types)
    Given a local copy of the Stripe OpenAPI spec at "fixtures/stripe.yaml"
    When the spec is loaded from "fixtures/stripe.yaml"
    Then the spec is parsed successfully
    And the spec contains at least 50 resources

  Scenario: Load Spotify spec (non-CRUD music domain)
    Given a local copy of the Spotify OpenAPI spec at "fixtures/spotify.yaml"
    When the spec is loaded from "fixtures/spotify.yaml"
    Then the spec is parsed successfully

  Scenario: Load Cloudflare spec (large multi-product)
    Given a local copy of the Cloudflare OpenAPI spec at "fixtures/cloudflare.yaml"
    When the spec is loaded from "fixtures/cloudflare.yaml"
    Then the spec is parsed successfully
    And the spec contains at least 50 resources

  Scenario: Load SendGrid spec (mail API)
    Given a local copy of the SendGrid OpenAPI spec at "fixtures/sendgrid.yaml"
    When the spec is loaded from "fixtures/sendgrid.yaml"
    Then the spec is parsed successfully

  Scenario: Load GitLab spec (DevOps API)
    Given a local copy of the GitLab OpenAPI spec at "fixtures/gitlab.yaml"
    When the spec is loaded from "fixtures/gitlab.yaml"
    Then the spec is parsed successfully
    And the spec contains at least 50 resources

  Scenario: Load Netlify spec (platform API)
    Given a local copy of the Netlify OpenAPI spec at "fixtures/netlify.json"
    When the spec is loaded from "fixtures/netlify.json"
    Then the spec is parsed successfully

  Scenario: Load PagerDuty spec (incident API)
    Given a local copy of the PagerDuty OpenAPI spec at "fixtures/pagerduty.json"
    When the spec is loaded from "fixtures/pagerduty.json"
    Then the spec is parsed successfully
    And the spec contains at least 20 resources

  Scenario: Load all 10 fixture specs without panic
    Given all 10 fixture specs are available locally
    When each spec is loaded sequentially
    Then all 10 specs parse successfully
    And no panic occurs for any spec

  Scenario: Handle nonexistent file gracefully
    When the spec is loaded from "nonexistent.yaml"
    Then the load fails with error code "FILE_NOT_FOUND"
    And the error message contains "nonexistent.yaml"

  Scenario: Handle invalid file gracefully
    Given a file "fixtures/garbage.txt" containing "this is not openapi"
    When the spec is loaded from "fixtures/garbage.txt"
    Then the load fails with error code "INVALID_SPEC"
    And no panic occurs

  Scenario: Resolve $ref references
    Given a spec with $ref references to shared schemas
    When the spec is loaded
    Then all $ref references are resolved inline
    And no unresolved $ref remains in the resource model

  Scenario: Configure resolves a spec from the LAP registry by name
    Given the LAP registry contains an API named "stripe"
    When the user runs "happi configure stripe"
    Then the spec source is resolved from LAP
    And the profile is created successfully

  Scenario: Remote specs are freshness-checked at most once every 24 hours
    Given a remote spec was checked 2 hours ago
    When the same command runs again
    Then the cached parsed model is reused without checking the remote source

  Scenario: Remote specs are rechecked after 24 hours
    Given a remote spec was checked 25 hours ago
    When the same command runs again
    Then the remote source is checked for freshness before using the cache
