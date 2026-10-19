# Connection setup

1. Install the CLI from a release wheel or source checkout using `uv tool install <wheel-or-project-path>`.
2. Open [YNAB Developer Settings](https://app.ynab.com/settings/developer) and generate a personal access token for your own account. [Authentication documentation](https://api.ynab.com/#personal-access-tokens).
3. In a local interactive terminal:

   ```text
   ynab-api-cli configure
   ynab-api-cli doctor
   ynab-api-cli plans get-plans
   ynab-api-cli select-plan EXPLICIT_PLAN_UUID
   ynab-api-cli doctor
   ```

Configuration uses `$XDG_CONFIG_HOME/ynab-api-cli` or `~/.config/ynab-api-cli`, including Windows. XDG_CONFIG_HOME must be absolute. `auth.json` holds `access_tokens` (or legacy `access_token`); `config.json` holds the optional `plan_id`. Existing unrelated fields are preserved.

`configure` uses hidden input and protects credentials with POSIX mode 600 or a private current-user Windows ACL. It refuses redirected input and existing credentials. `configure --replace` rotates credentials explicitly. Credentials are plaintext: use a private, local directory and exclude it from source control and shared storage.

`doctor --offline` validates files and protection only; it does not prove authentication. Online doctor reads the user and configured plan. `doctor --upstream` additionally checks the published contract.

| Failure | Action |
| --- | --- |
| Missing auth.json | Run configure locally |
| Permissions/ACL failure | Repair file protection or use configure --replace |
| HTTP 401 | Replace an invalid or revoked token |
| HTTP 403 | Check account access and token scope |
| HTTP 404 on selected plan | List plans and select the correct UUID |
| HTTP 429 | Stop requests; respect rate-limit guidance |
| Network failure during a write | Read affected records before any retry |
| Contract or model mismatch | Run compat check and review the supported version |

OAuth refresh and delegated multi-user authentication are outside this release. Each adopter configures a personal token locally.

## Multiple PATs

Run `ynab-api-cli configure --add` in a local terminal to append another hidden PAT; repeat for any number of distinct tokens. `configure --replace` replaces the entire pool with one PAT. Existing single-token auth files remain valid. New configuration stores the ordered pool under `access_tokens` in the same protected auth.json. Never supply tokens in argv, chat, or logs.

Only HTTP 429 advances to the next PAT. Every request tries each available PAT at most once. Authentication, authorization, redirects, network failures, and other errors fail immediately. Cooldowns and the successful cursor last for the process; new invocations start with the first PAT. Online doctor verifies every PAT, so a bad or throttled spare token is reported instead of hidden by another token. Offline doctor never verifies API access.

For fixture-based acceptance tests, use the installed interpreter's `python -m ynab_api_cli.e2e --help`. Explicit seed and mutation suites require --enable-writes, a disposable plan named YNAB API CLI TEST, and persistent private journal storage. Read-only acceptance fails when required seed fixtures are missing. Do not clear an interrupted write journal before reconciling actual server state. CI accepts either a single encrypted YNAB_ACCESS_TOKEN secret or a JSON-array YNAB_ACCESS_TOKENS secret, never both. Never configure remote credentials without the user's authorization.
