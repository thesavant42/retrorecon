# Status State Machine

This document lists the status codes emitted by Retrorecon and their meaning.
Status events are retrieved via the `/status` API and shown in the UI.

## Codes

- `cdx_api_waiting` – waiting for a response from the Wayback CDX API.
- `cdx_api_downloading` – currently downloading CDX records.
- `cdx_api_download_complete` – finished downloading the CDX data.
- `cdx_page_processed` – one page of CDX results has been inserted.
- `cdx_resume_key` – emitted when a resume key is available for the next page.
- `cdx_import_complete` – all CDX records processed and inserted.
- `layerpeek_start` – layerpeek fetch initiated.
- `layerpeek_fetch_manifest` – retrieving image manifest information.
- `layerpeek_fetch_layers` – downloading layer details.
- `layerpeek_done` – layerpeek inspection complete.
- `screenshot_start` – screenshot capture initiated.
- `screenshot_done` – screenshot capture finished.
- `screenshot_error` – screenshot capture failed.

The client polls `/status` frequently when new messages are being emitted and
gradually backs off to a slower pace when idle, up to 30 seconds between
requests. After a short delay the display resets to `idle`.
