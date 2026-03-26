# Module Intent: spec

> Parse any OpenAPI 3.x spec into a structured resource model with human
> verbs, parameters, and inferred relationships.

## Structure

```
spec/
├── loader.py           Fetch spec from URL/file/LAP, resolve $refs, cache
├── resources.py        Extract resources from paths, use tags as fallback hint
├── verbs.py            Map HTTP method + path shape → human verb
├── params.py           Map path/query/body params → CLI args/flags
├── relations.py        Infer relationships from field names, paths, $refs
└── model.py            ResourceModel, Resource, Operation, Relation types
```

## Constraints

| Rule | Rationale | Verified by |
|---|---|---|
| Must support OpenAPI 3.0 and 3.1 | Most common versions in the wild | BDD scenario |
| Must resolve all $ref references before processing | Resources reference shared schemas | BDD scenario |
| Must not panic on malformed specs | Graceful error with message, not crash | BDD scenario |
| Parsing a 500-operation spec must complete in < 300ms | CLI startup must feel instant | BDD scenario |
| Resource names are always lowercase plural | Consistency: "users" not "User" or "user" | BDD step assertion |
| Verb names are always lowercase | Consistency: "list" not "List" | BDD step assertion |
| Path segments take priority over tags for grouping | Paths usually reflect the true entity model better than broad tags | BDD scenario |
| Tags are only used when paths are ambiguous or too generic | Tags are a fallback hint, not the primary grouping source | BDD scenario |
| Resource names are normalized to kebab-case plural nouns | Stable, human-typed CLI surface | BDD step assertion |
| Simple body input uses top-level flags only; nested payloads require `--body` or stdin | Easiest usable model, avoids dot-notation complexity | BDD scenario |
| Local spec files auto-refresh on change; remote/LAP specs are freshness-checked at most once every 24h | Fast normal runs, predictable updates | BDD scenario |
| GET /{resource}/{id} without a matching GET /{resource} MUST map to `show`, never `list` | Prevents list-without-ID errors | BDD scenario |
| All paths in the spec MUST produce at least one resource; version prefixes like /v1 are stripped but no path is silently ignored | No silent loss of API coverage | BDD scenario |

## Examples

### Spec Loading

| Input | Output |
|---|---|
| `load("petstore.yaml")` (valid local file) | `ResourceModel` with resources parsed |
| `load("https://petstore3.swagger.io/api/v3/openapi.json")` (valid URL) | `ResourceModel` fetched and parsed |
| `load("nonexistent.yaml")` | `SpecError { code: "FILE_NOT_FOUND" }` |
| `load("garbage.txt")` (not valid OpenAPI) | `SpecError { code: "INVALID_SPEC", message: "..." }` |
| `load("has-refs.yaml")` (spec with $refs) | All $refs resolved inline |

### Resource Extraction

| Input (spec paths + tags) | Output (resources) |
|---|---|
| paths: `/pets`, `/pets/{id}`, tags: `["pet"]` | `[Resource{name:"pets"}]` |
| paths: `/billing/payment_intents`, tags: `["payments"]` | `[Resource{name:"payment-intents"}]` (path wins, tag is ignored) |
| paths: `/users`, `/users/{id}`, `/orders`, `/orders/{id}`, tags: `["user","order"]` | `[Resource{name:"users"}, Resource{name:"orders"}]` |
| paths: `/users`, `/users/{id}` with NO tags | `[Resource{name:"users"}]` (inferred from path) |
| paths: `/users/{id}/orders` | `Resource{name:"orders"}` with parent param `--user` |
| paths: `/me`, `/login`, `/search` (flat, no clear resources) | Best-effort grouping, warn once about ambiguity |
| paths: `/users/search` and `/admin/users/search` | `users search` and `users admin-search` (collision resolved with nearest path word) |

### Verb Mapping

| HTTP Method | Path Pattern | Output Verb |
|---|---|---|
| GET | `/users` | `list` |
| GET | `/users/{id}` | `show` |
| POST | `/users` | `create` |
| PUT | `/users/{id}` | `update` |
| PATCH | `/users/{id}` | `update` |
| DELETE | `/users/{id}` | `delete` |
| POST | `/users/{id}/activate` | `activate` (action) |
| POST | `/users/{id}/send-invite` | `send-invite` (action) |
| GET | `/users/{id}/status` | `status` (action) |
| POST | `/reports/generate` | `generate` (action on reports) |
| POST | `/users/search` | `search` (action on users) |

### Relationship Inference

| Input (field/path) | Output (relation) |
|---|---|
| field `customer_id` in Order schema, "customers" resource exists | `Relation{from:"orders", to:"customers", type:"belongs-to", via:"customer_id", confidence:"high"}` |
| field `userId` in Order schema, "users" resource exists | `Relation{from:"orders", to:"users", type:"belongs-to", via:"userId", confidence:"high"}` |
| field `tag_ids` (array) in Post schema, "tags" resource exists | `Relation{from:"posts", to:"tags", type:"has-many", via:"tag_ids", confidence:"high"}` |
| path `/users/{id}/orders` exists | `Relation{from:"users", to:"orders", type:"has-many", via:"path", confidence:"certain"}` |
| `$ref: '#/components/schemas/User'` in Order response | `Relation{from:"orders", to:"users", type:"belongs-to", via:"$ref", confidence:"certain"}` |
| field `parent_id` in Category schema, same resource | `Relation{from:"categories", to:"categories", type:"belongs-to", via:"parent_id", confidence:"high"}` (self-ref) |
| field `owner_id`, both "users" and "organizations" exist | `Relation{from:"...", to:"users", confidence:"medium"}` + `Relation{to:"organizations", confidence:"medium"}` (ambiguous) |
| field `coupon_code`, no "coupon_codes" resource exists | No relation inferred |
| field `created_by` | `Relation{to:"users", type:"belongs-to", via:"created_by", confidence:"medium"}` |

### Parameter Mapping

| OpenAPI Param | CLI Mapping |
|---|---|
| path param `{petId}` (required) | positional arg: `pets show <petId>` |
| query param `status` (optional, enum) | flag: `--status available\|pending\|sold` |
| query param `limit` (optional, integer) | flag: `--limit 10` |
| body field `name` (required, string) | flag: `--name "Alice"` |
| body field `tags` (optional, array of strings) | flag: `--tags foo,bar` |
| body field `address` (object) | use `--body '{"address":{"city":"NYC"}}'` or `< payload.json` |
| nested object payload | read from stdin (`< payload.json`) or `--body` |
