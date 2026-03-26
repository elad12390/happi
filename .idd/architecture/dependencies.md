# Module Dependencies

## Dependency Matrix

```
             config  spec  http  engine  display  docs
config         -      -     -      -       -       -
spec           ✓      -     -      -       -       -
http           ✓      -     -      -       -       -
engine         ✓      ✓     ✓      -       -       -
display        -      -     -      ✓       -       -
docs           ✓      ✓     -      -       -       -
```

Read as: row depends on column.

## Dependency Graph

```
                ┌────────┐
                │ config │  ← loaded first, provides API profiles
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

## Data Flow

```
1. config loads API profile (base URL, auth, spec location)
2. spec fetches + parses OpenAPI → produces ResourceModel
3. engine builds Typer command tree from ResourceModel
4. User runs a command → engine resolves args/flags
5. http builds + sends HTTP request
6. http returns parsed response
7. engine pushes to stack, determines display pattern
8. display renders output
```

For `docs` command:
```
1. config loads API profile
2. spec produces ResourceModel (with relations)
3. docs generates Markdown + Mermaid from ResourceModel
4. display outputs to stdout or file
```
