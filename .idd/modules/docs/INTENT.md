# Module Intent: docs

> Generate Markdown documentation with Mermaid relationship diagrams
> from a parsed ResourceModel.

## Structure

```
docs/
├── markdown.go         Full Markdown document generation
├── mermaid.go          Mermaid relationship diagram from relations
└── quickref.go         Quick reference table generation
```

## Constraints

| Rule | Rationale | Verified by |
|---|---|---|
| Output is valid Markdown (parseable by any Markdown renderer) | Portability — works on GitHub, GitLab, etc. | BDD scenario |
| Mermaid diagram is valid Mermaid syntax | Must render in GitHub, VS Code, etc. | BDD scenario |
| Docs generated from ResourceModel only — no HTTP calls | Docs work offline from cached/local spec | BDD step assertion |
| Every resource gets a section with actions table + schema | Completeness | BDD scenario |
| Example commands use the actual CLI binary name | Copy-paste ready | BDD step assertion |
| Relations table shows confidence level | Transparency about inference quality | BDD scenario |
| `docs` outputs to stdout by default (pipeable) | Unix convention: `docs > API.md` | BDD scenario |

## Examples

### Markdown Generation

| Input | Output |
|---|---|
| ResourceModel with 3 resources, 5 relations | Full Markdown with title, Mermaid diagram, 3 resource sections, relation table, quick reference |
| `docs --resource users` | Markdown for users resource only |
| `docs --map-only` | Just the Mermaid diagram section |
| `docs > API.md` | Full Markdown saved to file |

### Mermaid Diagram

| Input (relations) | Output (Mermaid edges) |
|---|---|
| `{from:"orders", to:"users", type:"belongs-to", via:"customer_id"}` | `orders -->|belongs to| users` |
| `{from:"users", to:"orders", type:"has-many", via:"path"}` | `users -->|has many| orders` |
| `{from:"categories", to:"categories", type:"belongs-to", via:"parent_id"}` | Self-referencing edge on categories |
| `{from:"projects", to:"users", confidence:"medium"}` | Edge with `?` annotation |
| No relations detected | Diagram with nodes only, no edges |

### Quick Reference

| Input | Output row |
|---|---|
| Resource "users" with verb "list" | `List all users \| happi myapi users list` |
| Resource "users" with action "activate" | `Activate a user \| happi myapi users activate <id>` |
| Stack reference | `Reference last result \| use _ (e.g., happi myapi users show _)` |
