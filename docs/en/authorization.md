# Authorization codes and CLI permissions

[Documentation](README.md) · English | [简体中文](../zh-CN/authorization.md) | [日本語](../ja/authorization.md)

Every data command needs an explicit mode: `--full-access` for the local owner, or `--code CODE` / `BLUEBIRD_CODE` for a scoped agent. A code has two independent limits: **allowed CLI functions** and **authorized tag IDs**. Both must permit an operation. This is separate from macOS Accessibility authorization; finish the [system setup](setup.md) first.

## Create a code in the local console

```sh
bluebird start web
# Optional: choose a port; 0 selects a free port.
bluebird start web --port 0
```

`start web` is the local owner entry point and needs no `--full-access` flag. It rejects `--code` and a nonempty `BLUEBIRD_CODE`; the owner should unset that variable first. The previous top-level `web` command has been replaced.

Run one of these commands and open the private URL in its JSON output. The server listens only on `127.0.0.1` (default port 8765). Keep that process running while managing permissions; Ctrl+C stops it. The `start web` command emits a startup record and a shutdown record, unlike one-result business commands.

The home page (`/`) shows totals and CLI instructions. Open Authorization codes (`/codes`), then use **New code** above the list to open the creation dialog. Editing also uses a dialog; Cancel, Close, or Escape dismisses unsaved changes.

1. Choose English, 简体中文, or 日本語 in the page header.
2. Enter a recognizable code name, such as “Codex · Work”.
3. Choose at least one existing Bluebird tag. Create missing tags in Bluebird, then use Refresh.
4. Choose at least one CLI function. Each group checkbox selects or clears that group; a partial group shows a mixed state. “Select all” / “Clear” apply to all functions. Selecting a tag does not automatically enable functions.
5. Generate the code and save the complete value shown once. The list shows metadata and permissions, never recoverable codes. The value is cleared when you hide it, navigate away, refresh, or open another create/edit dialog. If lost, revoke and generate a replacement.
6. Use “Edit permissions” to change the same code's functions and tags. Expand its function summary to inspect individual grants. “Revoke” permanently disables that code. Changes apply on the next command; already started UI actions are not rolled back.

The private URL contains a temporary owner session token, not an agent code. Do not give that URL to the agent. The page removes the fragment after loading and keeps its token only in memory. Browser reloads and new tabs need the original URL again; the page's Refresh button keeps the session. Restarting the server invalidates its previous admin URL.

## Granular functions

| Group | Individually selectable functions |
|---|---|
| Queries | `list`, `get`, `tags`, `logs` |
| Task operations | `add`, `update`, `complete`, `reopen`, `delete` |
| Timer controls | `timer.status`, `timer.start`, `timer.stop`, `timer.finish`, `timer.reset` |

Dots name stored permissions; CLI syntax remains `timer status`, etc. Permissions do not imply other permissions: `add` need not grant `list`; `timer.start` does not grant `timer.stop`. Query-only codes cannot mutate tasks, even inside their tag scope. Dry runs require the same permissions as execution. A mutation may return the task or timer result it modifies, even without a separate read grant.

`capabilities`, `locales`, and help are public. `auth-status` always lets a valid code inspect its own functions and tag bindings. `setup`, `doctor`, `ui`, `open`, `focus` require full access because they configure the system or expose/control the global app. Full access grants every operation, including administration; selecting all 14 functions on a code still retains tag restrictions and does not grant administration.

## Use a code

```sh
export BLUEBIRD_CODE='bb_REPLACE_WITH_YOUR_CODE'
bluebird auth-status
bluebird list
bluebird add 'Write proposal' --tags 'Work'
bluebird update ID --notes 'Outline ready'
bluebird delete ID --dry-run
bluebird delete ID --yes
unset BLUEBIRD_CODE
```

The example requires `list`, `add`, `update`, and `delete`, plus an authorized existing tag named Work. Give agents only the desired grants. `--code CODE` overrides the environment; explicit `--full-access` ignores `BLUEBIRD_CODE`. Supplying both flags is invalid. Codes are bearer credentials: avoid putting them in shared logs or command histories. Agents must not switch to full access when a code is denied.

`auth-status` returns the mode, granted functions, stable tag IDs, and currently available tag names. `capabilities` describes the permission groups for agent discovery. Authorization failures return JSON `access_denied` and exit **3**; other exit codes remain 0 success, 1 execution failure, and 2 invalid arguments.

## Tag rules

A task must have at least one tag, and **every tag on the task must be authorized**. A code for Work can access a Work task, but neither an untagged task nor a Work + Private task. A Work + Study code permits tasks with either or both tags.

Bindings use tag IDs: renaming a tag preserves its binding; deleting and recreating the same name does not. Missing tags grant no access. Creating tasks requires an explicit nonempty `--tags` value; changing tags must leave at least one authorized existing tag. A code cannot create new tags or clear all tags. Ambiguous duplicate tag names are rejected. Full access retains tag creation/clearing.

Lists and logs exclude out-of-scope tasks. A direct ID request cannot distinguish missing from unauthorized tasks. A timer for another scope returns `state: unavailable` without its task information; its controls are denied. The code cannot supply an alternate `--db` snapshot. Task targeting still checks duplicate titles across the full store to avoid editing a different task with the same title.

## Storage and boundary

Authorization records live at `~/Library/Application Support/bluebird-cli/authorization.sqlite3` with owner-only file permissions. Only SHA-256 code digests are stored, along with grant metadata. The file is independent of `BLUEBIRD_CLI_HOME` and the helper cache: clearing/rebuilding the helper does not reset grants. Back up this authorization file privately; deleting it invalidates all codes. Codes do not expire automatically. Old records without function grants receive no function permissions until edited explicitly.

The web server is needed only to manage grants. CLI code validation reads the local authorization database and works while the server is stopped. The console checks its loopback Host/Origin and owner session token; agent codes cannot authenticate to the admin API.

This is cooperative CLI permission control, **not an OS security sandbox**. A local user or agent allowed to run arbitrary commands under the same macOS account can choose full access, change authorization storage, or read app data directly. Use a restricted execution environment when that is outside the agent's trust boundary. CLI codes do not grant macOS Accessibility or sandbox permissions.
