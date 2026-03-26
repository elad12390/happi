# Intent: .idd/modules/docs/INTENT.md
# Layer: Examples (Mermaid Diagram)

Feature: Generate Mermaid Relationship Diagrams
  Mermaid diagrams visualize resource relationships inferred from
  field names, path nesting, and schema $refs.

  Scenario: Diagram includes all resources as nodes
    Given a resource model with resources "users", "orders", "products"
    When a Mermaid diagram is generated
    Then the diagram contains nodes for "users", "orders", "products"

  Scenario: Path nesting creates has-many edge
    Given a resource model with path "/users/{id}/orders"
    When a Mermaid diagram is generated
    Then the diagram contains an edge from "users" to "orders" labeled "has many"

  Scenario: Field _id creates belongs-to edge
    Given a resource model where "orders" has field "customer_id" → "customers"
    When a Mermaid diagram is generated
    Then the diagram contains an edge from "orders" to "customers" labeled "belongs to"

  Scenario: $ref creates direct link edge
    Given a resource model where "orders" has $ref to "User" schema
    When a Mermaid diagram is generated
    Then the diagram contains an edge from "orders" to "users"

  Scenario: Self-referential relation shown
    Given a resource model where "categories" has field "parent_id" → "categories"
    When a Mermaid diagram is generated
    Then the diagram contains a self-referencing edge on "categories"

  Scenario: Ambiguous relations marked
    Given a resource model with an ambiguous relation on "projects.owner_id"
    When a Mermaid diagram is generated
    Then the edge is annotated with a question mark or "ambiguous"

  Scenario: Output is valid Mermaid syntax
    Given any resource model with relations
    When a Mermaid diagram is generated
    Then the output starts with "```mermaid"
    And the output ends with "```"
    And the diagram type is "graph" or "flowchart"
