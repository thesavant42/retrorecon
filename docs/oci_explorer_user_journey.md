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

5. **Fetch a specific file**
   - Click a layer link and then a file path to view or download the file.
   - You can also request a file directly via `GET /dag/fs/<digest>/path?image=<ref>`

6. **Switch contexts**
   - Use the repository breadcrumb to jump back to `/repo/<repo>` and browse other tags.
   - The tool keeps the last image reference in the input for convenience.

This flow lets users peek inside any public or private registry that the server can reach, similar to the hosted service at https://oci.dag.dev.


## Example: Ubuntu root password file
1. Open OCI Explorer and enter `library/ubuntu:latest`.
2. Click the first layer digest link.
3. Navigate to `/etc`.
4. Select `passwd` (or `shadow`) to preview or download.

```mermaid
flowchart LR
    A(Open Retrorecon) --> B(Select OCI Explorer)
    B --> C(Input "ubuntu:latest" and Fetch)
    C --> D(View manifest)
    D --> E(Open first layer)
    E --> F(Navigate to /etc)
    F --> G{passwd or shadow}
    G --> H(View file)
```

