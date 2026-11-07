# Agent 调用约定

[文档目录](README.md) · [English](../en/agent-workflow.md) | 简体中文 | [日本語](../ja/agent-workflow.md)

下文任务闭环和 Python 示例使用明确的所有者权限。受限 Agent 应通过环境变量 `BLUEBIRD_CODE` 传入授权并移除 `--full-access`，先运行 `bluebird auth-status` 查看功能与标签。仅授予所需功能；创建任务必须使用现有授权标签。被拒绝时不得自行提升为 full-access，详见[授权说明](authorization.md)。

首次安装和授权请先完成[系统配置与首次运行](setup.md)，再从 Agent 实际执行命令的环境中检查 `doctor`。

通过 `python3 -m pip install .` 安装 `bluebird`，或在仓库目录运行 `./bluebird`。Python 3.9+，无第三方运行依赖。
执行 `./bluebird capabilities` 获取支持的操作，`./bluebird --full-access doctor` 检查环境。

所有业务命令 stdout 输出一行 JSON：

```json
{"ok":true,"data":{"id":"7705161843629854611","title":"实现 API"}}
```

失败时 stdout 仍然是 JSON，进程非零退出：

```json
{"ok":false,"error":{"code":"invalid_argument","message":"delete requires --yes and an exact task ID"}}
```

退出码：0 成功、1 执行/权限/验证错误、2 参数错误、3 CLI 授权拒绝。`--help` 是供人阅读的文本。
`doctor` 本身能成功执行不代表环境就绪，须检查 `data.ready`。
`bluebird locales` 列出已安装 App 的语言资源；默认自动检测 UI 语言。可用全局参数 `--locale ja` 消除歧义，它不改变 App 语言。语言不匹配时应检查当前界面，不能靠反复修改翻译字符串重试。
`setup` 的 helper 默认位于 `~/Library/Caches/bluebird-cli`；升级后重建。所有 agent 使用相同缓存目录，共享修改锁。
ID 必须始终作为字符串保存（Bluebird 的 64 位整数超过 JavaScript 安全整数范围）。

## 一次完整任务流程

1. `./bluebird --full-access doctor`：检查 `ready`。未编译时先 `./bluebird --full-access setup`。
2. `./bluebird --full-access list --status all --search '实现 API'`：确认是否已有目标，避免重试创建重复任务。
3. `./bluebird --full-access add '实现 API' --duration 25 --priority high --tags '工作' --notes '先写测试'`：保存返回的 `data.id`。
4. `./bluebird --full-access get ID`：读取完整任务。
5. `./bluebird --full-access update ID --title '实现并验证 API' --notes '测试已通过'`。
6. `./bluebird --full-access timer start --task ID --duration 25`。
7. `./bluebird --full-access timer status`：读取本地计时字段；`./bluebird --full-access logs --task ID` 读取已记录时长。
8. `./bluebird --full-access timer finish`：提前结束专注并保留进度；`stop` 放弃当前进度，二者不要混用。
9. `./bluebird --full-access timer reset` 返回初始计时状态，再 `./bluebird --full-access complete ID`：完成任务；需要恢复待办时 `./bluebird --full-access reopen ID`。
10. 用户要求删除时 `./bluebird --full-access delete ID --dry-run` 查看目标，再 `./bluebird --full-access delete ID --yes`。
11. `./bluebird --full-access get ID` 确认最终状态。删除保留 App 的软删除语义，不执行数据库清理。

`open`、`focus` 的 `dispatched` 只代表系统接受打开请求。`focus` 只打开计时界面，开始必须使用 `timer start`。
任务变更会回读本地数据库；出现 `UNVERIFIED` 表示动作可能已经发生，不要盲目重试，应先 `list/get/timer status`。

UI 操作要求 macOS 已登录、未锁屏，Bluebird 可显示窗口。串行调用修改命令，期间不要同时手动编辑 App。
CLI 不把任务内容当作 shell 代码；agent 使用 subprocess 参数数组，避免把用户提供的标题拼接成 shell 命令。
指定专注时长必须是 5 分钟的倍数（任务预计时长没有这一限制）。`timer status` 区分运行、已完成与休息，完成后用 `timer reset` 再开始下一轮。
本地成功并不代表 iCloud 已同步或 Watch 已收到通知。

## Python 调用示例

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

task = run('add', '写方案', '--duration', '25')
run('update', task['id'], '--notes', '已补充提纲')
run('complete', task['id'])
```

## 安装 Codex 技能

仓库提供 `skills/bluebird/SKILL.md`。将整个 `skills/bluebird` 目录复制到 `~/.codex/skills/bluebird`，并让 agent 知道仓库的绝对路径或把 CLI 加入 PATH。
其他支持终端工具的 agent（Claude Code 等）可直接使用同样的 JSON 命令，不需要 MCP 服务。
