---
name: ynab-api-cli
description: Use the YNAB API CLI to inspect plans, accounts, categories, transactions, scheduled transactions, and other REST API resources; configure a connection or perform explicitly requested changes.
---

# YNAB API CLI

Use `ynab-api-cli`, the REST-only CLI distributed with this skill. YNAB calls budgets **plans** in the current API.

- Resolve the installed executable with `ynab-api-cli --help`. For a source checkout, use `uv run --project <project> ynab-api-cli`.
- On first use in a session, run `doctor`. If configuration is missing, read [references/setup.md](references/setup.md) and give the user the hidden local token-prompt command. Never request a token in chat.
- `discover`, `discover GROUP`, and `inspect OPERATION_ID` require no connection and make no API requests. Inspect only the operation needed; its output includes only reachable schemas.
- Use resource commands for ordinary operations or `call OPERATION_ID --request @file` for a JSON envelope containing `path`, `query`, and optional `body`.
- Prefer explicit UUIDs. A configured default plan is supplied only when plan_id is omitted. Resolve duplicate names through IDs; never infer selection from list position.
- Read [references/operations.md](references/operations.md) for milliunits, request examples, delta responses, splits, and transfers.
- Read affected records before an authorized change. Writes preview by default; review target IDs and the exact payload, then use `--execute` within the user's authorization. Existing authorization is sufficient.
- Verify submitted changes through subsequent reads. After ambiguous failures, inspect state before retrying; the CLI never retries automatically.
- `compat check` reports upstream contract drift. It does not change the installed CLI or grant permission to adopt new operations.
- Output is JSON; errors go to stderr. Report exact records and any incomplete verification.

Export this bundled skill with `ynab-api-cli skill export <new-directory>`. This skill is supplementary; the CLI works independently of Codex.
