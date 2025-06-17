# Registry Explorer Feature Gap Analysis

This document compares the capabilities of the live interface at <https://oci.dag.dev/> with Retrorecon's current `registry_explorer` module. HTML samples from the DAG.dev instance are stored under `reports/oci_html/`.

## Feature Comparison

| Feature | DAG.dev | Retrorecon | Notes |
| --- | --- | --- | --- |
| Browse registry by repo (`/?repo=`) | yes | no | Retrorecon lacks UI for listing child images under a repo. |
| Show tags and manifests for a repo | yes | partial | Retrorecon fetches manifest digest but does not render tag listing. |
| View image details (`/?image=`) | yes | basic | Retrorecon displays layer digest/size via API; no JSON/command output styling. |
| Navigate layer filesystem (`/fs/...`) | yes | no | DAG.dev lists directories and files with links. Retrorecon only shows filenames inside a `<details>` element. |
| Hex viewer for binary files | yes | no | Retrorecon cannot display hex dumps. |
| Directory listing for arbitrary path (`/layers/.../dir/`) | yes | no | Not implemented in Retrorecon. |
| Linked shell commands (crane) | yes | no | Retrorecon does not render example crane commands. |
| Table column resizing & sorting | no | yes | Retrorecon adds extra UI polish not present in DAG.dev. |

## Plan for 1:1 Parity

1. **Repo Listing Endpoints** – Implement routes `/repo` and `/image` mirroring DAG.dev semantics. Use `registry_explorer.fetch_token` and related helpers to query registry catalogs and tag lists.
2. **HTML Templates** – Create Jinja templates that mimic DAG.dev’s minimal style (monospace font, inline CSS). Render results as `<pre>` blocks with nested `<div>` elements and anchor tags linking to deeper views.
3. **Filesystem Navigation** – Add routes `/fs/<repo>@<digest>/<path>` and `/layers/<image>/<path>` that return directory listings. Use `tarfile` to stream listings and file contents similar to DAG.dev.
4. **Binary Rendering** – For non-text files support `render=hex` and `render=elf` modes by piping blob data through Python equivalents of `xxd` and `pyelftools`.
5. **Crane Command Links** – Include helpful command examples (e.g., `crane ls`, `crane export`) in the rendered HTML for parity with DAG.dev output.
6. **Routing Integration** – Expose a `/tools/registry_explorer` page that loads the new templates directly rather than the current overlay. Preserve the existing overlay for quick lookups.
7. **Testing** – Extend `tests/test_registry_explorer.py` with cases covering repo listing, tag retrieval, directory browsing and file viewing.

