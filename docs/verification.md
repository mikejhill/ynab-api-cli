# Delivery verification

Verified on Windows with Python 3.12.13 on 2026-10-11.

| Check | Result |
| --- | --- |
| Reviewed API surface | All 44 operations across 10 groups |
| Reviewed schema witnesses | All 911 manifest entries exercised |
| Generated client | Pinned openapi-python-client 0.29.0; reproducible generation |
| Formatting, linting, and typing | Ruff and ty pass; every ty rule is an error |
| Unit and contract tests | 147 tests pass; combined statement-and-branch coverage exceeds 96% |
| codegen-check | Pass |
| contract-check | Pass; independent wire cases, static typing cases, and schema tests |
| compat-check | Pass against the published API 1.87.0; candidate generation, typing, and tests pass |
| Skill | Valid frontmatter and matching canonical/package resources |
| Distributions | Wheel and source archive contain required resources |
| Clean installation | Temporary uv tool install passes help, discovery, inspection, offline doctor, and skill export |

The default tests use synthetic credentials, temporary files, mock HTTP, and simulated live workflows. No real YNAB account was read or changed. Actual live tests require separately supplied protected credentials and an explicit disposable plan named with the `YNAB API CLI TEST` prefix.

The GitHub Actions workflow is bundled but becomes active only after the project is hosted in GitHub. No repository publication or account provisioning was performed.

## Rename and release-pipeline validation, 2026-10-18

Renamed the package, executable, skill, and configuration directory to `ynab-api-cli`, with Python imports under `ynab_api_cli`. Regenerated all endpoint bindings and models through the maintained templates and transforms.

- `poe check`: 147 tests passed; 96.34% combined statement-and-branch coverage.
- `poe codegen-check`, `poe contract-check` (55 tests), and `poe compat-check` (63 candidate tests): passed. Upstream API remains 1.87.0 with no detected contract changes.
- `poe skill-check` and Codex skill validation: passed.
- Wheel, source archive, release archive, clean uv tool installation, and strict twine metadata validation: passed.
- GitHub workflow actionlint and release-please schema validation: passed.
- Source/history and extracted artifact privacy checks: completed; see [privacy review](privacy-review.md).

These automated results do not resolve the manual design findings documented in [the Python development review](python-development-review.md). No live YNAB account was accessed.
