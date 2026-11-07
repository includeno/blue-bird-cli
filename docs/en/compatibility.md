# Compatibility

[Documentation](README.md) · English | [简体中文](../zh-CN/compatibility.md) | [日本語](../ja/compatibility.md)

The initial supported target is **macOS 15 or later**, Python 3.9 or later, and Bluebird 3.14.1 / build 437. Newer macOS or Bluebird releases are not automatically certified; unknown schemas and ambiguous UI controls fail explicitly. Older macOS versions are outside the initial support target rather than known to be incompatible.

| Environment | Evidence |
|---|---|
| macOS 15.7.5, Apple Silicon (arm64), Python 3.11, Bluebird 3.14.1 | Local live task and timer workflows; see the verification record |
| macOS 15 Apple Silicon and Intel hosted runners | CI installs the wheel, runs fixture tests, and compiles the Swift helper; runners do not contain Bluebird or grant Accessibility |
| Linux, Python 3.9 and 3.13 | CI covers portable parsing, authorization, HTTP and storage fixtures; Linux cannot control the macOS app |
| Other Bluebird versions, older macOS, Intel live UI | Not live-certified; report the precise environment when testing |

The helper is compiled locally for the host architecture; no prebuilt Universal binary is distributed. Native writes require Xcode Command Line Tools, an unlocked logged-in desktop, initialized Bluebird data, and Accessibility permission for the actual terminal/agent host. UI tests on one Mac do not prove Intel live behavior, remote iCloud sync, or behavior on a fresh macOS user account.

The adapter resolves resources from all 26 locales in the tested app. Full task/timer workflows were exercised in Simplified Chinese, English, Japanese, and Arabic; the remaining locales have resource and control checks, not every workflow. Web UI and documentation support English, Simplified Chinese, and Japanese.

Include `bluebird --version`, macOS version, chip architecture, Python version, Bluebird version/UI language, and sanitized error output in bug reports. `capabilities` returns `cli_version`; its separate `version` field describes the capability schema.
