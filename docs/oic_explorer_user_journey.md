# OCI Explorer User Journey

This document walks through a typical workflow using the Dag/OCI Explorer in Retrorecon.

1. **Open the tool**
   - From the Retrorecon interface choose **Tools → OCI Explorer**. This opens the overlay at `/dag_explorer`.

2. **Enter an image reference**
   - In the text field, provide a full image reference such as `ghcr.io/stargz-containers/node:13.13.0-esgz`.
   - Press **Fetch**. Retrorecon sends `GET /registry_explorer?image=<ref>` to retrieve the manifest.

3. **View manifest and layers**
   - The manifest details are displayed including media type, config and layer digests.
   - Each layer link navigates to `/dag/layer/<ref>@<digest>` showing the file list.

4. **Inspect layer contents**
   - Selecting a file path requests a small range of bytes so the archive need not be fully downloaded.
   - The browser view renders directories and allows quick exploration of the layer tarball.

5. **Switch contexts**
   - Use the repository breadcrumb to jump back to `/repo/<repo>` and browse other tags.
   - The tool keeps the last image reference in the input for convenience.

This flow lets users peek inside any public or private registry that the server can reach, similar to the hosted service at `https://oci.dag.dev`.
