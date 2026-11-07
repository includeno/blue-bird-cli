# Verification records

[Documentation](README.md) · English | [简体中文](../zh-CN/verification.md) | [日本語](../ja/verification.md)

## 0.3.0 release checks — 2026-11-07

- Local macOS 15.7.5 / Apple Silicon / Python 3.11: 79 tests passed, including the installed Bluebird 3.14.1 / 437 resource matrix for all 26 locales.
- Added package-version, archive-content/path, runnable error-hint, and DNS-independent loopback-startup checks. A migration fixture now explicitly closes its SQLite connection on Python 3.13.
- Standard wheel/sdist builds, package metadata checks, extracted-source tests, and installation outside the checkout are release gates. The [Tests workflow](https://github.com/includeno/blue-bird-cli/actions/workflows/test.yml) records Python 3.9/3.13 and clean macOS Intel/Apple Silicon results for each commit; the [Release workflow](https://github.com/includeno/blue-bird-cli/actions/workflows/release.yml) repeats package and native checks before publishing.
- Hosted runners do not have Bluebird or Accessibility authorization. Their native checks verify installation and compilation; live app evidence remains the separately recorded local checks below.

## Boundary regression tests — 2026-11-07

Added 22 test methods; the full suite now passes 74 tests, including the installed 26-locale resource matrix.

- [CLI tests](../../tests/test_cli.py): ports 0/1/65535, invalid ports and syntax, removed command, unsupported host option, and bind failures returning JSON.
- [Authorization tests](../../tests/test_auth.py): label type/length limits, duplicate grants, failed updates preserving state, persistent codes and idempotent revocation, all 14 function grants individually, explicit argument/environment precedence, scope/revocation changes while waiting for the lock, changed task/timer targets before UI writes, and redaction of missing/foreign timer targets.
- [HTTP tests](../../tests/test_web.py): malformed JSON/UTF-8 and wrong body types, excessive nesting, the 65,536-byte request limit, missing/duplicate/invalid lengths, incomplete bodies and read timeouts, origin/credential/session substitution, wrong routes/methods, revoked-grant updates, storage errors without private detail leakage, and occupied ports.
- [CLI service integration](../../tests/test_web_cli.py): a real `bluebird start web --port 0` child process emits its private URL, serves the page, keeps the token out of HTML, and exits cleanly on SIGINT.

Regression tests exposed and fixed request framing acceptance (missing/duplicate lengths and incomplete bodies), and misclassification of deep JSON and read timeouts as storage failures. Invalid bodies now return 400; body read timeouts return 408. Neither writes grants. Tests use temporary authorization data and do not mutate Bluebird. Browser and native CRUD flows were not rerun for this change; existing web processes must restart to load the HTTP fixes.

## 0.3 authorization console — 2026-11-07

- 51 automated tests passed, including the installed app's 26-locale resource matrix, function permissions, all-tags scope, revoked/updated grants, grant rechecks after lock acquisition, legacy grants without privileges, and local HTTP origin/authentication checks.
- Chromium: separate home and code list routes; list-top creation dialog; creation, editing, revocation, individual/group/mixed/select-all/clear controls; English/Chinese/Japanese home rendering; 390 px mobile overflow checks, Escape closing and browser-back navigation.
- Complete code values appear only after creation. HTTP list/update/read routes do not reveal them; stored authorization bytes contain no plaintext code. Browser checks confirmed navigation/editing/back cannot redisplay a code. Screenshots use synthetic fixture data, not user tasks.
- Live Bluebird 3.14.1 / 437, zh-Hans: code-authorized create/read/update/complete/reopen/delete and timer start/stop passed. Reducing the same code to read-only denied deletion. The disposable task was soft-deleted and its code revoked.
- Wheel build includes the native helper source and web HTML/CSS/JS; documentation languages and links checked. No cloud deployment, OS-level isolation, or new live certification of all 26 app languages is claimed. Earlier records below describe earlier versions; their commands predate the explicit access-mode requirement.

Date: 2026-11-07 (Asia/Shanghai). Environment: local macOS, Python 3.11, Bluebird **3.14.1 / build 437**.

## Automated tests and installation

- 33 tests passed, including the 26-locale resource matrix enabled with `BLUEBIRD_TEST_APP=/Applications/Bluebird.app`.
- Without that variable, 32 tests pass and one is explicitly skipped. Default tests do not operate the app.
- Coverage includes read-only SQLite, schema checks, 64-bit IDs, JSON contracts, argument validation, process locks, read-back verification, timer stepping, language detection/ambiguity/mismatches, Unicode/RTL, control identity, stale animation paths, system Back buttons, and tag-name collisions.
- The Swift helper compiled successfully; Python sources passed Python 3.9 syntax checks.
- A wheel was built and installed in an isolated virtual environment. Commands, resource discovery, dry-run, and native helper compilation worked from `/tmp`. Swift source is included in the package.
- GitHub Actions is configured for Linux Python 3.9/3.13 tests, installation checks, and macOS helper compilation. It has not yet been pushed and run on GitHub.

## Live language coverage

| Level | Scope | Checks performed |
|---|---|---|
| Resource and selector contracts | All 26 locales | Every semantic control, dynamic task actions, regional variants, English fallbacks, Unicode, and punctuation |
| Actual desktop controls | All 26 locales | Task editor, title/notes/priority, duration picker, tag picker/new-tag input, Back navigation, timer preparation screen, and control identification |
| Full CRUD and timer lifecycle | `zh-Hans`, `en`, `ja`, `ar` | Create → read back → edit fields → clear → complete → reopen → start/stop → start/finish → reset → delete |

Locales: `ar de en en-GB es es-ES fr he hi id it ja ko ms nl pl pt pt-PT ru th tr uk vi zh-HK zh-Hans zh-Hant`.

The English, Japanese, and Arabic lifecycle checks included associating and clearing existing tags. Mixed text included multiline Chinese, Arabic, Japanese, accented letters, and emoji. The other 22 UIs used one isolated probe task to check controls and navigation; not every write/timer state combination was executed in each language. Languages were selected using temporary process launch arguments. A normal launch afterward restored `zh-Hans`, which was confirmed.

## Issues found and fixed in this round

- Bluebird's base English resource table is incomplete. Development-language defaults fill missing entries without copying the app's full translations.
- The French Back button exposes `Précédent`, while the app's translation is `Retour`. It is now identified through its navigation-bar relationship with the stable `plus` control inside the popover; non-unique structures are rejected.
- Cmd+A occasionally failed to select the entire notes field during focus transitions. Native text selection is now checked before replacement to avoid appending text.
- New-tag submission needs reliable window activation and keyboard-event timing. Processing time is allowed between key down and key up; creation, selection, clearing, and task deletion were rechecked in the app.
- Popover animations can move AX tree paths. Refresh/retry is allowed only when the native layer confirms no action occurred, and the unique identity and selection state still match. Unknown outcomes are not retried.

## Cleanup and final state

Six test tasks from this round were soft-deleted through the app. Five temporary tags were deleted through the UI by exact name. No focus logs remain for these test tasks. Existing tasks and tags were not deleted. Final `doctor` output was `ready=true`, with locale `zh-Hans` and timer state `idle`. The default helper is installed in the user cache; the checkout runs without additional environment variables.

## Scope and remaining limits

This evidence applies to Bluebird 3.14.1. It does not certify other versions or every workflow in every language. Locked/logged-out operation, large virtualized task lists, natural timer-expiry notifications, and iCloud/iPhone/Watch synchronization were not verified. Date/recurrence editing and standalone tag management remain outside the CLI command scope.

The original verification record follows. Its unverified items describe the original version, not the current coverage.

---

# Original verification record (historical)

Date: 2026-11-07 (Asia/Shanghai). Environment: local macOS, Bluebird 3.14.1 / build 437, Simplified Chinese.

## Automated verification

`python3 -B -m unittest discover -s tests -v`: 20 tests passed.
Coverage included read-only connections, unknown schemas, time/ID/tag conversion, JSON errors, Chinese encoding, deletion arguments, process locks, duplicate/prefix ambiguity, real text-input routing, idempotent completion, timer-offset normalization, existing-session protection, and finished/break state detection.

The Swift helper compiled successfully. Python compilation and Codex skill frontmatter validation passed.

## Actual app operations

Only isolated tasks created for these checks were used; existing tasks were not modified.

| Operation | Observed result |
|---|---|
| Create task | Official URL creation followed by read-back returned a new ID with matching title, notes, duration, priority, and tags |
| List/search/get | Local read-only access succeeded |
| Edit title, notes, duration, priority, tags | Saved and verified by read-back |
| Multiline Chinese, `&`, emoji | Notes matched the input |
| Clear notes, tags, duration, priority | Empty string, empty list, 0, and none saved correctly |
| Create a tag during update | Text input and Return made the tag selectable and persisted it |
| Complete/reopen task | State transitions confirmed by read-back |
| Delete task | App soft-delete; get returned deleted |
| Start/stop focus | Real 5/10-minute sessions started; stop returned idle |
| Set a 2-minute task to 5-minute focus | Reset offset to zero before stepping; actual duration=5 |
| Focus logs | An app-saved one-minute record was read |
| Finished/break/reset | Finished and break states were recognized; reset returned idle from both |

Calibration fixes covered AX slider NaN breaking JSON, changing task-row roles, notes AXValue assignment failing to persist, Return events missing a character, non-five-minute timer offsets, and early completion retaining timestamps that falsely suggested a running session.

## Items unverified in the original version

English/other language UIs, other Bluebird versions, locked/logged-out operation, large virtualized lists, natural timer-expiry notifications, and iCloud/iPhone/Apple Watch synchronization were not verified.
Date/recurrence editing, standalone tag management, and remote background services were outside that version's commands.

## Test cleanup

The two test tasks were soft-deleted. Three test tags and two one-minute focus records were also deleted through the app. Existing tasks and records were unchanged.
The final `doctor` run with normal permissions returned `ready=true`.

During testing, the app later displayed an old test session's break phase again. The cause was not established; it was reset. The CLI confirms local state at the time of the operation and cannot guarantee that the app or another device will not subsequently overwrite that state.
