# Isolated live testing

For new setups, use [fixture-based CLI acceptance](e2e.md). It provides persistent seed fixtures, exact semantic assertions, real CLI subprocesses, multi-PAT support, and safer whole-run recovery guards. The legacy runner below remains available for compatibility and broader endpoint smoke checks.

Live testing is excluded from default pytest and scheduled CI. Every endpoint is tested offline; a live run reports its actual completed operations and capability gaps separately.

1. Create a disposable YNAB plan manually. Its name must begin `YNAB API CLI TEST`; the API does not create plans.
2. Create a separate protected auth.json for the test account. The runner never falls back to ordinary CLI credentials or a default plan.
3. Run read-only checks first:

   ```text
   uv run poe live --plan-id EXPLICIT_UUID --auth-file /private/test/auth.json --state-directory /private/test/state
   ```

4. Enable writes only for that isolated plan:

   ```text
   uv run poe live --plan-id EXPLICIT_UUID --auth-file /private/test/auth.json --state-directory /private/test/state --enable-writes
   ```

The runner creates or reuses two accounts, a category group, a category, and a payee named with the `ynab-api-cli-test` prefix. These resources persist because the API has no corresponding delete operations. Do not mix unrelated data into them.

It exercises transaction creation, bulk creation/update, splits, transfers, duplicate import IDs, scheduled transaction lifecycle, category/group/payee updates, and monthly budgeting. Created transaction records are deleted after verification where supported. Deleted records can remain as tombstones.

Before each mutation, the runner writes a private intent journal. An uncertain operation leaves the intent unresolved, and subsequent runs stop. Inspect the recorded target and the actual API state before manually clearing `pending`; never simply rerun a failed write. Readback mismatches also require investigation.

Payee-location reads require location fixtures. Direct Import needs a linked bank account; manual test accounts cannot verify actual bank imports. The report lists these gaps and never claims full live coverage when they remain.

No live account connection is provisioned by installing this project. Supply credentials and a designated plan explicitly to run these tests.

## Verified live run, 2026-10-18

An explicitly designated disposable plan passed the real read/write lifecycle run: 43 of 44 operations completed. The run covered accounts, categories, payees, transaction creation and bulk updates, duplicate import IDs, splits, transfers, scheduled transactions, budgeting, and deletion checks. The missing operation was `getPayeeLocationById` because no suitable location fixture existed. The import endpoint completed, but actual bank import remains unverified for manual accounts.

Subsequent reads confirmed that both fixture account balances returned to zero, and the private journal had no unresolved mutation. Reusable accounts, category group, category, and payee remain in the disposable plan. No token, plan UUID, account data, or response bodies are included in this report.

The proposed CI-specific read-only probe also passed 15 selected-plan operations against that plan. See [secure live CI](live-ci.md) before putting credentials on a remote runner. These results do not claim full live coverage.
