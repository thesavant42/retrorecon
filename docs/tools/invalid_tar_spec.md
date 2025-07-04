# Invalid Tar Error History

This document records occurrences of the "Invalid Tar" bug across Retrorecon and how each was resolved.

## Bug History

| Date | Commit | Issue | Fix |
|------|-------|-------|-----|
|2025-06-18|93c7603|Unhandled `tarfile.TarError` when parsing layer blobs|Added try/except in `dag.py` and `oci.py` returning HTTP 415 with an error page|
|2025-06-18|870aa71|Lack of diagnostics around tar failures|Logged warnings like `invalid tar for <repo>@<digest>` and updated tests|
|2025-06-18|0ace021|Regression where layer view still crashed on bad tars|Merged fix ensuring warnings were logged and responses used 415|
|2025-06-18|8462a7c|Incorrect layers link used manifest digest leading to wrong blob|Adjusted filters and overlay view to compute correct digest|
|2025-06-18|24d3669|Manifest view built layers link with wrong digest|Fixed filter so link includes manifest digest; added tests|
|2025-06-18|6ee4afe|Registry overlay links pointed at stale digests|Updated JavaScript and tests to avoid invalid tar downloads|
|2025-06-20|19370d4|Layers route for digest images generated wrong repo path|Parsed image reference properly before calling `fs_view`|
|2025-06-20|4bcce22|`/image` page size links triggered invalid tar via `/size`|Stopped linking size column and warned on unsupported media|

## Specification

All OCI routes must gracefully handle invalid or truncated tar archives. When a `tarfile.TarError` is raised while inspecting a layer:

- Respond with HTTP 415 and render `oci_error.html` with message `"invalid tar"`.
- Log a warning `"invalid tar for <repo>@<digest>"` (or `"invalid tar blob for <image> at <digest>"` for Dag Explorer).

The Dag Explorer `/dag/fs` endpoint should return JSON `{ "error": "invalid_blob" }` in this case.

## Test Cases

1. Requesting `/fs/<repo>@<digest>/<path>` with an invalid blob returns status 415 and logs the warning.
2. Requesting `/size/<repo>@<digest>` with an invalid blob returns status 415 and logs the warning.
3. Requesting `/dag/fs/<digest>/<file>` with an invalid blob returns JSON error and logs `invalid tar blob`.

These tests live in `tests/test_oci_routes.py` and `tests/test_dag_explorer.py`.
