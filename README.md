# Bluebird CLI for macOS

English | [简体中文](README.zh-CN.md) | [日本語ドキュメント](docs/ja/README.md)

[Compatibility](docs/en/compatibility.md) · [Release installation](docs/en/release.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md)

Control the installed **Bluebird focus app** from a terminal, Codex, or another agent. Task CRUD, completion, focus sessions, and JSON output. Python standard library plus a small Swift Accessibility helper; no third-party runtime dependencies.

This is an unofficial project. Bluebird is installed separately. Its translations and application binaries are not redistributed.

## Install

Start with the [step-by-step system setup guide](docs/en/setup.md) for dependencies, permission setup, agent sandbox checks, and troubleshooting.

Targets macOS 15+, Bluebird 3.14.1, Python 3.9+, and Xcode Command Line Tools (`swiftc`). From this checkout:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
bluebird --full-access setup
bluebird --full-access open
bluebird --full-access doctor
```

For development, use `./bluebird` without installing. `setup` builds the native helper in `~/Library/Caches/bluebird-cli/bluebird-ax`. Re-run it after upgrading the CLI; the transport checks the helper's source digest.

Enable the terminal or agent host in **System Settings → Privacy & Security → Accessibility**. macOS may attribute permission to the launching application, not the helper. If requested, also authorize the helper path returned by `setup`. Agent sandbox permissions are separate. Check `doctor`'s `data.ready`, not just its exit code.

`BLUEBIRD_CLI_HOME` overrides the cache directory. All processes controlling the same app should share this directory: its process lock serializes mutations across installations.

## Access modes and local console

Version 0.3 requires an explicit access mode for data commands. Use `--full-access` for owner operations, or give an agent a code with selected CLI functions and at least one tag:

```sh
bluebird start web
# Open the private URL printed by the server, configure functions/tags, and save the generated code.
export BLUEBIRD_CODE='bb_REPLACE_WITH_YOUR_CODE'
bluebird auth-status
bluebird list
```

The local console supports English, Chinese, and Japanese; creation, permission editing, and revocation; individual function checkboxes, group selection, select-all, and clear. Query, task CRUD/completion, and timer operations are separately granted. A task must have at least one tag and all of its tags must be authorized. All 14 functions selected still means scoped access, not administration. The code works with the console stopped. See [authorization and permissions](docs/en/authorization.md) for the full workflow and storage details.

Codes enforce cooperative CLI scope; an agent with unrestricted shell access under the same user can still run full-access or read app data directly. The owner examples below intentionally use full access.

## Tasks and focus

```sh
bluebird --full-access add 'Write proposal' --notes 'Draft outline' --duration 25 --priority high --tags 'Work'
bluebird --full-access list --status all --search proposal
bluebird --full-access get ID
bluebird --full-access update ID --title 'Review proposal' --notes 'Include budget' --duration 30 --priority medium --tags 'Work'
bluebird --full-access update ID --notes '' --duration 0 --priority none --tags ''
bluebird --full-access timer start --task ID --duration 25
bluebird --full-access timer status
bluebird --full-access timer finish
bluebird --full-access logs --task ID
bluebird --full-access timer reset
bluebird --full-access complete ID
bluebird --full-access reopen ID
bluebird --full-access delete ID --dry-run
bluebird --full-access delete ID --yes
```

Use the ID returned by `add` or `list`, preserving it as a **string**. `list` defaults to active tasks; statuses are `active`, `completed`, `deleted`, and `all`. Updates change only supplied fields. Task tags can be selected, removed, or created. Deletion uses the app's soft-delete behavior. Each task or timer mutation is verified by reading local state.

`timer start --duration` accepts multiples of 5 from 5 to 600 minutes, subject to the app's actual slider range. An unreachable duration fails before starting. Omit it to use the task's selected app duration, which may be count-up mode. Task estimates accept arbitrary positive whole minutes.

`finish` saves elapsed progress according to Bluebird's rounding rules. **`stop` discards progress.** `reset` exits a finished/break session; an active session must first be finished or stopped. Status distinguishes `idle`, `focusing`, `finished`, `break`, and `break_finished`. Existing focus/break sessions are never replaced by `start`.

`open` opens Bluebird; `focus` only opens its timer screen. Their `dispatched` result means the OS accepted the request, not that a timer started.

## Languages

```sh
bluebird locales
bluebird --full-access doctor
bluebird --full-access --locale ja update ID --notes '確認済み'
```

The adapter loads semantic resource keys from the installed app. Bluebird 3.14.1 ships **26 locales**, including regional variants. It prefers stable Accessibility identifiers, then localized role-qualified labels. Unicode normalization handles composed text, bidirectional display marks, and punctuation without modifying stored task text.

The default `--locale auto` detects the visible UI language. An explicit locale disambiguates variants; it does not change the app's language. Missing evidence, mismatches, and ambiguous targets fail before the relevant action. English development strings cover the app's sparse base English resource table.

Resource/selector tests cover all 26 installed localizations. This is separate from live UI certification; see [verification](docs/en/verification.md) for the tested app version and language coverage.

## Agents

Business commands emit one JSON object on stdout:

```json
{"ok":true,"data":{"id":"7705161843629854611","title":"Write proposal"}}
```

Failures return `{"ok":false,"error":{"code":"…","message":"…"}}`. Exit codes: `0` success, `1` execution/permission/verification failure, `2` invalid arguments, `3` CLI authorization denied. `--help` is text. Inspect `data.ready` after `doctor`.

Use argument arrays rather than interpolating task text into shell commands. Mutations support `--dry-run`; deletion requires an exact ID and `--yes`. `UNVERIFIED` means the action may have happened: read state before retrying, particularly creation.

- `bluebird capabilities`: commands, fields, output contract, limitations.
- `bluebird --full-access ui`: current Accessibility snapshot and detected locale; may contain private task text.
- [Agent workflow and Python example](docs/en/agent-workflow.md).
- [Codex skill](skills/bluebird/SKILL.md): copy its directory into `~/.codex/skills/bluebird` and make `bluebird` available on PATH.

## Architecture and limits

Creation uses the [official URL scheme](https://bluebird.app/url-scheme). Reads use SQLite in read-only mode. Updates and timer control use Accessibility. Application composition, task workflows, localization, transport, and storage are separate modules; see [architecture](docs/en/architecture.md).

- UI operations require an unlocked, logged-in desktop and bring Bluebird forward. Save or cancel existing editors first; avoid simultaneous manual editing.
- Duplicate or visually indistinguishable titles are rejected. Virtualized off-screen tasks may require scrolling to the target before retrying; reads are unaffected.
- Date/recurrence fields are readable but not editable through this CLI. There are no standalone tag-management commands.
- Multi-field UI updates are not atomic. Read back after failures. Local verification does not prove iCloud/device synchronization or notification delivery.
- `--db PATH` reads snapshots; mutations reject non-default database paths. Unknown schemas fail explicitly. Future Bluebird UI/schema changes may need adapter updates.

## Development

```sh
python3 -B -m unittest discover -s tests -v
# Optional read-only check of every installed app localization, after setup:
BLUEBIRD_TEST_APP=/Applications/Bluebird.app python3 -B -m unittest discover -s tests -v
```

Default tests use synthetic UI data and temporary databases; they do not operate the app. CI tests Python and package installation on Linux and compiles the installed Swift helper on macOS. See [CONTRIBUTING.md](CONTRIBUTING.md).

Licensed under [Apache 2.0](LICENSE).
