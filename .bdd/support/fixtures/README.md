# Test Fixtures — Real OpenAPI Specs

These are **real** OpenAPI specs from real APIs. No synthetic specs.

## Supplemental Fixtures

These are also downloaded and verified, but not yet wired into the core BDD matrix:

| API | File | Why keep it |
|---|---|---|
| **DigitalOcean** | `digitalocean.yaml` | Strong infrastructure API with many resources |
| **Slack** | `slack.json` | Widely used developer API with huge action surface |

## The 10 Test Specs

### Tier 1 — Core test suite

| # | API | File | Source | Why this one |
|---|---|---|---|---|
| 1 | **Petstore 3.0** | `petstore.json` | [petstore3.swagger.io](https://petstore3.swagger.io/api/v3/openapi.json) | Clean CRUD baseline |
| 2 | **GitHub REST API** | `github.yaml` | [github/rest-api-description](https://github.com/github/rest-api-description) | Massive real-world spec, deep nesting, pagination |
| 3 | **Stripe** | `stripe.yaml` | [stripe/openapi](https://github.com/stripe/openapi) | Gold-standard API design, many actions, rich schemas |
| 4 | **Spotify** | `spotify.yaml` | [sonallux/spotify-web-api](https://github.com/sonallux/spotify-web-api) | Non-CRUD domain with search/playback actions |
| 5 | **Cloudflare** | `cloudflare.yaml` | [cloudflare/api-schemas](https://github.com/cloudflare/api-schemas) | Huge multi-product API, broad resource surface |

### Tier 2 — Developer APIs & edge cases

| # | API | File | Source | Why this one |
|---|---|---|---|---|
| 6 | **SendGrid (Mail)** | `sendgrid.yaml` | [twilio/sendgrid-oai](https://github.com/twilio/sendgrid-oai) | Email API, compact but action-heavy |
| 7 | **GitLab** | `gitlab.yaml` | [gitlab-org/gitlab](https://gitlab.com/gitlab-org/gitlab) | Large DevOps API, many resources, mixed actions |
| 8 | **Netlify** | `netlify.json` | [netlify/open-api](https://open-api.netlify.com/swagger.json) | Modern platform API used by many frontend devs |
| 9 | **PagerDuty** | `pagerduty.json` | [PagerDuty/api-schema](https://github.com/PagerDuty/api-schema) | Operations-heavy incident management API |
| 10 | **httpbin** | `httpbin.json` | [httpbin.org](https://httpbin.org/spec.json) | Flat utility API, worst-case non-resource structure |

## Download Script

Run `./download-fixtures.sh` to fetch fresh copies of all 10 specs.

## Coverage Matrix

| Spec | Tags | OpIds | Nested | Relations | Actions | Size | Best for |
|---|---|---|---|---|---|---|---|
| Petstore | ✓ | ✓ | low | low | low | tiny | Happy-path CRUD |
| GitHub | ✓ | ✓ | high | medium | high | massive | Scale + deep trees |
| Stripe | ✓ | ✓ | medium | high | high | huge | Rich schemas + actions |
| Spotify | ✓ | ✓ | medium | medium | high | medium | Non-CRUD verbs |
| Cloudflare | ✓ | ✓ | medium | high | high | massive | Multi-product grouping |
| SendGrid | ✓ | ✓ | low | low | medium | small | Email-specific actions |
| GitLab | ✓ | ✓ | medium | medium | high | huge | DevOps workflows |
| Netlify | ✓ | ✓ | medium | medium | medium | medium | Modern platform API |
| PagerDuty | ✓ | ✓ | medium | medium | high | medium | Incident operations |
| httpbin | ✓ | ✓ | flat | none | medium | small | Edge-case path inference |

## Why These 10

This set covers:

- tiny → massive specs
- clean CRUD → action-heavy APIs
- platform/devtools APIs used by real developers
- deeply nested paths, flat utility paths, and mixed resource quality
- companies from OSS/community roots through major developer platforms

No fixture is fabricated. If a new edge case is needed, prefer another real public spec over inventing one.
