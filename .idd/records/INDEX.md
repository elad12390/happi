# Decision Records

| # | Date | Decision | Rationale |
|---|---|---|---|
| 001 | 2026-03-26 | Build from scratch, don't fork Restish | Our UX is fundamentally different (resource-first vs verb-first). Forking gives us plumbing but makes the UX layer harder. Clean architecture wins. |
| 002 | 2026-03-26 | Use Python as implementation language | Direct LAP integration, faster iteration, and the 2026 standard Python CLI stack is uv + Typer + Rich + Ruff. |
| 003 | 2026-03-26 | Human verbs only, no HTTP methods in UI | Users say "list users" not "GET users". HTTP is transport, not intent. Verb mapping is deterministic from method + path shape. |
| 004 | 2026-03-26 | Response stack is interactive-only | Stack (`_`, `_1`) adds hidden state that breaks script reproducibility. Disabled in non-TTY. Scripts use `--json` + `jq` or `@stdin`. |
| 005 | 2026-03-26 | Leaf resource is canonical, parents become flags | `orders list --user 123` not `users orders list 123`. Keeps command tree shallow and scriptable. Max 1 alias level deep. |
| 006 | 2026-03-26 | Relationship inference from field names + paths + $refs | `customer_id` → belongs-to customers. `/users/{id}/orders` → has-many. `$ref: User` → certain. Confidence scored. Override via config. |
| 007 | 2026-03-26 | Bulletproof methodology (IDD + BDD) | Intent before code. Every behavior has a Gherkin scenario. RED before GREEN. No mocks — real HTTP server for tests. |
| 008 | 2026-03-26 | pytest-bdd for BDD testing | Mature Python BDD stack. Tests execute the CLI as a real subprocess against a real local HTTP server. |
