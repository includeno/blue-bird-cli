# エージェントのコマンド仕様

[ドキュメント一覧](README.md) · [English](../en/agent-workflow.md) | [简体中文](../zh-CN/agent-workflow.md) | 日本語

以下のライフサイクルと Python の例は所有者権限を明示しています。制限付きエージェントは環境変数 `BLUEBIRD_CODE` を使い、`--full-access` を省略して、まず `bluebird auth-status` を確認します。必要な機能だけを許可し、作成時は既存の許可タグを指定してください。拒否時に full-access へ昇格してはいけません。[認証の説明](authorization.md)を参照してください。

初回のインストールと権限設定は[システム設定と初回起動](setup.md)に従い、エージェントが実際にコマンドを実行する環境から `doctor` を確認してください。

`python3 -m pip install .` で `bluebird` をインストールするか、リポジトリのルートから `./bluebird` を実行します。Python 3.9 以降が必要で、実行時の外部ライブラリ依存はありません。
`./bluebird capabilities` で対応する操作を確認し、`./bluebird --full-access doctor` で環境を確認します。

各操作コマンドは、標準出力に JSON オブジェクトを一行で返します。

```json
{"ok":true,"data":{"id":"7705161843629854611","title":"API を実装する"}}
```

失敗時も標準出力は JSON で、終了コードは 0 以外になります。

```json
{"ok":false,"error":{"code":"invalid_argument","message":"delete requires --yes and an exact task ID"}}
```

終了コードは、成功が 0、実行・権限・検証エラーが 1、引数エラーが 2、CLI 認証拒否が 3 です。`--help` は人が読むためのテキストです。
`doctor` の実行が成功しても、操作の準備が整ったとは限りません。`data.ready` を確認してください。
`bluebird locales` はインストール済みアプリの言語リソースを一覧表示します。既定では UI 言語を自動判定します。候補が曖昧な場合はグローバルオプション `--locale ja` を指定できますが、アプリの言語設定は変わりません。言語が一致しない場合は実際の画面を確認し、翻訳文字列を変更して再試行を繰り返さないでください。
`setup` が作成する helper の既定の保存先は `~/Library/Caches/bluebird-cli` です。アップグレード後は再ビルドしてください。更新ロックを共有するため、すべてのエージェントで同じキャッシュディレクトリを使用します。
ID は常に文字列として保持してください。Bluebird の 64 ビット整数は、JavaScript で安全に扱える整数の範囲を超えます。

## タスクの一連の操作

1. `./bluebird --full-access doctor` を実行して `ready` を確認します。helper が未作成なら先に `./bluebird --full-access setup` を実行します。
2. `./bluebird --full-access list --status all --search 'API を実装する'` で既存のタスクを確認し、再試行による重複作成を避けます。
3. `./bluebird --full-access add 'API を実装する' --duration 25 --priority high --tags '仕事' --notes '先にテストを書く'` を実行し、返された `data.id` を保存します。
4. `./bluebird --full-access get ID` でタスクの全情報を取得します。
5. `./bluebird --full-access update ID --title 'API の実装と検証' --notes 'テスト完了'` で更新します。
6. `./bluebird --full-access timer start --task ID --duration 25` で集中を開始します。
7. `./bluebird --full-access timer status` でローカルのタイマー状態を、`./bluebird --full-access logs --task ID` で記録済みの集中時間を確認します。
8. `./bluebird --full-access timer finish` で途中終了し、それまでの進捗を保存します。`stop` は現在の進捗を破棄するため、同じ操作として扱わないでください。
9. `./bluebird --full-access timer reset` でタイマーを初期状態に戻し、`./bluebird --full-access complete ID` でタスクを完了にします。未完了へ戻す場合は `./bluebird --full-access reopen ID` を使います。
10. ユーザーが削除を求めた場合、`./bluebird --full-access delete ID --dry-run` で対象を確認してから `./bluebird --full-access delete ID --yes` を実行します。
11. `./bluebird --full-access get ID` で最終状態を確認します。削除はアプリの論理削除に従い、データベースからの完全消去は行いません。

`open` と `focus` の `dispatched` は、OS が要求を受け付けたことだけを示します。`focus` はタイマー画面を開く操作で、開始には `timer start` が必要です。
タスクの変更後はローカルデータベースを読み戻します。`UNVERIFIED` は操作済みの可能性があることを示すため、再試行前に `list/get/timer status` で確認してください。

UI 操作には、ログイン済みでロックされておらず、Bluebird のウィンドウを表示できる macOS デスクトップが必要です。更新は順番に実行し、実行中は手動でアプリを編集しないでください。
タスクの内容をシェルコードとして扱わないでください。エージェントは、ユーザーのタイトルをシェルコマンド文字列に埋め込まず、subprocess の引数配列を使います。
集中時間を明示する場合は 5 分の倍数を指定します。タスクの見積もり時間にはこの制限はありません。`timer status` は実行中、終了済み、休憩中を区別します。終了後に次のセッションを始める前に `timer reset` を実行します。
ローカルでの成功は、iCloud の同期や Watch への通知配信を保証しません。

## Python の呼び出し例

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

task = run('add', '提案書を書く', '--duration', '25')
run('update', task['id'], '--notes', '構成を追加した')
run('complete', task['id'])
```

## Codex スキルの導入

リポジトリには `skills/bluebird/SKILL.md` が含まれています。`skills/bluebird` ディレクトリ全体を `~/.codex/skills/bluebird` にコピーし、リポジトリの絶対パスをエージェントに伝えるか、CLI を PATH に追加します。
Claude Code など、ターミナルツールを利用できる他のエージェントも、MCP サーバーなしで同じ JSON コマンドを使えます。
