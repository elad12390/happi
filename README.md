# happi

**Turn any OpenAPI spec into a human-friendly CLI.**

No HTTP verbs. No raw JSON. No copy-pasting IDs.  
Just `happi stripe customers list` and you're done.

```bash
# point it at any API
happi configure openai --spec https://raw.githubusercontent.com/openai/openai-openapi/2025-03-21/openapi.yaml
happi auth set openai --type bearer --token $OPENAI_API_KEY

# use it like a human
happi openai models list --json
happi openai completions create --body '{"model":"gpt-5.4","messages":[{"role":"user","content":"hello"}]}'
```

## Install

```bash
pipx install happi
```

Or from source:

```bash
git clone https://github.com/elad12390/openapi-cli
cd openapi-cli
uv sync
uv run happi --help
```

## How it works

1. **Configure** — point happi at an OpenAPI spec
2. **Explore** — browse resources and actions
3. **Use** — run commands with human verbs

```bash
happi configure petstore --spec https://petstore3.swagger.io/api/v3/openapi.json

happi petstore explore
# pets     create, delete, find-by-status, find-by-tags, show, update, upload-image
# orders   create, delete, show
# users    create, create-with-list, delete, login, logout, show, update

happi petstore pets show 1
# Pet 1
# name     doggie
# status   available

happi petstore pets show 1 --json
# {"id":1,"name":"doggie","status":"available",...}
```

## What happi does

| You type | What happens |
|---|---|
| `happi <api> explore` | See all resources and actions |
| `happi <api> find <query>` | Search commands by name |
| `happi <api> <resource> list` | GET collection → table |
| `happi <api> <resource> show <id>` | GET item → card |
| `happi <api> <resource> create --name Foo` | POST → success |
| `happi <api> <resource> update <id> --name Bar` | PUT → success |
| `happi <api> <resource> delete <id>` | DELETE with confirmation |
| `happi <api> <resource> <action> <id>` | Non-CRUD actions (activate, refund, send) |
| `happi <api> docs` | Generate Markdown with Mermaid diagram |
| `happi <api> history` | See what you did |
| `happi history` | Global history across all APIs |

## Output modes

```bash
happi stripe customers list              # pretty table (interactive)
happi stripe customers list --json       # raw JSON (also default in pipes)
happi stripe customers list --yaml       # YAML
happi stripe customers list --quiet      # no hints, no footer
happi stripe customers show cus_123 --output wide   # all fields
```

## Auth

```bash
# API key
happi auth set myapi --type api-key --value sk_123 --header X-API-Key

# Bearer token
happi auth set myapi --type bearer --token eyJ...

# OAuth2 (opens browser)
happi auth login myapi --authorize-url https://... --token-url https://... --client-id abc

# check what's configured
happi auth show myapi
happi auth show myapi --reveal
```

## Complex payloads

For endpoints that need nested JSON (like chat completions), use `--body` or stdin:

```bash
# inline JSON
happi openai completions create --body '{"model":"gpt-5.4","messages":[{"role":"user","content":"hello"}]}'

# from a file
happi openai completions create < payload.json

# piped
echo '{"model":"gpt-5.4","messages":[...]}' | happi openai completions create
```

## Config (git-style)

```bash
happi config list
happi config show stripe
happi config get apis.stripe.base_url
happi config set apis.stripe.base_url https://api.stripe.com
happi config unset apis.stripe.note
```

## Docs generation

```bash
happi myapi docs > API.md           # full Markdown with Mermaid relationship map
happi myapi docs --map-only         # just the Mermaid diagram
happi myapi docs --resource users   # docs for one resource
```

## Binary responses

Endpoints that return audio, images, or PDFs auto-save to `~/.happi/downloads/`:

```bash
happi elevenlabs text-to-speech create <voice_id> --text "hello world"
# ✓ Saved to ~/.happi/downloads/happi_1774563081.mp3 (23449 bytes, audio/mpeg)
```

## Tested against real APIs

happi has been verified end-to-end against:

- **OpenAI** — models, embeddings, chat completions with GPT-5.4
- **ElevenLabs** — agents, voices, text-to-speech with real audio output
- **Petstore** — full CRUD
- **archive.org** — search and scrape
- **httpbin** — flat utility API

Plus 12 OpenAPI fixture specs in the test suite (GitHub, Stripe, Spotify, Cloudflare, GitLab, PagerDuty, Netlify, SendGrid, DigitalOcean, Slack).

## Development

```bash
uv sync --all-extras

# lint
uv run ruff check .

# format
uv run ruff format .

# type check
uv run pyright

# run tests (download fixtures first)
bash .bdd/support/fixtures/download-fixtures.sh
uv run pytest .bdd/

# full CI check
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest .bdd/
```

## Architecture

happi follows the [Bulletproof](https://github.com/ArcBlock/idd) methodology: Intent-Driven Development + BDD E2E testing.

```
.idd/           Intent definitions (what SHOULD happen)
.bdd/           BDD tests (proves it works)
src/happi/      Source code
  spec/         OpenAPI loading, parsing, resource extraction
  engine/       Dynamic command tree, execution, stack, history
  display/      Output rendering (table, card, success, error, hints)
  http/         HTTP client with auth and binary response handling
  docs/         Markdown + Mermaid generation
  config/       API profiles, auth, overrides
```

## License

Apache 2.0 — see [LICENSE](LICENSE)
