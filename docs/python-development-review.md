# Python development review and disposable-plan testing

Reviewed on 2026-10-18 against the installed `python-development` skill and its code, CLI, project, and testing references.

## Verdict

The supplementary YNAB skill has valid Codex metadata, uses progressive discovery, and matches its packaged copy. The Python CLI follows the required toolchain and layout, but it does **not fully comply** with the skill's manual design rules. Automated linting and typing do not establish full compliance.

| Finding | Evidence | Required correction |
| --- | --- | --- |
| Construction performs I/O | `contract.py:36` reads contract resources; `live.py:40` reads the fixture journal; `__main__.py:31` constructs the contract | Move loading into explicit factories; inject loaded collaborators |
| Services expose mutable implementation state | `live.py:45-58`, `contract.py`, and `__main__.py` | Use private attributes and deliberate public interfaces |
| Generated models execute initialization during import | `generated/models/__init__.py:394` calls `ModelRegistry.rebuild()` | Resolve through generation templates and explicit initialization; never patch generated output manually |
| Large classes combine responsibilities | `LiveRunner` spans more than 400 lines; `Application` owns multiple command handlers | Separate fixture lifecycle, journal persistence, and command handlers; use subcommand settings types |
| Tests patch application internals | `test_cli.py:232`, `test_development.py:158`, and `test_live.py:265`; `SyntheticLive` overrides the runner's dispatch path | Inject collaborators and mock the HTTP/process boundary; retain end-to-end orchestration tests |
| Live orchestration reads the clock directly | `live.py:56`, `live.py:255`, and `live.py:369` | Inject a clock for deterministic orchestration tests |

The existing coverage threshold uses coverage.py's combined statement-and-branch metric. It does not independently enforce a minimum branch-only percentage. Generated code is excluded from runtime coverage, but included in strict typing and contract checks.

Current validation results:

- `uv run --offline --locked poe check`: passed; 147 tests, 96.34% combined coverage, and 319/346 branches covered (92.20%). Formatting, linting, and strict ty passed.
- `uv run --offline --locked poe codegen-check`: passed; regeneration occurred in a temporary directory and matched checked-in generated source.
- `uv run --offline --locked poe skill-check`: passed; canonical and packaged skill resources match.
- Codex `skill-creator/scripts/quick_validate.py skills/ynab-api-cli`: passed.
- Live-runner help and poe argument forwarding: checked without account access.
- Upstream compatibility and clean-wheel installation were not rerun in this review; prior delivery results are documented separately in `verification.md`.

## Test a real account with a disposable budget

YNAB's current API calls budgets **plans**. Create a new, empty plan in the YNAB web application named `YNAB API CLI TEST - disposable`. Do not link bank accounts or copy real transactions into it.

Generate your own personal access token under **Account Settings → Developer Settings → New Token**. See [YNAB's official authentication instructions](https://api.ynab.com/#personal-access-tokens). Enter the token only into the CLI's hidden local prompt. A separate configuration directory isolates local settings; it does not restrict the token to the dummy plan. The runner's explicit UUID and name check are application guards, not account permissions.

Open a dedicated PowerShell terminal, then run:

```powershell
Set-Location 'path\to\ynab-api-cli'
uv sync --locked
$env:XDG_CONFIG_HOME = Join-Path $env:USERPROFILE '.config/ynab-api-cli-test'
uv run ynab-api-cli configure
uv run ynab-api-cli doctor
uv run ynab-api-cli plans get-plans
```

Copy the UUID for the disposable plan from the output. Replace the placeholder below with that exact UUID:

```powershell
$testPlan = 'REPLACE-WITH-DISPOSABLE-PLAN-UUID'
$testAuth = Join-Path $env:XDG_CONFIG_HOME 'ynab-api-cli/auth.json'
$testState = Join-Path $env:USERPROFILE '.local/state/ynab-api-cli-test'
uv run ynab-api-cli select-plan $testPlan
uv run ynab-api-cli doctor
uv run poe live --plan-id $testPlan --auth-file $testAuth --state-directory $testState
```

That first live run is read-only. It checks the plan identity and available read operations; missing fixture-dependent operations are expected. An offline doctor result cannot establish authentication or API access.

When ready to create and update dummy records, run:

```powershell
uv run poe live --plan-id $testPlan --auth-file $testAuth --state-directory $testState --enable-writes
```

The live runner submits writes directly when `--enable-writes` is present; this is separate from the ordinary CLI's preview/`--execute` flow. It always requires the explicit plan and auth-file arguments and does not fall back to normal CLI defaults.

## Interpret results and clean up

- Review `completed_operations`, `missing_operations`, `gaps`, `retained_fixture_ids`, and `complete_live_coverage` in the JSON report. A successful process exit alone does not prove complete live coverage.
- The runner exercises transaction creation, bulk changes, duplicate import IDs, splits, transfers, scheduled transactions, and category budgeting. It verifies many writes through subsequent reads. The current implementation does not independently read back every mutation, including category-group updates and split/transfer deletions.
- Manual accounts cannot verify actual Direct Import. Payee-location tests also need suitable fixtures. Do not link a real bank solely to remove a coverage gap.
- Accounts, category groups, categories, and payees remain for reuse; transaction deletions may leave API tombstones. Delete the entire disposable plan through YNAB after testing if you no longer need it.
- On failure, inspect the journal at `<state-directory>/<plan-uuid>.json` and read the affected API records. Reconcile any `pending` mutation before changing the journal. Do not clear it and retry blindly.
- Close the dedicated PowerShell terminal to discard its XDG override. Revoke the test token in Developer Settings when finished, and remove its isolated credential file when no longer needed.

No real-account connection or live write was performed during this review. The procedure above is a path for user-run integration testing, not evidence that the live harness has already passed against YNAB.
