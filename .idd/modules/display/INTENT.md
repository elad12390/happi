# Module Intent: display

> Render all CLI output as one of 8 patterns, optimized for human
> readability in interactive mode and machine consumption in pipe mode.

## Structure

```
display/
├── table.py            List → numbered table
├── card.py             Show → key-value card
├── success.py          Create/update/action → ✓ summary
├── confirm.py          Delete/destructive → ⚠ confirmation
├── error.py            Errors → 3-layer rendering
├── hints.py            ↳ next-action suggestions
├── explore.py          Explore/explain/find output
├── history.py          History output formatting
├── format.py           Output mode switching (json/yaml/table/wide/csv)
└── humanize.py         Timestamps, numbers, truncation helpers
```

## Constraints

| Rule | Rationale | Verified by |
|---|---|---|
| Auto-detect TTY for interactive vs pipe mode | Tables in terminal, JSON in pipes | BDD scenario |
| `--json` always outputs raw JSON regardless of TTY | Scriptability escape hatch | BDD scenario |
| `--yaml` outputs YAML | Alternative structured format | BDD scenario |
| `--output wide` shows all fields in table | Power user control | BDD scenario |
| `--quiet` suppresses hints and non-essential output | Scripting cleanliness | BDD scenario |
| `--debug` shows raw HTTP request + response | Debugging escape hatch | BDD scenario |
| HTTP verbs never appear in user-facing output | Human-first design principle | BDD step assertion |
| Timestamps always humanized in interactive mode | "2h ago" not "2026-03-26T07:12:38Z" | BDD step assertion |
| Colors disabled when NO_COLOR env is set or non-TTY | Accessibility + pipe safety | BDD scenario |
| Hints (↳) hidden in non-TTY and --quiet mode | Don't pollute scripted output | BDD scenario |
| `show` title always includes resource type + primary ID | Operationally stable across all APIs | BDD scenario |
| `show --full` expands known nested data and prints runnable related commands, but does not auto-fetch related resources | Fast, predictable, rate-limit safe | BDD scenario |
| `explore` prints a static pretty tree with action counts and copy-pasteable examples | Easiest onboarding, agent-friendly | BDD scenario |
| Help output is example-first and copy-pasteable | Best first-run UX | BDD scenario |

## Examples

### Table Output (list)

| Input | Output |
|---|---|
| `list` response: `[{id:1,name:"Buddy",status:"available"},{id:2,name:"Rex",status:"sold"}]` | Numbered table: `#0 1 Buddy available`, `#1 2 Rex sold`, footer: `2 pets` |
| `list` with `--json` | Raw JSON array |
| `list` in non-TTY (pipe) | Raw JSON (auto-detected) |
| `list` with `--output wide` | Table with ALL fields, not just auto-selected |
| `list` with `--query .name` | Filtered output: just names |

### Card Output (show)

| Input | Output |
|---|---|
| `show` response: `{id:1,name:"Buddy",status:"available",created:"2026-03-24T..."}` | Card: title "Pet 1", fields grouped, `Created: 2 days ago` |
| `show --full` | Card + deeper nested data + related runnable commands |
| `show --json` | Raw JSON object |

### Success Output (create/update/action)

| Input | Output |
|---|---|
| `create` → 201 with `{id:3,name:"Max"}` | `✓ Created pet 3` + key fields + hints |
| `update 1 --status sold` → 200 | `✓ Updated pet 1` + changed fields + hints |
| `activate 1` → 200 | `✓ Activated pet 1` + hints |

### Confirm Output (delete)

| Input | Output |
|---|---|
| `delete 1` in interactive mode | `⚠ Delete pet "Buddy" (1)? [y/N]` with context fields |
| `delete 1 --yes` | No prompt, proceed directly |
| `delete 1` in non-TTY | ERROR: "Use --yes to confirm deletion in non-interactive mode" |

### Error Output

| Input | Output |
|---|---|
| 422 with validation errors `{errors:[{field:"email",message:"required"}]}` | `✗ Couldn't create user (422)` + `• email is required` + suggestion command |
| 401 | `✗ Authentication failed (401)` + declared auth scheme + exact setup/login command + likely auth route if inferable |
| 404 | `✗ User not found (404)` + `↳ users list` + `↳ users search --query <term>` |
| 500 | `✗ Server error (500)` + `The API returned an internal error.` + `Run with --debug for details.` |
| Any error with `--debug` | Full HTTP request + response headers + body |

### Hint Output

| After command | Hints shown |
|---|---|
| `create` | `↳ <resource> show _` + `↳ <resource> update _` |
| `list` | `↳ <resource> show _N` |
| `show` | `↳ <resource> update _` + related resource hints |
| `delete` | No hints referencing deleted resource |
| Any command with `--quiet` | No hints |
| Any command in non-TTY | No hints |

### Explore / Find Output

| Input | Output |
|---|---|
| `stripe explore` | Pretty tree of resources with action counts and 2-3 runnable examples |
| `stripe explore customers` | Verbs/actions, important flags, related resources, examples |
| `stripe find refund` | Ranked results: exact command matches first, then prefix, then description, then param-name matches |
