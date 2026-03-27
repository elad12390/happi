# Intent: .idd/modules/engine/INTENT.md
# Layer: Examples (Command Tree Generation)

Feature: Generate Command Tree from Resource Model
  The CLI dynamically registers Typer commands from the parsed resource model.
  Resources become subcommands, verbs become sub-subcommands, path params
  become positional args, and query/body params become flags.

  @wip
  Scenario: Resources appear as top-level subcommands
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore --help"
    Then the output lists "pet", "store", "user" as available commands

  @wip
  Scenario: Verbs appear as subcommands under a resource
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore pet --help"
    Then the output lists verbs including "list", "show", "create", "update", "delete"
    And the output lists actions including "upload-image"

  @wip
  Scenario: Path params become positional arguments
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore pet show --help"
    Then the help shows a positional argument for the pet ID

  @wip
  Scenario: Query params become optional flags
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore pet list --help"
    Then the help shows optional flags including "--status"

  @wip
  Scenario: Body schema fields become flags
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore pet create --help"
    Then the help shows flags including "--name" and "--status"

  @wip
  Scenario: Help shows response schema
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore pet show --help"
    Then the help includes a response schema section

  @wip
  Scenario: Unknown command suggests closest match
    Given the CLI is configured with the Petstore spec
    When the user runs "happi petstore pets"
    Then the output contains "Did you mean" or "pet"
    And the exit code is non-zero

  @wip
  Scenario: GitHub API registers 100+ resources without panic
    Given the CLI is configured with the GitHub spec
    When the user runs "happi github --help"
    Then the output lists at least 50 resources
    And no panic occurs
    And startup completes in less than 1000 milliseconds

  @wip
  Scenario: Stripe API groups resources with complex actions
    Given the CLI is configured with the Stripe spec
    When the user runs "happi stripe customers --help"
    Then the output lists verbs including "list", "show", "create", "update", "delete"
    When the user runs "happi stripe charges --help"
    Then the output lists actions including "capture" and "refund"

  @wip
  Scenario: Spotify API shows non-CRUD actions
    Given the CLI is configured with the Spotify spec
    When the user runs "happi spotify --help"
    Then the output lists resources including "albums", "artists", "tracks", "playlists"

  @wip
  Scenario: Cloudflare API handles multi-product grouping
    Given the CLI is configured with the Cloudflare spec
    When the user runs "happi cloudflare --help"
    Then the output lists resources including "zones" and "dns-records"
    And no panic occurs

  @wip
  Scenario: Directus API registers dynamic endpoints
    Given the CLI is configured with the Directus spec
    When the user runs "happi directus --help"
    Then the output lists at least 20 resources
    And no panic occurs

  @wip
  Scenario: Path naming beats broad tags
    Given a spec where path "/billing/payment_intents" has tag "payments"
    When the command tree is built
    Then the resource command is named "payment-intents"
    And the resource command is not named "payments"

  @wip
  Scenario: Command collisions are disambiguated with path words
    Given a spec with paths "/users/search" and "/admin/users/search"
    When the command tree is built
    Then commands named "users search" and "users admin-search" both exist
