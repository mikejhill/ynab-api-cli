# YNAB API CLI

Complete, synchronous REST CLI for the reviewed YNAB API contract. The official SDK is not a dependency. Generated, strictly typed endpoint classes and models are included for Python callers.

## Install and connect

```text
uv tool install ynab-api-cli
ynab-api-cli configure
ynab-api-cli doctor
ynab-api-cli plans get-plans
ynab-api-cli select-plan PLAN_UUID
ynab-api-cli doctor
```

Generate your personal token in [YNAB Developer Settings](https://app.ynab.com/settings/developer), then enter it through the hidden terminal prompt. Do not put it in command arguments. Configuration is stored under `$XDG_CONFIG_HOME/ynab-api-cli`, falling back to `~/.config/ynab-api-cli` on all platforms. Credentials are plaintext and protected with private POSIX permissions or a current-user Windows ACL.

```text
ynab-api-cli discover
ynab-api-cli discover transactions
ynab-api-cli inspect createTransaction
ynab-api-cli transactions get-transactions --since-date 2026-01-01
ynab-api-cli call getTransactions --request @request.json
```

Uniform requests use `{"path":{},"query":{},"body":{}}`; omit body for operations without one. `--request -` and `--body -` read stdin. Endpoint flags use kebab-case names. Boolean flags take `true` or `false`.

Writes preview by default. Add `--execute` only for an intended mutation and verify its result through reads. Requests use TLS, a 30-second timeout, and no automatic retries or redirects. An uncertain write must be reconciled before retrying. Amounts are integer milliunits, and explicit null differs from omission.

`--metadata` adds status, selected headers, and contract version. Exit codes: 0 success, 1 configuration/API/compatibility failure, 2 usage error, and 130 interruption. `doctor --offline` does not validate API access. `configure --replace` explicitly rotates credentials while preserving unrelated fields.

## Typed Python interface

```python
from ynab_api_cli.generated.api.transactions.get_transactions import Endpoint
from ynab_api_cli.transport import Connection, Transport

# Load protected credentials through ConfigStore in real applications.
response = Endpoint.execute(transport=Transport(Connection(token)), plan_id=plan_id)
raw_json = response.raw
typed_result = response.parsed
```

Typed endpoint execution directly submits mutations; preview guards belong to the CLI. The transport independently validates requests and responses against the bundled contract. Raw JSON remains available alongside typed parsing.

## Development and maintenance

```text
uv sync --locked
uv run poe fix
uv run poe check
uv run poe codegen-check
uv run poe contract-check
uv run poe compat-check
uv build
```

The contract snapshot, reviewed operation catalog, and provenance are packaged resources. Generator configuration lives in pyproject.toml; templates and deterministic transforms produce all generated code. Do not edit generated files manually.

See [maintenance](docs/maintenance.md) for reviewed upgrades, test coverage, and CI. See [live testing](docs/live-testing.md) before enabling writes against a dedicated test plan.

See [secure live CI](docs/live-ci.md) for the separate, manually approved read-only workflow. Ordinary CI requires no YNAB credentials. No local token is uploaded automatically.

## Supplementary Codex skill

```text
ynab-api-cli skill show
ynab-api-cli skill export /path/to/codex/skills/ynab-api-cli
```

Export refuses an existing destination. The canonical skill is in skills/ynab-api-cli and is also included as installed package data. The CLI works independently of Codex.

For a source checkout, install with `uv tool install .` or run commands with `uv run ynab-api-cli`.

## Releases

The publishing pipeline follows VerdiClip's release-please and PyPI trusted-publishing pattern. See [publishing](docs/publishing.md) for the initial project setup, release process, and TestPyPI option.
