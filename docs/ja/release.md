# インストールとリリース手順

[ドキュメント](README.md) · [English](../en/release.md) | [简体中文](../zh-CN/release.md) | 日本語

## GitHub Release のインストール

[Releases](https://github.com/includeno/blue-bird-cli/releases) から wheel を取得し、仮想環境で `python -m pip install /path/to/blue_bird_cli-0.3.0-py3-none-any.whl` を実行します。ソースアーカイブを展開して、そのディレクトリで `python -m pip install .` でもインストールできます。`bluebird --version` を確認し、[システム設定](setup.md)を完了してください。Swift ソースと Web リソースを同梱し、ヘルパーは手元の Mac でコンパイルします。`shasum -a 256 FILE` の結果を添付の `SHA256SUMS.txt` と比較できます。

## メンテナーの手順

1. 唯一の版情報 `bluebird_cli.__version__` と `CHANGELOG.md` を更新し、三言語文書を揃えます。
2. 空の出力先で `python -m pip install build twine`、`python -m build`、`python -m twine check dist/*`、`python scripts/check_distribution.py dist` を実行します。最後のコマンドは同梱ファイルと展開したソースのテストを確認します。
3. PR を作成し、二つの Python、Distribution、二つの macOS アーキテクチャの必須チェックを待ちます。ホストランナーはインストールとコンパイルを検証し、実際の Bluebird 操作は検証しません。
4. レビュー後の変更をマージし、`git tag -a v0.3.0 -m 'Bluebird CLI 0.3.0'` のような注釈付きタグを作成して、そのタグを push します。公開済みタグは移動しません。
5. Release ワークフローはタグと版を照合し、ビルド・アーカイブテスト・両 macOS アーキテクチャでのコンパイル後に、wheel、sdist、リリースノート、チェックサムを GitHub Release に添付します。リポジトリのワークフロートークンを使い、追加の公開シークレットは不要です。
6. 添付とワークフロー結果を確認します。公開後の修正は版を上げて新しいタグを作り、既存成果物を上書きしません。

初回公開では完全なソースのコミット、公開設定、非公開脆弱性報告、必須 CI・強制 push/削除禁止・議論の解決を求めるブランチ保護を設定します。Issue テンプレートでは秘匿情報を除いてください。初版は GitHub で配布し、PyPI と Homebrew は別の配布経路です。
