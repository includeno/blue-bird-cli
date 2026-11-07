# 系统配置与首次运行

[文档目录](README.md) · [English](../en/setup.md) | 简体中文 | [日本語](../ja/setup.md)

支持目标：macOS 15+、Python 3.9+、Bluebird 3.14.1。架构与验证边界见[兼容范围](compatibility.md)，诊断时运行 `bluebird --version`。

下文系统初始化命令使用 `--full-access`。交给 Agent 前，运行 `bluebird start web` 配置可用 CLI 功能，并绑定至少一个标签，详见[授权说明](authorization.md)。CLI code 与 macOS 辅助功能是两层权限。未选择模式、无效 code 或功能未授权均返回退出码 3。

按顺序完成：准备 Bluebird 和开发工具 → 安装 CLI → 编译 helper → 授予辅助功能权限 → 在实际使用环境中运行 `doctor`。`setup` 只编译程序，不会替你打开系统权限；`doctor` 的 `data.ready=true` 才是 UI 操作的就绪标志。

## 1. 准备运行环境

| 项目 | 要求与用途 |
|---|---|
| macOS 桌面 | 使用已登录、未锁屏的图形桌面，UI 操作会把 Bluebird 切到前台 |
| Bluebird | 安装 macOS App，至少手动启动一次并完成首次使用流程；CLI 读取当前 macOS 用户的数据 |
| Python | 3.9 或更新版本，用于运行 CLI |
| Xcode Command Line Tools | 提供 `swiftc`，用于编译原生辅助程序 |
| 辅助功能权限 | 编辑、完成、恢复、删除及计时控制所需 |

当前真实 App 验证版本为 Bluebird 3.14.1 / build 437，详细范围见[验证记录](verification.md)。先保存或取消 Bluebird 中尚未提交的编辑器，配置时保持主窗口可见。

在终端检查依赖：

```sh
python3 --version
xcode-select -p
xcrun --find swiftc
swiftc --version
```

如果找不到 Python，可从 [Python 官方 macOS 下载页](https://www.python.org/downloads/macos/)安装，重新打开终端后检查版本。
如果尚未安装开发工具，执行下面的命令，并完成系统安装窗口中的步骤，安装完成后再检查 `swiftc`。参见 [Apple 的命令行工具安装说明](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools)。

```sh
xcode-select --install
```

## 2. 安装 CLI，并确定以后使用的命令路径

以下命令在仓库根目录运行。把示例路径替换为你实际下载或克隆的目录。使用虚拟环境可避免修改系统或包管理器维护的 Python 环境。

```sh
cd "/absolute/path/to/blue-bird-cli"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
bluebird capabilities
```

激活只对当前 shell 有效。以后打开新终端，可重新激活，或直接使用绝对路径：

```sh
/absolute/path/to/blue-bird-cli/.venv/bin/bluebird capabilities
```

Agent 也应使用这个绝对路径，不能假定它继承了你终端中的虚拟环境。若只想从源码运行，可在仓库根目录使用 `./bluebird`，把下文命令中的 `bluebird` 换成 `./bluebird` 即可；此方式仍需要 Python 和 Swift 编译器。

## 3. 编译原生 helper

```sh
bluebird --full-access setup
```

首次编译可能需要几分钟。输出示例：

```json
{"ok":true,"data":{"helper":"/Users/your-name/Library/Caches/bluebird-cli/bluebird-ax","trusted":false}}
```

`ok=true` 表示编译完成；`trusted=false` 表示当前执行环境尚未获得辅助功能信任，不是编译失败。保留 `data.helper` 返回的实际路径，下一步需要时使用。默认路径为 `~/Library/Caches/bluebird-cli/bluebird-ax`；旧版仓库中的 `.build/bluebird-ax` 已不是默认位置。

## 4. 在 macOS 中授权实际启动 CLI 的应用

进入 **苹果菜单 → 系统设置 → 隐私与安全性 → 辅助功能**，开启启动 CLI 的应用。未列出时点添加按钮，选择对应 App；如系统要求，完成本机身份验证。设置入口见 [Apple 辅助功能授权说明](https://support.apple.com/en-ie/guide/mac-help/mh43185/27/mac/27)。

| 从哪里执行 CLI | 优先检查的授权对象 |
|---|---|
| Terminal 或 iTerm | 实际使用的终端 App |
| 编辑器的集成终端 | 承载该终端的编辑器 App |
| Codex 或其他桌面 Agent | macOS 实际显示的启动应用；本项目测试机曾显示为 ChatGPT，不能把这一名称当作所有机器的固定值 |

macOS 可能把权限归给启动者。**只添加 `bluebird-ax`，不代表 Terminal 或 Agent 已获得权限。** 如果系统仍要求 helper 授权，在同一列表中添加 `setup` 返回的程序：在文件选择窗口按 **⌘⇧G**，粘贴实际的完整路径，添加后开启开关。

授权后，从原来的终端或 Agent 再运行检查。如果权限仍未生效，先保存工作，再退出并重新打开该启动应用后重试。不要通过 `sudo` 换成另一个用户运行 CLI；Bluebird 数据和权限均与当前用户环境相关。

## 5. 单独检查 Agent 的执行沙箱

系统辅助功能授权和 Agent 的命令执行沙箱是两回事。必须从以后实际运行 CLI 的地方验证权限，而不仅是在 Terminal 中验证一次。

如果普通终端中的 `doctor` 显示 `trusted=true`，但 Agent 内显示 `trusted=false` 或系统访问被阻止：

1. 确认两边使用同一 CLI 路径、macOS 用户和 `BLUEBIRD_CLI_HOME` 配置。
2. 确认系统辅助功能列表中也已允许实际的 Agent 启动应用。
3. 使用该 Agent 正常提供的逐命令权限申请机制，允许需要的本地系统自动化访问；之后在该执行环境中重新运行 `doctor`。

Terminal 已获得的权限不会证明另一个宿主或沙箱也可操作 UI。SSH 或没有可交互桌面的后台进程也不能仅凭授权替代已登录、未锁屏的桌面。

## 6. 打开 App，确认就绪

```sh
bluebird --full-access open
bluebird --full-access doctor
bluebird locales
bluebird --full-access list
bluebird --full-access timer status
```

`open` 后等待 Bluebird 主窗口出现，再执行 `doctor`。首次运行可能需要在 App 内完成初始化。成功输出中的关键字段应类似下面的节选；`locale` 应与你实际使用的界面语言一致：

```json
{"ok":true,"data":{"macos":true,"helper":true,"trusted":true,"locale":"zh-Hans","ready":true}}
```

| 字段 | 如何判断 |
|---|---|
| `ok` / 进程退出码 | 表示诊断命令是否完成，不能单独判断 UI 是否就绪 |
| `data.helper` | 是否找到 helper；旧 helper 仍可能在 `adapter_error` 中报版本不符 |
| `data.trusted` | 当前执行上下文是否获得辅助功能信任 |
| `data.database_error` | 若出现，先处理本地数据库读取或结构问题 |
| `data.adapter_error` | 若出现，处理 App 未启动、helper 版本或语言识别问题 |
| `data.ready` | 必须为 `true`，然后再执行 UI 修改 |

`locales` 只列举资源，不代表 UI 授权通过。默认语言是自动识别；只有确实需要消除歧义、且 App 当前使用对应语言时，才指定全局参数，例如 `bluebird --full-access --locale ja doctor`。这不会把 App 切换为日文。

以上检查不创建任务，也不开始计时。确认就绪后，按照 [Agent 调用流程](agent-workflow.md)执行任务和计时操作。首次写入验证可使用一个名称唯一的临时任务，并在完成后按返回的精确 ID 删除；不要拿原有任务做配置测试。

## 7. 路径、升级和多进程配置

| 内容 | 默认位置或规则 |
|---|---|
| CLI（上述虚拟环境安装） | 仓库下 `.venv/bin/bluebird` |
| 原生 helper | `~/Library/Caches/bluebird-cli/bluebird-ax` |
| 源码摘要、编译缓存和修改锁 | 同一 `~/Library/Caches/bluebird-cli` 目录 |
| Bluebird 数据库 | `~/Library/Group Containers/group.com.cub-and-pup.Bluebird/Bluebird.sqlite`，CLI 只读 |

CLI 升级后，在同一虚拟环境重新安装并编译：

```sh
python -m pip install .
bluebird --full-access setup
bluebird --full-access doctor
```

只有需要自定义缓存目录时才设置 `BLUEBIRD_CLI_HOME`。更改后需在同一环境再次运行 `setup`，并以新的 `data.helper` 路径检查权限。控制同一个 App 的终端和 Agent 必须使用相同缓存目录，才能共享修改锁；在一个终端里设置环境变量不会自动配置另一个 Agent。

`--db PATH` 仅用于读取快照或测试库，不能把修改命令重定向到任意数据库，也不是解决权限问题的办法。

## 常见问题

| 现象 | 处理方式 |
|---|---|
| `bluebird: command not found` | 激活 `.venv` 或使用其绝对命令路径；源码方式使用 `./bluebird` |
| pip 报 `externally-managed-environment` | 使用第 2 步的虚拟环境安装 |
| 找不到 `swiftc`，或 developer directory 无效 | 完成 Command Line Tools 安装，用 `xcode-select -p` 和 `xcrun --find swiftc` 检查开发工具路径 |
| `Accessibility helper missing` | 在当前 CLI 和缓存配置下运行 `setup` |
| `Native helper is outdated` | CLI 升级后重新运行 `setup`，不要混用不同副本的旧 helper |
| `ACCESSIBILITY_REQUIRED` / `trusted=false` | 按第 4、5 步检查启动应用、helper 路径以及实际执行沙箱 |
| `Bluebird is not running` | 执行 `open`，等待主窗口出现，再运行 `doctor` |
| `database_error` / 无法打开数据库 | 确认 Bluebird 在同一 macOS 用户下完成初始化；检查错误中的路径和文件访问限制。辅助功能授权不等于文件读取授权，不要创建空数据库替代 |
| `Unsupported Bluebird database schema` | 当前 App 数据结构与适配器不兼容，需要更新适配器；不要修改原数据库来绕过校验 |
| `LOCALE_UNDETECTED` / `LOCALE_MISMATCH` / `LOCALE_AMBIGUOUS` | 打开主窗口，核对 `locales` 和实际 UI 语言；必要时指定一致的 `--locale` |
| 已有编辑器或弹窗 | 手动保存或取消，再重试操作 |
| `Task is not exposed` | 在 Bluebird 中滚动到目标任务；读取命令不受可见范围限制 |
| `UNVERIFIED` | 动作可能已发生；先 `get/list/timer status` 回读，尤其不要盲目再次创建 |
