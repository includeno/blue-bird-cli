# システム設定と初回起動

[ドキュメント一覧](README.md) · [English](../en/setup.md) | [简体中文](../zh-CN/setup.md) | 日本語

対象は macOS 15+、Python 3.9+、Bluebird 3.14.1 です。アーキテクチャと検証の限界は[互換性](compatibility.md)を参照し、診断時は `bluebird --version` を使用してください。

以下のシステム設定には `--full-access` を使用します。エージェントに委任する前に `bluebird start web` で CLI 機能と一つ以上のタグを設定してください。[認証の説明](authorization.md)を参照してください。CLI コードと macOS アクセシビリティは別の権限です。モード未指定、無効なコード、機能の拒否は終了コード 3 を返します。

Bluebird と開発ツールの準備 → CLI のインストール → helper のコンパイル → アクセシビリティの許可 → 実際に使う実行環境での `doctor` 確認、の順に進めます。`setup` はコンパイルだけを行い、システムの権限は有効にしません。UI 操作の準備完了は `doctor` の `data.ready=true` で判断します。

## 1. 実行環境を準備する

| 項目 | 要件と用途 |
|---|---|
| macOS デスクトップ | ログイン済みでロックされていない GUI 環境。UI 操作時は Bluebird が前面に移動します |
| Bluebird | macOS アプリをインストールし、手動で一度起動して初期設定を完了します。CLI は現在の macOS ユーザーのデータを読み取ります |
| Python | CLI 実行用の 3.9 以降のバージョン |
| Xcode Command Line Tools | ネイティブ helper のコンパイルに使う `swiftc` を提供します |
| アクセシビリティの許可 | 編集、完了、未完了への復帰、削除、タイマー操作に必要です |

実際のアプリで確認済みのバージョンは Bluebird 3.14.1 / build 437 です。範囲は[検証記録](verification.md)を参照してください。未保存の編集画面を保存またはキャンセルし、設定中は Bluebird のメインウィンドウを表示しておきます。

ターミナルで依存ツールを確認します。

```sh
python3 --version
xcode-select -p
xcrun --find swiftc
swiftc --version
```

Python がなければ [Python 公式の macOS ダウンロードページ](https://www.python.org/downloads/macos/)からインストールし、ターミナルを開き直してバージョンを確認します。
開発ツールが未導入なら、次のコマンドを実行し、システムのインストール画面で手続きを完了してから `swiftc` を再確認します。[Apple の Command Line Tools 導入手順](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools)も参照できます。

```sh
xcode-select --install
```

## 2. CLI をインストールし、実行パスを決める

以下はリポジトリのルートで実行します。パスはダウンロードまたはクローンした実際の場所に置き換えてください。仮想環境を使うと、OS やパッケージマネージャーが管理する Python 環境を変更せずにインストールできます。

```sh
cd "/absolute/path/to/blue-bird-cli"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
bluebird capabilities
```

仮想環境の有効化は現在のシェルだけに適用されます。新しいターミナルでは再度有効化するか、実行ファイルの絶対パスを使います。

```sh
/absolute/path/to/blue-bird-cli/.venv/bin/bluebird capabilities
```

エージェントにもこの絶対パスを指定してください。ターミナルの仮想環境を自動で引き継ぐとは限りません。ソースから直接使う場合は、リポジトリのルートで `./bluebird` を実行し、以下の `bluebird` を `./bluebird` に読み替えます。この方法でも Python と Swift コンパイラーは必要です。

## 3. ネイティブ helper をコンパイルする

```sh
bluebird --full-access setup
```

初回のコンパイルには数分かかることがあります。出力例：

```json
{"ok":true,"data":{"helper":"/Users/your-name/Library/Caches/bluebird-cli/bluebird-ax","trusted":false}}
```

`ok=true` はコンパイルの完了を示します。`trusted=false` は現在の実行環境にアクセシビリティの許可がまだないことを示し、コンパイル失敗ではありません。次の手順で必要になった場合に備えて、実際の `data.helper` のパスを控えます。既定のパスは `~/Library/Caches/bluebird-cli/bluebird-ax` です。旧版の `.build/bluebird-ax` は現在の既定の保存先ではありません。

## 4. CLI を起動するアプリを macOS で許可する

**アップルメニュー → システム設定 → プライバシーとセキュリティ → アクセシビリティ**を開き、CLI を起動するアプリを有効にします。一覧になければ追加ボタンから該当するアプリを選び、macOS が求めた場合は認証します。設定場所は [Apple のアクセシビリティ許可の説明](https://support.apple.com/en-ie/guide/mac-help/mh43185/27/mac/27)を参照してください。

| CLI の実行場所 | 最初に許可を確認するアプリ |
|---|---|
| Terminal、iTerm | 実際に使用するターミナルアプリ |
| エディター内のターミナル | そのターミナルを内蔵するエディター |
| Codex などのデスクトップエージェント | macOS に表示される実際の起動元アプリ。検証機では ChatGPT と表示されましたが、すべての環境で同じ名前とは限りません |

macOS は権限を起動元に関連付ける場合があります。**`bluebird-ax` だけを追加しても、Terminal やエージェントの許可が完了したことにはなりません。** helper の許可も要求された場合は、`setup` が返した実行ファイルを同じ一覧に追加します。ファイル選択画面で **⌘⇧G** を押して実際のフルパスを貼り付け、追加後にスイッチを有効にします。

元のターミナルまたはエージェントから再確認します。許可が反映されなければ、作業を保存して起動元アプリを終了・再起動してから確認してください。`sudo` で別ユーザーとして実行しないでください。Bluebird のデータと権限は現在のユーザー環境に対応しています。

## 5. エージェントの実行サンドボックスを別途確認する

システムのアクセシビリティ権限と、エージェントのコマンド実行サンドボックスは別です。Terminal で一度確認するだけでなく、実際に CLI を使う環境から検証してください。

通常のターミナルでは `doctor` が `trusted=true` を返すのに、エージェント内では `trusted=false` やシステムアクセス拒否になる場合：

1. 両方の CLI パス、macOS ユーザー、`BLUEBIRD_CLI_HOME` 設定が同じか確認します。
2. エージェントの実際の起動元アプリも、macOS のアクセシビリティ設定で許可されているか確認します。
3. エージェントが通常提供するコマンド単位の承認手順で、必要なローカルのシステム自動操作を許可し、その実行環境で `doctor` を再実行します。

Terminal の許可だけでは、別の起動元やサンドボックスから UI を操作できるとは判断できません。SSH や対話可能なデスクトップのないバックグラウンド処理も、権限だけでログイン済み・ロック解除済みのデスクトップを代替することはできません。

## 6. アプリを開き、準備完了を確認する

```sh
bluebird --full-access open
bluebird --full-access doctor
bluebird locales
bluebird --full-access list
bluebird --full-access timer status
```

`open` 後、Bluebird のメインウィンドウが表示されるのを待ってから `doctor` を実行します。初回はアプリ内で初期設定が必要な場合があります。主要なフィールドは次の抜粋のようになります。`locale` は実際の UI 言語と一致する必要があります。

```json
{"ok":true,"data":{"macos":true,"helper":true,"trusted":true,"locale":"ja","ready":true}}
```

| フィールド | 判断方法 |
|---|---|
| `ok` / 終了コード | 診断コマンドが完了したかどうか。これだけで UI の準備完了とは判断できません |
| `data.helper` | helper が存在するか。古い helper は `adapter_error` にバージョン不一致を出す場合があります |
| `data.trusted` | 現在の実行コンテキストにアクセシビリティの許可があるか |
| `data.database_error` | 存在する場合はローカル DB の読み取りやスキーマの問題を解決します |
| `data.adapter_error` | 存在する場合はアプリ起動、helper の版、言語判定の問題を解決します |
| `data.ready` | UI を変更する前に `true` である必要があります |

`locales` はリソースを列挙するだけで、UI 操作の許可を確認するものではありません。言語は既定で自動判定されます。候補の曖昧さを解消する必要があり、実際にその言語を使用している場合だけ、例えば `bluebird --full-access --locale ja doctor` のようにグローバルオプションを指定します。この指定でアプリが日本語に切り替わるわけではありません。

ここまでの確認ではタスクの作成やタイマーの開始は行いません。準備完了後は[エージェント操作手順](agent-workflow.md)に従って操作できます。初めて書き込みを確認する際は、一意な名前の一時タスクを使い、終了後に返された正確な ID で削除してください。既存のタスクを設定確認用に使わないでください。

## 7. パス、アップグレード、複数プロセスの設定

| 項目 | 既定の場所またはルール |
|---|---|
| 上記の仮想環境にインストールした CLI | リポジトリ内の `.venv/bin/bluebird` |
| ネイティブ helper | `~/Library/Caches/bluebird-cli/bluebird-ax` |
| ソースダイジェスト、コンパイルキャッシュ、更新ロック | 同じ `~/Library/Caches/bluebird-cli` ディレクトリ |
| Bluebird データベース | `~/Library/Group Containers/group.com.cub-and-pup.Bluebird/Bluebird.sqlite`。CLI は読み取り専用で使用します |

CLI のアップグレード後は、同じ仮想環境で再インストールとコンパイルを行います。

```sh
python -m pip install .
bluebird --full-access setup
bluebird --full-access doctor
```

独自のキャッシュディレクトリが必要な場合だけ `BLUEBIRD_CLI_HOME` を設定します。変更後は同じ環境で `setup` を再実行し、新しい `data.helper` のパスで権限を確認してください。同じアプリを操作するターミナルとエージェントは、更新ロックを共有するため同じキャッシュディレクトリを使う必要があります。ターミナルで環境変数を設定しても、別のエージェントには自動適用されません。

`--db PATH` はスナップショットやテスト用 DB の読み取り専用です。任意の DB に更新を振り向ける機能ではなく、権限の問題を解決するものでもありません。

## よくある問題

| 症状 | 対処 |
|---|---|
| `bluebird: command not found` | `.venv` を有効化するか実行ファイルの絶対パスを使います。ソース実行では `./bluebird` を使います |
| pip の `externally-managed-environment` | 手順 2 の仮想環境にインストールします |
| `swiftc` がない、または developer directory が無効 | Command Line Tools の導入を完了し、`xcode-select -p` と `xcrun --find swiftc` でパスを確認します |
| `Accessibility helper missing` | 現在の CLI とキャッシュ設定で `setup` を実行します |
| `Native helper is outdated` | 更新後に `setup` を再実行し、別のチェックアウトの古い helper と混在させないでください |
| `ACCESSIBILITY_REQUIRED` / `trusted=false` | 手順 4、5 に従い起動元アプリ、helper のパス、実行サンドボックスを確認します |
| `Bluebird is not running` | `open` 後にメインウィンドウを待ち、`doctor` を実行します |
| `database_error` / DB を開けない | 同じ macOS ユーザーで初期設定済みか確認し、エラーのパスとファイルアクセス制限を調べます。アクセシビリティとファイル読み取りの権限は別です。代わりに空の DB を作成しないでください |
| `Unsupported Bluebird database schema` | アプリの構造にアダプターが対応していません。元の DB を変更して検証を回避せず、アダプターを更新します |
| `LOCALE_UNDETECTED` / `LOCALE_MISMATCH` / `LOCALE_AMBIGUOUS` | メイン画面を開き、`locales` と実際の言語を確認し、必要なら一致する `--locale` を指定します |
| 編集画面やダイアログが開いている | 手動で保存またはキャンセルしてから再試行します |
| `Task is not exposed` | Bluebird で対象タスクまでスクロールします。読み取りは表示範囲に制限されません |
| `UNVERIFIED` | 操作済みの可能性があります。特に作成を再試行する前に `get/list/timer status` で読み直します |
