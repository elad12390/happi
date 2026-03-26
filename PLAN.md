# happi — Bulletproof Plan

> Turn any OpenAPI spec into a human-friendly CLI.
> Built with Intent-Driven Development + BDD E2E testing.
> See AGENTS.md for the full tech stack, code rules, and conventions.

## Methodology

Every feature follows the Bulletproof loop:

```
INTENT  →  RED  →  GREEN  →  REFACTOR
  │         │        │          │
  │         │        │          └─ Clean up. Tests still green.
  │         │        └─ Implement until test passes. Minimal change.
  │         └─ Write Gherkin scenario. Run it. Watch it FAIL.
  └─ Update INTENT.md with behavior/constraint/example.
```

**No code without intent. No fix without a failing test. No mocks.**

Testing archetype: **CLI tool** — subprocess runner, real filesystem, real
HTTP against real APIs (Petstore, httpbin, local test server).

## Project Structure

```
happi/
  .idd/                                 # Intent (source of truth)
    project.intent.md                   #   Vision, module index, non-goals
    architecture/
      dependencies.md                   #   Module dependency graph
      boundaries.md                     #   Forbidden patterns
    modules/
      spec/INTENT.md                    #   OpenAPI loading, parsing, analysis
      engine/INTENT.md                  #   Command tree generation, execution
      display/INTENT.md                 #   All 8 output patterns
      http/INTENT.md                    #   API client, auth
      docs/INTENT.md                    #   Markdown/Mermaid generation
      config/INTENT.md                  #   API profiles, overrides
    records/INDEX.md                    #   Decision log
    plans/                              #   Phased execution (this file drives it)

  .bdd/                                 # Verification (proves it works)
    features/                           #   Mirrors .idd/modules/
      spec/
        load-spec.feature               #   Loading and parsing OpenAPI specs
        extract-resources.feature       #   Resource extraction from paths/tags
        infer-verbs.feature             #   HTTP method → human verb mapping
        infer-relations.feature         #   Relationship inference from schemas
      engine/
        command-tree.feature            #   Dynamic command registration
        execute-crud.feature            #   CRUD operations
        execute-actions.feature         #   Non-CRUD actions
        response-stack.feature          #   _ references
      display/
        table-output.feature            #   List display
        card-output.feature             #   Show display
        success-output.feature          #   Create/update confirmations
        confirm-output.feature          #   Delete confirmations
        error-output.feature            #   Error rendering
        hints.feature                   #   ↳ suggestions
      http/
        requests.feature                #   HTTP request building
        auth.feature                    #   Authentication
      docs/
        markdown-gen.feature            #   Markdown generation
        mermaid-gen.feature             #   Mermaid diagram generation
      config/
        profiles.feature                #   API profile management
    steps/                              #   Step definitions by domain
      spec_steps.py
      engine_steps.py
      display_steps.py
      http_steps.py
      docs_steps.py
      config_steps.py
    interactions/                       #   CLI runner + output parser
      cli_runner.py                     #   Execute happi as subprocess
      output_parser.py                  #   Parse table/card/error output
      test_server.py                    #   Local OpenAPI server for testing
    support/
      fixtures/                         #   10 real OpenAPI specs (no synthetic)
        petstore.json
        github.yaml
        stripe.yaml
        spotify.yaml
        cloudflare.yaml
        sendgrid.yaml
        directus.yaml
        fakestoreapi.json
        httpbin.json
        dummyjson.json
      conftest.py
    qa/
      findings/                         #   What happened when tests ran
      resolutions/                      #   What was fixed

  src/happi/                            # Source code
    __init__.py
    __main__.py                         # Entry point
    cli.py                              # Typer app, root command, global flags
    spec/                               # OpenAPI loading & analysis
    engine/                             # Command generation & execution
    display/                            # Output rendering (Rich)
    http/                               # API client (httpx)
    docs/                               # Documentation generation
    config/                             # Configuration & profiles
  pyproject.toml
  uv.lock
```

## Module Index

| Module | Anchor | Intent File |
|---|---|---|
| **spec** | Parse any OpenAPI 3.x spec into a resource model with verbs, params, and relations | `.idd/modules/spec/INTENT.md` |
| **engine** | Generate a Typer command tree from the resource model and execute commands | `.idd/modules/engine/INTENT.md` |
| **display** | Render 8 output patterns (table, card, success, confirm, error, explore, explain, stack) | `.idd/modules/display/INTENT.md` |
| **http** | Build and send HTTP requests with auth, parse responses | `.idd/modules/http/INTENT.md` |
| **docs** | Generate Markdown documentation with Mermaid relationship diagrams | `.idd/modules/docs/INTENT.md` |
| **config** | Manage API profiles, auth credentials, and override mappings | `.idd/modules/config/INTENT.md` |

## Phased Build Plan

Each phase follows: **Intent → Gherkin (RED) → Implement (GREEN) → Sync**

---

### Phase 1 — Spec Loading + Resource Extraction (Week 1)

**Behavioral goal**: Given an OpenAPI spec, produce a structured resource
model with human verbs and grouped operations.

#### Intent work (before any code)

Write INTENT.md for `spec` module:
- Anchor: "Parse any OpenAPI 3.x spec into a resource model"
- Structure: loader → resource extractor → verb mapper → param mapper
- Constraints: must handle $ref resolution, must not panic on malformed specs
- Examples: Petstore spec → resources `[pets, store, users]` with verbs

#### Gherkin scenarios (RED)

```
.bdd/features/spec/
  load-spec.feature
    ✦ Load spec from local YAML file
    ✦ Load spec from local JSON file
    ✦ Load spec from URL
    ✦ Handle malformed spec gracefully (no panic, clear error)
    ✦ Resolve $ref references within spec

  extract-resources.feature
    ✦ Extract resources from paths with tags
    ✦ Extract resources from paths without tags (infer from path segments)
    ✦ Group operations under resource by tag
    ✦ Handle flat path structures (no nesting)
    ✦ Handle deeply nested paths (flatten to leaf resource + parent flags)

  infer-verbs.feature
    ✦ GET /resources → list
    ✦ GET /resources/{id} → show
    ✦ POST /resources → create
    ✦ PUT /resources/{id} → update
    ✦ PATCH /resources/{id} → update
    ✦ DELETE /resources/{id} → delete
    ✦ POST /resources/{id}/activate → action "activate"
    ✦ POST /resources/{id}/send → action "send"
    ✦ GET /resources/{id}/status → action "status"
    ✦ Non-CRUD action uses last path segment as verb name
```

#### Implementation

| # | Task | Test file |
|---|---|---|
| 1.1 | Project scaffold (`uv init`, `src/happi/`, Typer root) | — |
| 1.2 | Spec loader (`openapi-pydantic` or `prance`, $ref resolution, caching) | `load-spec.feature` |
| 1.3 | Resource extractor (paths + tags → resource list) | `extract-resources.feature` |
| 1.4 | Verb mapper (HTTP method + path → human verb) | `infer-verbs.feature` |
| 1.5 | Param mapper (path params → args, query params → flags) | `infer-verbs.feature` |

**Milestone**: `uv run pytest .bdd/features/spec/` — all spec features GREEN.

---

### Phase 2 — Command Tree + Basic Execution (Week 2)

**Behavioral goal**: Run `happi <api> <resource> <verb>` and get a response.

#### Intent work

Write INTENT.md for `engine` and `http` modules:
- Engine anchor: "Generate a Typer command tree and execute commands"
- HTTP anchor: "Build HTTP requests from command context, send, parse response"
- Constraints: command tree must be generated dynamically at runtime,
  startup must be < 200ms

#### Gherkin scenarios (RED)

```
.bdd/features/engine/
  command-tree.feature
    ✦ Resources become top-level subcommands under API name
    ✦ Verbs become subcommands under resource
    ✦ Path params become positional arguments
    ✦ Query params become optional flags
    ✦ Body schema fields become flags with types
    ✦ --help shows resource list with descriptions
    ✦ --help on resource shows available verbs
    ✦ --help on verb shows params, flags, and response schema
    ✦ Unknown command suggests closest match

  execute-crud.feature
    ✦ list command sends GET to collection endpoint, displays table
    ✦ show command sends GET to item endpoint, displays card
    ✦ create command sends POST with body from flags, displays success
    ✦ update command sends PUT/PATCH with body from flags, displays success
    ✦ delete command prompts confirmation, sends DELETE, displays success
    ✦ delete --yes skips confirmation

  execute-actions.feature
    ✦ Custom action sends correct method to correct endpoint
    ✦ Action with path param takes it as positional arg
    ✦ Action with body takes it from flags

.bdd/features/http/
  requests.feature
    ✦ Build GET request with query params from flags
    ✦ Build POST request with JSON body from flags
    ✦ Build PUT request with JSON body from flags
    ✦ Build DELETE request
    ✦ Set Content-Type to application/json for requests with body
    ✦ Include auth header when configured
```

#### Implementation

| # | Task | Test file |
|---|---|---|
| 2.1 | Command tree builder (resource → verb → args/flags) | `command-tree.feature` |
| 2.2 | HTTP client (build request, send, parse response) | `requests.feature` |
| 2.3 | List executor (GET collection → table) | `execute-crud.feature` |
| 2.4 | Show executor (GET item → card) | `execute-crud.feature` |
| 2.5 | Create executor (POST with JSON body) | `execute-crud.feature` |
| 2.6 | Update executor (PUT/PATCH with JSON body) | `execute-crud.feature` |
| 2.7 | Delete executor (DELETE with confirmation) | `execute-crud.feature` |
| 2.8 | Action executor (non-CRUD operations) | `execute-actions.feature` |

**Milestone**: Full CRUD against Petstore via CLI. All engine + http features GREEN.

---

### Phase 3 — Display System (Week 3)

**Behavioral goal**: All 8 output patterns render correctly.

#### Intent work

Write INTENT.md for `display` module:
- Anchor: "Render all CLI output as one of 8 patterns, optimized for humans"
- Constraints: auto-detect TTY, support --json/--yaml/--output, respect --quiet
- Examples: list response → numbered table, show response → card, etc.

#### Gherkin scenarios (RED)

```
.bdd/features/display/
  table-output.feature
    ✦ List renders numbered table with # column
    ✦ Auto-selects columns (id, name/title, + 3 interesting fields)
    ✦ Truncates long values with ...
    ✦ Humanizes timestamps (2h ago, not ISO)
    ✦ Shows count + pagination footer
    ✦ --output wide shows all fields
    ✦ --json outputs raw JSON (no table)
    ✦ Pipe mode (non-TTY) defaults to JSON

  card-output.feature
    ✦ Show renders key-value card with title line
    ✦ Groups simple scalars above, arrays/objects below
    ✦ Shows status indicators (✓/✗) for boolean/enum fields
    ✦ --full fetches and inlines related resources

  success-output.feature
    ✦ Create shows ✓ + resource type + ID + key fields
    ✦ Update shows ✓ + what changed
    ✦ Action shows ✓ + action name + target

  confirm-output.feature
    ✦ Delete shows ⚠ + human-readable name + identifying fields
    ✦ Waits for y/N input in interactive mode
    ✦ --yes skips confirmation
    ✦ Non-interactive mode requires --yes or fails

  error-output.feature
    ✦ 4xx shows "Couldn't <action> <resource>" + field problems + suggestion
    ✦ 401 shows auth failure + config hint
    ✦ 404 shows "not found" + search suggestion
    ✦ 422 shows validation errors mapped from response body
    ✦ --debug shows raw HTTP request + response

  hints.feature
    ✦ After create: shows ↳ show _ and ↳ update _
    ✦ After list: shows ↳ show _N
    ✦ After delete: no ↳ referencing deleted resource
    ✦ Hints hidden in --quiet mode
    ✦ Hints hidden in non-TTY mode
```

#### Implementation

| # | Task | Test file |
|---|---|---|
| 3.1 | Table renderer | `table-output.feature` |
| 3.2 | Card renderer | `card-output.feature` |
| 3.3 | Success renderer | `success-output.feature` |
| 3.4 | Confirm renderer | `confirm-output.feature` |
| 3.5 | Error renderer (3-layer) | `error-output.feature` |
| 3.6 | Hint system | `hints.feature` |
| 3.7 | Output mode switching (--json, --yaml, --output, --quiet) | all display features |
| 3.8 | TTY detection + pipe-mode defaults | `table-output.feature` |

**Milestone**: All display features GREEN. Output looks polished.

---

### Phase 4 — Response Stack + Config (Week 4)

**Behavioral goal**: `_` references work in interactive mode. API profiles stored.

#### Intent work

Write INTENT.md for `engine/stack` (sub-module) and `config`:
- Stack anchor: "Reference previous results with _ syntax in interactive mode"
- Config anchor: "Store API profiles with base URL, auth, and overrides"

#### Gherkin scenarios (RED)

```
.bdd/features/engine/
  response-stack.feature
    ✦ _ resolves to last result's primary ID
    ✦ _1 resolves to previous result's primary ID
    ✦ _.field resolves to a specific field from last result
    ✦ _1.field resolves to a field from previous result
    ✦ _ after show coerces object to ID
    ✦ _ after create coerces to created resource ID
    ✦ _ after list errors: "Last result is a list. Use _[0].id or --pick"
    ✦ Stack holds max 20 entries
    ✦ Stack is session-local (not persisted)
    ✦ Stack is disabled in non-TTY mode
    ✦ stack command shows stack contents with source + timestamp

.bdd/features/config/
  profiles.feature
    ✦ configure creates new API profile with base URL
    ✦ configure prompts for auth type and credentials
    ✦ Config stored in ~/.happi/config.yaml
    ✦ Multiple API profiles supported
    ✦ --profile flag switches active profile
    ✦ Override file (.happi.yaml) in cwd is loaded
    ✦ Override relation mappings applied during inference

.bdd/features/http/
  auth.feature
    ✦ API key sent in header when configured
    ✦ API key sent in query when configured
    ✦ Bearer token sent in Authorization header
    ✦ Auth credentials loaded from profile
```

#### Implementation

| # | Task | Test file |
|---|---|---|
| 4.1 | Stack storage (ring buffer, structured entries) | `response-stack.feature` |
| 4.2 | Stack resolution (`_`, `_1`, `_.field`) | `response-stack.feature` |
| 4.3 | Primary ID detection | `response-stack.feature` |
| 4.4 | List coercion guard | `response-stack.feature` |
| 4.5 | `stack` command | `response-stack.feature` |
| 4.6 | Config store (PyYAML + pydantic, yaml) | `profiles.feature` |
| 4.7 | `configure` wizard | `profiles.feature` |
| 4.8 | API key auth | `auth.feature` |
| 4.9 | Bearer auth | `auth.feature` |
| 4.10 | Override loading from `.happi.yaml` | `profiles.feature` |

**Milestone**: Create → show _ works. Auth works. All stack + config features GREEN.

---

### Phase 5 — Discovery + Documentation (Week 5)

**Behavioral goal**: `explore`, `explain`, `find`, `docs` with Mermaid diagrams.

#### Intent work

Write INTENT.md for `docs` module. Extend `spec` INTENT.md with relation inference.

#### Gherkin scenarios (RED)

```
.bdd/features/spec/
  infer-relations.feature
    ✦ user_id field → belongs-to users (high confidence)
    ✦ userId field → belongs-to users (high confidence)
    ✦ tag_ids array field → has-many tags (high confidence)
    ✦ $ref to User schema → belongs-to users (certain)
    ✦ /users/{id}/orders path → users has-many orders (certain)
    ✦ parent_id → self-referential relation (high confidence)
    ✦ owner_id with multiple matching resources → ambiguous (medium)
    ✦ coupon_code with no matching resource → no relation
    ✦ created_by → belongs-to users (medium confidence)
    ✦ Singular/plural matching (user_id → users, category_id → categories)

.bdd/features/docs/
  markdown-gen.feature
    ✦ docs command outputs valid Markdown to stdout
    ✦ Markdown includes API title and base URL
    ✦ Markdown includes resource table with actions for each resource
    ✦ Markdown includes schema for each resource
    ✦ Markdown includes filter flags for list operations
    ✦ Markdown includes example commands
    ✦ Markdown includes quick reference table
    ✦ docs --resource users outputs docs for one resource only
    ✦ docs > file.md saves to file

  mermaid-gen.feature
    ✦ Mermaid diagram includes all resources as nodes
    ✦ Mermaid edges from path nesting (has-many)
    ✦ Mermaid edges from _id fields (belongs-to)
    ✦ Mermaid edges from $ref (direct link)
    ✦ Self-referential relations shown as self-loop
    ✦ Ambiguous relations marked with ?
    ✦ Confidence levels shown in relation table
    ✦ docs --map-only outputs just the Mermaid diagram

  explore/explain (in display features):
    ✦ explore shows resource tree with action counts
    ✦ explore <resource> shows actions, filters, schema, examples
    ✦ explain <resource> <verb> shows endpoint, schema, auth, examples
    ✦ find <query> fuzzy-matches across operation names/summaries
    ✦ Unknown command suggests `happi <api> find <query>`
```

#### Implementation

| # | Task | Test file |
|---|---|---|
| 5.1 | Relation inference engine | `infer-relations.feature` |
| 5.2 | Singular/plural matching | `infer-relations.feature` |
| 5.3 | Confidence scoring | `infer-relations.feature` |
| 5.4 | Mermaid diagram generator | `mermaid-gen.feature` |
| 5.5 | Markdown documentation generator | `markdown-gen.feature` |
| 5.6 | `docs` command | `markdown-gen.feature` |
| 5.7 | `explore` command | display features |
| 5.8 | `explain` command | display features |
| 5.9 | `find` command (fuzzy search) | display features |
| 5.10 | `--full` flag (inline related resources) | `card-output.feature` |

**Milestone**: `docs > API.md` produces Markdown with Mermaid. All features GREEN.

---

### Phase 6 — Hardening + Ship (Week 6)

**Behavioral goal**: Works against 5+ real specs. Installable. README-ready.

#### Gherkin scenarios (RED)

```
.bdd/features/spec/
  real-world-specs.feature
    ✦ Petstore spec produces clean resource tree
    ✦ GitHub API spec handles 800+ operations without panic
    ✦ Spec with no tags falls back to path-based grouping
    ✦ Spec with no operationIds falls back to path-derived names
    ✦ RPC-style POST-everything spec produces usable (if ugly) commands
    ✦ Startup time < 200ms for 100-operation spec
    ✦ Startup time < 500ms for 500-operation spec
    ✦ Malformed spec produces clear error, no panic

  shell-completion.feature
    ✦ Bash completion for resource names
    ✦ Bash completion for verb names under resource
    ✦ Zsh completion works
```

#### Implementation

| # | Task | Test file |
|---|---|---|
| 6.1 | Test + fix against Petstore | `real-world-specs.feature` |
| 6.2 | Test + fix against GitHub API | `real-world-specs.feature` |
| 6.3 | Test + fix against FastAPI app | `real-world-specs.feature` |
| 6.4 | Test + fix against messy spec (no tags, no operationIds) | `real-world-specs.feature` |
| 6.5 | Spec caching (SHA256 content hash, `--refresh`) | `load-spec.feature` |
| 6.6 | Shell completion (Typer built-in) | `shell-completion.feature` |
| 6.7 | `raw <operationId>` escape hatch | — |
| 6.8 | README with demo | — |
| 6.9 | GitHub Actions CI (ruff, pyright, pytest) | — |
| 6.10 | PyPI publishing via `uv publish` | — |

**Milestone**: Public release. All features GREEN. `pipx install happi`.

---

## Test Infrastructure

### BDD Framework

**pytest-bdd** — mature Gherkin BDD runner for Python. Integrates with pytest
fixtures, markers, and parametrize. Reads `.feature` files directly.

### CLI Runner (interaction layer)

All tests execute `happi` as a **real subprocess** — no mocking:

```python
import subprocess

@dataclass
class CLIResult:
    stdout: str
    stderr: str
    exit_code: int

def run(*args: str) -> CLIResult:
    result = subprocess.run(
        ["uv", "run", "happi", *args],
        capture_output=True, text=True
    )
    return CLIResult(result.stdout, result.stderr, result.returncode)
```

### Test API Server

A local HTTP server serving fixture OpenAPI specs + predictable API responses:

```python
import uvicorn
from fastapi import FastAPI

# Serves petstore.json at /openapi.json
# Handles CRUD at /pets, /pets/{id}, etc.
# Returns predictable responses for assertions
```

This is a **real HTTP server** (not a mock). It runs during tests, listens
on localhost, and serves real HTTP responses.

### Test Fixtures

10 real OpenAPI specs in `.bdd/support/fixtures/`. See AGENTS.md for the full list.

## Sync Checklist

After each phase, before moving on:

- [ ] Every INTENT.md Layer 3 example has a Gherkin scenario
- [ ] Every runtime constraint has a step assertion
- [ ] All scenarios pass (GREEN)
- [ ] No mocks introduced
- [ ] Feature directories mirror module directories
- [ ] BDD findings documented in `.bdd/qa/findings/`
- [ ] Any fixes documented in `.bdd/qa/resolutions/`
- [ ] INTENT.md updated with what actually shipped (sync)

## Success Criteria

### V1 is done when:

1. All `.bdd/features/**/*.feature` scenarios are GREEN
2. Works against Petstore + 2 real-world APIs
3. `docs` produces Markdown with Mermaid diagram
4. `_` stack works in interactive sessions
5. Installable via `pipx install happi` and PyPI
6. README makes someone want to try it in under 60 seconds
7. Startup < 200ms for typical specs

### It's NOT done if:

- Any scenario is RED
- Any mock exists in `.bdd/`
- Any display shows HTTP verbs
- Intent and code have unresolved drift
- The `.bdd/qa/findings/` has unresolved items

## Non-Goals (V1)

- OAuth2 flows (PKCE, device code)
- Interactive REPL / shell mode
- OpenAPI 2.0 (Swagger) support
- Auto-pagination
- Plugin system
- Code generation (outputting a standalone CLI project)
- WebSocket / streaming support
- TUI mode
