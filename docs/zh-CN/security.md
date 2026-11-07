# 安全与漏洞报告

[文档首页](README.md) · [English](../en/security.md) | 简体中文 | [日本語](../ja/security.md)

安全修复面向最新的 0.3.x 版本。请通过 [GitHub 私密漏洞报告](https://github.com/includeno/blue-bird-cli/security/advisories/new)提交漏洞，不要公开发布漏洞细节。提供版本、涉及的权限边界和使用虚构数据的最小复现。请勿附带 code、私有管理员 URL、数据库或个人任务内容。不承诺固定响应时限。

code 提供协作式功能/标签限制，不能隔离同一 macOS 账户下可执行任意命令的 Agent；该 Agent 仍可使用 full-access 或读取/修改本地数据。如果这超出了你的信任范围，需要额外的执行沙箱。`bluebird start web` 是所有者管理入口，不接受 Agent code。

管理页仅监听 127.0.0.1，需要私有管理 URL。不要通过反向代理或隧道暴露。完整 code 仅在创建成功时显示，由用户自行保存；持久化只保存摘要及授权信息。妥善保管授权库和备份。code 丢失或暴露后应撤销并重新创建。授权变更对后续命令生效，不撤销已开始的动作。

macOS 辅助功能、Agent 执行沙箱和 CLI 授权是不同层次。详见[授权说明](authorization.md)和根目录[安全政策](../../SECURITY.md)。
