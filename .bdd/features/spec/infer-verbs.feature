# Intent: .idd/modules/spec/INTENT.md
# Layer: Examples (Verb Mapping)

Feature: Infer Human Verbs from HTTP Methods
  HTTP methods are mapped to human verbs based on path shape.
  Non-CRUD actions use the last non-parameter path segment as the verb name.
  HTTP verbs never appear in user-facing output.

  Scenario Outline: Standard CRUD verb mapping
    Given a spec with "<method>" on path "<path>"
    When verbs are inferred
    Then the operation verb is "<verb>"

    Examples:
      | method | path            | verb    |
      | GET    | /users          | list    |
      | GET    | /users/{id}     | show    |
      | POST   | /users          | create  |
      | PUT    | /users/{id}     | update  |
      | PATCH  | /users/{id}     | update  |
      | DELETE | /users/{id}     | delete  |

  Scenario Outline: Non-CRUD action verb mapping
    Given a spec with "<method>" on path "<path>"
    When verbs are inferred
    Then the operation verb is "<verb>"
    And the operation is classified as an action

    Examples:
      | method | path                        | verb           |
      | POST   | /users/{id}/activate        | activate       |
      | POST   | /users/{id}/send-invite     | send-invite    |
      | GET    | /users/{id}/status          | status         |
      | POST   | /reports/generate           | generate       |
      | POST   | /users/search               | search         |
      | POST   | /invoices/{id}/refund       | refund         |
      | POST   | /pets/{id}/upload-image     | upload-image   |

  Scenario: Petstore verbs are correctly inferred
    Given the Petstore spec is loaded
    When verbs are inferred for resource "pet"
    Then the following verbs exist:
      | verb   |
      | show   |
      | create |
      | update |
      | delete |
    And the verb "upload-image" exists as an action
    And the verb "find-by-status" exists as an action

  Scenario: Netlify sites have CRUD-style verbs
    Given the Netlify spec is loaded
    When verbs are inferred for resource "sites"
    Then the verbs include "list", "show", "create", "update", "delete"

  Scenario: Verb names never contain HTTP method names
    Given any spec is loaded
    When all verbs are inferred
    Then no verb name contains "get", "post", "put", "patch", or "delete" as a prefix
