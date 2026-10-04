# karpathy-llm-wiki

**一个可复用的技能（skill），用于在 Claude Code、Cursor、Codex 及其他 Agent Skills 工具中构建 Karpathy 风格的 LLM 维基。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Astro-Han/karpathy-llm-wiki?style=social)](https://github.com/Astro-Han/karpathy-llm-wiki)
[![GitHub forks](https://img.shields.io/github/forks/Astro-Han/karpathy-llm-wiki?style=social)](https://github.com/Astro-Han/karpathy-llm-wiki)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-compatible-blue)](https://agentskills.io)
[![Install](https://img.shields.io/badge/Install-npx_add--skill-green)](https://github.com/Astro-Han/karpathy-llm-wiki#install)

<p align="center">
  <img src="assets/karpathy-tweet.png" alt="Karpathy 关于 LLM Wiki 的推文" width="560">
</p>

`karpathy-llm-wiki` 将 [Karpathy 的 LLM Wiki 理念](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 打包为一个可安装的 [Agent Skills](https://agentskills.io) 技能。你的编码智能体（coding agent）会把信息源摄取（ingest）到 `raw/`，把持久性知识页面编译（compile）到 `wiki/`，带引用地回答问题，并对维基做一致性检查（lint）。

## 什么是 LLM 维基？

**LLM 维基**是一种知识系统：由 LLM 维护结构化的维基页面，而不是在每次提问时重新搜索原始文档。新的信息源会被编译成持久性的 markdown 页面，交叉引用会随时间不断更新，而回答会引用那些已经包含了综合知识的维基页面。

这个技能提供三种操作：

| 操作 | 作用 | 输出 |
|-----------|--------------|--------|
| **Ingest（摄取）** | 将信息源收集到 `raw/`，进行甄别分类，然后创建或更新维基文章 —— 或者在没有新内容时只记录日志 | 新建或更新的维基页面 |
| **Query（查询）** | 搜索维基并带引用地回答 | 有据可依、链接到 markdown 页面的回答 |
| **Lint（检查）** | 检查索引完整性、链接和维基健康度 | 自动修复以及报告的问题 |

完整的技能规范见 [SKILL.md](SKILL.md)。

## LLM 维基 vs RAG

| 方式 | 知识存放于 | 综合发生在何时 | 适合场景 |
|----------|--------------------|------------------------|----------|
| **RAG** | 原始分块与嵌入（embeddings） | 查询时 | 在大型语料库上进行广泛检索 |
| **LLM 维基** | 精心维护的 markdown 页面 | 摄取与维护期间 | 可复合增长的知识、摘要，以及持久的交叉链接 |

本技能针对维基模式做了优化：知识随时间不断改进，而不是在每次查询时重新推导关系。

## 使用统计

基于一个自 2026 年 4 月起每日维护的生产知识库：

- **94** 篇维基文章，分布在 **13** 个主题目录中
- 已摄取 **99** 份信息源
- 最近 7 天内有 **87** 条操作日志

维基页面、信息源文件和操作日志的示例见 [examples/](examples/)。

## 安装

```bash
npx add-skill Astro-Han/karpathy-llm-wiki
```

适用于任何支持 [Agent Skills](https://agentskills.io) 标准的工具。

## 快速开始

### 1. 摄取你的第一个信息源

给技能一个 URL、一个文件或粘贴的文本：

> "Ingest this article: https://example.com/attention-is-all-you-need"（摄取这篇文章：…）

技能会把信息源存储到 `raw/`，然后在 `wiki/` 中编译或更新相应的知识页面。

### 2. 向你的维基提问

> "What do I know about attention mechanisms?"（关于注意力机制我知道些什么？）

技能会搜索维基，并在回答中引用链接回你的 markdown 页面。

### 3. 保持维基健康

> "Lint my wiki"（检查我的维基）

检查失效链接、缺失的索引条目、过时的交叉引用等相关问题。

## 工作流程如何运作

来自 Karpathy 的核心思想：LLM 负责维护维基，而人类专注于选择信息源并提出好问题。

```text
your-project/
├── raw/            ← 不可变的原始素材
│   └── topic/
│       └── 2026-04-03-source-article.md
├── wiki/           ← 由 LLM 维护的编译后的知识页面
│   ├── topic/
│   │   └── concept-name.md
│   ├── index.md    ← 全局目录
│   └── log.md      ← 仅追加的操作日志
```

每个新信息源都可以更新多个页面、加强交叉引用并记录矛盾之处。这正是维基能够随时间复合增长的原因。

## 工具兼容性

本技能遵循 [agentskills.io](https://agentskills.io) 开放标准：

| 工具 | 安装方式 |
|------|----------------|
| Claude Code | `npx add-skill Astro-Han/karpathy-llm-wiki` |
| Cursor | `npx add-skill Astro-Han/karpathy-llm-wiki` |
| Codex CLI | 复制到 `.agents/skills/karpathy-llm-wiki/` |
| OpenCode | `npx add-skill Astro-Han/karpathy-llm-wiki` |
| 其他工具 | 将 `SKILL.md`、`references/` 和 `scripts/` 复制到该工具的技能目录中 |

## 常见问题

### LLM 维基与个人维基有什么区别？

LLM 维基由模型维护。随着新材料到来，它会更新摘要、交叉链接、索引条目和矛盾记录。普通个人维基依赖手工编辑。

### 我可以摄取哪些信息源？

网页、论文、博客文章、PDF、markdown 文件、文本文件和粘贴的文本。技能会把所有内容转换为 markdown 存入 `raw/`，并将其编译进 `wiki/`。

### 这是生产可用的吗？

该工作流基于一个自 2026 年 4 月起每日维护的真实知识库，包含 94 篇文章和 99 个信息源。仓库中包含示例、模板和设计规范。

## 设计边界

在三个月的生产日志和对生态系统（LLM Wiki v2、llm-wiki-compiler、OKF、agent-memory 文献）的调研之后，刻意没有构建的东西：

- **信息源哈希新鲜度追踪** —— raw/ 是不可变的，因此哈希防备的是不可能发生的事件。真正的新信息会作为新信息源通过正常摄取流程到来。
- **持久化的行号引用** —— 所有观察到的保真度错误都是"值在信息源中不存在"，用全文件 grep 就能发现。锚点只是用来区分一种从未发生过的失败模式，而且这种标注摩擦会让智能体跳过该规则。
- **数值化的置信度或质量评分** —— 没有校准依据的虚假精度。证据强度应该写在正文中。
- **按文章的审查日期** —— 没有人能在编译时预测一个领域的变化速度。维护由整个维基的 lint 驱动，而不是按页面的定时器。
- **基于访问的衰减** —— 被频繁提问不等于正确。
- **撤回 / 坏信息源机制** —— 尚未发生过。在发生之前先手动处理。
- **自动钩子与定时运行** —— 那些属于智能体运行时（agent harness），不属于工具无关的技能。
- **向量或图搜索** —— 在 5 万–10 万 token 精心维护的维基规模下，grep 和读取更可靠。只在召回率可度量地下降时才添加搜索工具。
- **类型化的关系本体** —— 链接的语义存在于链接周围的正文中。
- **OKF 合规** —— 该规范还是 v0.1 草案，工具生态最小。已在跟踪；届时会重新评估。
- **MCP 服务器、UI、输出子系统** —— 在工具无关技能的边界之外。

## 灵感来源

这是 [Karpathy 的 LLM Wiki 理念](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)工作流的非官方社区实现。这里的价值在于可复用的工作流、提示词结构，以及经过实战检验的知识编译规则。

另请参阅：[lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki)、[atomicmemory/llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler)。我们正在跟踪 Google 的 [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) 草案，待规范和工具成熟后将评估兼容性。

## 许可证

[MIT](LICENSE)
