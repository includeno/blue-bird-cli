# Changelog

## 0.3.0 — 2026-11-07

First public release of the macOS Bluebird CLI.

- Task create/read/update/delete, completion/reopening, and focus timer workflows with JSON results and read-back verification.
- Read-only Bluebird storage access, official URL creation, and a Swift Accessibility helper.
- Dynamic localization from the installed app; 26 resource locales with live coverage recorded separately.
- `bluebird start web`: loopback authorization console with separate home/list pages and creation/edit dialogs in English, Chinese, and Japanese.
- Fourteen individual CLI permissions, grouped selection, and scopes requiring all nonempty task tags to be authorized.
- Codes displayed once at creation, stored as digests, editable grants, and revocation. Owner mode uses `--full-access`.
- Boundary validation for HTTP request framing, JSON, timeouts, and authorization changes during lock waits.
- `bluebird --version` and machine-readable `capabilities.data.cli_version`.
- Complete source distributions, installation checks, three-language setup/security/compatibility guides, and release CI.

### Migration from development snapshots

Data commands require `--full-access`, `--code CODE`, or `BLUEBIRD_CODE`. The former `bluebird --full-access web` command is replaced by `bluebird start web`. Authorization failures exit with code 3. Older grants without function permissions have no delegated functions until explicitly edited.

### Known limits

Codes are cooperative CLI restrictions, not an OS sandbox. UI writes require an unlocked desktop and are not atomic. Bluebird UI/schema changes may require adapter changes. Date/recurrence editing and standalone tag management are not exposed. See the compatibility and verification documents for tested environments and language coverage.
