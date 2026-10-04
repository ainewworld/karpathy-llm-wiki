# 来自真实维基的示例

本目录包含一个自 2026 年 4 月起使用 `karpathy-llm-wiki` 维护的知识库中的真实文件。

## 文件

| 文件 | 展示内容 |
|------|---------------|
| `claude-code-statusline-landscape.md` | 带结构化数据（表格、引用、交叉引用）的编译后维基文章 |
| `2026-03-19-claude-code-statusline-landscape.md` | 编译前的原始信息源素材 |
| `ai-coding-tools-index.md` | 全局索引的一个主题小节（每篇文章的摘要 + Updated） |
| `log-sample.md` | 操作日志的示例条目（当前所有条目类型） |

## 原始 vs 编译对比

**原始信息源**（`2026-03-19-claude-code-statusline-landscape.md`）：
- 原始研究笔记
- 非结构化内容
- 元数据头（Source、Collected、Published 日期）

**编译后文章**（`claude-code-statusline-landscape.md`）：
- 结构化章节（概述、竞争格局、用户痛点）
- 从多个信息源综合而成的表格
- 指向其他维基文章的交叉引用
- 经过多次 ingest 操作累积更新

## 操作日志

日志记录每一个动作：
- `ingest` —— 信息源被收集进 raw/ 并编译（Disposition 为 New / Update / Disputed，或在没有值得编译的内容时为 `no material`）
- `query` —— 归档的查询结果
- `lint` —— 质量检查及其结果

近期活动显示了每日维护：仅最近 7 天就有 87 条记录。
