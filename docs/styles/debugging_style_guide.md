# Debugging Style Guide

This document describes how Retrorecon handles logging and debugging and lists best practices for contributors.

## Current Debugging Strategy

- **Logging library**: The application uses Python's built‑in `logging` module. The root `app.py` configures global logging via `logging.basicConfig` using the `LOG_LEVEL` value from `config.py`.
- **Environment variable**: Set `RETRORECON_LOG_LEVEL` before running the app to control verbosity. Example from the README:
  ```bash
  # Enable verbose logging
  RETRORECON_LOG_LEVEL=DEBUG python app.py
  ```
- **Module loggers**: Modules create a logger with `logging.getLogger(__name__)` (e.g. in `retrorecon/subdomain_utils.py` and `retrorecon/status.py`). They emit `debug` and `info` messages as appropriate.
- **Flask routes**: Route files typically use `current_app.logger` for warnings or debug output.
- **Command line tools**: Scripts such as `tools/layer_slayer.py` set up their own logger and optionally write to a file when passed `--log-file`.

## Debugging Practices

To improve consistency and diagnostic value, follow these guidelines:

1. **Always use `logging`** – avoid `print()` statements. Create a logger per module via `logging.getLogger(__name__)`.
2. **Granular levels** – prefer `logger.debug()` for step‑by‑step traces and `logger.info()` for high‑level events. Use `logger.warning()` or `logger.error()` for problems.
3. **Structured messages** – include key variables in log messages, e.g. `logger.debug("import file=%s count=%d", path, n)`. This aids troubleshooting without enabling debugging.
4. **Centralize configuration** – rely on the global `RETRORECON_LOG_LEVEL` setting. If a CLI tool needs separate verbosity, expose `--log-level` and funnel it through `logging.basicConfig`.
5. **Exception context** – log exceptions with `logger.exception()` inside `except` blocks to capture stack traces.
6. **Testing hooks** – unit tests may raise log level using `caplog.set_level(logging.DEBUG)` to assert specific messages.
7. **Noisy operations** – for loops that process many items, emit a start/end log and use `logger.debug()` inside the loop only when necessary.
8. **Documentation** – mention noteworthy logs in docstrings or README sections so that engineers know how to enable them.

Adhering to these practices will keep output predictable, make debugging easier and provide enough information to diagnose issues at scale.
