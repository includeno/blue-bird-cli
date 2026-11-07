# Security policy

[English](docs/en/security.md) · [简体中文](docs/zh-CN/security.md) · [日本語](docs/ja/security.md)

Security fixes target the latest 0.3.x release. Older development snapshots are unsupported; update before reproducing an issue.

Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/includeno/blue-bird-cli/security/advisories/new). Include the CLI and Bluebird versions, macOS version, the affected permission boundary, and minimal reproduction steps using dummy data. Do not open a public issue with exploit details, codes, admin URLs, databases, or personal task text. There is no guaranteed response-time SLA.

Authorization codes restrict cooperative CLI commands; they do not isolate an agent with arbitrary execution under the same macOS user. Such an agent can select owner mode, edit the authorization database, or read app data directly. The web console binds only to 127.0.0.1 and requires its private session URL. Do not expose it through a proxy or tunnel. Codes are shown once, stored as digests, and revoked locally; protect the authorization database and backups. Accessibility and agent execution permissions remain separate.

This is an unofficial Bluebird integration. App binaries, user databases, and proprietary translations are not distributed.
