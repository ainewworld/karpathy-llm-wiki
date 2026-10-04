# Claude Code 状态栏市场扫描

> 来源：claude-pace 项目调研
> 采集时间：2026-03-19（GitHub star 数通过 gh api 验证）
> 发布时间：未知

以下市场数据截至 2026-03-19。

## 竞争格局

| 项目 | Stars | 语言 | 形态 | 最近更新 | 特性 |
|---------|------:|----------|------|-------------|----------|
| [ccusage](https://github.com/ryoppippi/ccusage) | 11,693 | TypeScript | CLI + 状态栏 | 03-18 | 用量分析 + 消耗速率 |
| [claude-hud](https://github.com/jarrodwatts/claude-hud) | 7,038 | JavaScript | 状态栏 | 03-15 | 功能最全、先驱者 |
| [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | 7,009 | Python | 独立仪表盘 | 2025-09 | ML 预测、无人维护 |
| [ccstatusline](https://github.com/sirmalloc/ccstatusline) | 5,421 | TypeScript | 状态栏 | 03-16 | 高度可定制 + 主题 |
| [CCometixLine](https://github.com/Haleclipse/CCometixLine) | 2,227 | Rust | 状态栏 | 03-14 | 高性能二进制 |
| [claude-powerline](https://github.com/Owloops/claude-powerline) | 931 | TypeScript | 状态栏 | 03-18 | vim powerline 风格 |
| [kamranahmedse/claude-statusline](https://github.com/kamranahmedse/claude-statusline) | 726 | Shell | 状态栏 | 03-10 | 极简主义 |
| [claude-code-statusline](https://github.com/rz1989s/claude-code-statusline) | 397 | Shell | 状态栏 | 03-14 | 4 行增强 + 主题 |
| [claude-code-usage-bar](https://github.com/leeguooooo/claude-code-usage-bar) | 159 | Python | 状态栏 | 2025-11 | 消耗速率 + 耗尽预测 |
| [claudia-statusline](https://github.com/hagan/claudia-statusline) | 21 | Rust | 状态栏 | 2026-01 | SQLite 持久化 + 云同步 |
| [felipeelias/claude-statusline](https://github.com/felipeelias/claude-statusline) | 2 | Go | 状态栏 | 03-17 | 单二进制、极简 |
| claude-pace | 3 | Bash+jq | 状态栏 | 03-19 | 节奏追踪、零运行时依赖 |

另有 6+ 个 npm 包：ccstatusline、@owloops/claude-powerline、@illumin8ca/claude-statusline、@chongdashu/cc-statusline、@sponzig/cc-statusline、@this-dot/claude-code-context-status-line。

## 详细竞品分析

### ccusage（11,693 stars）—— 整体最强

- 定位：CLI 用量分析工具，状态栏只是子功能
- 状态栏显示：模型、会话成本、当日成本、5h 区块剩余时间、消耗速率、上下文占用
- 技术：TypeScript，默认离线模式（缓存定价数据），无网络延迟
- 优势：用户基数最大、功能覆盖广、维护活跃
- 与 claude-pace 的差异：ccusage 的消耗速率只展示趋势，无预测性告警；需要 Node.js 运行时

### claude-hud（7,038 stars）—— 先驱者

- 功能最多：上下文进度条、速率限制占用、工具活动、子代理状态、Todo 进度、Git 集成
- Usage API 缓存 TTL 60 秒（成功）/ 15 秒（失败）
- 已知问题：冷缓存/API 超时导致冷启动失败（#214）、0 字节锁文件永久阻塞（#220）、Windows 兼容性（#196）
- 未被收录进 awesome-claude-code 列表（29K stars，列出 5 个状态栏工具但不含 claude-hud）

### Claude-Code-Usage-Monitor（7,009 stars）—— 无人维护

- 独立终端仪表盘（非内嵌状态栏），Python 实现
- 预测能力最强：P90 ML + 消耗速率，使用过去 192 小时历史
- HN：245 赞 / 135 评论，但代码质量被批评（"vibe-coding 风格"，主文件 1000+ 行）
- 最近更新 2025-09-14，无积极维护

### ccstatusline（5,421 stars）—— 可定制

- 定位为"格式化器"，无 API 调用
- Powerline 风格、交互式 TUI 配置、多主题
- npm 分发，性能受 Node.js 启动开销制约

### CCometixLine（2,227 stars）—— Rust 性能

- Git 集成、模型显示、用量追踪、交互式 TUI 配置
- awesome-claude-code 中唯一的 Rust 方案
- 文档缺少具体的毫秒级性能数据

## 社区分发渠道

| 渠道 | Stars | claude-pace 状态 |
|---------|------:|--------------------|
| [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 29,014 | 未收录 |
| Anthropic 官方插件目录 | 12,653 | 状态栏收录数为零 |

awesome-claude-code 目前列出 5 个状态栏：CCometixLine、ccstatusline、claude-code-statusline、claude-powerline、claudia-statusline。

## 用户痛点与未满足需求

### 核心痛点：配额不透明

1. **毫无预警地突然触发限额** —— $200/月的 Max 用户在 10-15 分钟内触发限额，只看到 "usage limit reached"（The Register，2026-01-05）
2. **配额重置时间不可见** —— 2026-03-18 同一天有 3 个独立 issue 请求该功能（#35747、#35672、#35827）
3. **5h + 7d 双窗口认知负担** —— 用户分不清触发的是哪个限额

### 官方态度

- **明确拒绝原生 token 指示器**：issue #10593 被标记为 "Not Planned"（2026-01-19），推荐使用 ccusage
- **statusline stdin JSON 不暴露配额字段**：session_used_percentage、weekly_used_percentage、resets_at 全部缺失
- 第三方工具只能通过 Usage API 变通或解析本地 JSONL 文件

### 其他请求

- 触发限额后自动恢复任务执行（#18980、#26775、#35744）
- 推送式配额告警（80% 时提醒）vs 查询式（#35947）
- 跨会话累计用量追踪（#13891、#13892）

## 技术趋势

- **从 Node.js 向轻量运行时迁移**：Rust（CCometixLine、claudia-statusline）、Go（felipeelias）、Shell（kamranahmedse、rz1989s、claude-pace）
- **零依赖安装作为卖点**：Go 单二进制、Bash 脚本 curl 一行安装
- **无公开性能基准**：没有任何工具公布过 hyperfine 或同等毫秒级基准数据

## 用户反馈分析（2026-03-24 补充）

### 跨会话每日成本汇总 —— 最好的反馈

ccusage 的核心价值是"一条命令看清成本"和"验证月费是否值得"。多篇独立评测一致将"成本可视化"列为选择 ccusage 的首要原因。

### 上下文进度条 —— 首要安装动机

多个独立来源一致认同：上下文条就是"安装理由"。SAP 社区作者写道"光上下文条就值回安装成本"。

### 速率限制 5h/7d 可视化 —— 第二大需求

v2.1.80 之后 stdin 提供官方数据，所有工具机会均等，差异化从"有没有"转向"准不准"。

### 子代理状态监控 —— 博客火热、用户投票冷淡

claude-hud 的子代理监控被多篇博客列为第二价值点。但实际数据不支持"强需求"的判断：
- 6 个子代理相关 issue 全部 0 反应
- 编号全部连续，疑似维护者或 AI 批量创建，并非用户驱动

### 消耗速率（Burn Rate）—— 竞品已经失败过

ccusage 的 Live Blocks 功能（实时 token 消耗监控）因准确性问题被正式移除（issue #782）。Issue #288（16 反应）和 #483（11 反应）记录了用户对"显示未达限额但实际已触发"的持续投诉。

### 零运行时依赖 —— 真正的差异点

ccusage 状态栏存在严重的进程管理 bug（issue #459，10 反应、17 评论）：在 hooks 中运行 `bun x ccusage statusline` 会导致无限进程生成、CPU 100%。

多位社区作者明确将"减少依赖"列为工具选择因素。Go/Rust 单二进制和纯 Bash 方案的动机都包含这一点。

### 功能蔓延是被明确警告的反模式

- Ovidiu（Substack）："当所有东西都被高亮时，就没有东西被高亮了"
- ccusage 的 Live Blocks 从上线到移除就是一个活生生的案例。

## 矛盾与不确定性

1. **子代理监控需求强度矛盾**：博客作者高度评价 vs GitHub issue 0 反应。可能解释：博客作者从功能完备性角度评估，实际用户投票反映的是"最痛的需求"
2. **ccusage 状态栏用户粘性 vs bug 严重度矛盾**：被多个第三方依赖（准确性获认可），但准确性投诉也最多。可能：CLI 报告准确，statusline/live 组件不准确
3. **claude-hud star 数从 7,038（3/19）跃升至 11,842（3/24）**：5 天涨 4,804 star，符合 Trending 效应

## 竞品功能反馈排序

| 排名 | 功能 | 证据强度 | 是否值得做 |
|------|---------|-------------------|-------------|
| 1 | 跨会话每日成本汇总 | 高（多来源独立正面反馈） | 值得评估 —— 但订阅制用户可能不在乎成本 |
| 2 | 子代理/工具活动监控 | 低（博客热、issue 冷） | 不推荐 —— 等 CC stdin 暴露相关字段 |
| 3 | 多设备数据同步 | 低 | 不推荐 |
| 4 | 按项目分组用量 | 低 | 不推荐 |

## 结论

**更有价值的方向不是"把竞品有的功能都加上"，而是"把现有功能做到最准确、最可靠"。** ccusage 的 live blocks 因不准确被移除、claude-hud 的 429 永久告警 bug，都表明状态栏竞争焦点已从"功能数量"转向"数据准确性与运行时可靠性"。
