# Intent: .idd/modules/spec/INTENT.md
# Layer: Examples (Relationship Inference)

Feature: Infer Resource Relationships
  Relationships between resources are inferred from field names (_id, _ids),
  path nesting, and $ref schema references. Each relation has a confidence
  level: certain, high, or medium.

  @wip
  Scenario Outline: Infer belongs-to from _id fields
    Given a spec where resource "<resource>" has field "<field>"
    And a resource named "<target>" exists
    When relations are inferred
    Then a relation exists from "<resource>" to "<target>"
    And the relation type is "belongs-to"
    And the relation confidence is "<confidence>"

    Examples:
      | resource | field         | target      | confidence |
      | orders   | customer_id   | customers   | high       |
      | orders   | userId        | users       | high       |
      | posts    | author_id     | users       | high       |
      | comments | post_id       | posts       | high       |

  @wip
  Scenario: Infer has-many from array _ids fields
    Given a spec where resource "posts" has field "tag_ids" of type array
    And a resource named "tags" exists
    When relations are inferred
    Then a relation exists from "posts" to "tags"
    And the relation type is "has-many"
    And the relation confidence is "high"

  @wip
  Scenario: Infer has-many from path nesting
    Given a spec with path "/users/{userId}/orders"
    When relations are inferred
    Then a relation exists from "users" to "orders"
    And the relation type is "has-many"
    And the relation via is "path"
    And the relation confidence is "certain"

  @wip
  Scenario: Infer from $ref in schema
    Given a spec where resource "orders" response schema contains "$ref" to "User"
    And a resource named "users" exists
    When relations are inferred
    Then a relation exists from "orders" to "users"
    And the relation confidence is "certain"

  @wip
  Scenario: Detect self-referential relationship
    Given a spec where resource "categories" has field "parent_id"
    When relations are inferred
    Then a relation exists from "categories" to "categories"
    And the relation type is "belongs-to"
    And the relation via is "parent_id"

  @wip
  Scenario: No relation when target resource doesn't exist
    Given a spec where resource "orders" has field "coupon_code"
    And no resource named "coupon-codes" or "coupons" exists
    When relations are inferred
    Then no relation is created for field "coupon_code"

  @wip
  Scenario: Ambiguous relation detected
    Given a spec where resource "projects" has field "owner_id"
    And resources named "users" and "organizations" both exist
    When relations are inferred
    Then relations to both "users" and "organizations" are created
    And both relations have confidence "medium"

  @wip
  Scenario: Medium confidence for convention fields
    Given a spec where resource "orders" has field "created_by"
    And a resource named "users" exists
    When relations are inferred
    Then a relation exists from "orders" to "users"
    And the relation via is "created_by"
    And the relation confidence is "medium"

  @wip
  Scenario: Singular/plural matching works
    Given a spec where resource "orders" has field "category_id"
    And a resource named "categories" exists
    When relations are inferred
    Then a relation exists from "orders" to "categories"

  @wip
  Scenario: Infer relations from Fake Store API spec
    Given the Fake Store API spec is loaded
    When relations are inferred
    Then relations exist connecting products, carts, and users

  @wip
  Scenario: Override config suppresses a relation
    Given a spec where resource "orders" has field "coupon_id"
    And a resource named "coupons" exists
    And an override config sets "orders.coupon_id" to null
    When relations are inferred
    Then no relation is created for field "coupon_id"

  @wip
  Scenario: Override config redirects a relation
    Given a spec where resource "projects" has field "owner_id"
    And resources named "users" and "organizations" both exist
    And an override config sets "projects.owner_id" to "organizations"
    When relations are inferred
    Then a single relation from "projects" to "organizations" exists
    And the relation confidence is "configured"
