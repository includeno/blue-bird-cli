# Bluebird CLI ドキュメント

[English](../en/README.md) | [简体中文](../zh-CN/README.md) | 日本語

- [互換性](compatibility.md)
- [リリース手順](release.md)
- [セキュリティ報告](security.md)

- [認証コードと機能権限](authorization.md)

Bluebird CLI は、インストール済みの macOS アプリ Bluebird をターミナルやエージェントから操作するツールです。タスクの作成・取得・更新・削除、完了状態の変更、集中タイマーの操作結果を JSON で返します。

- [システム設定と初回起動](setup.md)：依存ツール、インストール、macOS の権限、エージェントのサンドボックス、準備確認、トラブル対処。
- [アーキテクチャ](architecture.md)：モジュールの役割、多言語対応、UI 要素の特定、エラー処理。
- [エージェント操作手順](agent-workflow.md)：コマンドの仕様、タスクの一連の操作、Python の例、Codex スキルの導入。
- [検証記録](verification.md)：自動テスト、実際の言語別 UI の検証範囲、過去の結果、残る制限。

macOS、Bluebird、Python 3.9 以降、Xcode Command Line Tools の `swiftc` が必要です。リポジトリのルートで次を実行します。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
bluebird --full-access setup
bluebird --full-access open
bluebird --full-access doctor
```

「システム設定 → プライバシーとセキュリティ → アクセシビリティ」で、CLI を起動するターミナルやエージェントのアプリを許可してください。必要に応じて `setup` が返す helper のパスも追加します。エージェントのサンドボックス権限は別です。準備完了の判定には `doctor` の終了コードだけでなく `data.ready` を確認します。

コマンド一覧は `bluebird capabilities`、開発手順は [CONTRIBUTING（英語）](../../CONTRIBUTING.md)、詳細な導入説明は[プロジェクト README（英語）](../../README.md)を参照してください。
