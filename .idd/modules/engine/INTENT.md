# Module Intent: engine

> Generate a Typer command tree from the resource model, execute commands
> against the API, and manage the response stack.

## Structure

```
engine/
├── tree.py             Build resource → verb command tree from ResourceModel
├── executor.py         Execute a command: resolve args → build request → send → display
├── stack.py            Response stack (_, _1, _.field)
├── history.py          Persist command history in SQLite
└── resolver.py         Resolve _ references and history references
```

## Constraints

| Rule | Rationale | Verified by |
|---|---|---|
| Commands are registered dynamically at runtime from spec | No hardcoded commands per API | BDD scenario |
| Command tree: `<api> <resource> <verb> [args] [--flags]` | Consistent grammar | BDD step assertion |
| Resources are top-level subcommands under the API name | Flat, discoverable | BDD scenario |
| Verbs are subcommands under each resource | `users list`, `users show`, `users create` | BDD scenario |
| Path params become positional args (required) | `users show 123` not `users show --id 123` | BDD scenario |
| Query params become optional flags | `users list --status active` | BDD scenario |
| Body fields become flags with type hints | `users create --name Alice --role admin` | BDD scenario |
| Unknown command suggests closest match | Typo recovery | BDD scenario |
| Stack is disabled in non-TTY mode | Scripts must be deterministic | BDD scenario |
| Stack max size: 20 entries, ~5 MB total | Prevent memory bloat | BDD step assertion |
| `_` after a list MUST error, never auto-pick | Prevent silent wrong selection | BDD scenario |
| Command tree is fully built at startup from the parsed model | Reliable help, completion, explore, and find | BDD scenario |
| Stack is per API, per process/session only | Prevent cross-API confusion and hidden persistent state | BDD scenario |
| History is persisted per API in SQLite, but full response bodies are never persisted | Useful recall without secret/data leakage | BDD scenario |
| Destructive replays from history require confirmation unless `--yes` | Safe defaults for `redo` | BDD scenario |
| Global flags (--json, --output, --yes, --quiet, --yaml) MUST be stripped from raw args BEFORE splitting into positional vs extras | Prevents flags from being consumed as path parameter values | BDD scenario |
| When a resource has multiple operations mapping to the same verb, disambiguate with a suffix (e.g. list, list-by-id, list-summaries) | Prevents silent loss of operations | BDD scenario |
| `--body '{...}'` flag sends raw JSON as the request body, bypassing flag-based body construction | Handles complex/nested payloads that can't be expressed as flat flags | BDD scenario |
| Stdin pipe (`echo '{}' \| happi ...`) reads JSON from stdin and uses it as the request body | Enables scripting with prebuilt payloads and file input via `< file.json` | BDD scenario |
| `--body` takes priority over flag-based body; stdin is used only when no `--body` and no body flags are present and stdin is not a TTY | Clear precedence, no surprises | BDD scenario |

## Examples

### Command Tree Generation

| Input (ResourceModel) | Output (command tree) |
|---|---|
| Resource "pets" with ops [list, show, create, delete] | Commands: `petstore pets list`, `petstore pets show`, `petstore pets create`, `petstore pets delete` |
| Resource "pets" with action "upload-image" | Command: `petstore pets upload-image <petId>` |
| Resource "users" with parent path `/orgs/{orgId}/users` | Commands: `petstore users list --org <orgId>` |
| Duplicate operations from `/users/search` and `/admin/users/search` | Commands: `myapi users search` and `myapi users admin-search` |

### Command Execution

| Input (command) | Output |
|---|---|
| `petstore pets list` | GET /pets → display table |
| `petstore pets show 42` | GET /pets/42 → display card |
| `petstore pets create --name Buddy --status available` | POST /pets body:`{"name":"Buddy","status":"available"}` → display success |
| `petstore pets update 42 --status sold` | PUT /pets/42 body:`{"status":"sold"}` → display success |
| `petstore pets delete 42` | prompt `⚠ Delete pet "Buddy"?` → DELETE /pets/42 → display success |
| `petstore pets delete 42 --yes` | DELETE /pets/42 → display success (no prompt) |
| `petstore pets activate 42` | POST /pets/42/activate → display success |
| `openai completions create --body '{"model":"gpt-5.4","messages":[...]}'` | POST /chat/completions with raw JSON body → display success |
| `echo '{"model":"gpt-5.4","messages":[...]}' \| happi openai completions create` | POST /chat/completions with stdin JSON body → display success |
| `happi openai completions create < payload.json` | POST /chat/completions with file contents as body → display success |

### Response Stack

| Sequence | `_` resolves to |
|---|---|
| `pets create --name Buddy` → returns `{id:42,...}` | `_` = `42` (primary ID) |
| `pets show _` | = `pets show 42` |
| `pets show 42` → returns `{id:42,name:"Buddy",...}` then `pets show _.name` | = `"Buddy"` |
| `pets list` → returns `[{id:1,...},{id:2,...}]` then `pets show _` | ERROR: "Last result is a list of 2 pets. Use _[0].id or choose a specific row." |
| `pets create --name A` then `pets create --name B` then `_1` | = ID of pet A (previous result) |
| Non-TTY mode: `pets create` then `pets show _` | ERROR: "_ references are only available in interactive mode. Use --json and pipe." |

### History

| Sequence | Persisted history |
|---|---|
| `pets create --name Buddy` succeeds with id `42` | history row with command, success=`true`, primary_id=`42`, resource=`pets`, verb=`create` |
| new process starts later | `_` is empty, but `happi petstore history` still shows the command |
| `happi petstore redo 0` for a create/delete/refund action | confirmation required unless `--yes` |
| `happi history` | global history across all APIs |
| `happi petstore history` | history filtered to petstore only |

### Help Output

| Input | Output |
|---|---|
| `petstore --help` | List of resources with short descriptions |
| `petstore pets --help` | List of verbs + actions for pets |
| `petstore pets create --help` | Required/optional flags, request schema, response schema, example |
| `petstore nonexistent` | "Unknown resource 'nonexistent'. Did you mean 'pet'? Try: happi petstore find nonexistent" |
