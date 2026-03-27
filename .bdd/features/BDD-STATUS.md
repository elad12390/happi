# BDD Feature File Status

## Wired to pytest-bdd (running in CI)

| Module | Feature files | Step definitions |
|--------|---------------|------------------|
| `spec/` | load-spec, extract-resources, infer-verbs, infer-relations, bugfixes | `steps/spec_steps.py` via `features/spec/test_spec.py` |

## Covered by integration tests (not Gherkin-wired)

These behaviors are tested in `.bdd/test_integration.py` via subprocess, but
their `.feature` files are NOT yet wired to pytest-bdd step definitions.
All scenarios are tagged `@wip`.

| Module | Feature files | Integration test coverage |
|--------|---------------|--------------------------|
| `engine/` | command-tree, execute-crud, execute-actions, response-stack, bugfixes | Yes (45 tests) |
| `display/` | error-output, hints | Yes |
| `http/` | auth | Yes |
| `docs/` | markdown-gen, mermaid-gen | Yes |
| `config/` | profiles | Yes |

## Next steps

To wire a feature file to pytest-bdd:
1. Create step definitions in `.bdd/steps/{module}_steps.py`
2. Register scenarios in a test file using `pytest_bdd.scenarios()`
3. Remove `@wip` tags from wired scenarios
