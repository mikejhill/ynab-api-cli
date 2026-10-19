# Fixture-based CLI acceptance tests

These suites invoke the installed `ynab-api-cli` Python module as real subprocesses. They validate public argument parsing, stdin JSON, previews, execution guards, exit status, metadata, generated bindings, HTTP, and independent response schemas. Expected fixture amounts and relationships are specified independently of returned values.

## Prepare a disposable plan

1. Use a dedicated test account where possible. Create a disposable plan named with the prefix `YNAB API CLI TEST` and copy its explicit UUID. No default plan fallback is permitted.
2. Configure protected credentials locally. Single-PAT and multi-PAT files both work; see [PAT pools](pat-pools.md). Do not share these credentials through chat.
3. Choose a durable private state directory **outside the Git checkout**, such as `~/.local/state/ynab-api-cli/e2e`. Keep the same directory for every write run. Journals and locks are private, and must not be uploaded as Actions artifacts.
4. Run the following commands from this project. Replace placeholders with paths and the explicit UUID; they contain no access tokens.

```text
uv run poe e2e seed --plan-id TEST_UUID --auth-file /private/auth.json --state-directory /private/e2e-state --enable-writes
uv run poe e2e reads --plan-id TEST_UUID --auth-file /private/auth.json --state-directory /private/e2e-state
uv run poe e2e mutations --plan-id TEST_UUID --auth-file /private/auth.json --state-directory /private/e2e-state --enable-writes
```

For an installed wheel, replace `uv run poe e2e` with `python -m ynab_api_cli.e2e` using its interpreter. Ordinary `uv run poe check` never reads account credentials or runs live writes.

## What remains in the plan

The versioned `ynab-api-cli-e2e-v1` namespace owns two manual accounts, a category group, a category, a payee, four source transactions (ordinary, zero, split, and transfer), the linked transfer counterpart, and one future monthly scheduled transaction. These synthetic records remain for read-only CI. Do not add unrelated records to these accounts or edit these fixtures.

Baseline source balance is -15000 milliunits; target balance is 2000; category activity is -13000 and January 2026 budgeting is 1000. The ordinary record has an exact Unicode memo, payee, category, date, cleared state, and approval state. Splits are -400 and -600; the transfer has linked opposite entries. Null and zero values are explicit. Historical fixture dates stay fixed across runs.

The schedule starts four years after initial seeding, within YNAB's documented five-year limit. Reads require it to remain unchanged and more than 90 days from execution. Reconcile and replace it before that threshold; it is not renewed silently. Do not use this plan for unrelated work. Reusable resources cannot all be deleted through the API; remove the disposable plan manually when finished.

Seed reuses unique named resources and import identifiers. Ambiguous identities, missing required fixtures in reads, wrong balances, changed values, and unsupported required fixture capabilities fail. Seed does not delete unexpected records or silently repair corrupted baseline transactions.

## Pass criteria and coverage

| Suite | Required verification |
| --- | --- |
| seed | Provision absent baseline resources, then pass all seeded reads |
| reads | Exact balances, monetary values, Unicode, nulls, splits, transfer links, date and resource filters, scheduled values, budgeting/activity, unchanged deltas, default/explicit plan equivalence |
| mutations | Create/read/update/read/delete, bulk create/update, duplicate import IDs, null/zero/omitted updates, split and transfer writes, scheduled lifecycle, category/group/payee updates, budget restoration, delta tombstones, then all baseline reads again |

Every submitted mutation first passes a network-free preview comparison. Required assertions fail the process on mismatch. Reports contain only static scenario/operation labels, fixture version, request counts, and capability gaps; no plan IDs, financial payloads, token values, or journal paths.

Direct Import with actual bank results and payee-location behavior require separate capabilities and remain explicit gaps. Account-wide user and plan-list operations are intentionally excluded. `complete_live_coverage` remains false. Passing these suites proves the listed scenarios, not every possible bank/provider behavior. The deterministic offline contract and error suites remain separate required release gates.

The default per-suite request cap is 180 **HTTP attempts across all PATs**, including rejected 429 attempts. `--request-limit N` changes it explicitly. The harness retains the last working PAT by reordering only its private temporary copy, leaving the user’s saved pool untouched. Each subprocess reserves enough headroom to try each PAT once before starting; it returns actual successful-command attempt counts. Failed subprocesses conservatively consume the full reservation. This cap does not estimate other applications' traffic or bypass server quotas. Stop and wait if the pool is exhausted; no automatic waits or uncertain-write retries occur.

## Interruption and reconciliation

Run one write suite at a time, and do not run local mutations while approving CI reads. The local exclusive lock prevents concurrent runs sharing the same state directory; it cannot coordinate separate machines. CI reads need no private journal copy and make no writes.

Before the first write, the entire suite is marked active in its durable journal. Every write records its exact intent before submission and appends its response receipt afterward. Success clears the active-run marker only after readback and baseline restoration pass. Failure leaves the run latched even if the last HTTP response was successful. A network failure leaves the pending intent intact. Subsequent local runs refuse execution.

After failure:

1. Stop other runs. Inspect the private journal locally; never paste it into chat or public logs.
2. Read the actual server records using IDs, import identifiers, and memos from the journal. Establish whether the pending write occurred. Do not repeat a create blindly.
3. Remove only positively identified temporary records created by that run, restore the baseline budgeting/category note, and verify balances, split/transfer cleanup, and scheduled cleanup through reads. Reusable v1 baseline records must remain.
4. Preserve a private copy of the journal. Only after verifying reconciliation, remove its `pending` and `active_run` entries locally, preserving private file permissions. Do not delete the entire state directory as a recovery shortcut.
5. If a lock remains after a crash, verify the recorded process has stopped before removing that lock. Run `reads` to establish the baseline before starting another mutation suite.

Mutation tests remain local because GitHub-hosted ephemeral runners do not provide the durable private journal required for safe recovery. Read-only CI installs the built wheel and runs the exact same required baseline assertions; see [CI configuration](live-ci.md).

Baseline amounts use whole currency units so account and category aggregates do not depend on currency-precision rounding. Mutation tests separately verify fractional milliunit amounts through raw transaction readbacks. Account creation can add a zero Starting Balance record; assertions recognize only an exact zero, null-import, null-memo record with that payee name. Other unexpected account records still fail the fixture identity checks.
