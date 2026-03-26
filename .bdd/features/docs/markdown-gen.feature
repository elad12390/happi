# Intent: .idd/modules/docs/INTENT.md
# Layer: Examples (Markdown Generation)

Feature: Generate Markdown Documentation
  The docs command outputs complete Markdown documentation from a parsed
  OpenAPI spec, including resource tables, schemas, examples, and
  Mermaid relationship diagrams.

  Scenario: Generate full documentation from Petstore
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore docs"
    Then the output is valid Markdown
    And the output contains a Mermaid code block
    And the output contains sections for "pet", "store", "user"
    And each resource section contains an actions table
    And each resource section contains a schema
    And the output contains a quick reference table
    And the output contains example commands

  Scenario: Docs for a single resource
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore docs --resource pet"
    Then the output is valid Markdown
    And the output contains a section for "pet"
    And the output does not contain a section for "user"

  Scenario: Map-only outputs just the Mermaid diagram
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore docs --map-only"
    Then the output contains a Mermaid code block
    And the output does not contain resource action tables

  Scenario: Docs can be saved to a file
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore docs" and pipes to "test-output.md"
    Then the file "test-output.md" exists
    And the file contains valid Markdown

  Scenario: Docs from Stripe show complex relation graph
    Given the CLI is configured with the Stripe spec
    When the user runs "happi stripe docs"
    Then the output is valid Markdown
    And the Mermaid diagram shows edges between customers, charges, and invoices
    And the output contains at least 50 resource sections

  Scenario: Docs from GitHub handle massive spec
    Given the CLI is configured with the GitHub spec
    When the user runs "happi github docs"
    Then the output is valid Markdown
    And the Mermaid diagram shows edges between repos, issues, and pulls
    And the command completes in less than 10 seconds

  Scenario: Docs from Spotify show non-CRUD actions
    Given the CLI is configured with the Spotify spec
    When the user runs "happi spotify docs"
    Then the output is valid Markdown
    And the actions table for "tracks" includes non-CRUD verbs

  Scenario: Docs from Cloudflare handle multi-product API
    Given the CLI is configured with the Cloudflare spec
    When the user runs "happi cloudflare docs"
    Then the output is valid Markdown
    And the output contains at least 50 resource sections

  Scenario: Docs from Fake Store API include relation diagram
    Given the CLI is configured with the Fake Store API spec
    When the user runs "happi fakestore docs"
    Then the Mermaid diagram shows edges between products and categories
    And the relations table includes confidence levels

  Scenario: Docs from Directus spec handles large resource set
    Given the CLI is configured with the Directus spec
    When the user runs "happi directus docs"
    Then the output is valid Markdown
    And the output contains at least 20 resource sections
    And the command completes in less than 5 seconds

  Scenario: Docs from httpbin gracefully handles no-resource API
    Given the CLI is configured with the httpbin spec
    When the user runs "happi httpbin docs"
    Then the output is valid Markdown
    And the Mermaid diagram has nodes but minimal or no edges
