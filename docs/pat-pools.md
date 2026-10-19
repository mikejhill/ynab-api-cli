# PAT pools and rate-limit rollover

Credentials live in `$XDG_CONFIG_HOME/ynab-api-cli/auth.json`, falling back to `~/.config/ynab-api-cli/auth.json`, including Windows. Configure them only in a local terminal:

```text
ynab-api-cli configure
ynab-api-cli configure --add
ynab-api-cli configure --add
ynab-api-cli doctor
```

Every configure invocation prompts for one hidden PAT. Repeat `--add` for any number of distinct PATs. Tokens never belong in arguments, chat, logs, or the repository. The protected JSON format is `access_tokens`: an ordered, nonempty array of strings. Existing `access_token` files remain supported and migrate on the next configuration change. Do not supply both fields. Duplicate and malformed tokens are rejected. Unrelated settings survive configuration changes.

`configure --replace` replaces the entire pool with the single PAT entered at its hidden prompt. To remove selected PATs while keeping others, edit the protected file locally, preserving its permissions and the array order. Never use a command that prints the file.

Only an explicit HTTP 429 advances to the next available PAT. Each request tries each configured PAT at most once. When all are exhausted, it fails without sleeping or looping. A session retains the successful PAT and skips throttled PATs until a numeric Retry-After expires; absent that header, cooldown is conservatively one hour. Cooldowns are in memory, so a new CLI process starts at the first configured PAT. The E2E harness retains the working PAT in its private temporary copy across subprocesses; it never reorders your saved pool. Its request budget counts all HTTP attempts, including 429s.

401, 403, other HTTP errors, redirects, timeouts, malformed responses, and contract failures stop immediately. They never trigger credential rollover. An uncertain write must be reconciled through reads before any retry. Only a server-declared rejection with HTTP 429 permits replay of that same write using another PAT.

`configure` validates local token syntax; it does not contact YNAB. Online `doctor` checks **every PAT individually**, including selected-plan access if configured; an invalid or throttled spare PAT therefore fails doctor. `doctor --offline` reports the pool size and validates local configuration and file protection, without claiming authentication was verified.

The selected plan remains in `config.json`. Resource commands accept explicit `--plan-id UUID` or `--plan UUID`, overriding the saved default for that request. A PAT is account-scoped; selecting a test plan does not narrow its server-side permissions.
