# Module Intent: config

> Manage API profiles (base URL, auth, spec location) and override
> mappings for relationship inference and custom verb names.

## Structure

```
config/
├── config.py           Read/write config file
├── profiles.py         API profile management (CRUD)
├── auth.py             Auth storage and login state
└── overrides.py        Relation overrides, custom verb mappings
```

## Constraints

| Rule | Rationale | Verified by |
|---|---|---|
| Config stored in `~/.happi/config.yaml` | XDG-ish standard location | BDD scenario |
| Multiple API profiles supported | Users work with multiple APIs | BDD scenario |
| Auth credentials stored in config (not env vars by default) | Simplicity — one config file | BDD scenario |
| Override file `.happi.yaml` in cwd is loaded if present | Per-project customization | BDD scenario |
| Override file merges with, doesn't replace, global config | Additive customization | BDD step assertion |
| Config file created on first `configure` if absent | No manual setup required | BDD scenario |
| Profile name is user-owned and independent from spec title | Supports `stripe-live`, `stripe-test`, etc. | BDD scenario |
| `configure` may skip auth; auth can be added later via `auth set` or `auth login` | Fast first-run onboarding | BDD scenario |
| If multiple auth schemes exist, auth commands require explicit `--type` | No guessing wrong auth flow | BDD scenario |
| Secrets are masked by default and only revealed with `--reveal` | Safe config inspection | BDD scenario |
| Config UX follows git-config style: list/get/set/unset/show | Familiar, low-cognitive-load interface | BDD scenario |
| For specs with multiple servers, prefer explicit `--server`, otherwise auto-pick the most production-like HTTPS server | Deterministic and agent-friendly | BDD scenario |

## Examples

### Profile Management

| Input | Output |
|---|---|
| `configure stripe-live --spec stripe.yaml` | Creates profile named `stripe-live` even if spec title is `Stripe API` |
| `configure petstore` (first time) | Creates `~/.happi/config.yaml` with petstore profile; auth may be empty |
| `configure petstore` (existing) | Updates existing profile in place, preserves auth unless replaced |
| Config file with profiles `[petstore, github]` | Both APIs accessible: `happi petstore pet list`, `happi github repos list` |

### Config File Format

```yaml
# ~/.happi/config.yaml
apis:
  petstore:
    base_url: https://petstore3.swagger.io/api/v3
    spec_url: https://petstore3.swagger.io/api/v3/openapi.json  # or auto-discovered
    auth:
      type: api-key
      header: X-API-Key
      value: abc123
  github:
    base_url: https://api.github.com
    auth:
      type: bearer
      token: ghp_xxxxxxxxxxxx
    spec:
      source: lap
      name: github-com
      current_hash: sha256:abc123
      last_checked_at: 2026-03-26T12:00:00Z
```

### Override File Format

```yaml
# .happi.yaml (in project root)
relations:
  orders.owner_id: organizations    # override: not users
  orders.coupon_code: ~             # explicit: not a relation
  projects.lead: users              # custom: "lead" field → users

verbs:
  # Custom verb overrides
  POST /users/batch: bulk-create    # override inferred name

display:
  # Column selection overrides for list
  users.list.columns: [id, name, email, role, created_at]

names:
  resources:
    payment_intents: payment-intents
  actions:
    payment-intents.confirm: confirm
```

### Override Application

| Input (field, override config) | Output |
|---|---|
| field `owner_id`, override says `organizations` | Relation to organizations (not users) |
| field `coupon_code`, override says `~` (null) | No relation (suppressed) |
| field `lead`, override says `users` | Relation to users with confidence "configured" |
| No override for field `customer_id` | Normal inference applies |
