# Contributing

Use Python 3.9+ and the standard library. No Bluebird install or macOS is needed for the default unit tests:

```sh
python3 -B -m unittest discover -s tests -v
python3 -m pip install .
bluebird capabilities
```

For macOS installation and permissions, follow the [system setup guide](docs/en/setup.md). Install Bluebird and Xcode Command Line Tools, then run `bluebird --full-access setup`. Enable Accessibility for your terminal/agent host and inspect `bluebird --full-access doctor`.

For the optional read-only localization matrix:

```sh
BLUEBIRD_TEST_APP=/Applications/Bluebird.app python3 -B -m unittest discover -s tests -v
```

Do not commit app translations, databases, UI dumps, or user task data. Synthetic fixtures should exercise English fallbacks, non-Latin scripts, regional variants, RTL marks, and Unicode normalization. Report the app version, locale, failed command with private content removed, and error output.

For live verification, use uniquely named disposable tasks, start only when the timer is idle, and verify read-back after every operation. Test create/read/update/clear/complete/reopen/delete, tag association, start/stop/finish/reset, and restore the original app language after testing. Clean up only your own test tasks/tags/logs through the app. Keep resource-only coverage distinct from live coverage in `docs/en/verification.md`.

Follow the dependency direction in [architecture](docs/en/architecture.md). Keep translations in the installed app, UI selectors in the adapter, and business flows free of locale strings. A UI action is not success until the local read model confirms it.

Documentation lives in `docs/en`, `docs/zh-CN`, and `docs/ja`. Keep matching filenames and update all three language versions when changing documented behavior. Each page links to its translated counterparts.

HTTP tests bind a temporary loopback port and use temporary authorization databases; allow localhost binding in restricted test environments. Permission changes must cover command grants independently of tag scope, revocation, and denial before native actions. Never commit codes, admin URLs, or browser artifacts.

Before release, install `build` and `twine`, run `python -m build`, `python -m twine check dist/*`, and `python scripts/check_distribution.py dist` with a clean output directory. See [the release procedure](docs/en/release.md). Use `bluebird --version` in reports, and send vulnerabilities through [private reporting](SECURITY.md).
