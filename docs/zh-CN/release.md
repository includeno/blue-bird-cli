# 安装与发布流程

[文档首页](README.md) · [English](../en/release.md) | 简体中文 | [日本語](../ja/release.md)

## 安装 GitHub Release

从 [Releases](https://github.com/includeno/blue-bird-cli/releases) 下载 wheel，在虚拟环境执行 `python -m pip install /path/to/blue_bird_cli-0.3.0-py3-none-any.whl`；也可以解压源码包，进入目录执行 `python -m pip install .`。用 `bluebird --version` 确认版本，然后完成[系统配置](setup.md)。发布包包含 Swift 源码和网页资源，辅助工具在你的 Mac 编译。使用 `shasum -a 256 FILE` 对照附件 `SHA256SUMS.txt` 检查下载文件。

## 维护者发布步骤

1. 更新唯一版本来源 `bluebird_cli.__version__` 和 `CHANGELOG.md`，同步中英日文档。
2. 使用干净的输出目录：`python -m pip install build twine`，然后执行 `python -m build`、`python -m twine check dist/*`、`python scripts/check_distribution.py dist`。最后一项检查必要文件，并在解压后的源码包中运行测试，避免仅在工作区通过却缺少发布文件。
3. 创建 PR，等待两个 Python 测试、Distribution、两个 macOS 架构检查全部通过。托管 macOS 检查证明安装与辅助工具编译，不证明真实 Bluebird 操作。
4. 合并审核后的代码，创建带注释的版本标签，例如 `git tag -a v0.3.0 -m 'Bluebird CLI 0.3.0'`，推送该标签。不要移动已发布标签。
5. Release 工作流核对标签和软件版本，构建与测试压缩包，在两种 macOS 架构编译安装后的辅助工具，再创建 GitHub Release，附 wheel、sdist、版本说明和校验和。它使用仓库工作流令牌，不需要额外的发布密钥。
6. 检查 Release 附件与工作流结果。修正已发布版本时提升版本号并创建新标签，不覆盖旧附件。

首次公开还需提交完整源码、开启仓库公开可见性、私密漏洞报告和主分支保护；保护应要求 CI 通过、禁止强推/删除并解决审核讨论。通过 Issue 模板提交脱敏问题。首版使用 GitHub 分发，PyPI 和 Homebrew 是独立渠道，不影响使用此版本。
