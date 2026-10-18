# Contract maintenance

The upstream contract is https://api.ynab.com/papi/open_api_spec.yaml. Runtime uses the bundled reviewed snapshot rather than silently adopting remote changes.

1. Run `ynab-api-cli compat check` or `uv run poe compat-check`. Structural additions, removals, changed parameters, schemas, and server declarations fail compatibility. Documentation-only changes are reported separately.
2. Inspect the candidate report, generated code, and typing results. Additions need reviewed catalog entries and independent wire fixtures; optional fields also require feature-matrix updates.
3. Update the bundled specification and provenance deliberately. Regenerate through `uv run poe generate`; fix templates or documented transforms rather than generated output.
4. Review the static operation catalog, schema-feature manifest, and independent fixtures. Never regenerate acceptance manifests automatically during CI.
5. Run every quality gate, build distributions, and smoke-test a clean installation before releasing.

The pinned openapi-python-client generator supplies parsed schema and endpoint structure. Custom templates emit Pydantic models and class-based typed methods. Deterministic transforms change relative imports to absolute imports, use StrEnum, resolve forward references, and create static endpoint dispatch. Naming overrides shorten duplicate nullable enum classes without changing wire values.

Tests combine independently authored request expectations for every endpoint, runtime JSON Schema probes, a reviewed feature manifest, generated-model round trips, deliberate static typing failures, property tests, and failure-path tests. Synthetic schema responses supplement the independent wire fixtures; they are not evidence of live API behavior.

The daily GitHub Actions workflow checks the public contract without account credentials. It becomes active only when this project is hosted in GitHub. Scheduled checks detect drift but never adopt it or run live writes.

Semantic overlay: transaction creation must specify exactly one transaction representation, as documented in the createTransaction operation description. Milliunits, transfer linkage, split restrictions, import matching, and delta deletion semantics remain explicitly tested examples and documented API behavior; tests do not invent stricter server rules absent from the contract.

The published OpenAPI 3.1 document retains legacy `nullable: true` annotations. Runtime validation maps them to explicit JSON Schema null branches, matching the generator's interpretation; the original snapshot stays unchanged. Nullable witnesses and typed additional-property models are tested.
