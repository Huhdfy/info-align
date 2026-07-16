# 分支 A：原生交互按钮 — 完整示例

> 场景：用户说 `"帮我做一个客户流失预测模型"`，当前平台为 **opencode**（提供 `question` 原生问答工具）。

---

## 阶段 1：Context Extraction → TaskContext

```json
{
  "user_request": "帮我做一个客户流失预测模型",
  "skill_source": null,
  "conversation": [],
  "meta": null
}
```

---

## 阶段 2：Requirement Extraction → RawFields[]

对 user_request 应用 6 类语义模式。该句未命中任何关键词：

```json
[]
```

---

## 阶段 2.5：四象限发问 → QuadrantFields[]

```json
[
  {
    "key": "数据来源",
    "source": "quadrant_1",
    "status": "missing",
    "required": true,
    "value": null,
    "options": ["CSV / Excel 本地文件", "数据库直连", "API 接口"],
    "risk": null,
    "constraint": null
  },
  {
    "key": "技术栈",
    "source": "quadrant_1",
    "status": "missing",
    "required": true,
    "value": null,
    "options": ["Python + scikit-learn", "Python + XGBoost / LightGBM", "PyTorch 深度学习"],
    "risk": null,
    "constraint": null
  },
  {
    "key": "输出形式",
    "source": "quadrant_1",
    "status": "missing",
    "required": true,
    "value": null,
    "options": ["Jupyter Notebook", "Python 脚本 + 模型文件", "Streamlit 交互页面"],
    "risk": null,
    "constraint": null
  },
  {
    "key": "评估指标",
    "source": "quadrant_2",
    "status": "defaulted",
    "required": false,
    "value": "AUC-ROC + F1",
    "options": ["AUC-ROC + F1", "Recall 优先", "Precision 优先"],
    "risk": null,
    "constraint": null
  },
  {
    "key": "数据不平衡处理",
    "source": "quadrant_4",
    "status": "defaulted",
    "required": false,
    "value": "SMOTE 过采样",
    "options": ["SMOTE 过采样", "class_weight 加权", "不做特殊处理"],
    "risk": "warning",
    "constraint": null
  }
]
```

> 象限❸ 未触发。

---

## 阶段 3：确定性合并 → FieldList[]

**Step 1** — RawFields 为空，QuadrantFields 全部保留。

**Step 2** — QuadrantField 已是 Field schema 子集，直接映射。

**Step 3** — 状态判定：

| 字段 | 条件 | status |
|------|------|--------|
| 数据来源 | required=true, value=null | `missing` |
| 技术栈 | required=true, value=null | `missing` |
| 输出形式 | required=true, value=null | `missing` |
| 评估指标 | 有 default 值 | `defaulted` |
| 数据不平衡处理 | 有 default 值, risk=warning | `defaulted` |

**Step 4** — 无字段依赖触发。

**Step 5** — options 已生成，保留。

最终 FieldList：

```json
[
  {
    "key": "任务",
    "value": "客户流失预测模型",
    "source": "user_request",
    "status": "locked",
    "required": true,
    "risk": null,
    "constraint": null,
    "options": null
  },
  {
    "key": "数据来源",
    "value": null,
    "source": "quadrant_1",
    "status": "missing",
    "required": true,
    "risk": null,
    "constraint": null,
    "options": ["CSV / Excel 本地文件", "数据库直连", "API 接口"]
  },
  {
    "key": "技术栈",
    "value": null,
    "source": "quadrant_1",
    "status": "missing",
    "required": true,
    "risk": null,
    "constraint": null,
    "options": ["Python + scikit-learn", "Python + XGBoost / LightGBM", "PyTorch 深度学习"]
  },
  {
    "key": "输出形式",
    "value": null,
    "source": "quadrant_1",
    "status": "missing",
    "required": true,
    "risk": null,
    "constraint": null,
    "options": ["Jupyter Notebook", "Python 脚本 + 模型文件", "Streamlit 交互页面"]
  },
  {
    "key": "评估指标",
    "value": "AUC-ROC + F1",
    "source": "quadrant_2",
    "status": "defaulted",
    "required": false,
    "risk": null,
    "constraint": null,
    "options": ["AUC-ROC + F1", "Recall 优先", "Precision 优先"]
  },
  {
    "key": "数据不平衡处理",
    "value": "SMOTE 过采样",
    "source": "quadrant_4",
    "status": "defaulted",
    "required": false,
    "risk": "warning",
    "constraint": null,
    "options": ["SMOTE 过采样", "class_weight 加权", "不做特殊处理"]
  }
]
```

---

## 阶段 4：生成确认单

### 第一步：✅ 已确认（locked 字段）

```
✅ 已确认
- 任务：客户流失预测模型
```

### 第二步：原生 question 工具调用

从 FieldList 中取 `status=missing` 和 `status=defaulted` 的字段，映射为 question 参数：

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

## 阶段 5：生成 ResolvedFields[]

工具返回示例：

```
User has answered your questions:
"请选择数据来源："="CSV / Excel 本地文件 (推荐)",
"请选择技术栈："="Python + scikit-learn (推荐)",
"请选择输出形式："="Jupyter Notebook (推荐)",
"请选择评估指标："="AUC-ROC + F1 (推荐)",
"请选择数据不平衡处理策略："="SMOTE 过采样 (推荐)".
```

解析：去掉 "(推荐)" 后缀，合入 locked 字段 → ResolvedFields：

```json
[
  {"key": "任务", "value": "客户流失预测模型", "status": "locked"},
  {"key": "数据来源", "value": "CSV / Excel 本地文件", "status": "resolved"},
  {"key": "技术栈", "value": "Python + scikit-learn", "status": "resolved"},
  {"key": "输出形式", "value": "Jupyter Notebook", "status": "resolved"},
  {"key": "评估指标", "value": "AUC-ROC + F1", "status": "resolved"},
  {"key": "数据不平衡处理", "value": "SMOTE 过采样", "status": "resolved"}
]
```

回显：**已确认：CSV 数据，Python + scikit-learn，输出 Jupyter Notebook，AUC-ROC+F1 评估，SMOTE 处理失衡。**

---

## 阶段 6：交付下游 Skill

将 ResolvedFields[] 完整交给下游，下游按 `key` 取 `value`，无需再次询问。
