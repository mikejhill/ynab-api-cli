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

## Fixture acceptance and PAT pools, 2026-10-18

The versioned v1 baseline passed all 33 required real-account read assertions in the explicitly designated disposable plan. The installed-wheel write lifecycle passed 55 distinct assertions across 93 HTTP requests, including duplicate import IDs, fractional milliunits, null/omitted updates, bulk updates, splits, linked transfers, schedules, budgeting, delta tombstones, and cleanup. Subsequent baseline assertions passed, and the private journal had no pending intent or active-run marker. The ordinary default plan was not changed.

Baseline seeding revealed automatic zero Starting Balance records and aggregate currency-precision rounding. The fixture contract now recognizes that exact zero opening record and uses whole-currency baseline amounts; separate mutation readbacks still verify fractional milliunits. These adjustments do not relax OpenAPI validation or normalize API response bodies.

The deterministic suite now includes 220 tests. `poe check` enforces the existing combined coverage gate and a separate minimum of 90% authored branch coverage. Generation, operation/schema-feature coverage, upstream compatibility, skill validation, and clean-install distribution checks remain separate release gates. Direct bank import and payee-location prerequisites remain live coverage gaps, and account-wide reads are excluded from these suites.

Read-only GitHub acceptance now requires the seeded baseline and installs the built wheel. Multi-PAT secrets are optional and entered manually by the owner; this implementation did not upload local credentials. Mutation suites remain local because safe recovery requires durable private journals.
