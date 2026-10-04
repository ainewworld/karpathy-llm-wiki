---
name: karpathy-llm-wiki
description: "在构建或维护个人 LLM 驱动的知识库时使用。触发条件：向维基摄取信息源、查询维基知识、检查维基质量、'add to wiki'、'what do I know about'，或任何提到 'LLM wiki' 或 'Karpathy wiki' 的场景。"
---

# Karpathy LLM 维基

使用 LLM 构建和维护个人知识库。你管理两个目录：`raw/`（不可变的原始素材）和 `wiki/`（编译后的知识文章）。信息源进入 raw/，你把它们编译成维基文章，维基随时间复合增长。

来自 Karpathy 的核心思想：
- "LLM 负责编写和维护维基；人类负责阅读和提问。"
- "维基是一个持久的、可复合增长的产物。"

## 架构

三层结构，全部位于用户的项目根目录下：

**raw/** —— 不可变的原始素材。只读，永不修改。按主题子目录组织（例如 `raw/machine-learning/`）。

**wiki/** —— 编译后的知识文章。你拥有完全的所有权。按主题子目录组织，仅限一层：`wiki/<topic>/<article>.md`。包含两个特殊文件：
- `wiki/index.md` —— 全局索引。每篇文章一行，按主题分组，包含链接 + 摘要 + 更新日期（Updated）。
- `wiki/log.md` —— 仅追加的操作日志。

**SKILL.md**（本文件）—— 模式层（schema layer）。定义结构和工作流规则。

模板位于本文件相对的 `references/` 目录中。当你需要 raw 文件、文章、归档页面或索引的确切格式时，请阅读它们。

### 初始化

仅在第一次 Ingest 时触发。检查 `raw/` 和 `wiki/` 是否存在。只创建缺失的部分；永不覆盖已有文件：

- `raw/` 目录（带 `.gitkeep`）
- `wiki/` 目录（带 `.gitkeep`）
- `wiki/index.md` —— 标题为 `# Knowledge Base Index`，正文为空
- `wiki/log.md` —— 标题为 `# Wiki Log`，正文为空

如果 Query 或 Lint 找不到维基结构，告诉用户："先运行一次 ingest 来初始化维基。"不要自动创建。

## 溯源不变量（The Grounding Invariant）

wiki/ 中每一个承重事实 —— 数字、日期、直接引语 —— 都必须逐字存在于该文章 Raw 字段所链接的 raw/ 文件中。编译（Compile）*确立*这一不变量（先定位再写）；lint *验证*它（`scripts/check_evidence.py` 会在被链接的 raw 文件中 grep 高信号字面量 —— 带后缀或较大的数字、小数、ISO 日期、较长的引语；编译期的"先定位再写"规则覆盖其余情况）。由于 raw/ 是不可变的，一篇已验证的文章会一直保持已验证状态；该脚本可在数秒内重新检查整个维基，因此不存在需要维护的增量状态。

---

## Ingest（摄取）

将信息源抓取到 raw/，然后将其编译进 wiki/ —— 除非该信息源没有增加任何新内容。始终要抓取；是否编译取决于下面的甄别分类。

### Fetch（抓取，raw/）

1. 使用你的环境提供的任何网页或文件工具获取信息源内容。如果没有任何工具能访问该信息源，请用户直接粘贴。

2. 选择一个主题目录。先检查现有的 `raw/` 子目录；如果主题足够接近就复用一个。只为真正截然不同的主题创建新子目录。

3. 保存为 `raw/<topic>/YYYY-MM-DD-descriptive-slug.md`。
   - slug 来自信息源标题，kebab-case，最多 60 个字符。
   - 发布日期未知 → 文件名中省略日期前缀（例如 `descriptive-slug.md`）。元数据中的 Published 字段仍要出现；将其设为 `Unknown`。
   - 如果同名文件已存在，追加数字后缀（例如 `descriptive-slug-2.md`）。
   - 包含元数据头：信息源 URL、采集日期、发布日期。
   - 保留原文。清理格式噪音。不要改写观点。

   确切格式见 `references/raw-template.md`。

### Triage（甄别分类）

保存 raw 文件之后、编辑 wiki/ 之前，用信息源的关键实体及同义词搜索 wiki/，然后说明处置结果：

- **New（新知）** —— 创建一篇或多篇新文章。
- **Update（更新）** —— 合并进已有文章。
- **Disputed（有争议）** —— 与已有内容矛盾；可与 New 或 Update 组合（冲突标注见 Compile）。
- **No material（无实质内容）** —— 没有增加维库已有知识之外的内容。保留 raw 文件，记录日志（见 Post-Ingest），然后停止。不要强行从单薄的信息源中挤出文章。

New、Update 和 Disputed 可以组合。No material 是排他的。

### Compile（编译，wiki/）

确定新内容的归属：

- **与已有文章的核心论点相同** → 合并进该文章。将新信息源加入 Sources/Raw。更新受影响的章节。
- **新概念** → 在最相关的主题目录中创建新文章。文件以概念命名，而不是以 raw 文件命名。
- **跨越多个主题** → 放在最相关的目录中。向其他地方的相关文章添加 See Also 交叉引用。

这些并不互斥。单个信息源可能既需要合并进一篇文章，又需要为它引入的一个独立概念另建一篇文章。在所有情况下，都要检查事实冲突：如果新信息源与已有内容矛盾，用 **Status: Disputed** 块标注有争议的断言（见 `references/article-template.md`）。当冲突内容分属不同文章时，两篇都标注并互相链接。

**信息源保真度。** 每一个数字、日期和直接引语在写入之前都必须在 raw 文件中定位到（grep 或读取）；写入的值要与找到的完全一致 —— 如果信息源写的是 42K，就写 42K，而不是 42,000。推导值（你计算出的和、差、计数）必须展示其组成部分，以便每个部分都能在 raw 中找到。如果无法定位某个值，就不要写它的精确形式；舍弃它或不带精度地陈述它。

文章格式见 `references/article-template.md`。要点：
- Sources 字段：作者、组织或刊物名 + 日期，用分号分隔。
- Raw 字段：指向 raw/ 文件的 markdown 链接，用分号分隔。
- 从 `wiki/<topic>/` 出发的相对路径使用 `../../raw/<topic>/<file>.md`（向上两级回到项目根目录）。

### Cascade Updates（级联更新）

处理完主文章后，检查涟漪效应。不要只依赖索引：用信息源的关键实体、别名以及它触及的断言全文搜索整个维基，然后更新每一篇内容受到实质性影响的非归档文章。每个被更新的文件都要刷新其 Updated 日期。

当新信息源取代或推翻某个已有断言时，保留旧断言以作记录，但用 Status 块标注（见 `references/article-template.md`）：有更新内容取代时用 **Outdated**，信息源之间不一致时用 **Disputed**。永不静默改写历史。

归档页面永不级联更新（它们是时间点快照）。

### Post-Ingest（摄取后处理）

更新 `wiki/index.md`：为每一篇被触及的文章添加或更新条目。添加新主题小节时，附上一行描述。Updated 日期反映文章知识内容最后一次变化的时间，而不是文件系统时间戳。格式见 `references/index-template.md`。

向 `wiki/log.md` 追加：

```
## [YYYY-MM-DD] ingest | <主文章标题>
- Disposition: <New; Update; Disputed>
- Raw: <raw 文件路径>
- Updated: <被级联更新的文章标题>
```

没有级联更新时省略 `- Updated:` 行。对于 No material，记录日志后停止。使用相对于项目根目录的 raw 路径（例如 `raw/topic/file.md`）：

```
## [YYYY-MM-DD] ingest | no material: <相对于项目根目录的 raw 文件路径>
- Disposition: No material
```

确切的 no-material 标题是机器可读的清点键；Disposition 行仍然必需，以构成完整的人类可读日志条目。

### Research（多信息源摄取）

仅在用户明确要求研究某个主题或为维基收集信息源时使用。普通的知识问题走 Query，Query 永不写文件。

1. 将主题拆分为几个角度。对每个角度，撒网式搜索 —— 官方名称、缩写和同义词，而不仅是字面关键词。
2. 对于任何你预期要得出的核心断言，刻意搜索对立面：失败案例、批评、失败的复现。
3. 照常将选中的信息源保存到 raw/。搜索可以并行；编译不可以 —— 一次只编译一个信息源，因为 index.md、log.md 和级联更新是共享状态。

---

## Query（查询）

搜索维基并回答问题。触发示例：
- "What do I know about X?"（关于 X 我知道什么？）
- "Summarize everything related to Y"（总结与 Y 相关的一切）
- "Compare A and B based on my wiki"（基于我的维基比较 A 和 B）

### 步骤

1. 读取 `wiki/index.md` 定位候选文章，然后用该主题的关键词*及其同义词*全文搜索 wiki/。在索引和全文搜索都为空之前，永不声称维基没有相关内容 —— 并且要说明你搜索过了。
2. 阅读找到的文章并综合出答案。
3. 优先使用维基内容而非你自己的训练知识。用 markdown 链接引用来源：`[文章标题](wiki/topic/article.md)`（对话中的引用使用项目根相对路径；在 wiki/ 文件内部，使用相对于当前文件的路径）。
4. 在对话中输出答案。除非被要求，否则不写文件。

### Archiving（归档）

当用户明确要求将答案归档或保存到维基时：

1. 将答案写为一个新的维基页面。见 `references/archive-template.md`。将对话中的引用转换为归档页面时，把项目根相对路径（例如 `wiki/topic/article.md`）改写为文件相对路径（例如 `../topic/article.md`，同目录则用 `article.md`）。
   - Sources：指向答案中引用的维基文章的 markdown 链接。
   - 没有 Raw 字段（内容并非来自 raw/）。
   - 文件名反映查询主题，例如 `transformer-architectures-overview.md`。
   - 放在最相关的主题目录中。
2. 始终创建新页面。永不合并进已有文章（归档内容是综合出的答案，不是原始素材）。
3. 更新 `wiki/index.md`。在 Summary 前加 `[Archived]` 前缀。
4. 向 `wiki/log.md` 追加：
   ```
   ## [YYYY-MM-DD] query | Archived: <页面标题>
   ```

---

## Lint（检查）

对维基做质量检查。三类检查，权限级别不同。

### Safe Fixes（安全修复，自动修复）

自动修复以下问题：

**索引一致性** —— 将 `wiki/index.md` 与实际的 wiki/ 文件（排除 index.md 和 log.md）对比：
- 文件存在但索引中缺失 → 添加条目并以 `(no summary)` 占位。Updated 使用文章元数据中的 Updated 日期（归档页面则用 Archived 日期）如果存在；否则回退到文件的最后修改日期。
- 索引条目指向不存在的文件 → 在索引中标记为 `[MISSING]`。不要删除条目；让用户决定。
- 索引条目的 Updated 与文章元数据的 Updated（归档页面为 Archived）不一致 → 更新索引条目使其与文章一致。

**内部链接** —— 对 wiki/ 文章文件中的每一个 markdown 链接（正文和 Sources 元数据），排除 Raw 字段链接（由下面的 Raw 引用规则校验），排除 See Also 小节的链接（由下面的 See Also 规则处理），并排除 index.md/log.md（已在上面处理）：
- 目标不存在 → 在 wiki/ 中搜索同名文件。
  - 恰好一个匹配 → 修复路径。
  - 零个或多个匹配 → 报告给用户。

**Raw 引用** —— Raw 字段中的每个链接必须指向存在的 raw/ 文件：
- 目标不存在 → 在 raw/ 中搜索同名文件。
  - 恰好一个匹配 → 修复路径。
  - 零个或多个匹配 → 报告给用户。

**See Also** —— 在每个主题目录内：
- See Also 链接的目标不存在 → 在 wiki/ 中搜索同名文件。
  - 恰好一个匹配 → 修复路径。
  - 零个匹配 → 移除该链接（死掉的交叉引用不是承重内容）。
  - 多个匹配 → 报告给用户。

### Mechanical Reports（机械化报告，不修复）

用 `python3 <skill-dir>/scripts/check_evidence.py <project-root>` 机械地运行这些检查（后面可选地跟项目根相对的文章路径以限定范围）。默认范围是整个维基；脚本很快。报告发现的问题；永不自动修复事实。

**信息源保真度** —— 被报告的嫌疑项只是候选，不是结论：推导值和产品名也可能出现。结合 raw 上下文逐个判断，只报告真正的不匹配。

**证据错误** —— 脚本无法验证的文章（缺少 Raw 字段、Raw 链接无法解析、或 Raw 链接逃逸出 `raw/`）。这些始终需要人来决策，而不是由脚本修复。

**未被引用的 raw 文件** —— 以 No material 处置记录过日志的文件被排除；其余都是真正的积压提醒。

### Judgment Reports（判断性报告，不修复）

这些依赖你的判断。报告发现的问题，但不自动修复：

- 跨文章的事实矛盾
- 已被更新信息源取代却仍未加 Status 块呈现的过时断言
- 信息源不一致处缺失冲突标注
- 相关文章之间明显缺失的交叉引用（提出建议；不要静默添加）
- 格式错误的 Status 块（Outdated 缺少日期，或任一块缺少解释；格式参考：`references/article-template.md`）
- 没有任何来自其他维基文章入链的孤儿页面
- 缺失的跨主题引用
- 被频繁提及却没有专属页面的概念
- 归档后其被引用的来源文章已发生实质性更新的归档页面

### Post-Lint（检查后处理）

向 `wiki/log.md` 追加：

```
## [YYYY-MM-DD] lint | 发现 <N> 个问题，自动修复 <M> 个
```

---

## 约定

- 全程使用带相对链接的标准 markdown。
- wiki/ 仅支持一层主题子目录。不允许更深的嵌套。
- 日志条目、Collected 日期和 Archived 日期使用当天日期。Updated 日期反映文章知识内容最后一次变化的时间。Published 日期来自信息源（无法获得时用 `Unknown`）。
- 在 wiki/ 文件内部，所有 markdown 链接使用相对于当前文件的路径。在对话输出中，使用项目根相对路径（例如 `wiki/topic/article.md`）。
- Ingest 同时更新 `wiki/index.md` 和 `wiki/log.md`（No material 的 ingest 只更新日志）。归档（来自 Query）两者都更新。Lint 更新 `wiki/log.md`（仅在自动修复索引条目时才更新 `wiki/index.md`）。普通查询不写任何文件。
