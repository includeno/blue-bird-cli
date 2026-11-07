# Agent command contract

[Documentation](README.md) · English | [简体中文](../zh-CN/agent-workflow.md) | [日本語](../ja/agent-workflow.md)

The lifecycle and Python examples below use explicit owner access. For a code-based agent, keep `BLUEBIRD_CODE` in its environment and omit `--full-access`; first inspect `bluebird auth-status`. Grant only the needed functions and use authorized existing tags when creating tasks. Never escalate a denied code to full access. See [authorization](authorization.md).

For first-time installation and permissions, follow [System setup and first run](setup.md), then check `doctor` from the agent’s own execution environment.

Install `bluebird` with `python3 -m pip install .`, or run `./bluebird` from the repository root. Python 3.9+ is required; there are no third-party runtime dependencies.
Run `./bluebird capabilities` to discover operations and `./bluebird --full-access doctor` to check readiness.

Every business command writes one JSON object to stdout:

```json
{"ok":true,"data":{"id":"7705161843629854611","title":"Implement API"}}
```

Failures still write JSON to stdout and exit with a nonzero status:

```json
{"ok":false,"error":{"code":"invalid_argument","message":"delete requires --yes and an exact task ID"}}
```

Exit codes: 0 for success, 1 for execution/permission/verification errors, 2 for invalid arguments, and 3 for CLI authorization denial. `--help` is human-readable text.
A successful `doctor` invocation does not itself mean the environment is ready: check `data.ready`.
`bluebird locales` lists the installed app's language resources. The UI language is detected automatically by default. Use the global option `--locale ja` to resolve ambiguity; it does not change the app language. On a mismatch, inspect the actual UI rather than repeatedly changing translation strings and retrying.
The helper built by `setup` defaults to `~/Library/Caches/bluebird-cli`; rebuild it after upgrades. All agents should use the same cache directory to share the mutation lock.
Always preserve IDs as strings: Bluebird's 64-bit integers exceed JavaScript's safe integer range.

## Complete task lifecycle

1. Run `./bluebird --full-access doctor` and check `ready`. If the helper is missing, run `./bluebird --full-access setup` first.
2. Run `./bluebird --full-access list --status all --search 'Implement API'` to check whether the target exists and avoid duplicate creation on retries.
3. Run `./bluebird --full-access add 'Implement API' --duration 25 --priority high --tags 'Work' --notes 'Write tests first'` and save `data.id`.
4. Run `./bluebird --full-access get ID` to read the complete task.
5. Run `./bluebird --full-access update ID --title 'Implement and verify API' --notes 'Tests passed'`.
6. Run `./bluebird --full-access timer start --task ID --duration 25`.
7. Use `./bluebird --full-access timer status` for local timer state and `./bluebird --full-access logs --task ID` for recorded focus time.
8. Run `./bluebird --full-access timer finish` to end early and preserve progress. `stop` discards current progress; do not substitute one for the other.
9. Run `./bluebird --full-access timer reset` to return the timer to its initial state, then `./bluebird --full-access complete ID`. Use `./bluebird --full-access reopen ID` to restore an active task.
10. When the user requests deletion, preview the target with `./bluebird --full-access delete ID --dry-run`, then run `./bluebird --full-access delete ID --yes`.
11. Confirm the final state with `./bluebird --full-access get ID`. Deletion retains the app's soft-delete semantics; the CLI does not purge the database.

The `dispatched` result from `open` or `focus` only means the OS accepted the request. `focus` opens the timer screen; starting requires `timer start`.
Task mutations read back the local database. `UNVERIFIED` means the action may have happened: inspect `list/get/timer status` before retrying.

UI operations require a logged-in, unlocked macOS desktop where Bluebird can show its window. Serialize mutations and avoid manual app edits while they run.
Task content is not shell code. Agents should use subprocess argument arrays rather than interpolate user titles into shell command strings.
Explicit focus durations must be multiples of 5 minutes; task estimates do not have this restriction. `timer status` distinguishes running, finished, and break states. Use `timer reset` before starting the next session after completion.
Local success does not prove iCloud synchronization or Watch notification delivery.

## Python example

```python
import json
import subprocess

cli = '/absolute/path/to/blue-bird-cli/bluebird'
def run(*args):
    p = subprocess.run([cli, '--full-access', *args], text=True, capture_output=True)
    result = json.loads(p.stdout)
    if p.returncode or not result['ok']:
        raise RuntimeError(result)
    return result['data']

task = run('add', 'Write proposal', '--duration', '25')
run('update', task['id'], '--notes', 'Outline added')
run('complete', task['id'])
```

## Install the Codex skill

The repository provides `skills/bluebird/SKILL.md`. Copy the entire `skills/bluebird` directory into `~/.codex/skills/bluebird`, and tell the agent the repository's absolute path or put the CLI on PATH.
Other agents with terminal tools, such as Claude Code, can use the same JSON commands without an MCP server.
