# Installation and release procedure

[Documentation](README.md) · English | [简体中文](../zh-CN/release.md) | [日本語](../ja/release.md)

## Install a GitHub release

Download the wheel from [Releases](https://github.com/includeno/blue-bird-cli/releases). In a virtual environment, run `python -m pip install /path/to/blue_bird_cli-0.3.0-py3-none-any.whl`. Alternatively extract the source archive, change to its directory, and run `python -m pip install .`. Verify with `bluebird --version`, then follow [system setup](setup.md). The release contains Swift source and web resources; the helper is compiled on your Mac. Compare downloaded files with the attached `SHA256SUMS.txt` using `shasum -a 256 FILE`.

## Maintainer checklist

1. Update `bluebird_cli.__version__` (the single package-version source) and `CHANGELOG.md`. Keep English/Chinese/Japanese docs aligned.
2. Use a clean output directory: `python -m pip install build twine`, `python -m build`, `python -m twine check dist/*`, then `python scripts/check_distribution.py dist`. The latter verifies required files and runs tests from the extracted source, so a checkout-only success cannot conceal missing release files.
3. Open a PR and wait for all required checks: both Python unit jobs, Distribution, and both macOS architecture jobs. Hosted macOS checks prove installation and helper compilation, not live Bluebird control.
4. Merge the reviewed change, create an annotated version tag such as `git tag -a v0.3.0 -m 'Bluebird CLI 0.3.0'`, and push that exact tag. Do not move a published tag.
5. The Release workflow verifies tag/version agreement, builds and tests the archives, compiles the installed helper on both macOS architectures, then creates the GitHub Release with wheel, sdist, notes, and checksums. It uses the repository workflow token; no publishing secret is needed.
6. Confirm the release assets and workflow results. For a corrected release, increment the version and publish a new tag instead of overwriting existing artifacts.

Initial publication also requires committing all source, enabling public visibility, private vulnerability reporting, and branch protection with required CI, no force pushes/deletion, and resolved review conversations. Use the issue templates for sanitized reports. The first release is distributed on GitHub; PyPI and Homebrew are separate distribution channels, not prerequisites for using this release.
