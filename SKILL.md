---
name: info-align
version: 12
domain: meta
author: skill-evolution
created_at: '2026-07-15T13:48:48.453160+00:00'
evolved_at: '2026-07-16T00:00:00.000000+00:00'
parent_hash: 44c27e0e154f
tags:
- information-alignment
- requirement-extraction
- chinese
- meta-skill
evolution_round: 1
---


# 信息对齐 Skill (Info Align)

在用户任务请求模糊或不完整时，用最小交互成本消除 AI 与用户之间的信息不对称，产出一份结构化需求确认单。下游 Skill 直接消费确认单，无需再次对齐。

## 触发条件

当 User Request 不完整、信息不足、需求本身不清晰时触发。简单问答、一次性事实查询、已明确完整的任务不触发。

---

## 核心流程

### 阶段 1：Context Extraction — 上下文收集

收集所有信息来源形成统一 Task Context，不做任何推理。

Task Context 来源（仅 User Request 必须存在）：
- User Request（必选）
- Skill Source（可选）— 下游 SKILL.md 全文或关键段落
- Conversation History（可选）— 本会话相关历史消息
- External Metadata（可选）— 上传文件元信息

将所有 source 原文拼接为完整文本。不做任何过滤、不改写、不推理。

### 阶段 2：Requirement Extraction — 语义模式提取（委托 Python Parser）

语义模式匹配是正则/规则引擎的工作，不由 LLM 直接推理。Agent 将 Task Context 传入 `scripts/requirement_parser.py`，获取结构化字段列表。

```bash
echo "<Task Context>" | python scripts/requirement_parser.py
# 或
python scripts/requirement_parser.py -f task_context.txt
```

Parser 内部规则（与旧版语义一致，交由代码执行）：

| Pattern | 提取对象 | 输出 |
|---------|---------|------|
| 需要、必须、请提供、务必 | Required Field | `required: true` |
| 可以、省略、可选、若不需要可 | Optional Field | `required: false` |
| 默认、通常、若未指定、一般情况下 | Default Policy | `default: <value>` |
| 不要、禁止、不得、切勿、严禁 | Constraint | `constraint: <description>` |
| 输出、生成、返回、产出、格式为 | Output Format | `output: <descriptor>` |
| 优先、首先、最后、先…再 | Execution Policy | `priority/order` |

Parser 原则（已在 `scripts/requirement_parser.py` 中实现）：
- 只关心语义模式，不关心领域
- 仅提取显式信息
- 同一句子多模式命中时，按 Required > Default > Optional > Constraint 优先级消歧
- 未命中任何模式的文本丢弃
- "需要/必须"的宾语/主语是"你/AI"时，不作为 Required Field

Parser 输出为 JSON 数组，每个元素含 `pattern`、`key`、`value`、`source: "parser"`、`sentence` 等字段。若 Task Context 中无任何语义关键词命中，返回 `[]`——正常，进入阶段 2.5。

### 阶段 2.5：四象限发问 — 主动兜底

Agent 用四象限视角依次自问，扫描 Task Context 补充阶段 2 可能遗漏的字段。

象限❶ — 用户以为我知道了但其实不知道什么？
  同领域任务中"成对出现"但用户没提的信息。用户用了专有名词但没展开的。
  → 产出 missing 字段
  → 同时为该字段生成 3 个候选 options：基于领域常见做法，第 1 个为最推荐选项

  **Guidance**: When a Skill Source is available, scan it for required input parameters and compare against the User Request to identify fields the user implicitly assumes you know. For common domain tasks (e.g., deployment, report generation), use your knowledge to surface fields that are almost always necessary (e.g., for deployment: model source, framework, target environment, purpose). These should be surfaced as missing fields unless explicitly provided.

象限❷ — 用户知道但嫌麻烦没说全的？
  有多个可选项、用户心里有偏好但懒得逐一指定的维度。
  → 产出 defaulted 字段（预填最常见选项）
  → 同时为该字段生成 3 个候选 options：第 1 个为预填默认值，第 2/3 个为常见替代方案。options 覆盖不同方向，避免同质化。

象限❸ — 用户自己也不确定、可能指向多种方向的？
  用词本身模糊（"分析""优化""做一下"）、缺乏限定条件。
  → 不直接生成字段，标记为需要维度展开

象限❹ — 用户根本不知道但执行会遇到的坑？
  同类任务前置条件。默认值兜底但在什么情况下默认值可能错误。
  → 产出 defaulted + risk=warning 字段（盲区预警）

规则：四象限不重复阶段 2 已提取字段。产出字段标记 source: quadrant。

### 阶段 3：Field Reasoning — 合并 + 状态判定

合并阶段 2（语义提取）和阶段 2.5（四象限）的字段：
1. 同一 key 双来源 → 语义提取的值优先
2. 四象限独有字段 → 保留

字段模型：
```
{ key, value, source, status, required, risk, constraint, options }
```

`options` 是一个最多 3 个候选值的字符串数组，供用户快速选择。仅 `missing` 和 `defaulted` 字段需生成 options。生成原则：覆盖最可能的 3 种不同方向，按推荐度降序排列，第 1 个为推荐项。

状态判定：

| 条件 | status |
|------|--------|
| User Request 明确提供了值 | locked |
| 有 default 可用 | defaulted |
| required=true 且无任何值 | missing |
| required=false 且无任何值 | defaulted（用通用基线） |
| 多 source 冲突且无法裁决 | conflicting |

覆盖优先级：User > Conversation > Skill > Quadrant > Meta > Platform

Conversation 防污染：历史偏好需检查与当前任务的主题关联性，不相关的历史偏好不采纳。

字段依赖推理：当 locked 字段触发依赖时（如"估值方法"=DCF → 需要增长率、WACC），追加依赖字段为 required=true。

### 阶段 4：生成需求确认单

分两步输出。

**第一步**：纯文本输出已确认字段摘要。

```
✅ 已确认
- 任务：客户流失预测模型
- 数据格式：CSV
（无 locked 字段则跳过此步）
```

**第二步**：检测平台能力，选择交互模式。

检查当前平台是否提供**原生问答工具**——即具有可点击选项/按钮的选择器组件，支持预设选项并自动附带自定义文本输入入口。典型如 opencode 的 `question` 工具。若存在此类工具则走分支 A，否则走分支 B。

---

#### 分支 A：原生交互按钮

调用平台原生问答工具，将 ⚠️ 和 ❓ 字段打包为交互式选项。完整字段→工具参数映射示例见 `examples/branch-a-native-tool.md`。映射规则：

| 字段属性 | 映射目标 | 说明 |
|---------|----------|------|
| `options[0]` | 第 1 个选项，label 为 `"<值> (推荐)"` | ⚠️ 字段用默认值，❓ 字段用最推荐值 |
| `options[1]` | 第 2 个选项 | 不同方向 |
| `options[2]` | 第 3 个选项 | 不同方向 |
| `key` | 问答工具的 `header` 或 title（≤30 字符） | 字段名 |
| 工具内置 custom 特性 | 自定义输入入口 | 不手动添加 "自定义" 选项，依赖工具自动生成 |
| `risk=warning` | 写入推荐选项的 description | 在描述末尾附加风险提示 |

调用策略：
- 所有 ⚠️ 和 ❓ 字段合并为一次原生工具调用
- ❓ 字段排在 ⚠️ 字段前面
- 字段总数 ≤ 7 时一次全部展示；> 7 时分两轮（第一轮 ❓，第二轮 ⚠️）
- 所有字段为单选

输出中禁止出现手写的 A/B/C 选项文本——必须交由原生工具渲染。

---

#### 分支 B：纯文本降级

平台无原生问答工具时，退化为纯文本逐字段交互。按以下格式逐字段弹出：

```
❓ 数据来源
A. CSV / Excel 本地文件 (推荐)
B. 数据库直连
C. API 接口
回复 A/B/C，或直接输入自定义值
```

规则：
- ⚠️ 字段：`options[0]` 标注 "(默认)"，其余照常
- ❓ 字段：`options[0]` 标注 "(推荐)"
- 一次只展示一个字段，用户回复后弹出下一个
- ❓ 字段优先于 ⚠️ 字段
- 在第一个字段后附带提示："可随时回复「确认」采用所有默认/推荐值"

纯文本模式中，禁止调用原生问答工具，禁止使用 HTML 按钮，所有选项通过文本 A/B/C 呈现。

### 阶段 5：Validate — 收集结果并回显理解

根据阶段 4 选择的模式，走对应的结果处理路径。

---

#### 分支 A：处理原生工具返回

平台原生问答工具的返回格式依平台而异，典型为 `<header>: <selected_label>` 映射。处理规则：
- 去掉 label 中的 "(推荐)"、"(默认)" 等后缀得到最终字段值
- 用户通过工具内置 custom 入口输入的值直接作为字段值
- 所有字段结果收集完毕后 → 回显一句话理解摘要，交给下游 Skill

---

#### 分支 B：解析纯文本回复

逐字段状态机，每次等待用户输入：

| 用户输入 | 处理 |
|---------|------|
| `A` / `B` / `C`（大写单字母） | 选定对应选项作为当前字段值。回显："已选 `<字段名>` = `<值>`"，弹出下一个字段 |
| 自定义文本（非 A/B/C 且非全局指令） | 将文本作为当前字段值。回显："已选 `<字段名>` = `<自定义值>`"，弹出下一个字段 |
| `"确认"` / `"开始"` / `"没问题"` | 剩余未选字段：❓ 取 `options[0]`（推荐值），⚠️ 取其 `value`（默认值）。一次性回显所有剩余选择，结束 |
| `"重置 <字段名>"` | 将该字段重置为未选状态，重新弹出该字段 |

所有字段完成后不重新输出整个确认单，直接交给下游 Skill。

### 阶段 6：启动下游 Skill

交给下游 Skill，直接使用确认单中字段值，无需再次询问。

---

## 特殊处理

| 用户输入 | 策略 | 适用分支 |
|---------|------|---------|
| "随便"/"你决定"/"都可以" | 全默认，所有 ❓ 取 options[0]，跳过交互，告警后交付 | A / B |
| "直接做，不用确认" | 跳过对齐流程，所有字段用默认值 / options[0]，告警后交付 | A / B |
| "跟上次一样" | 从 Conversation History 定位复用（>3轮交互则降级） | A / B |
| "不是，我要的不是这个" | 不归 Info Align 处理；建议追问具体偏差 | A / B |
| 维度展开 | 用户请求极度模糊时，不输出确认单，输出维度分类帮助用户确定方向 | A / B |
| "A"/"B"/"C"（大写字母） | 选定当前字段对应选项，回显后弹出下一个字段 | 仅分支 B |
| 自定义文本回复 | 将文本作为当前字段值，回显后弹出下一个字段 | 仅分支 B |

===


## Appendix

### 输出中禁止出现（高频遗漏项）

- 字段 status 内部标识（locked / defaulted / missing / conflicting）
- 四象限标签（象限❶、象限❷等）
- source 标识（user / skill / quadrant / meta）
- HTML 注释（<!-- @option ... -->）
- 文件路径引用
- "示例："前缀 — 直接以自然语言呈现
- "可逆/不可逆"标签
- "skip / display / display_warning / force"策略名
- 阶段标签（阶段1、阶段2、阶段2.5等）
- 流程阶段名称（Context Extraction、Requirement Extraction 等）

### 确认单结构强制项

- ALWAYS 使用 ✅ ⚠️ ❓ 三色标记，不得引入其他符号
- ALWAYS 按区块结构输出，无内容板块不展示
- ALWAYS 在确认单末尾附操作提示（"回复确认开始"或等效表述）
- NEVER 在用户可见输出中展示内部推理过程
- NEVER 对简单问答/事实查询触发票对齐流程
- BEFORE outputting, review your response to ensure no internal process artifacts (phase numbers, stage names, field status values) are visible to the user.

===

