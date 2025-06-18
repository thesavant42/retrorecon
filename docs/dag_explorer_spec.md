# Dag Explorer Use Cases

The **Dag Explorer** overlay provides a lightweight browser for fetching image manifests and listing repository tags from any OCI registry.

## Public Non-GitHub Repositories

Dag Explorer is not limited to GitHub projects. You can inspect images from any publicly accessible registry by supplying the full reference. The following example uses the [stargz‑containers](https://github.com/containerd/stargz-snapshotter) Node image hosted on GitHub Container Registry:

```
https://oci.dag.dev/?image=ghcr.io/stargz-containers/node:13.13.0-esgz
```

Opening this link displays the image manifest and lets you browse its layers just like Docker Hub images.
