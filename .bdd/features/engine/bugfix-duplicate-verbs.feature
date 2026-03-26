Feature: Duplicate verb names within a resource must be disambiguated
  When multiple operations on the same resource map to the same verb name
  (e.g. two different endpoints both becoming "list"), the duplicates must
  be disambiguated so no operation is silently lost.

  Scenario: Two GET endpoints on same resource produce distinct verbs
    Given a spec with "GET" on "/agents" and "GET" on "/agents/{agentId}"
    When resources are extracted
    Then resource "agents" has both "list" and "show" verbs
    And no verb is duplicated within resource "agents"

  Scenario: Multiple action endpoints with different paths get unique names
    Given a spec with "POST" on "/agents/{id}/branches" and "DELETE" on "/agents/{id}/branches/{branchId}"
    When resources are extracted
    Then resource "agents" has verbs that are all unique
