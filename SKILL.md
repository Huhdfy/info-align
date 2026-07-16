---
name: info-align
description: "当用户任务请求存在未解决的决策点时触发——即任务存在≥2种有效执行路径、动作可映射为多种操作序列、或格式/范围/工具链/输出形式等维度未指定。触发信号：模糊动词（设计/分析/做一下/优化）、泛指名词未消解、缺少必要参数的新建类任务。豁免：纯事实查询、读文件/展示内容（不涉及修改或生成）。触发后执行6阶段信息对齐流水线，用AskUserQuestion原生工具产出结构化需求确认单交付下游。"
version: 14
domain: meta
author: skill-evolution
created_at: '2026-07-15T13:48:48.453160+00:00'
evolved_at: '2026-07-16T15:00:00.000000+00:00'
parent_hash: 64702e8a315f
tags:
- information-alignment
- requirement-extraction
- chinese
- meta-skill
evolution_round: 3
---

# 信息对齐 Skill (Info Align)

在用户任务请求模糊或不完整时，用最小交互成本消除 AI 与用户之间的信息不对称，产出一份结构化需求确认单。下游 Skill 直接消费确认单，无需再次对齐。

## 🛑 触发门控

读到本节后，不得调用任何工具或读取任何文件。先完成以下判定。

### 判定准则

本 Skill 触发当且仅当用户请求中存在**未解决的决策点**。

> 决策点：Agent 执行时存在 ≥2 种有效选项、且该选择会改变执行路径的任何信息缺口。

### 判定流程

逐项检查以下 3 类决策点。**任一类命中 → 立即执行 Phase 1。全未命中且不在豁免范围 → 跳过本 Skill。**

1. **指代未消解** — 请求中的名词短语无法从上下文唯一确定所指对象
2. **动作多义** — 请求中的动词在工具层面可映射为 ≥2 种不同的操作序列
3. **维度开放** — 任务在格式、范围、工具链、输出形式等维度存在未指定的自由度

### 反模式

以下行为模式是本 Skill 被跳过的典型信号：

- 为推测用户意图而发起 read / glob / ls — 这正是 Phase 1 要收集的上下文
- 将未消解的泛指词自行代入为当前环境中的某个具体实例
- 在多种实现路径之间，凭"常见做法"直接选择其一

### Phase 1 成本

不调用工具、不分析、不向用户提问。仅将已有信息填入 TaskContext schema。秒级完成。

---

## 触发条件详解

默认触发所有任务。

仅当任务同时满足以下 3 项时才可跳过：
1. 用户请求中每个动词/动作只有唯一无歧义的解释
2. 无需任何额外输入即可完整执行（无隐性维度需决策）
3. 不存在可选的格式、风格、范围、工具或技术选型

豁免白名单（必须严格命中，不可类推）：
- 纯事实查询（"Python 是什么"）
- 查找/读取/展示文件或代码（不涉及修改或生成）

---

## 数据契约

字段模型 `{ key, value, source, status, required, risk, constraint, options }` 是贯穿全部阶段的唯一载体。每个阶段读入上一个阶段的结构化输出、丰富它、输出下一个阶段的结构化输出。

```
Phase 1          Phase 2          Phase 2.5           Phase 3          Phase 4        Phase 5           Phase 6
TaskContext ──► RawFields[] ──► QuadrantFields[] ──► FieldList[] ──► (UI渲染) ──► ResolvedFields[] ──► 下游
```

### TaskContext（阶段 1 输出）

```json
{
  "user_request": "string — 用户原始请求（必填）",
  "skill_source": "string | null — 下游 SKILL.md 关键段落",
  "conversation": [
    {"role": "user | assistant", "content": "string"}
  ],
  "meta": "string | null — 上传文件元信息"
}
```

### RawField（阶段 2 输出，数组中每个元素）

```json
{
  "pattern": "required | default | optional | constraint | output | execution",
  "key": "string — 字段名",
  "value": "string | null",
  "source": "user_request | conversation | skill_source | meta",
  "sentence": "string — 匹配到的原句"
}
```

### QuadrantField（阶段 2.5 输出，数组中每个元素）

```json
{
  "key": "string — 字段名",
  "source": "quadrant_1 | quadrant_2 | quadrant_4",
  "status": "missing | defaulted",
  "required": true | false,
  "value": "string | null",
  "options": ["string", "string", "string"] | null,
  "risk": "warning | null",
  "constraint": "string | null"
}
```

> 象限❸ 不产生 QuadrantField，触发维度展开（见特殊处理）。

### Field（阶段 3 输出 = 规范化字段模型，FieldList[]）

```json
{
  "key": "string",
  "value": "string | null",
  "source": "user_request | conversation | skill_source | quadrant_n | dependency | meta",
  "status": "locked | defaulted | missing | conflicting",
  "required": true | false,
  "risk": "warning | null",
  "constraint": "string | null",
  "options": ["string", "string", "string"] | null
}
```

生成 `options` 规则：覆盖最可能的 3 种不同方向，按推荐度降序排列，第 1 个为推荐项。仅 `status` 为 `missing` 或 `defaulted` 时生成。

### ResolvedField（阶段 5 输出，交付下游）

```json
{
  "key": "string",
  "value": "string",
  "status": "locked | resolved"
}
```

---

## 核心流程

### 阶段 1：Context Extraction

分别收集各项来源，**填入 TaskContext JSON schema**。不拼接、不合并、不推理。

| 来源 | 字段 | 要求 |
|------|------|------|
| User Request | `user_request` | 必填，用户原话 |
| Skill Source | `skill_source` | 可选，下游 SKILL.md 全文或关键段落 |
| Conversation History | `conversation` | 可选，本会话相关历史消息，按 role+content 记录 |
| External Metadata | `meta` | 可选，上传文件元信息 |

输出 TaskContext JSON，进入阶段 2。

> **重申**：Phase 1 是触发门控自检的产物。如果你还没执行自检就跳到了这里——退回，先过门控。

---

### 阶段 2：Requirement Extraction

对 TaskContext 的 `user_request` 和 `conversation` 字段应用 6 类语义模式，**只提取显式信息，不判断缺什么**。每命中一个模式输出一个 RawField。

| 关键词 | pattern | 字段设置 |
|--------|---------|---------|
| 需要、必须、请提供、务必 | `required` | `required: true`，value = 原文中紧随的值 |
| 可以、省略、可选、若不需要可 | `optional` | `required: false` |
| 默认、通常、若未指定、一般情况下 | `default` | `required: false`，value = 默认值 |
| 不要、禁止、不得、切勿、严禁 | `constraint` | constraint = 约束描述 |
| 输出、生成、返回、产出、格式为 | `output` | — |
| 优先、首先、最后、先…再 | `execution` | — |

规则：
- 只关心语义模式，不关心领域
- 仅提取显式信息
- 同一句子多模式命中，按 `required` > `default` > `optional` > `constraint` 优先级只取最高优先级
- 未命中任何模式的文本丢弃
- "需要/必须"的主语或宾语是"你/AI/您"时，不作为 `required` 提取

**禁止只输出自然语言摘要——必须输出 RawFields[] JSON 数组。** 无命中时输出 `[]`。

---

### 阶段 2.5：四象限发问

Agent 用四象限视角依次自问，扫描 TaskContext，补充阶段 2 可能遗漏的字段。每个产出按 QuadrantField schema 输出。

**象限❶** — 用户以为我知道了但其实不知道什么？
同领域任务中"成对出现"但用户没提的信息。用户用了专有名词但没展开的。
→ `status: "missing"`, `source: "quadrant_1"`, 生成 3 个 options，第 1 个为最推荐选项

> 若存在 Skill Source，扫描其中 required input parameters，对比 user_request，找出用户隐式假设你已知的字段。

**象限❷** — 用户知道但嫌麻烦没说全的？
有多个可选项、用户心里有偏好但懒得逐一指定的维度。
→ `status: "defaulted"`, `source: "quadrant_2"`, value 预填最常见选项，生成 3 个 options，第 1 个为预填值

**象限❸** — 用户自己也不确定、可能指向多种方向的？
用词本身模糊（"分析""优化""做一下"）、缺乏限定条件。
→ 不产生 QuadrantField，触发**维度展开**（见特殊处理）

**象限❹** — 用户根本不知道但执行会遇到的坑？
同类任务前置条件。默认值兜底但某些情况下默认值可能错误。
→ `status: "defaulted"`, `source: "quadrant_4"`, `risk: "warning"`，生成 3 个 options

规则：
- 不重复阶段 2 已有的 key
- 仅 `status` 为 `missing` 或 `defaulted` 时生成 options
- options 覆盖不同方向、互斥，3 个以内

**禁止只输出自然语言推理——必须输出 QuadrantFields[] JSON 数组。**

---

### 阶段 3：Field Reasoning（确定性合并 SOP）

以下 5 步按顺序执行，每步的输出是下一步的输入。不跳过、不自行发挥。

---

**Step 1 — 合并去重**

```
输入: RawFields[] + QuadrantFields[]
对于每个 QuadrantField:
  如果 RawFields 中存在 key 相同的 RawField → 丢弃该 QuadrantField
  如果 RawFields 中不存在 → 保留
结果: 合并后的字段集合
```

---

**Step 2 — 转换为规范化 Field**

将每个 RawField 和保留的 QuadrantField 转换为统一的 Field schema：

| 来源 | 转换规则 |
|------|---------|
| RawField, pattern=required | `required=true`, `source`=原 source, `value`=原 value |
| RawField, pattern=default | `required=false`, `source`=原 source, `value`=原 value |
| RawField, pattern=optional | `required=false`, `source`=原 source, `value`=null |
| RawField, pattern=constraint | `required=false`, `constraint`=原 value |
| RawField, pattern=output | `required=false` |
| RawField, pattern=execution | `required=false` |
| QuadrantField | 原字段映射，schema 已对齐 |

---

**Step 3 — 状态判定**

按顺序应用以下规则（命中即停止）：

| 优先级 | 条件 | 赋 status |
|--------|------|----------|
| 1 | 来自 `user_request` 且有明确值 | `locked` |
| 2 | 来自 `conversation` 且有明确值 | `locked` |
| 3 | 有 default 值（RawField pattern=default 或 QuadrantField status=defaulted） | `defaulted` |
| 4 | `required=true` 且 `value` 为空 | `missing` |
| 5 | `required=false` 且 `value` 为空 | `defaulted`，value 填入通用基线 |
| 6 | 同一 key 来自多个 source 且值不同，无法裁决 | `conflicting` |

---

**Step 4 — 字段依赖推理**

对每个 `status=locked` 的字段，检查其 key/value 组合是否触发已知依赖关系（如"估值方法"=DCF → 需要 WACC、增长率）。如有，追加新 Field：

```json
{
  "key": "依赖字段名",
  "status": "missing",
  "required": true,
  "source": "dependency",
  ...
}
```

---

**Step 5 — 生成 options**

对每个 `status` 为 `missing` 或 `defaulted` 的字段：
- 已有 options → 保留
- 无 options → 生成 3 个（覆盖不同方向，推荐度降序，第 1 个为推荐项）

对 `status=locked` 的字段：`options = null`。

---

**最终输出 FieldList[] JSON。**

---

### 阶段 4：生成需求确认单

从 FieldList 中读取字段，分两步输出。

**第一步**：筛选 `status=locked` 的字段，纯文本摘要：

```
✅ 已确认
- 任务：客户流失预测模型
- 数据格式：CSV
（无 locked 字段则跳过此步）
```

**第二步**：对 `status=missing` 和 `status=defaulted` 的字段，检测平台能力，选择交互模式。

检查当前平台是否提供**原生问答工具**——即具有可点击选项/按钮的选择器组件，支持预设选项并自动附带自定义文本输入入口。典型如 opencode 的 `question` 工具。若存在此类工具则走分支 A，否则走分支 B。

---

#### 分支 A：原生交互按钮

调用平台原生问答工具，将 ⚠️ 和 ❓ 字段打包为交互式选项。完整字段→工具参数映射示例见 `examples/branch-a-native-tool.md`。

| 字段属性 | 映射目标 | 说明 |
|---------|----------|------|
| `options[0]` | 第 1 个选项，label 为 `"<值> (推荐)"` | defaulted 字段用默认值，missing 字段用最推荐值 |
| `options[1]` | 第 2 个选项 | — |
| `options[2]` | 第 3 个选项 | — |
| `key` | 问答工具的 `header`（≤30 字符） | 字段名 |
| 工具内置 custom | 自定义输入入口 | 不手动添加"自定义"选项 |
| `risk=warning` | 写入推荐选项的 description | 附加风险提示 |

调用策略：
- `missing` 字段排在 `defaulted` 字段前面
- 字段总数 ≤ 7 时一次全部展示；> 7 时分两轮（第一轮 missing，第二轮 defaulted）
- 所有字段为单选
- 禁止手写 A/B/C 文本——必须交由原生工具渲染

---

#### 分支 B：纯文本降级

平台无原生问答工具时，退化为纯文本逐字段交互：

```
❓ 数据来源
A. CSV / Excel 本地文件 (推荐)
B. 数据库直连
C. API 接口
回复 A/B/C，或直接输入自定义值
```

规则：
- `defaulted` 字段：`options[0]` 标注 "(默认)"
- `missing` 字段：`options[0]` 标注 "(推荐)"
- 一次只展示一个字段，用户回复后弹出下一个
- `missing` 字段优先于 `defaulted` 字段
- 在第一个字段后附带提示："可随时回复「确认」采用所有默认/推荐值"
- 禁止调用原生问答工具，禁止 HTML 按钮

---

### 阶段 5：Validate — 生成 ResolvedFields

根据阶段 4 选择的模式，走对应的结果处理路径，最终输出 ResolvedFields[]。

---

#### 分支 A：处理原生工具返回

解析平台原生工具的返回值（典型格式为 `<header>: <selected_label>` 映射）：
- 去掉 label 中的 "(推荐)"、"(默认)" 后缀 → 得到最终值
- 用户通过工具内置 custom 入口输入的值 → 直接作为字段值
- 将所有 locked 字段 + 解析后的字段合入 ResolvedFields

完成后回显一句话理解摘要，然后交给阶段 6。

---

#### 分支 B：解析纯文本回复

逐字段状态机：

| 用户输入 | 处理 |
|---------|------|
| `A` / `B` / `C`（大写单字母） | 选定对应 option 作为当前字段值。回显："已选 `<key>` = `<值>`"，弹出下一个字段 |
| 自定义文本（非 A/B/C 且非全局指令） | 将文本作为当前字段值。回显："已选 `<key>` = `<自定义值>`"，弹出下一个字段 |
| `"确认"` / `"开始"` / `"没问题"` | 剩余 missing 字段取 `options[0]`，剩余 defaulted 字段取其 `value`。一次性回显，结束 |
| `"重置 <字段名>"` | 将该字段重置为未选状态，重新弹出该字段 |

所有字段完成后，将 locked 字段 + 已解析字段合入 ResolvedFields。

---

**ResolvedFields 输出格式：**

```json
[
  {"key": "任务", "value": "客户流失预测模型", "status": "locked"},
  {"key": "数据来源", "value": "CSV / Excel 本地文件", "status": "resolved"},
  {"key": "技术栈", "value": "Python + scikit-learn", "status": "resolved"}
]
```

---

### 阶段 6：启动下游 Skill

将 ResolvedFields[] 完整交付给下游 Skill。下游按 `key` 取 `value`，无需再次询问用户。

---

## 特殊处理

| 用户输入 | 策略 | 适用分支 |
|---------|------|---------|
| "随便"/"你决定"/"都可以" | missing 字段取 options[0]，defaulted 字段取 value，跳过交互，告警后交付 | A / B |
| "直接做，不用确认" | 跳过对齐流程，全默认，告警后交付 | A / B |
| "跟上次一样" | 从 Conversation History 定位复用（>3轮交互则降级） | A / B |
| "不是，我要的不是这个" | 不归 Info Align 处理；建议追问具体偏差 | A / B |
| 维度展开 | 象限❸ 触发，不输出确认单，输出若干分类方向帮助用户聚焦。随后从象限❸ 退出，用户重新提供具体需求后再进入阶段 1 | A / B |
| "A"/"B"/"C"（大写字母） | 选定当前字段对应选项，回显后弹出下一个字段 | 仅分支 B |
| 自定义文本回复 | 将文本作为当前字段值，回显后弹出下一个字段 | 仅分支 B |

===

## Appendix

### 输出中禁止出现（高频遗漏项）

- 字段 status 内部标识（locked / defaulted / missing / conflicting）——仅可在内部 JSON 中使用
- 四象限标签（象限❶、象限❷等）——仅可在内部推理中使用
- source 标识（user / skill / quadrant / meta）——仅可在内部 JSON 中使用
- HTML 注释（<!-- @option ... -->）
- 文件路径引用
- "示例："前缀 — 直接以自然语言呈现
- "可逆/不可逆"标签
- "skip / display / display_warning / force"策略名
- 阶段标签（阶段1、阶段2、阶段2.5等）
- 流程阶段名称（Context Extraction、Requirement Extraction 等）
- RawField / QuadrantField / FieldList 等内部 JSON ——禁止展示给用户

### 确认单结构强制项

- ALWAYS 使用 ✅ ⚠️ ❓ 三色标记，不得引入其他符号
- ALWAYS 按区块结构输出，无内容板块不展示
- ALWAYS 在确认单末尾附操作提示（"回复确认开始"或等效表述）
- NEVER 在用户可见输出中展示内部推理过程
- NEVER 对简单问答/事实查询触发票对齐流程
- BEFORE outputting, review your response to ensure no internal process artifacts are visible to the user

===
