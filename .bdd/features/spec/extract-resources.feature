# Intent: .idd/modules/spec/INTENT.md
# Layer: Examples (Resource Extraction)

Feature: Extract Resources from OpenAPI Specs
  Resources are inferred from OpenAPI tags (primary) or path segments
  (fallback). The tool must handle clean specs, tag-less specs, flat specs,
  and deeply nested specs.

  Scenario: Extract resources from Petstore (clean spec with tags)
    Given the Petstore spec is loaded
    When resources are extracted
    Then the following resources exist:
      | name    |
      | pet     |
      | store   |
      | user    |
    And each resource has at least one operation

  Scenario: Extract resources from GitHub API (massive well-structured spec)
    Given the GitHub spec is loaded
    When resources are extracted
    Then resources include "repos", "issues", "pulls", "actions", "users", "orgs"
    And at least 50 resources are found
    And no two resources share the same name

  Scenario: Extract resources from Stripe (complex relations, many actions)
    Given the Stripe spec is loaded
    When resources are extracted
    Then resources include "customers", "charges", "invoices", "subscriptions", "products"
    And resources include actions like "refund", "capture", "confirm"

  Scenario: Extract resources from Spotify (non-CRUD domain)
    Given the Spotify spec is loaded
    When resources are extracted
    Then resources include "albums", "artists", "tracks", "playlists"
    And resources include actions like "play", "pause", "search"

  Scenario: Extract resources from Cloudflare (multi-product API)
    Given the Cloudflare spec is loaded
    When resources are extracted
    Then at least 50 resources are found
    And resources include "zones", "dns-records", "workers"

  Scenario: Extract resources from SendGrid (mail API)
    Given the SendGrid spec is loaded
    When resources are extracted
    Then resources include "mails", "batches"
    And resources include actions like "send"

  Scenario: Extract resources from GitLab (DevOps API)
    Given the GitLab spec is loaded
    When resources are extracted
    Then resources include "groups", "projects", "issues", "merge-requests", "pipelines"
    And at least 50 resources are found

  Scenario: Extract resources from Netlify (platform API)
    Given the Netlify spec is loaded
    When resources are extracted
    Then resources include "sites", "forms", "functions", "deploys"

  Scenario: Extract resources from PagerDuty (incident API)
    Given the PagerDuty spec is loaded
    When resources are extracted
    Then resources include "incidents", "services", "schedules", "users"
    And at least 20 resources are found

  Scenario: Extract resources from httpbin (flat utility paths, edge case)
    Given the httpbin spec is loaded
    When resources are extracted
    Then resources are grouped by first path segment
    And no resource has an empty name

  Scenario: Handle nested paths by creating parent flags
    Given a spec with path "/users/{userId}/orders"
    When resources are extracted
    Then a resource "orders" exists
    And the "orders" resource has a "list" operation
    And the "list" operation has a flag "--user" derived from the path param "userId"

  Scenario: Paths take priority over tags for resource naming
    Given a spec where path "/api/v1/customer-accounts" has tag "customers"
    When resources are extracted
    Then a resource "customer-accounts" exists
    And no resource named "customers" exists

  Scenario: Resource names are always lowercase plural
    Given any spec is loaded
    When resources are extracted
    Then all resource names are lowercase
