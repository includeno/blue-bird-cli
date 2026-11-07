# 授权 code 与 CLI 功能权限

[文档首页](README.md) · [English](../en/authorization.md) | 简体中文 | [日本語](../ja/authorization.md)

所有数据命令都必须明确选择模式：本机所有者使用 `--full-access`，受限 Agent 使用 `--code CODE` 或环境变量 `BLUEBIRD_CODE`。每个 code 同时限制 **可使用的 CLI 功能** 和 **允许访问的标签 ID**，两项检查均通过才能操作。它与 macOS 辅助功能授权是两回事，请先完成[系统配置](setup.md)。

## 在本机管理页创建授权

```sh
bluebird start web
# 也可以指定端口；0 表示自动选择空闲端口。
bluebird start web --port 0
```

`start web` 是本机所有者管理入口，不需要 `--full-access`。它拒绝 `--code` 和非空的 `BLUEBIRD_CODE`；所有者启动前应先清除该环境变量。旧的顶层 `web` 命令已替换。

选择其中一条运行，打开 JSON 输出中的专用 URL。服务仅监听 `127.0.0.1`，默认端口 8765。管理期间保持进程运行，Ctrl+C 停止。`start web` 会输出启动记录和结束记录，区别于只返回一条结果的业务命令。

首页（`/`）展示概览与 CLI 使用指引。进入独立的“授权列表”（`/codes`），点击列表上方的 **新增授权** 打开弹窗。编辑权限也使用弹窗；取消、关闭按钮或 Escape 可放弃尚未保存的更改。

1. 页头可切换中文、英文、日文。
2. 输入便于识别的名称，例如“Codex · 工作”。
3. 至少选择一个现有 Bluebird 标签。缺少标签时先在 Bluebird 创建，再点击刷新。
4. 至少选择一项 CLI 功能。每组复选框支持整组全选或清空，部分选中时显示半选状态；“全部选择”和“全部清空”作用于全部功能。选择标签不会自动开放功能。
5. 点击生成并保存完整 code。完整值只显示一次；列表仅展示授权信息，无法找回原值。隐藏、切换页面、刷新或打开其他新增/编辑弹窗时会清除完整值。丢失后撤销旧 code，重新创建。
6. 点击“设置权限”修改原 code 的功能和标签；展开功能摘要可查看具体授权。“撤销”永久禁用 code。修改从下一条命令起生效，不回滚已经开始的界面操作。

专用 URL 中的是临时管理员会话令牌，不是 Agent code，请勿把管理地址交给 Agent。页面载入后会移除地址片段，仅在内存保存会话；刷新浏览器或新开标签页需要再次使用原 URL。页面内的“刷新”按钮保留会话。重启服务后，旧管理 URL 失效。

## 按功能细分授权

| 分组 | 可独立勾选的功能 |
|---|---|
| 查询功能 | `list` 查询列表、`get` 读取详情、`tags` 查询授权标签、`logs` 查询专注记录 |
| 任务增删改 | `add` 创建、`update` 修改、`complete` 完成、`reopen` 恢复、`delete` 删除 |
| 计时控制 | `timer.status` 查询、`timer.start` 开始、`timer.stop` 停止、`timer.finish` 完成本轮、`timer.reset` 重置 |

点号用于存储权限名称，实际命令仍是 `timer status` 等。功能互不隐式包含：只授予 `add` 不代表可用 `list`；可开始计时不代表可停止。只读 code 即使绑定正确标签，也不能修改任务。`--dry-run` 与实际执行需要相同权限。写操作会返回自身修改的任务或计时结果，不额外要求读取权限。

`capabilities`、`locales` 和帮助无需授权；有效 code 始终可以通过 `auth-status` 查看自身的功能和标签。`setup`、`doctor`、`ui`、`open`、`focus` 涉及系统配置或全局 App，只允许 full-access。full-access 拥有所有功能及管理权限；code 勾选全部 14 项功能后仍受标签范围限制，也不会获得管理权限。

## CLI 与 Agent 使用

```sh
export BLUEBIRD_CODE='bb_替换为实际授权值'
bluebird auth-status
bluebird list
bluebird add '编写方案' --tags '工作'
bluebird update ID --notes '大纲已完成'
bluebird delete ID --dry-run
bluebird delete ID --yes
unset BLUEBIRD_CODE
```

上述示例需要 `list`、`add`、`update`、`delete` 权限，以及名为“工作”的现有授权标签。按实际需求勾选即可。`--code CODE` 优先于环境变量；明确使用 `--full-access` 时忽略环境变量，两个命令行选项不能同时传入。code 是持有即可使用的凭据，请避免出现在共享日志和命令历史中。Agent 遇到拒绝时不得自行改用 full-access。

`auth-status` 返回模式、功能权限、稳定标签 ID 和当前可用的标签名；`capabilities` 提供功能分组，方便 Agent 发现能力。授权拒绝返回 JSON `access_denied`，退出码 **3**；其余退出码为 0 成功、1 执行失败、2 参数错误。

## 标签作用范围

任务必须至少有一个标签，且 **任务全部标签都在 code 授权范围内**。仅授权“工作”可以访问“工作”任务，不能访问无标签任务，也不能访问“工作 + 私人”任务；授权“工作 + 学习”可以访问其中任一或两个标签的任务。

绑定使用标签 ID：重命名不影响授权；同名标签删除后重建不继承旧授权；已不存在的标签不产生访问权。创建任务必须明确传入非空 `--tags`，修改标签后仍须保留至少一个现有授权标签。code 不能创建新标签或清空全部标签；同名标签有歧义时拒绝操作。full-access 保留创建和清空标签能力。

列表和记录只返回范围内的任务；按 ID 查询时不区分不存在与越权。其他范围的计时器仅返回 `state: unavailable`，不暴露任务信息，也不能操作。code 不允许指定其他 `--db` 快照。界面定位仍检查全库同名任务，避免误操作范围外同名任务。

## 存储与边界

授权保存在 `~/Library/Application Support/bluebird-cli/authorization.sqlite3`，文件仅所有者可读写。只持久化 code 的 SHA-256 摘要及授权信息。此文件独立于 `BLUEBIRD_CLI_HOME` 和辅助工具缓存，重编译或清理缓存不会重置授权。需要备份时妥善保管；删除该文件会使所有 code 失效。目前不设自动过期。旧记录没有功能权限字段时默认不开放任何功能，需管理员明确编辑。

网页服务只用于管理授权；服务关闭后 CLI 仍可读取本机授权库验证 code。管理 API 检查回环 Host、Origin 和管理员会话令牌，Agent code 不能调用管理 API。

这是协作式 CLI 权限控制，**不是操作系统安全沙箱**。同一 macOS 账户下可执行任意命令的用户或 Agent 仍可选择 full-access、修改授权库或直接读取 App 数据。若不信任 Agent 的命令执行能力，需要额外限制执行环境。CLI code 不会替代 macOS 辅助功能授权或 Agent 沙箱授权。
