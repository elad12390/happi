# Project Intent: happi

> A CLI tool that reads any OpenAPI 3.x spec and produces a human-first
> command interface — no HTTP verbs, no raw JSON, no copy-pasting IDs.

## Vision

Developers interact with REST APIs daily via curl, httpie, or Postman.
These tools expose the transport layer (HTTP methods, URLs, headers)
instead of the domain layer (users, orders, invoices). happi
bridges this gap: it reads an OpenAPI spec and generates a CLI where
commands map to what humans want to DO, not how HTTP works.

```
# Not this (transport-first):
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'

# This (human-first):
happi myapi users create --name Alice --email alice@example.com
```

## Module Index

```
happi
├── spec        Parse OpenAPI 3.x → resource model with verbs, params, relations
├── engine      Generate Typer command tree, execute commands, response stack
├── display     Render 8 output patterns (table, card, success, confirm, error, explore, explain, stack)
├── http        Build + send HTTP requests, auth providers
├── docs        Generate Markdown docs with Mermaid relationship diagrams
└── config      API profiles, auth credentials, override mappings
```

## Module Dependency Graph

```
                ┌────────┐
                │ config │
                └───┬────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌──────┐
    │  spec  │ │  http  │ │ docs │
    └───┬────┘ └───┬────┘ └──┬───┘
        │          │         │
        └─────┬────┘         │
              ▼              │
         ┌────────┐          │
         │ engine │◄─────────┘
         └───┬────┘
             ▼
        ┌─────────┐
        │ display │
        └─────────┘
```

- `config` is loaded first, provides API profiles to all modules
- `spec` parses the OpenAPI spec into a resource model
- `http` sends requests, receives responses
- `engine` wires spec + http together, builds the command tree, manages stack
- `display` renders engine output to the terminal
- `docs` reads from spec (resource model + relations) to generate documentation

## Core Design Decisions

### 1. Human verbs, not HTTP methods

| HTTP | CLI verb | Inference rule |
|---|---|---|
| GET collection | `list` | path has no `{id}` param |
| GET item | `show` | path ends with `{id}` param |
| POST collection | `create` | POST to collection path |
| PUT/PATCH item | `update` | PUT or PATCH to item path |
| DELETE item | `delete` | DELETE to item path |
| POST item/action | action name | last non-param path segment |

HTTP verbs never appear in user-facing output.

### 2. Resource-first command structure

```
happi <api> <resource> <verb> [args] [--flags]
```

Resources are inferred from path segments (primary) or tags (fallback hint).
Leaf resource is canonical. Parent resources become flags:

```
# /users/{id}/orders → canonical:
happi myapi orders list --user 123

# command names are normalized to plural kebab-case:
happi stripe payment-intents list
```

If two endpoints want the same command name, keep the cleanest name for the
most obvious one, then disambiguate with the nearest meaningful path word.

### 3. Response stack (interactive only)

```
_       last result (coerces to primary ID when context expects it)
_1      previous result
_.field field access
```

- Ring buffer of 20 entries, capped at ~5 MB
- Session-local, per API, not persisted
- Disabled in non-TTY / pipe mode
- Never auto-picks from a list — errors with guidance

Command history is persisted separately in `~/.happi/history.db` (SQLite).
The stack is ephemeral; history is durable.

### 4. Relationship inference

Detects relations from:
- Path nesting: `/users/{id}/orders` → has-many
- Field naming: `customer_id` → belongs-to customers
- Schema $ref: `$ref: '#/.../User'` → direct link (certain)
- Convention: `created_by` → likely users

Confidence levels: certain / high / medium.
Overridable via `.happi.yaml`.

### 5. Eight display patterns

| Pattern | Trigger | Key feature |
|---|---|---|
| Table | `list` | Numbered rows (#0, #1), humanized timestamps |
| Card | `show` | Grouped key-value, status indicators |
| Success | `create`, `update`, actions | `✓` + key fields |
| Confirm | `delete`, destructive | `⚠` + human name + y/N |
| Error | Failed requests | 3-layer: summary → fix → --debug |
| Explore | `explore` | Resource tree with action counts |
| Explain | `explain` | Schema, endpoint, auth, examples |
| Stack | `stack` | Recent results with source + timestamp |

`show --full` expands the main resource and prints runnable related commands,
but does not auto-fetch all related resources.

`explore` prints a pretty static tree with action counts and copy-pasteable
examples. No TUI in V1.

### 6. Documentation generation

`happi <api> docs` outputs Markdown with:
- Mermaid relationship diagram (auto-inferred)
- Resource tables with all actions
- Schema reference per resource
- Example commands
- Quick reference card

### 7. Auth and configure flow

- `configure` may skip auth for a fast first-run experience
- auth is set later via `happi auth set <api>` or `happi auth login <api>`
- if only one auth scheme exists, happi uses it automatically
- if multiple schemes exist, happi requires explicit `--type`
- OAuth2 browser login is the default, manual copy/paste fallback exists

### 8. Spec source and cache flow

- `configure <name>` tries LAP registry first, then common OpenAPI discovery URLs
- parsed models are cached by SHA256 hash of spec content
- local spec files auto-refresh on change
- remote/LAP specs are freshness-checked at most once every 24 hours

### 9. History

- every command appends a lightweight row to `~/.happi/history.db`
- history is available globally (`happi history`) and per API (`happi stripe history`)
- history stores metadata only (command, time, success, primary ID, summary)
- full response bodies are never persisted

## Non-Goals (V1)

These are explicitly out of scope. Do not build them.

- OAuth2 browser flows (PKCE, device code, client credentials)
- Interactive REPL / shell mode
- OpenAPI 2.0 (Swagger) support
- Automatic pagination following
- Plugin system for custom auth/extensions
- Code generation (outputting a standalone CLI project)
- WebSocket / streaming / SSE support
- TUI mode (full-screen terminal UI)
- Auto-update mechanism
- Telemetry / analytics
- Windows-specific UX beyond standard Python cross-platform support

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.12+ | Fast iteration, direct LAP integration, modern typing |
| CLI framework | Typer | Type hints → commands, dynamic registration via `app.add_typer()` |
| OpenAPI parser | openapi-pydantic or prance | Parse and validate OpenAPI 3.x with `$ref` resolution |
| Terminal styling | Rich | Best-in-class tables, panels, markdown, syntax highlighting |
| Interactive UI | Rich prompts / future Textual | Pretty static CLI now, richer interaction later if needed |
| Markdown render | Rich Markdown | Render markdown in terminal when needed |
| Config | PyYAML + pydantic | Typed config with validation |
| Pluralization | inflect | Singular/plural resource name matching |
| BDD testing | pytest + pytest-bdd | Mature Python BDD stack |

## Success Criteria

The tool is ready when:

1. All `.bdd/features/**/*.feature` scenarios are GREEN
2. Works against Petstore + 2 real-world APIs without panic
3. `docs` produces valid Markdown with correct Mermaid diagram
4. `_` stack works in interactive sessions
5. Installable via `pipx install happi` and PyPI
6. Startup < 200ms for typical specs (< 100 operations)
7. README makes someone want to try it in under 60 seconds
8. No HTTP verbs visible anywhere in user-facing output
