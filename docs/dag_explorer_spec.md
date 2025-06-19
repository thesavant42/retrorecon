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
http://127.0.0.1:5000/image/migueldisney/dev:TAE-254
```

This page links each layer to:

```
http://127.0.0.1:5000/layers/migueldisney/dev:TAE-254@sha256:2eb5ae5626329845e85d70a53694a99165471ae7970435ed4d4bad24933d963c/
```

Hosted equivalent:

```
https://oci.dag.dev/?image=migueldisney/dev:TAE-254
```

Layers open to:

```
https://oci.dag.dev/layers/migueldisney/dev:TAE-254@sha256:2eb5ae5626329845e85d70a53694a99165471ae7970435ed4d4bad24933d963c/
```

## Partial Tar Ranges

Dag Explorer intentionally issues HTTP range requests to peek inside layer blobs. When about 32 KiB of uncompressed data before a target offset is available, the gzip stream can be repositioned to read arbitrary sections. Storing only ~1% of a layer allows directory listings without downloading the entire archive. As a result the data may appear as an "invalid tar" when viewed in full, but this is expected behavior.

## Sample Registry HTML

A full crawl of the Kubernetes registry on [oci.dag.dev](https://oci.dag.dev/) is available in `docs/html-container-reg-k8s.txt`. These pages show the minimal markup returned by the Go version of Dag Explorer. Retrorecon uses nearly identical HTML, but links differ slightly: the hosted service relies on query parameters like `/?repo=<name>` and `/?image=<ref>` whereas Retrorecon exposes path-based routes such as `/repo/<name>` and `/image/<ref>`. The captured HTML can be used as a reference when updating the templates or comparing behaviors.

