# Status State Machine

This document lists the status codes emitted by Retrorecon and their meaning.
Status events are retrieved via the `/status` API and shown in the UI.

## Codes

- `cdx_api_waiting` – waiting for a response from the Wayback CDX API.
- `cdx_api_downloading` – currently downloading CDX records.
- `cdx_api_download_complete` – finished downloading the CDX data.
- `cdx_import_complete` – all CDX records processed and inserted.

The client polls `/status` every second and displays the most recent message.
After a short delay the display resets to `idle`.
