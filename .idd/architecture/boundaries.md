# Module Boundaries

## Forbidden Patterns

| Rule | Rationale | Verified by |
|---|---|---|
| display never imports http | Display renders data, doesn't fetch it | CI lint |
| display never imports spec | Display receives structured data from engine | CI lint |
| docs never imports engine | Docs reads from spec model directly | CI lint |
| http never imports spec | HTTP client is generic, doesn't know about OpenAPI | CI lint |
| spec never imports engine | Spec produces the model, engine consumes it | CI lint |
| No module imports display | Display is a leaf — nothing depends on it | CI lint |
| No circular dependencies | Dependency graph is a DAG | CI lint |

## Interface Contracts

### spec → engine

spec exports a `ResourceModel`:
```
ResourceModel {
  Resources []Resource
  Relations []Relation
}

Resource {
  Name        string        // "users", "orders"
  Operations  []Operation   // list, show, create, update, delete, custom actions
}

Operation {
  Verb        string        // "list", "show", "create", "activate"
  HTTPMethod  string        // "GET", "POST" (internal only, never displayed)
  Path        string        // "/users/{id}" (internal only)
  Args        []Param       // positional (from path params)
  Flags       []Param       // optional (from query params + body fields)
  BodySchema  *Schema       // request body structure
  Responses   []Response    // response schemas by status code
}

Relation {
  From       string         // "orders"
  To         string         // "users"
  Type       string         // "belongs-to", "has-many"
  Via        string         // "customer_id", path nesting, $ref
  Confidence string         // "certain", "high", "medium"
}
```

### engine → display

engine passes a `DisplayPayload`:
```
DisplayPayload {
  Pattern     string        // "table", "card", "success", "confirm", "error", etc.
  Data        any           // parsed response body
  Resource    string        // "users"
  Verb        string        // "create"
  StatusCode  int           // 200, 201, 404, 422
  Schema      *Schema       // response schema (for column selection, field types)
  StackIndex  int           // position in response stack
  Hints       []Hint        // suggested next commands
}
```

### config → all

config exports:
```
APIProfile {
  Name        string        // "petstore"
  BaseURL     string        // "https://petstore3.swagger.io/api/v3"
  SpecURL     string        // auto-discovered or explicit
  Auth        AuthConfig    // type + credentials
  Overrides   Overrides     // relation mappings, custom verb names
}
```
