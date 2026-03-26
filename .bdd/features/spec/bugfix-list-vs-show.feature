Feature: GET with path param and no collection GET must map to show not list
  When a spec has GET /resources/{id} but no GET /resources, the operation
  must be classified as "show" not "list". Calling "list" without an ID
  should not exist as a command.

  Scenario: GET /{resource}/{id} without GET /{resource} becomes show
    Given a spec with only "GET" on path "/phone-numbers/{phoneNumberId}"
    When verbs are inferred
    Then the operation verb is "show"
    And no "list" verb exists for resource "phone-numbers"

  Scenario: GET /{resource} without {id} becomes list
    Given a spec with only "GET" on path "/secrets"
    When verbs are inferred
    Then the operation verb is "list"
