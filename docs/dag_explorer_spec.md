# Dag Explorer Use Cases

The **Dag Explorer** overlay provides a lightweight browser for fetching image manifests and listing repository tags from any OCI registry.

## Public Non-GitHub Repositories

Dag Explorer is not limited to GitHub projects. You can inspect images from any publicly accessible registry by supplying the full reference. The following example uses the [stargz‑containers](https://github.com/containerd/stargz-snapshotter) Node image hosted on GitHub Container Registry:

```
https://oci.dag.dev/?image=ghcr.io/stargz-containers/node:13.13.0-esgz
```

Opening this link displays the image manifest and lets you browse its layers just like Docker Hub images.

## Local vs Hosted Links

You can explore the same image using the local Dag Explorer or the hosted version on oci.dag.dev.

Local server example:

```
http://127.0.0.1:5000/image/ubuntu/dev:TAE-254
```

This page links each layer to:

```
http://127.0.0.1:5000/layers/ubuntu/dev:TAE-254@sha256:2eb5ae5626329845e85d70a53694a99165471ae7970435ed4d4bad24933d963c/
```

Hosted equivalent:

```
https://oci.dag.dev/?image=ubuntu/dev:TAE-254
```

Layers open to:

```
https://oci.dag.dev/layers/ubuntu/dev:TAE-254@sha256:2eb5ae5626329845e85d70a53694a99165471ae7970435ed4d4bad24933d963c/
```

## Partial Tar Ranges

Dag Explorer intentionally issues HTTP range requests to peek inside layer blobs. When about 32 KiB of uncompressed data before a target offset is available, the gzip stream can be repositioned to read arbitrary sections. Storing only ~1% of a layer allows directory listings without downloading the entire archive. As a result the data may appear as an "invalid tar" when viewed in full, but this is expected behavior.
