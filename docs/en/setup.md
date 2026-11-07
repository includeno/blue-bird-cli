# System setup and first run

[Documentation](README.md) · English | [简体中文](../zh-CN/setup.md) | [日本語](../ja/setup.md)

Supported target: macOS 15+, Python 3.9+, Bluebird 3.14.1. See [compatibility](compatibility.md) for architecture and verification limits. Use `bluebird --version` in diagnostics.

Use `--full-access` for owner setup. Before delegating to an agent, open `bluebird start web` and configure both CLI functions and at least one tag; see [authorization](authorization.md). CLI codes and macOS Accessibility are separate permissions. A missing/invalid mode or denied function returns exit code 3.

Follow this order: prepare Bluebird and developer tools → install the CLI → compile the helper → grant Accessibility access → run `doctor` in the environment you will actually use. `setup` only compiles the helper; it does not enable system permissions. UI operations are ready when `doctor` reports `data.ready=true`.

## 1. Prepare the environment

| Component | Requirement and purpose |
|---|---|
| macOS desktop | A logged-in, unlocked graphical desktop; UI operations bring Bluebird forward |
| Bluebird | Install the macOS app, launch it manually at least once, and complete initial onboarding; the CLI reads the current macOS user's data |
| Python | Version 3.9 or later, to run the CLI |
| Xcode Command Line Tools | Provide `swiftc` for compiling the native helper |
| Accessibility access | Required for editing, completion, reopening, deletion, and timer control |

Live app verification currently covers Bluebird 3.14.1 / build 437; see the [verification record](verification.md). Save or cancel unfinished editors and leave the main Bluebird window visible during setup.

Check dependencies in a terminal:

```sh
python3 --version
xcode-select -p
xcrun --find swiftc
swiftc --version
```

If Python is missing, install it from the [official Python downloads for macOS](https://www.python.org/downloads/macos/), reopen your terminal, and check its version.
If developer tools are missing, run the following command and complete the system installer before checking `swiftc` again. See [Apple's Command Line Tools installation instructions](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools).

```sh
xcode-select --install
```

## 2. Install the CLI and choose its command path

Run these commands from the repository root. Replace the example path with your actual downloaded or cloned directory. A virtual environment avoids changing the Python environment maintained by your OS or package manager.

```sh
cd "/absolute/path/to/blue-bird-cli"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
bluebird capabilities
```

Activation applies only to the current shell. In a new terminal, activate it again or use the absolute executable path:

```sh
/absolute/path/to/blue-bird-cli/.venv/bin/bluebird capabilities
```

Agents should also use that absolute path; do not assume they inherit your terminal's virtual environment. To run directly from source, use `./bluebird` in the repository root and replace `bluebird` with `./bluebird` in the commands below. Source execution still requires Python and the Swift compiler.

## 3. Compile the native helper

```sh
bluebird --full-access setup
```

The first compilation may take a few minutes. Example output:

```json
{"ok":true,"data":{"helper":"/Users/your-name/Library/Caches/bluebird-cli/bluebird-ax","trusted":false}}
```

`ok=true` means compilation completed. `trusted=false` means the current execution context is not yet trusted for Accessibility; it is not a compilation failure. Keep the actual `data.helper` path for the next step. The default is `~/Library/Caches/bluebird-cli/bluebird-ax`; the older checkout path `.build/bluebird-ax` is no longer the default.

## 4. Authorize the application that launches the CLI

Open **Apple menu → System Settings → Privacy & Security → Accessibility** and enable the app that launches the CLI. Use the add button if it is absent, select the app, and authenticate locally if macOS requests it. See [Apple's Accessibility permission guide](https://support.apple.com/en-ie/guide/mac-help/mh43185/27/mac/27).

| Where you run the CLI | Host application to check first |
|---|---|
| Terminal or iTerm | The terminal app you actually use |
| An editor's integrated terminal | The editor hosting that terminal |
| Codex or another desktop agent | The launching app shown by macOS; the test machine showed ChatGPT, but this name is not universal |

macOS may attribute permission to the launcher. **Adding only `bluebird-ax` does not establish permission for Terminal or the agent.** If the system also requires the helper, add the executable returned by `setup` to the same list. In the file picker, press **⌘⇧G**, paste the actual full path, add it, and enable its switch.

Recheck from the original terminal or agent. If authorization has not taken effect, save your work, quit and reopen that host app, then retry. Do not use `sudo` to run the CLI as a different user; Bluebird data and permissions belong to the current user's environment.

## 5. Check the agent's execution sandbox separately

System Accessibility permission and an agent's command-execution sandbox are separate. Verify from the environment that will actually run the CLI, not only from Terminal.

If `doctor` reports `trusted=true` in a regular terminal but `trusted=false` or blocked system access inside the agent:

1. Confirm both environments use the same CLI path, macOS user, and `BLUEBIRD_CLI_HOME` setting.
2. Confirm the actual agent host is also enabled in macOS Accessibility settings.
3. Use the agent's normal per-command approval mechanism to allow the required local system automation access, then rerun `doctor` in that execution context.

Terminal's permission does not prove that a different host or sandbox can operate the UI. SSH and background processes without an interactive desktop cannot replace a logged-in, unlocked desktop merely by receiving permission.

## 6. Open the app and confirm readiness

```sh
bluebird --full-access open
bluebird --full-access doctor
bluebird locales
bluebird --full-access list
bluebird --full-access timer status
```

After `open`, wait for Bluebird's main window before running `doctor`. First launch may require initialization inside the app. The relevant fields should resemble this excerpt; `locale` should match the actual UI language:

```json
{"ok":true,"data":{"macos":true,"helper":true,"trusted":true,"locale":"en","ready":true}}
```

| Field | Interpretation |
|---|---|
| `ok` / process exit code | Whether the diagnostic command completed; insufficient on its own to establish UI readiness |
| `data.helper` | Whether the helper exists; an old helper can still cause a version error in `adapter_error` |
| `data.trusted` | Whether the current execution context has Accessibility trust |
| `data.database_error` | If present, address the local database read or schema problem |
| `data.adapter_error` | If present, address app startup, helper version, or language detection |
| `data.ready` | Must be `true` before UI mutations |

`locales` only enumerates resources; it does not prove UI authorization. Language detection is automatic by default. Use a global override only to resolve ambiguity when the app actually uses that language, for example `bluebird --full-access --locale ja doctor`. This does not switch the app to Japanese.

These checks neither create tasks nor start a timer. Once ready, follow the [agent workflow](agent-workflow.md) for task and timer operations. For an initial write check, use a uniquely named temporary task and delete it by its returned exact ID afterward; do not use existing tasks for setup tests.

## 7. Paths, upgrades, and multiple processes

| Item | Default location or rule |
|---|---|
| CLI installed in the virtual environment above | `.venv/bin/bluebird` under the repository |
| Native helper | `~/Library/Caches/bluebird-cli/bluebird-ax` |
| Source digest, compiler cache, mutation lock | The same `~/Library/Caches/bluebird-cli` directory |
| Bluebird database | `~/Library/Group Containers/group.com.cub-and-pup.Bluebird/Bluebird.sqlite`; read-only access by the CLI |

After a CLI upgrade, reinstall and compile in the same virtual environment:

```sh
python -m pip install .
bluebird --full-access setup
bluebird --full-access doctor
```

Set `BLUEBIRD_CLI_HOME` only when you need a custom cache directory. After changing it, rerun `setup` in that environment and use the new `data.helper` path when checking permissions. Terminals and agents controlling the same app must share the cache directory to share the mutation lock. Setting a variable in one terminal does not configure another agent automatically.

`--db PATH` is only for reading snapshots or test databases. It does not redirect mutations to arbitrary databases or solve permission problems.

## Troubleshooting

| Symptom | Next step |
|---|---|
| `bluebird: command not found` | Activate `.venv` or use its absolute executable path; use `./bluebird` for source execution |
| pip reports `externally-managed-environment` | Install in the virtual environment from step 2 |
| `swiftc` missing or invalid developer directory | Complete Command Line Tools installation; inspect paths with `xcode-select -p` and `xcrun --find swiftc` |
| `Accessibility helper missing` | Run `setup` with the current CLI and cache configuration |
| `Native helper is outdated` | Re-run `setup` after upgrading; avoid mixing old helpers from different checkouts |
| `ACCESSIBILITY_REQUIRED` / `trusted=false` | Check the host app, helper path, and execution sandbox in steps 4 and 5 |
| `Bluebird is not running` | Run `open`, wait for the main window, then run `doctor` |
| `database_error` / unable to open database | Confirm initialization under the same macOS user; inspect the reported path and file-access restrictions. Accessibility permission is separate from file access. Do not create an empty replacement database |
| `Unsupported Bluebird database schema` | The app schema is incompatible with the adapter; update the adapter rather than altering the original database to bypass checks |
| `LOCALE_UNDETECTED` / `LOCALE_MISMATCH` / `LOCALE_AMBIGUOUS` | Show the main window, compare `locales` with the actual UI, and specify a matching `--locale` if needed |
| Existing editor or dialog | Save or cancel it manually before retrying |
| `Task is not exposed` | Scroll to the target in Bluebird; read commands are not limited to visible rows |
| `UNVERIFIED` | The action may have happened. Read `get/list/timer status` first, especially before retrying creation |
