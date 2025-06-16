# TLS Encryption Implementation Plan

This document outlines how Retrorecon can optionally support HTTPS using a self-signed certificate. The goal is to encrypt local traffic without requiring a certificate from a trusted authority.

## Goals
- Allow running the Flask server over HTTPS for testing purposes.
- Automatically generate a development certificate if one does not exist.
- Keep the existing HTTP workflow unchanged when TLS is disabled.

## Proposed Implementation
1. **Self-signed certificate generation**
   - Add `scripts/generate_selfsigned.py` which creates `cert.pem` and `key.pem` under a new `certs/` directory using Python's `ssl` and `cryptography` modules.
   - The script runs automatically from `launch_app.bat` and the Dockerfile if the cert files are missing.
2. **Application startup flag**
   - Update `app.py` to read an environment variable `RETRORECON_USE_HTTPS` (default `0`).
   - When set to `1`, call `app.run(ssl_context=("certs/cert.pem", "certs/key.pem"))`.
3. **Configuration updates**
   - When HTTPS is enabled, set `SESSION_COOKIE_SECURE` in `Config` to ensure cookies are marked secure.
   - Document that the app should be opened via `https://127.0.0.1:5000` and that browsers will warn about the untrusted certificate.
4. **Documentation**
   - Provide instructions in `README.md` on how to trust the certificate or disable warnings.
   - Update `docs/api_routes.md` examples to reference `https://localhost:5000` when TLS is active.

## Security Considerations
- A self-signed certificate encrypts the connection but does not provide authenticity. Users must manually trust it.
- For remote or multi-user deployments a valid certificate from a CA should replace the self-signed files.
- Enabling TLS allows use of secure cookies and better parity with production-like setups.

## Migration and Compatibility
- HTTPS remains optional; without `RETRORECON_USE_HTTPS`, the server behaves exactly as before.
- Existing scripts and unit tests using `http://` continue to work because the default scheme does not change.
- Tools that explicitly fetch `http://localhost` may require `https://` when TLS is enabled, but no fundamental breakage is expected.

## Will this break anything?
Running Flask with `ssl_context` does not alter route logic. The primary change is that browsers will show a warning for the self-signed certificate. As long as relative URLs are used in templates, the application should function over either scheme. Therefore no major breaking changes are anticipated.

## Task Checklist for Codex
- [ ] Create `scripts/generate_selfsigned.py` and ensure it writes `certs/cert.pem` and `certs/key.pem`.
- [ ] Add `RETRORECON_USE_HTTPS` handling in `app.py` to start with `ssl_context` when enabled.
- [ ] Update `launch_app.bat` and the Dockerfile to call the certificate generator if needed.
- [ ] Document HTTPS usage in `README.md` and adjust examples in `docs/api_routes.md`.
- [ ] Add unit tests verifying the server starts with SSL when the environment variable is set.
- [ ] Extend `docs/test_plan.md` with corresponding tests.
