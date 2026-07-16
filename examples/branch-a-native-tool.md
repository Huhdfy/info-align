# 分支 A：原生交互按钮 — 完整示例

> 场景：用户说 `"帮我做一个客户流失预测模型"`，当前平台为 **opencode**（提供 `question` 原生问答工具）。

---

## 阶段 1：上下文收集

```
Task Context:
- User Request: "帮我做一个客户流失预测模型"
- Skill Source: (无下游 SKILL.md)
- Conversation History: (无历史)
- External Metadata: (无)
```

---

## 阶段 2：语义提取（Python parser）

将 Task Context 输入 `scripts/requirement_parser.py`：

```bash
echo "帮我做一个客户流失预测模型" | python scripts/requirement_parser.py --pretty
```

输出（该句未命中任何语义模式关键词）：

```json
[]
```

Parser 无产出，阶段 2 交白卷——正常。

---

## 阶段 2.5：四象限发问（LLM）

Agent 执行四象限自问：

**象限 ❶** — 用户以为我知道但没说：
- 数据来源（CSV？DB？API？）→ `missing`，options = [CSV文件, 数据库, API接口]
- 技术栈（sklearn？XGBoost？PyTorch？）→ `missing`，options = [scikit-learn, XGBoost/LightGBM, PyTorch]
- 输出形式（Notebook？脚本？页面？）→ `missing`，options = [Jupyter Notebook, Python脚本, Streamlit页面]

**象限 ❷** — 用户嫌麻烦没指定：
- 评估指标 → `defaulted`，value = AUC-ROC + F1，options = [AUC-ROC+F1, Recall优先, Precision优先]

**象限 ❸** — 用户自己也不确定：无触发

**象限 ❹** — 盲区预警：
- 数据不平衡处理 → `defaulted`，risk=warning，value = SMOTE，options = [SMOTE, class_weight, 不处理]

---

## 阶段 3：合并 + 状态判定

```
字段列表:
┌─────────────────┬──────────┬──────────────────────────────────┬──────────┐
│ key             │ status   │ value / options                  │ required │
├─────────────────┼──────────┼──────────────────────────────────┼──────────┤
│ 任务             │ locked   │ "客户流失预测模型"                 │ true     │
│ 数据来源          │ missing  │ [CSV文件, 数据库, API]            │ true     │
│ 技术栈            │ missing  │ [scikit-learn, XGBoost, PyTorch] │ true     │
│ 输出形式          │ missing  │ [Notebook, 脚本, Streamlit]       │ true     │
│ 评估指标          │ defaulted│ [AUC-ROC+F1, Recall, Precision]  │ false    │
│ 数据不平衡处理    │ defaulted│ [SMOTE, class_weight, 不处理]     │ false    │
└─────────────────┴──────────┴──────────────────────────────────┴──────────┘
```

---

## 阶段 4：生成确认单

### 第一步：纯文本 ✅ 已确认摘要

```
✅ 已确认
- 任务：客户流失预测模型
- 类型：二分类（是否流失）
```

### 第二步：调用原生问答工具（opencode `question`）

字段到 tool 参数的完整映射：

```
┌─────────────────┬──────────────────────────────────────────────────────┐
│ 字段 (key)       │ → question 参数                                      │
├─────────────────┼──────────────────────────────────────────────────────┤
│ 数据来源          │ header="数据来源"                                    │
│ (missing)        │ options=[                                           │
│                  │   {label="CSV / Excel 本地文件 (推荐)",               │
│                  │    description="离线分析最通用"},                     │
│                  │   {label="数据库直连",                                │
│                  │    description="MySQL/PostgreSQL 等关系型数据库"},     │
│                  │   {label="API 接口",                                 │
│                  │    description="通过 REST API 拉取数据"}              │
│                  │ ]                                                   │
├─────────────────┼──────────────────────────────────────────────────────┤
│ 技术栈            │ header="技术栈"                                      │
│ (missing)        │ options=[                                           │
│                  │   {label="Python + scikit-learn (推荐)",             │
│                  │    description="传统机器学习，快速搭建"},              │
│                  │   {label="Python + XGBoost / LightGBM",             │
│                  │    description="树模型，精度更高"},                    │
│                  │   {label="PyTorch 深度学习",                          │
│                  │    description="神经网络，适合复杂特征"}               │
│                  │ ]                                                   │
├─────────────────┼──────────────────────────────────────────────────────┤
│ 输出形式          │ header="输出形式"                                    │
│ (missing)        │ options=[                                           │
│                  │   {label="Jupyter Notebook (推荐)",                  │
│                  │    description="完整分析报告，含图表"},                │
│                  │   {label="Python 脚本 + 模型文件",                    │
│                  │    description="独立可部署脚本"},                     │
│                  │   {label="Streamlit 交互页面",                       │
│                  │    description="可在线操作的仪表板"}                  │
│                  │ ]                                                   │
├─────────────────┼──────────────────────────────────────────────────────┤
│ 评估指标          │ header="评估指标"                                    │
│ (defaulted)      │ options=[                                           │
│                  │   {label="AUC-ROC + F1 (推荐)",                      │
│                  │    description="业界标准，平衡评估"},                  │
│                  │   {label="Recall 优先",                              │
│                  │    description="宁可误报也要抓住更多流失客户"},         │
│                  │   {label="Precision 优先",                           │
│                  │    description="减少误报，精准营销"}                   │
│                  │ ]                                                   │
├─────────────────┼──────────────────────────────────────────────────────┤
│ 数据不平衡处理     │ header="数据不平衡处理"                              │
│ (defaulted,      │ options=[                                           │
│  risk=warning)   │   {label="SMOTE 过采样 (推荐)",                      │
│                  │    description="合成少数类样本 ⚠️ 若数据量极大可能OOM"},│
│                  │   {label="class_weight 加权",                        │
│                  │    description="不改数据，仅调整损失权重"},             │
│                  │   {label="不做特殊处理",                              │
│                  │    description="仅在类别比例尚可时使用"}               │
│                  │ ]                                                   │
└─────────────────┴──────────────────────────────────────────────────────┘
```

完整 `question` 工具调用（JSON 参数）：

```json
{
  "questions": [
    {
      "question": "请选择数据来源：",
      "header": "数据来源",
      "options": [
        {"label": "CSV / Excel 本地文件 (推荐)", "description": "离线分析最通用"},
        {"label": "数据库直连", "description": "MySQL/PostgreSQL 等关系型数据库"},
        {"label": "API 接口", "description": "通过 REST API 拉取数据"}
      ]
    },
    {
      "question": "请选择技术栈：",
      "header": "技术栈",
      "options": [
        {"label": "Python + scikit-learn (推荐)", "description": "传统机器学习，快速搭建"},
        {"label": "Python + XGBoost / LightGBM", "description": "树模型，精度更高"},
        {"label": "PyTorch 深度学习", "description": "神经网络，适合复杂特征"}
      ]
    },
    {
      "question": "请选择输出形式：",
      "header": "输出形式",
      "options": [
        {"label": "Jupyter Notebook (推荐)", "description": "完整分析报告，含图表"},
        {"label": "Python 脚本 + 模型文件", "description": "独立可部署脚本"},
        {"label": "Streamlit 交互页面", "description": "可在线操作的仪表板"}
      ]
    },
    {
      "question": "请选择评估指标：",
      "header": "评估指标",
      "options": [
        {"label": "AUC-ROC + F1 (推荐)", "description": "业界标准，平衡评估"},
        {"label": "Recall 优先", "description": "宁可误报也要抓住更多流失客户"},
        {"label": "Precision 优先", "description": "减少误报，精准营销"}
      ]
    },
    {
      "question": "请选择数据不平衡处理策略：",
      "header": "数据不平衡",
      "options": [
        {"label": "SMOTE 过采样 (推荐)", "description": "合成少数类样本 ⚠️ 若数据量极大可能OOM"},
        {"label": "class_weight 加权", "description": "不改数据，仅调整损失权重"},
        {"label": "不做特殊处理", "description": "仅在类别比例尚可时使用"}
      ]
    }
  ]
}
```

---

## 阶段 5：处理返回 + 回显

opencode `question` 工具返回示例：

```
User has answered your questions:
"请选择数据来源："="CSV / Excel 本地文件 (推荐)",
"请选择技术栈："="Python + scikit-learn (推荐)",
"请选择输出形式："="Jupyter Notebook (推荐)",
"请选择评估指标："="AUC-ROC + F1 (推荐)",
"请选择数据不平衡处理策略："="SMOTE 过采样 (推荐)".
```

解析规则：
1. 按 `"<header>"="<label>"` 逐条提取
2. 去掉 label 中的 `(推荐)` / `(默认)` 后缀
3. 若为自定义输入 → 直接取值

解析后字段值：

```
数据来源      = CSV / Excel 本地文件
技术栈        = Python + scikit-learn
输出形式      = Jupyter Notebook
评估指标      = AUC-ROC + F1
数据不平衡    = SMOTE 过采样
```

回显（一句话）：

> 已确认：用 CSV 数据，Python + scikit-learn，输出 Jupyter Notebook，以 AUC-ROC+F1 评估，SMOTE 处理失衡。

---

## 阶段 6：交付下游 Skill

完整确认单字段（locked + resolved），交给下游直接消费，无需再次询问。
