# 互換性

[ドキュメント](README.md) · [English](../en/compatibility.md) | [简体中文](../zh-CN/compatibility.md) | 日本語

初期のサポート対象は **macOS 15 以降**、Python 3.9 以降、Bluebird 3.14.1 / build 437 です。新しい OS や Bluebird は自動的に検証済みとはなりません。不明なスキーマや曖昧な UI は明示的に失敗します。古い macOS は初期対象外であり、非互換と確認されたわけではありません。

| 環境 | 検証内容 |
|---|---|
| macOS 15.7.5、Apple Silicon（arm64）、Python 3.11、Bluebird 3.14.1 | ローカル実機でタスクとタイマーを操作。検証記録を参照 |
| macOS 15 の Apple Silicon / Intel ホストランナー | CI で wheel のインストール、フィクスチャテスト、Swift のコンパイル。Bluebird やアクセシビリティ権限はありません |
| Linux、Python 3.9 / 3.13 | 引数、認証、HTTP、ストレージのフィクスチャを CI で検証。macOS アプリは操作できません |
| 他の Bluebird、古い macOS、Intel の実機 UI | 実機認証は未実施。正確な環境を報告してください |

ヘルパーは利用者の Mac のアーキテクチャ向けにコンパイルし、Universal バイナリは配布しません。UI 操作には開発ツール、ログイン済みでロックされていないデスクトップ、初期化済み Bluebird、実際の起動元へのアクセシビリティ許可が必要です。一台の実機検証は Intel の動作、遠隔同期、新しい macOS ユーザーでの動作を保証しません。

検証対象アプリの全 26 言語リソースを解決します。完全なタスク・タイマー操作は簡体中国語、英語、日本語、アラビア語で実施済みです。他の言語はリソースとコントロールの確認で、全操作の認証ではありません。Web と文書は英語、中国語、日本語に対応します。

問題報告には `bluebird --version`、OS、チップ、Python、Bluebird の版と言語、秘匿情報を除いたエラーを含めてください。`capabilities` の `cli_version` は製品版、`version` は能力記述の形式バージョンです。
