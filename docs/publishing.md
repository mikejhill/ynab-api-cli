# Publishing ynab-api-cli

The release workflow follows VerdiClip: Conventional Commits feed release-please, a reviewed version/changelog pull request produces a tag, and the tagged revision passes validation before upload. Wheels, source archives, and the supplementary skill are checked through a clean uv tool installation. The publishing job receives immutable build artifacts and uses short-lived GitHub OIDC credentials, PyPI attestations, and build provenance. No long-lived PyPI token is required.

## Initial account setup

1. Host this project in a GitHub repository with default branch `main` and enable Actions to create pull requests. Use the repository owner and name consistently below.
2. Create the GitHub environment `pypi`. Restrict release workflows to `main`; add required reviewers if appropriate for the repository's ownership.
3. In [PyPI account publishing](https://pypi.org/manage/account/publishing/), add a pending GitHub publisher with project name `ynab-api-cli`, the repository owner/name, workflow filename `release.yml`, and environment `pypi`.
4. Optionally repeat for TestPyPI using environment `testpypi` and [TestPyPI account publishing](https://test.pypi.org/manage/account/publishing/).

A pending publisher does not reserve or create a PyPI project. The first successful upload creates it, as described in the [PyPI documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/). Account login, 2FA, and any required environment review must be completed by the appropriate account owner.

## First release or retry

Commit and push the fully validated source to `main`, create and push tag `v0.1.0` at that commit, then dispatch **Release** on `main` with `tag=v0.1.0` and `testpypi=false`. The workflow resolves the existing tag to a commit, verifies it belongs to main's history, tests that exact commit on Windows and Linux, checks its package version, builds distributions, and publishes them. A tag push alone does not publish.

Use `testpypi=true` to publish to TestPyPI instead. TestPyPI has separate accounts and trusted-publisher configuration. Production publication deliberately does not skip existing versions; investigate a partial upload rather than silently treating it as a complete release.

After publication, verify:

```text
uv tool install ynab-api-cli==0.1.0
ynab-api-cli --help
ynab-api-cli discover
ynab-api-cli skill show
```

The package should appear at [PyPI](https://pypi.org/project/ynab-api-cli/) with wheel, source archive, and publishing attestations. The GitHub release also receives the standalone release archive.

## Subsequent releases

Use Conventional Commits on main. Release-please updates `pyproject.toml`, the project's package version in `uv.lock`, and `CHANGELOG.md`. Review and merge its pull request to create the release and run the same publication gates. A manual CI dispatch validates release-please pull requests even when GitHub suppresses automatic runs for its own bot token.

`RELEASE_PLEASE_TOKEN` is optional; by default the workflow uses `GITHUB_TOKEN`. Repository settings must permit that token to create pull requests. No personal token is provisioned by this project.

## Naming and connection configuration

The package, executable, and skill are named `ynab-api-cli`; Python imports use `ynab_api_cli`. Configuration is read from `$XDG_CONFIG_HOME/ynab-api-cli/`, or `~/.config/ynab-api-cli/` when XDG_CONFIG_HOME is unset. It does not read the former generic directory. Run `ynab-api-cli configure` locally to create protected credentials at the new location; no credentials are copied automatically.
