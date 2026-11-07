# 兼容范围

[文档首页](README.md) · [English](../en/compatibility.md) | 简体中文 | [日本語](../ja/compatibility.md)

初始支持目标为 **macOS 15 及以上**、Python 3.9 及以上、Bluebird 3.14.1 / build 437。新 macOS 或 Bluebird 版本不自动视为已验证；未知数据库结构和有歧义的界面目标会明确失败。旧 macOS 不在本次支持目标内，不代表已确认不兼容。

| 环境 | 验证依据 |
|---|---|
| macOS 15.7.5、Apple Silicon（arm64）、Python 3.11、Bluebird 3.14.1 | 本机真实任务与计时流程，详见验证记录 |
| macOS 15 的 Apple Silicon 和 Intel 托管 runner | CI 安装 wheel、运行模拟数据测试、编译 Swift 辅助工具；runner 不包含 Bluebird，也不授予辅助功能权限 |
| Linux、Python 3.9 和 3.13 | CI 检查参数、授权、HTTP 和数据库模拟数据；不能操作 macOS App |
| 其他 Bluebird 版本、旧 macOS、Intel 真实界面 | 尚未实机认证，测试时请记录准确环境 |

辅助工具在本机按当前架构编译，不分发预编译的 Universal 二进制。界面写操作需要 Xcode Command Line Tools、已登录并解锁的桌面、初始化完成的 Bluebird，以及实际终端/Agent 宿主的辅助功能权限。同一台 Mac 的验证不能证明 Intel 实机行为、远端同步或全新 macOS 用户环境的行为。

适配器解析已验证 App 的全部 26 种语言资源；完整任务/计时流程已在简体中文、英文、日文和阿拉伯文运行，其他语言有资源与控件检查，未覆盖每种流程组合。网页和文档支持中文、英文、日文。

提交问题时提供 `bluebird --version`、macOS 版本、芯片架构、Python 版本、Bluebird 版本/界面语言，以及脱敏错误。`capabilities` 中 `cli_version` 是软件版本，独立的 `version` 字段是能力描述格式版本。
