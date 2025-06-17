# Porting `dagdotdev` to Python

This document explores the feasibility of porting the Golang project [`dagdotdev`](https://github.com/jonjohnsonjr/dagdotdev) to a Python based module for Retrorecon. The goal is to reuse the registry browsing and layer inspection capabilities within Retrorecon's existing Flask architecture.

## Overview of `dagdotdev`

`dagdotdev` is a web server that lets users interactively explore an OCI registry. Key points from the project's README:

- The server is written in Go and is intended for quick exploration. It is "not production quality"【F:dagdotdev-main/README.md†L3-L7】.
- It is typically built with [`ko`](https://github.com/ko-build/ko) and deployed on Cloud Run【F:dagdotdev-main/README.md†L11-L33】.
- Many dependencies are forked for performance reasons【F:dagdotdev-main/README.md†L39-L47】.

Within `internal/explore`, the author describes several performance techniques:

- Browser caching through strong `Cache-Control` headers so the client can avoid repeated requests【F:dagdotdev-main/internal/explore/README.md†L5-L9】.
- A ping cache and registry cookie to avoid repeated authentication preambles, reducing per-request latency by ~200ms【F:dagdotdev-main/internal/explore/README.md†L10-L63】.
- Seeking into large gzipped layers using SOCI-style indices for random access without decompressing the entire blob【F:dagdotdev-main/internal/explore/README.md†L80-L130】.
- Support for Range requests with redirect caching to minimize roundtrips when fetching layer content【F:dagdotdev-main/internal/explore/README.md†L132-L151】.

### High Level Functionality

The server exposes handlers that:

1. List repositories and tags.
2. Display manifest contents and render JSON with links.
3. Browse an image layer as a virtual file system, streaming specific files via Range requests.
4. Handle OAuth authentication for private images.

These handlers rely heavily on [`go-containerregistry`](https://github.com/google/go-containerregistry) and custom caching logic found in the `internal/explore` package.

## Porting Considerations

### Feature Parity

To match the Go implementation, a Python port should provide:

- Basic registry browsing (list repos, list tags, fetch manifests).
- Layer filesystem exploration with minimal data transfer.
- Optional OAuth login for private registries.
- Caching of registry pings, tokens and layer descriptors to speed up repeated requests.
- SOCI-style gzip indexing to allow random access reads.

### Candidate Libraries

Python has several relevant libraries:

- [`oras-py`](https://github.com/oras-project/oras-py) or [`oras` CLI](https://oras.land/) for registry interactions.
- [`docker` Python SDK](https://docker-py.readthedocs.io/en/stable/) for common registry APIs.
- [`google-auth`](https://google-auth.readthedocs.io/en/latest/) for OAuth flows.
- [`aiohttp`](https://docs.aiohttp.org/) or `requests` for HTTP.
- For gzip range seeks, we could adapt [`soci-snapshotter`](https://github.com/awslabs/soci-snapshotter) ideas or port the `zran` logic to Python (e.g. using `gzip` + custom index).

### Architectural Integration

Retrorecon already provides a Flask application with a database and tagging UI. The registry explorer could be integrated as a blueprint:

```
retrorecon/
├── retrorecon/  # existing modules
├── registry_explorer/  # new package
│   ├── __init__.py  # Flask blueprint
│   ├── client.py    # registry API wrappers
│   ├── soci.py      # gzip index / range helpers
│   └── templates/
│       └── explorer.html
```

1. **Client Wrapper** – Provide a small abstraction layer that wraps registry operations. Initially it can shell out to the `oras` CLI for simplicity and gradually move to a pure Python implementation.
2. **Caching Layer** – Store ping responses, OAuth tokens and manifest descriptors in Redis or an in-memory dictionary similar to the Go cache. Tokens could also be persisted in cookies like the original implementation.
3. **Layer FS** – Implement a `tarfile`-based file system that can read from Range requests. A background task would generate a SOCI-style index upon first fetch, storing checkpoints (compressed offset, uncompressed offset, dictionary) in a small sidecar file.
4. **Flask Blueprint** – Expose routes `/repo/<name>`, `/image/<ref>` and `/fs/<digest>/...` that mirror the Go server's behaviour. Jinja templates can render JSON with hyperlinks similar to the `render.go` output.
5. **OAuth** – Integrate `google-auth` or provider-specific flows. Reuse Retrorecon's session management to store credentials.

### Feasibility & Effort

- **Registry API** – Python libraries exist but may not match `go-containerregistry` feature parity. Some performance or compatibility issues may arise. Initial version can rely on command-line tools like `oras` to reduce complexity.
- **Random Access Gzip** – Python's built-in `gzip` module lacks native support for the SOCI approach. We would need to port the indexing logic or call out to existing Go code via a small command-line helper. This is the most complex part of the port.
- **Performance** – The Go server benefits from concurrency and efficient I/O. Python's async features (e.g. `aiohttp`) can mitigate overhead, but the port may not match Go's speed without careful optimization.
- **Maintenance** – Keeping parity with upstream `dagdotdev` may require periodic syncing of features. The port could focus on a subset of capabilities (public repositories, read-only browsing) to reduce scope.

Overall, porting is feasible but non-trivial. A staged approach is recommended:

1. **Phase 1 – Basic Browser**
   - Use `oras` or the Docker SDK to list repos/tags and fetch manifests.
   - Implement Flask templates that mimic `dagdotdev`'s landing page.
   - No layer browsing yet.
2. **Phase 2 – Layer Access**
   - Add SOCI-inspired indexing for gzipped layers.
   - Stream file content via Range requests.
   - Introduce caching (ping, token, redirect) to improve latency.
3. **Phase 3 – OAuth & Advanced Features**
   - Integrate OAuth login.
   - Support additional media types (e.g. cosign signatures).
   - Polish UI and error handling.

## Conclusion

`dagdotdev` offers powerful container registry exploration features implemented in Go. Porting it to Python for Retrorecon would enable a unified toolchain but requires substantial work, particularly around gzip range access and efficient caching. Focusing on a minimal feature set first—then iterating—will make the port manageable while preserving the unique capabilities that distinguish `dagdotdev`.
