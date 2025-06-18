# PRD: Porting `dagdotdev` Functionality to Python

This document outlines requirements for extending Retrorecon with all features from [`dagdotdev`](https://github.com/jonjohnsonjr/dagdotdev). The goal is route and feature parity so the Python version can fully replace the Go implementation.

## 1. Overview

Retrorecon currently exposes a simplified set of endpoints for exploring OCI images. `dagdotdev` provides a faster and more comprehensive interface. Porting its routes and behaviors to Python will bring Retrorecon up to feature parity and improve performance.

## 2. Existing Route Comparison

The table below lists routes implemented in `dagdotdev` and whether an equivalent exists in Retrorecon today.

| Route pattern (dagdotdev) | Exists in Retrorecon? |
|---------------------------|-----------------------|
| `/` with query params like `image`, `repo`, `blob`, `history`, `referrers` | **No** |
| `/fs/<digest>/<path>` | **No** (`retrorecon` uses `/dag/fs/<digest>/<path>` with an `image` query) |
| `/size/<digest>` | **No** |
| `/sizes/<image>` | **No** |
| `/http/<path>` | **No** |
| `/https/<path>` | **No** |
| `/layers/<digest>` | **No** |
| `/cache/<digest>` | **No** |
| `/blob/<digest>` | **No** |
| `/oauth` | **No** |
| `/zurl/<digest>` | **No** |
| *(Retrorecon only)* `/dag_explorer`, `/tools/dag_explorer`, `/dag/repo/<repo>`, `/dag/image/<image>`, `/dag/fs/<digest>/<path>`, `/dag/layer/<digest>` | Not present in `dagdotdev` |

All `dagdotdev` routes are currently missing from Retrorecon, which implements only a minimal explorer.

## 3. Porting `dagdotdev` to Python: Route and Functionality Mapping

The following sections summarize key features and recommended Python implementations derived from the original Go server.

### Essential Features

- **Purpose:** Web server for exploring OCI registry contents.
- **Key Features:**
  - Browse OCI images and layers.
  - Explore APK packages.
  - Support local and Cloud Run deployment.
  - Caching via local directories or GCS buckets.
  - OAuth for private GCP images.
  - Minimal/no JavaScript frontend.
  - Performance-focused with forked dependencies.

### Core Routes and Their Functions

| Route Pattern | Purpose/Functionality |
| --- | --- |
| `/` | Home page, search box or welcome message |
| `/r/<registry>/<repo>` | View repository details, list tags/images |
| `/r/<registry>/<repo>:<tag>` | View specific image/tag details, including layers |
| `/r/<registry>/<repo>@<digest>` | View image by digest (immutable reference) |
| `/layer/<digest>` | Explore details of a specific layer |
| `/apk/<package>` | (Optional) Explore APK package details |
| `/search` | Search for repositories, tags, or layers |
| `/static/*` | Serve static assets (CSS, logo, etc.) |
| `/auth/callback` | OAuth callback endpoint for GCP image access |

### Python Implementation Recommendations

- **Framework:** Flask or FastAPI for route definitions.
- **OCI Registry Interaction:** Use `oras`, `docker-py`, or `oci-distribution`.
- **Caching:** Local filesystem or GCS buckets configured via environment variables.
- **Authentication:** OAuth2 and keychain-based auth for private registries.
- **Frontend:** Minimal server-rendered HTML/CSS.
- **Deployment:** Support local and Cloud Run deployment.

### Example Route Mapping

| Go Route Example | Python Equivalent | Description |
| --- | --- | --- |
| `/` | `@app.route("/")` | Home page |
| `/r/<registry>/<repo>` | `@app.route("/r/<registry>/<repo>")` | Repo details |
| `/r/<registry>/<repo>:<tag>` | `@app.route("/r/<registry>/<repo>:<tag>")` | Image/tag details |
| `/r/<registry>/<repo>@<digest>` | `@app.route("/r/<registry>/<repo>@<digest>")` | Image by digest |
| `/layer/<digest>` | `@app.route("/layer/<digest>")` | Layer details |
| `/apk/<package>` | `@app.route("/apk/<package>")` | APK package details |
| `/search` | `@app.route("/search")` | Search endpoint |
| `/auth/callback` | `@app.route("/auth/callback")` | OAuth callback |

### Additional Considerations

- **Environment Variables:** `CACHE_DIR`, `CACHE_BUCKET`, `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URL`, `AUTH`.
- **Performance:** Consider async handlers for network-bound operations.
- **Testing:** Write integration tests to ensure route parity and feature completeness.

### Why Is Retrorecon Slower?

- `dagdotdev` is written in Go with aggressive caching and optimized registry access, resulting in load times around 10 ms.
- Retrorecon, written in Python, takes ~30 seconds due to less aggressive caching and slower I/O.
- Go's concurrency model and forked dependencies provide major performance benefits.
- Retrorecon can improve by profiling, implementing more caching, using async I/O, and optimizing registry libraries.

## 4. Next Steps

1. Clone the `dagdotdev` repository and review all HTTP handler definitions.
2. Implement Python route handlers matching each Go route.
3. Add caching logic and OAuth flows based on environment variables.
4. Profile Retrorecon to close the performance gap with `dagdotdev`.
5. Write integration tests for every route to ensure feature parity.

