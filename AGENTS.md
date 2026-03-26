# AGENTS.md — happi

> Turn any OpenAPI spec into a human-friendly CLI.

## What This Project Is

`happi` (Human API Interface) reads an OpenAPI 3.x spec and generates a
CLI where commands map to what humans want to DO, not how HTTP works.
No GET/POST/PUT anywhere. Just `happi myapi users list`, `happi myapi
orders create --name Foo`, `happi myapi invoices send 456`.

## Tech Stack (Non-Negotiable)

| Layer | Tool | Version | Why |
|---|---|---|---|
| Language | Python 3.12+ | | Type hints, async, modern syntax |
| Package manager | **uv** | latest | Fast, replaces pip/poetry. Use `uv add`, `uv run`, `uv sync` |
| CLI framework | **Typer** | 0.24+ | Type hints → commands, dynamic registration via `app.add_typer()` |
| Terminal output | **Rich** | 14+ | Tables, colors, trees, markdown, panels, syntax highlighting |
| HTTP client | **httpx** | latest | Async HTTP, modern, replaces requests |
| OpenAPI parser | **openapi-pydantic** or **prance** | latest | Parse + validate OpenAPI 3.x, $ref resolution |
| Config | **PyYAML** + **pydantic** | latest | Typed config with validation |
| Pluralization | **inflect** | latest | Singular/plural matching for relation inference |
| LAP integration | **LAP Registry + direct HTTP lookup** | latest | Resolve API names to real spec URLs from `registry.lap.sh` |
| Linter + formatter | **Ruff** | latest | Replaces black + flake8 + isort. One tool |
| Type checker | **pyright** or **mypy** | latest | Strict type checking, no `Any` allowed |
| Testing | **pytest** + **pytest-bdd** | latest | BDD Gherkin tests in `.bdd/` |
| CI | **GitHub Actions** | | Lint, type-check, test, publish |
| Distribution | **PyPI** via `uv publish` | | Install via `pipx install happi` |

## Project Structure

```
happi/
├── .idd/                           # Intent (what SHOULD happen)
│   ├── project.intent.md
│   ├── architecture/
│   │   ├── dependencies.md
│   │   └── boundaries.md
│   ├── modules/
│   │   ├── spec/INTENT.md          # OpenAPI loading, parsing, analysis
│   │   ├── engine/INTENT.md        # Command tree, execution, stack
│   │   ├── display/INTENT.md       # Output rendering (8 patterns)
│   │   ├── http/INTENT.md          # API client, auth
│   │   ├── docs/INTENT.md          # Markdown/Mermaid generation
│   │   └── config/INTENT.md        # Profiles, overrides
│   └── records/INDEX.md
│
├── .bdd/                           # Verification (proves it works)
│   ├── features/                   # Gherkin specs (mirrors .idd/modules/)
│   │   ├── spec/
│   │   ├── engine/
│   │   ├── display/
│   │   ├── http/
│   │   ├── docs/
│   │   └── config/
│   ├── steps/                      # Step definitions
│   ├── interactions/               # CLI runner, test server, output parser
│   ├── support/fixtures/           # 10 real OpenAPI specs (no synthetic)
│   └── qa/                         # Findings + resolutions
│
├── src/happi/                      # Source code
│   ├── __init__.py
│   ├── __main__.py                 # Entry point
│   ├── cli.py                      # Typer app, root command, global flags
│   ├── log.py                      # Rich-based logger, --verbose/--debug
│   ├── spec/                       # OpenAPI loading & analysis
│   │   ├── __init__.py
│   │   ├── loader.py               # Fetch/read spec, resolve $refs, cache
│   │   ├── lap.py                  # LAP registry resolution
│   │   ├── resources.py            # Extract resources from paths + tags
│   │   ├── verbs.py                # HTTP method → human verb mapping
│   │   ├── params.py               # Params/body → CLI args/flags
│   │   ├── relations.py            # Infer relationships
│   │   └── model.py                # ResourceModel, Resource, Operation, Relation
│   ├── engine/                     # Command generation & execution
│   │   ├── __init__.py
│   │   ├── tree.py                 # Build Typer command tree from ResourceModel
│   │   ├── executor.py             # Run command: resolve args → request → display
│   │   ├── stack.py                # Response stack (_, _1, _.field)
│   │   └── resolver.py             # Resolve _ references
│   ├── display/                    # Output rendering
│   │   ├── __init__.py
│   │   ├── table.py                # list → numbered table
│   │   ├── card.py                 # show → key/value card
│   │   ├── success.py              # create/update → ✓ summary
│   │   ├── confirm.py              # delete → ⚠ confirmation
│   │   ├── error.py                # errors → 3-layer display
│   │   ├── hints.py                # ↳ next-action suggestions
│   │   ├── explore.py              # explore/explain/find output
│   │   ├── format.py               # Output mode switching
│   │   └── humanize.py             # Timestamps, numbers, truncation
│   ├── http/                       # API client
│   │   ├── __init__.py
│   │   ├── client.py               # httpx-based request builder
│   │   ├── auth.py                 # Auth providers (api key, bearer)
│   │   └── response.py             # Response parsing, error detection
│   ├── docs/                       # Documentation generation
│   │   ├── __init__.py
│   │   ├── markdown.py             # Full Markdown output
│   │   ├── mermaid.py              # Relationship diagrams
│   │   └── quickref.py             # Quick reference table
│   └── config/                     # Configuration
│       ├── __init__.py
│       ├── config.py               # Read/write ~/.happi/config.yaml
│       ├── auth.py                 # Auth storage/login state (planned)
│       ├── profiles.py             # API profile CRUD
│       └── overrides.py            # .happi.yaml override loading
│
├── pyproject.toml                  # Project config, deps, scripts, ruff, pyright
├── uv.lock                        # Locked dependencies
├── PLAN.md                         # Bulletproof build plan
├── AGENTS.md                       # This file
└── README.md
```

## Methodology: Bulletproof (IDD + BDD)

Every feature follows:

```
INTENT → RED → GREEN → REFACTOR
```

1. Update INTENT.md with expected behavior
2. Write Gherkin scenario in `.bdd/features/`
3. Run test → must FAIL (RED)
4. Implement → test must PASS (GREEN)
5. Sync intent ↔ code

**No code without intent. No fix without a failing test. No mocks.**

## Code Rules (STRICT)

### Formatting & Linting

Ruff handles everything. Config is in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "RUF",    # ruff-specific rules
    "PTH",    # use pathlib
    "ERA",    # eradicate commented-out code
    "TID",    # tidy imports
    "PIE",    # misc lints
    "T20",    # no print statements (use Rich console)
    "S",      # bandit security
    "C4",     # comprehension improvements
    "DTZ",    # datetime timezone awareness
    "FA",     # future annotations
    "ISC",    # implicit string concat
    "PGH",    # pygrep hooks
    "RSE",    # raise improvements
    "RET",    # return improvements
    "FLY",    # flynt f-string improvements
    "PERF",   # performance anti-patterns
]
ignore = [
    "S101",   # allow assert in tests
]

[tool.ruff.lint.per-file-ignores]
".bdd/**" = ["T20", "S"]  # allow print and assert in tests
```

**Run before every commit:**
```bash
uv run ruff check --fix .
uv run ruff format .
```

### Type Checking

Pyright in strict mode. Config in `pyproject.toml`:

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingTypeStubs = false
```

**Run before every commit:**
```bash
uv run pyright
```

### Hard Blocks (NEVER do these)

| Rule | Why |
|---|---|
| Never use `Any` type | Defeats type safety. Use `object`, generics, or proper types |
| Never use `# type: ignore` | Fix the type, don't suppress the error |
| Never use `print()` | Use `rich.console.Console()` for all output |
| Never use `requests` library | Use `httpx` (modern, async-capable) |
| Never use bare `except:` | Always catch specific exceptions |
| Never use mutable default args | `def f(x: list = [])` is a bug. Use `None` sentinel |
| Never commit with ruff errors | CI blocks merge. Fix locally first |
| Never commit with pyright errors | CI blocks merge. Fix locally first |
| Never leave TODO without issue link | `TODO(#123): description` or don't write it |
| Never use `os.path` | Use `pathlib.Path` everywhere |
| Never suppress test failures | Fix the code, not the test |
| Never mock in tests | Real HTTP, real filesystem, real subprocess |

### Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `resource_model.py` |
| Classes | `PascalCase` | `ResourceModel`, `SpecLoader` |
| Functions | `snake_case` | `extract_resources()`, `infer_verbs()` |
| Constants | `UPPER_SNAKE` | `MAX_STACK_SIZE = 20` |
| Private | `_prefixed` | `_parse_path()`, `_resolve_ref()` |
| Type aliases | `PascalCase` | `Verb = Literal["list", "show", ...]` |
| Test files | `test_*.py` or `*.steps.py` | `spec_steps.py` |

### Import Order (Ruff handles this automatically)

```python
# 1. stdlib
from pathlib import Path
from typing import Any

# 2. third-party
import httpx
import typer
from rich.console import Console
from rich.table import Table

# 3. local
from happi.spec.model import ResourceModel
from happi.display.table import render_table
```

### Error Handling Pattern

```python
# Always use custom exception hierarchy
class HappiError(Exception):
    """Base for all happi errors."""

class SpecLoadError(HappiError):
    """Failed to load OpenAPI spec."""

class AuthError(HappiError):
    """Authentication failed."""

class APIError(HappiError):
    """API returned an error response."""
    def __init__(self, status: int, message: str, details: dict | None = None):
        self.status = status
        self.message = message
        self.details = details
```

### Output Pattern (Rich everywhere)

```python
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

# Success
console.print("[green]✓[/green] Created user usr_abc12")

# Error
err_console.print("[red]✗[/red] Couldn't create user (422)")

# Tables
from rich.table import Table
table = Table()
table.add_column("#", style="dim")
table.add_column("ID", style="cyan")
table.add_column("Name")
console.print(table)

# NEVER use print(). Ruff rule T20 catches this.
```

## Architecture Decisions

### Command Grammar
```
happi <api> <resource> <verb> [args] [--flags]
```
Always explicit. API name is always required.

### Spec Input (3 modes, priority order)
1. `--spec URL/file` on any command (inline, highest priority)
2. Named profile: `happi configure myapi` → `happi myapi ...`
3. `.happi.yaml` in cwd (auto-detect, lowest priority but still requires `happi <api>`)

`happi configure <name>` without `--spec` must:
1. Try LAP registry lookup first
2. Fallback to common OpenAPI discovery URLs if LAP misses
3. Fail with explicit next commands if nothing is found

### Spec Caching
SHA256 hash of spec content → cache parsed ResourceModel by hash.
Cache location: `~/.happi/cache/<hash>.json`
Local spec files refresh automatically on change.
Remote/LAP specs are freshness-checked at most once every 24 hours.
Spec changes = new hash = fresh parse. `--refresh` forces re-check.

### Verb Mapping
```
GET    /resources           →  list
GET    /resources/{id}      →  show
POST   /resources           →  create
PUT    /resources/{id}      →  update
PATCH  /resources/{id}      →  update
DELETE /resources/{id}      →  delete
POST   /resources/{id}/X    →  X (action name from last path segment)
```
HTTP verbs NEVER appear in user-facing output.

### Resource Grouping
Leaf resource is canonical. Parents become flags:
```
/users/{id}/orders → orders list --user 123
```
Paths win over tags when choosing resource names. Tags are fallback hints only.
Resource names are plural kebab-case (`payment-intents`, `dns-records`).
If command names collide, disambiguate with the nearest meaningful path word.

### Body Input
- Top-level scalar fields → `--flag value`
- Simple arrays → `--tags admin,active`
- Complex/nested → `< file.json` or `--body '{...}'`
- No dot notation (YAGNI)

### Response Stack
- `_` = last result, `_1` = previous, `_.field` = field access
- Interactive (TTY) only. Disabled in pipes
- Ring buffer of 20, ~5MB cap
- Never auto-picks from list — errors with guidance
- Per API, per process/session only. Never persisted across sessions.

### History
- SQLite at `~/.happi/history.db`
- Persist command metadata only: API, timestamp, command, success, primary ID, summary
- Never persist full response bodies or secrets
- Support both `happi history` and `happi <api> history`

### Display (8 patterns, always pretty-printed static text)
1. Table (list) — numbered rows, humanized timestamps
2. Card (show) — grouped key-value
3. Success (create/update/action) — ✓ + key fields
4. Confirm (delete) — ⚠ + human name + y/N
5. Error — 3-layer: what failed → fix → --debug
6. Explore — resource tree with action counts
7. Explain — schema, endpoint, auth, examples
8. Stack — recent results with source + timestamp

All output uses Rich. No TUI. No interactive widgets. Just gorgeous static print.
`show --full` expands the main resource and prints related runnable commands,
but does NOT auto-fetch every relation.

### Pagination
Auto-detect style from spec (page/offset/cursor/link-header/next-url).
First page by default. `--all` fetches everything (cap: 1000). `--max N` overrides cap.

### Auth
Plain text in `~/.happi/config.yaml` (chmod 600).
V1 auth supports:
- API key (header or query)
- Bearer token
- OAuth2 (browser-first, manual fallback)

Auth is optional during `configure` and can be added later via:
- `happi auth set <api>`
- `happi auth login <api>`

If multiple auth schemes exist, require explicit `--type`.

### Error Recovery
Fail fast with clear message. Suggest `--retry N`. Exponential backoff (2s, 4s, 8s). Max 5 retries.

### Bad Specs
Always try, never refuse. Best-effort inference from paths when tags/operationIds are missing. One-time warning per session.

### Logging
- `--verbose` / `-v` → info-level logs
- `--debug` → debug-level logs + raw HTTP context
- Logger must show spec loading, cache hits/misses, resource extraction decisions, and LAP resolution

## Global Flags

```
Output:
  --json            Raw JSON output
  --yaml            YAML output
  --quiet / -q      Suppress hints and non-essential output
  --debug           Show raw HTTP request + response
  --output / -o     Output format (table|wide|json|yaml|csv)
  --query           JMESPath filter on response

Behavior:
  --yes / -y        Skip confirmations
  --retry N         Retry failed requests N times (max 5, exponential backoff)
  --refresh         Force re-parse spec (ignore cache)
  --no-color        Disable colors (also respects NO_COLOR env)

Connection:
  --timeout N       Request timeout in seconds (default: 30)
  --spec URL        Use this spec instead of configured one
```

## Module Boundaries (enforced by CI)

| Rule | Check |
|---|---|
| `display` never imports `http` | ruff/import check |
| `display` never imports `spec` | ruff/import check |
| `docs` never imports `engine` | ruff/import check |
| `http` never imports `spec` | ruff/import check |
| `spec` never imports `engine` | ruff/import check |
| No module imports `display` (it's a leaf) | ruff/import check |
| No circular imports | ruff/import check |

## Commands to Run

```bash
# Install dependencies
uv sync

# Run the CLI
uv run happi --help

# Run all tests
uv run pytest .bdd/

# Run BDD features for one module
uv run pytest .bdd/features/spec/

# Lint (check)
uv run ruff check .

# Lint (fix)
uv run ruff check --fix .

# Format
uv run ruff format .

# Type check
uv run pyright

# Full CI check (what GitHub Actions runs)
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest .bdd/
```

## CI Pipeline (GitHub Actions)

```yaml
on: [push, pull_request]
jobs:
  lint:
    - ruff check .
    - ruff format --check .
  typecheck:
    - pyright
  test:
    - pytest .bdd/ --tb=short
  build:
    - uv build
```

All four gates must pass. No merge with failures.

## Test Fixtures

Core 10 real OpenAPI specs (no synthetic). Located in `.bdd/support/fixtures/`:

| Tier | API | Tests what |
|---|---|---|
| Core | Petstore | Clean CRUD baseline |
| Core | GitHub (900+ ops) | Massive scale |
| Core | Stripe (300+ ops) | Complex relations |
| Core | Spotify (100+ ops) | Non-CRUD actions |
| Core | Cloudflare (500+ ops) | Multi-product |
| Edge | SendGrid (mail) | Email actions |
| Edge | GitLab | DevOps workflows |
| Edge | Netlify | Platform workflows |
| Edge | PagerDuty | Incident operations |
| Edge | httpbin | Flat, no resources |

Supplemental verified fixtures:
- DigitalOcean
- Slack

IMPORTANT: Intended functionality must not be hidden behind skipped tests.
If a feature is in INTENT.md and part of the current phase, its BDD scenario must run.
Only skip scenarios for functionality that is explicitly not implemented yet or for truly unavailable external fixtures.

## Definition of Done

A task is complete when:
- [ ] INTENT.md updated with the behavior
- [ ] Gherkin scenario exists and was RED before implementation
- [ ] Scenario is GREEN after implementation
- [ ] `ruff check .` passes with zero errors
- [ ] `ruff format --check .` passes
- [ ] `pyright` passes with zero errors
- [ ] All pre-existing tests still pass
- [ ] No intended-functionality scenarios are skipped
- [ ] No mocks introduced
- [ ] No `Any` types introduced
- [ ] No `print()` statements (use Rich)
- [ ] No `# type: ignore` comments
