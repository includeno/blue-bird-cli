# Security and vulnerability reporting

[Documentation](README.md) · English | [简体中文](../zh-CN/security.md) | [日本語](../ja/security.md)

Security fixes target the latest 0.3.x release. Report vulnerabilities using [GitHub private vulnerability reporting](https://github.com/includeno/blue-bird-cli/security/advisories/new), not a public issue. Include versions, the affected permission boundary, and a minimal reproduction with dummy data. Never attach codes, private admin URLs, databases, or personal task text. No response-time SLA is promised.

Codes provide cooperative function/tag restrictions. They do not isolate an agent with arbitrary commands under the same macOS user; that agent can run full-access or read/modify local data. Use an execution sandbox if that is outside your trust boundary. `bluebird start web` is an owner entry point and rejects a supplied agent code.

The console listens only on 127.0.0.1 and requires its private admin URL. Do not expose it through a reverse proxy or tunnel. The agent code appears only immediately after creation; save it yourself. Persistent storage holds only its digest and grant metadata. Protect the authorization database and private backups. Revoke lost or exposed codes and create replacements. Changes affect subsequent commands and do not undo actions already in progress.

macOS Accessibility, the agent execution sandbox, and CLI grants are separate layers. See [authorization](authorization.md) and the root [security policy](../../SECURITY.md).
