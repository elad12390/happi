Feature: All spec paths must produce resources with no silent omissions
  Every path in the OpenAPI spec must result in at least one resource
  and operation. Version prefixes (/v1, /v2, /api) are stripped but
  the path segment after them must still produce a resource.

  @wip
  Scenario: Paths with version prefix still produce resources
    Given a spec with paths "/v1/voices", "/v1/voices/{voiceId}"
    When resources are extracted
    Then a resource named "voices" exists
    And resource "voices" has verbs including "list" and "show"

  @wip
  Scenario: Deep nested paths still produce resources
    Given a spec with path "/v1/text-to-speech/{voice_id}/stream"
    When resources are extracted
    Then the path produces at least one resource with at least one operation
