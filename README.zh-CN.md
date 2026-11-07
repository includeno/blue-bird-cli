# Bluebird CLI for macOS

[English](README.md) | 简体中文 | [日本語ドキュメント](docs/ja/README.md)

[兼容范围](docs/zh-CN/compatibility.md) · [版本安装](docs/zh-CN/release.md) · [版本记录](CHANGELOG.md) · [安全报告](docs/zh-CN/security.md)

## 授权模式与本机管理页

0.3 版的数据命令必须明确选择 `--full-access` 或授权 code。下文安装和完整操作示例使用所有者模式。给 Agent 分配受限权限时，运行：

```sh
bluebird start web
# 打开输出的专用 URL，选择功能和标签，生成并保存 code。
export BLUEBIRD_CODE='bb_替换为实际授权值'
bluebird auth-status
bluebird list
```

网页支持中文、英文、日文，提供创建、修改、撤销授权；可逐项设置查询、任务增删改及计时权限，支持分组全选、全部选择和清空。至少选择一项功能和一个标签。任务必须有标签，且全部标签均在授权范围内；勾选全部 14 项功能仍不获得管理权限。CLI 拒绝授权时返回退出码 **3**。关闭管理页服务后 code 仍可使用。完整流程见[授权 code 与 CLI 功能权限](docs/zh-CN/authorization.md)。

code 提供协作式 CLI 范围控制，不是 OS 沙箱：同账户下能任意执行命令的 Agent 仍能使用 full-access 或直接读取数据。

在终端及 Codex、Claude Code 等 agent 中操作已安装的 **Bluebird 专注计时 App**。
提供任务增删改查、完成/恢复待办、专注计时控制和 JSON 结果。
Python 标准库 + 一个 Swift 辅助功能程序，没有第三方运行依赖，也不直接改写 Bluebird 数据库。

## 安装与权限

首次使用请按[系统配置引导](docs/zh-CN/setup.md)逐步完成依赖安装、辅助功能授权、Agent 沙箱检查和就绪验证；其中包含常见错误的处理方法。

需要 macOS、Bluebird、Python 3.9+ 和 Xcode Command Line Tools（`swiftc`）。
可安装为独立命令，也可在仓库内直接使用 `./bluebird`：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
bluebird --full-access setup
bluebird --full-access open
bluebird --full-access doctor
```

开发时：

```sh
./bluebird --full-access setup
./bluebird --full-access open
./bluebird --full-access doctor
```

`setup` 编译 `~/Library/Caches/bluebird-cli/bluebird-ax`；首次编译可能需要几分钟。
在「系统设置 → 隐私与安全性 → 辅助功能」开启**启动 CLI 的应用**：

- Codex 或其他桌面 Agent：以 macOS 显示的实际启动应用为准；本项目测试机曾显示为 **ChatGPT**，并非所有环境都使用这个名称。
- 终端运行：Terminal、iTerm 或其他实际使用的终端。
- 系统另外要求时，添加 `setup` 返回的 helper 路径。

macOS 会把权限归给启动者，仅授权辅助程序可能不够。`doctor` 返回 `data.ready: true` 才表示 UI 修改环境已就绪。
Agent 的 shell 沙箱仍可能限制系统自动化；已授权但沙箱内 `trusted: false` 时，应通过 agent 的正常权限机制在沙箱外运行，不能靠重复开关系统权限解决。

从其他目录使用，可将当前仓库加入 PATH（不会自动修改 shell 配置）：

```sh
export PATH="$PWD:$PATH"
bluebird capabilities
```

## 任务增删改查

```sh
./bluebird --full-access add '写项目方案' --duration 25 --priority high --tags '工作,写作' --notes '先整理提纲'
./bluebird --full-access list
./bluebird --full-access list --status all --search '项目'
./bluebird --full-access get ID
./bluebird --full-access update ID --title '完善项目方案' --notes '补上预算' --duration 30 --priority medium --tags '工作'
./bluebird --full-access complete ID
./bluebird --full-access reopen ID
./bluebird --full-access delete ID --dry-run
./bluebird --full-access delete ID --yes
```

把 `ID` 替换成 `add/list/get` 返回的 `data.id`，始终保留为字符串。
`list` 默认只查未完成任务；`--status` 支持 `active`、`completed`、`deleted`、`all`。
读取不限于屏幕上可见的任务。修改按 ID 获取任务，再通过当前 UI 中可唯一辨认的标题定位。
同名或标签文本无法区分的任务会明确报错，不会猜测目标。

`update` 只修改传入的字段，支持新标签自动创建。清空字段：

```sh
./bluebird --full-access update ID --notes '' --tags '' --duration 0 --priority none
```

创建的时长是正整数分钟；优先级为 `low`、`medium`、`high`。
删除经由 App 执行软删除，不清空回收数据。每次任务变更后回读本地存储，确认后才返回成功。

## 专注闭环

```sh
./bluebird --full-access timer start --task ID --duration 25
./bluebird --full-access timer status
./bluebird --full-access timer finish
./bluebird --full-access logs --task ID
./bluebird --full-access timer reset
./bluebird --full-access complete ID
```

- `start` 真正开始计时；指定时长按 App 辅助功能的 **5 分钟步长**调节，CLI 接受 5–600 的 5 倍数，若超出 App 实际范围会报错而不启动。省略 `--duration` 使用 App 为该任务选中的时长（可能是正计时）。
- `finish` 提前结束并由 App 记录已有进度；不足一分钟的记录遵循 App 自身取整规则。
- `stop` **放弃当前进度**，与 `finish` 不同。
- `reset` 从完成/休息阶段返回初始状态；正在专注时要求先明确选择 `finish` 或 `stop`。
- `status` 返回 `idle`、`focusing`、`finished`、`break`、`break_finished`，以及任务 ID、时长、剩余秒数和原始本地计时字段。
- 不覆盖已经运行的专注或休息会话。

`./bluebird --full-access open` 打开应用；`./bluebird --full-access focus` **仅打开**计时界面。二者的 `dispatched` 只表示系统已接受打开请求。

## Agent 接入

业务命令默认输出一行 JSON，不需要 `--json`：

```json
{"ok":true,"data":{"id":"7705161843629854611","title":"写项目方案"}}
```

退出码 `0` 成功，`1` 执行/权限/结果验证失败，`2` 参数错误，`3` CLI 授权拒绝。失败时输出 `{"ok":false,"error":{"code":"…","message":"…"}}`。
`--help` 是文本；`doctor` 成功退出后仍须检查 `data.ready`。
任务变更与计时命令支持 `--dry-run`；删除需要精确 ID 和 `--yes`。
同一用户缓存目录中的修改命令用进程锁串行执行，跨仓库和安装副本共用。

- [完整 agent 流程和 Python 示例](docs/zh-CN/agent-workflow.md)
- [可安装到 Codex 的技能](skills/bluebird/SKILL.md)
- `./bluebird capabilities`：能力、字段、限制与输出约定。
- `./bluebird --full-access ui`：诊断当前辅助功能控件。

## 实现与边界

创建使用 [Bluebird 官方 URL Scheme](https://bluebird.app/url-scheme)；编辑、完成、恢复、删除和计时使用 macOS Accessibility，查询使用只读 SQLite 连接。
语言适配直接读取已安装 Bluebird 的语言资源，当前 **3.14.1 / build 437** 提供 26 种语言/地区变体。优先使用稳定控件 ID，其次用资源键解析文案；任务文本匹配兼容 Unicode、RTL 标记及不同标点。

```sh
bluebird locales
bluebird --full-access doctor
bluebird --full-access --locale ja update ID --notes '確認済み'
```

默认 `--locale auto` 从实际控件识别语言；显式选项用于消除地区变体歧义，不会修改 App 的语言设置。语言不匹配或无法可靠识别时，停止操作。26 种资源通过选择器契约测试；实际界面验证范围以 [验证记录](docs/zh-CN/verification.md) 为准。

架构及贡献方式见 [architecture.md](docs/zh-CN/architecture.md) 和 [CONTRIBUTING.md](CONTRIBUTING.md)。升级 CLI 后重新执行 `setup`；原生源码摘要不符时会拒绝运行旧 helper。`BLUEBIRD_CLI_HOME` 可指定缓存目录；控制同一个 App 的进程应使用同一目录，以共享修改锁。

- UI 操作需要已登录、未锁屏的桌面，会把 Bluebird 切到前台。若有未保存的编辑器/弹窗，先保存或取消。不要让人和多个独立 CLI 副本同时编辑窗口。
- 日期、重复规则可读取，本版未提供它们的编辑参数；标签操作针对任务关联，不提供独立标签管理命令。
- 任务列表的 UI 虚拟化可能使屏幕外任务暂时无法操作；此时会报错，滚动到目标后重试。查询不受此限制。
- `UNVERIFIED` 表示动作可能已经发生，先 `get/list/timer status`，不要盲目再次创建。UI 更新不是跨多个字段的数据库事务，失败后也应回读。
- 本地成功不代表 iCloud 已同步或 iPhone/Watch 已收到通知。CLI 不修改通知设置。
- `--db PATH` 用于读取已有快照/测试库，只读且拒绝用该路径执行修改。

## 验证

```sh
python3 -B -m unittest discover -s tests -v
```

自动测试使用临时数据库与 mock，不修改 App。实际桌面验证记录见 [verification.md](docs/zh-CN/verification.md)。
