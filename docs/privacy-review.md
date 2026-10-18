# Initial publication privacy review

Reviewed on 2026-10-18 before uploading source to the public repository.

- Git contained zero commits, no refs, and no reflog entries. There was no earlier commit history to sanitize. The initial commit uses a GitHub noreply address.
- Reviewed authored source, generated source, templates, tests, fixtures, contract resources, skill resources, documentation, package metadata, and workflow configuration.
- Removed an author email from package metadata and a machine-specific checkout path from documentation.
- A detect-secrets 1.5.0 scan found only published contract SHA-256 fingerprints and ignored cache identifiers. Those were inspected as false positives. Additional credential-pattern, local-path, email, and credential-file searches found no sensitive publishable content.
- Test tokens and records are synthetic. The specification and its examples come from the published YNAB contract. No personal YNAB records or credentials were used for tests or included in the source.
- Credentials, environment files, caches, virtual environments, and build artifacts are excluded from Git. Old build artifacts were moved outside the repository before rebuilding under the new package name.
- Extracted the rebuilt wheel, source distribution, and release archive. Credential-file and local-path searches found no sensitive content; secret detection on extracted source and wheel files found only the same reviewed contract hashes.
- No credentials are copied from the former configuration directory. Connection setup remains a hidden local prompt.

Secret scanners cannot prove the absence of every possible sensitive value. This review combines automated detection, inspection of scanner findings, and source/history checks; future contributions and releases require their own review.
