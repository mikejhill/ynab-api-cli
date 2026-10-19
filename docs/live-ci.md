# Live tests without publishing credentials

The ordinary PR, push, scheduled contract, and release checks do not use YNAB credentials. The separate `live.yml` workflow is manual, restricted to main, and read-only. It installs the built wheel, checks the explicit disposable plan, and requires the exact seeded assertions described in [E2E acceptance](e2e.md). An empty plan fails. Seed the v1 fixtures locally before the next run. It does not print plan IDs, journal paths, response bodies, or fixture IDs.

## Security boundary

GitHub encrypts environment secrets, but the approved runner and application necessarily receive the plaintext token in memory. Secret masking is not an exfiltration barrier: malicious workflow code, actions, or dependencies can steal a token. If your requirement is that the token never leaves this computer, keep live tests local and do not configure a GitHub secret. See [GitHub's secret guidance](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

YNAB personal access tokens are account credentials. Selecting a dummy plan in the CLI does not restrict the token's API permissions. For CI, use a dedicated test account containing only disposable data where possible; a separately issued token on the same account is independently revocable but still has account access. See [YNAB authentication](https://api.ynab.com/#personal-access-tokens).

## Configure the protected environment before enabling the workflow

1. Open repository **Settings → Environments → New environment**, and name it `ynab-e2e`. Do not reuse `pypi`.
2. Add a trusted maintainer as a required reviewer. For a single-maintainer repository, allow that maintainer to review their own manual run; preventing self-review requires another reviewer. Restrict deployment branches to the selected branch `main`, and prevent bypassing protection rules where available.
3. Protect main through branch rules, require code review, and review changes to `live.yml`, `ci_live.py`, `live.py`, transport code, actions, and `uv.lock` before approving a live job. Pin actions to reviewed commit SHAs.
4. Create environment secret `YNAB_TEST_PLAN_ID` and either `YNAB_ACCESS_TOKEN` (one PAT) or `YNAB_ACCESS_TOKENS` (a JSON array of distinct PAT strings). Never configure both token secrets; delete the old single-token secret when switching to the pool. Enter the array only in GitHub’s encrypted environment-secret UI or a hidden local prompt. The latter must be the explicit dummy-plan UUID. The plan name must begin `YNAB API CLI TEST`.

Use GitHub's environment-secret UI or hidden local GitHub CLI prompts:

```text
gh secret set YNAB_ACCESS_TOKEN --repo mikejhill/ynab-api-cli --env ynab-e2e
gh secret set YNAB_TEST_PLAN_ID --repo mikejhill/ynab-api-cli --env ynab-e2e
```

Enter each value only at its local prompt. Do not use `--body TOKEN`, shell literals, command substitution that could echo it, chat, or a committed file. This setup sends the token to GitHub's encrypted secret store; it does not keep the token exclusively local.

5. After merging the reviewed workflow into main, open **Actions → Read-only live YNAB tests → Run workflow**, choose main, inspect the exact commit and changes, then approve its environment deployment. [Environment protection rules](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) gate when environment secrets become available.

The workflow has no PR trigger, no `pull_request_target`, no user-selected checkout ref, no artifact uploads, and no dependency caching. Dependency installation runs before the token-bearing step. Only that step receives the secrets. The helper consumes them from its process environment, creates a permission-protected temporary auth file, and removes its temporary files on success or failure. The job uses a fresh GitHub-hosted runner. Reports contain only fixed status fields, reviewed operation names, and capability gaps. Do not enable shell tracing, HTTP/debug logging, step debugging, core dumps, response uploads, or caches containing configuration.

Account-wide plan listing and user reads are excluded. This reduces application scope; it does not reduce token permissions. Read-only CI requires all seeded semantic assertions and validates remaining selected-plan read responses. Missing required fixtures fail; unsupported bank-import and location capabilities remain reported gaps. Success does not mean all-feature live coverage.

## Keep mutation tests local

The legacy live runner creates reusable accounts, a category group, a category, and a payee, and exercises transaction and budgeting changes. Some fixtures cannot be deleted through the API. It persists private mutation intents and stops on uncertain outcomes. Keep that journal outside the repository and reconcile uncertain writes before rerunning.

Write tests are deliberately absent from `live.yml`. Ephemeral CI journals disappear when a job ends; blindly rerunning a failed write job can duplicate an uncertain mutation. Adding CI writes requires a reviewed design for durable private journal storage, restoration before every run, concurrency, reconciliation, retention, and cleanup. Do not upload an auth file or mutation journal as a public workflow artifact.

## Rotation and incident response

Revoke the CI token in YNAB Developer Settings and replace the environment secret to rotate it. Remove the secret and disable the live workflow when no longer needed. If a token may have appeared in output or an untrusted runner, revoke it immediately; deleting logs alone is insufficient. No local token is uploaded automatically by this project.

## Required baseline and multi-PAT operation

Run `e2e seed --enable-writes` locally as documented in [E2E acceptance](e2e.md), then run `e2e reads` before approving CI. Both use the same versioned fixture contract. Do not run local mutation suites concurrently with CI reads. The optional JSON-array secret uses the same bounded 429-only rollover as the ordinary CLI. An authentication or authorization error from any attempted PAT fails immediately. Never upload auth.json, journals, captured subprocess output, or financial response bodies. The pool is temporary and permission-protected on the runner; no token values are included in reports.

## Multi-PAT CI secret

In **Settings → Environments → ynab-e2e → Environment secrets**, store a JSON array such as `["PAT_ONE", "PAT_TWO"]` as `YNAB_ACCESS_TOKENS`, replacing the placeholders only in the secret editor. Delete `YNAB_ACCESS_TOKEN` when switching to the pool; configuring both formats deliberately fails. Keep the existing explicit `YNAB_TEST_PLAN_ID` secret.

Alternatively, run `gh secret set YNAB_ACCESS_TOKENS --repo mikejhill/ynab-api-cli --env ynab-e2e` and enter the JSON array only at its hidden prompt. No credentials are supplied as command arguments. Each PAT is registered separately using GitHub's [runner masking protocol](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#masking-a-value-in-a-log), because masking the complete JSON secret alone does not cover individual tokens. Masking is defense in depth; reports and errors still omit credentials entirely.
