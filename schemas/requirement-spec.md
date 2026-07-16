# 需求确认单结构定义

信息对齐 Skill 向下的接口规范。任何下游 Skill 读取此结构即可开始执行，无需再次对齐。

## 字段

```
{
  "task": "任务一句话描述",
  "category": "12大类之一，如'商业报告'",
  "target_skill": "目标下游Skill名称或slug",

  "confirmed": [
    {
      "key": "维度名",
      "value": "确认值",
      "source": "user_provided | extracted_from_context"
    }
  ],

  "defaults": [
    {
      "key": "维度名",
      "value": "采用的默认值",
      "confidence": 0.75,
      "risk_label": "none | warning",
      "example_snippet": "生成的示例文字片段"
    }
  ],

  "pending": [
    {
      "key": "维度名",
      "reason": "执行中何时暂停确认",
      "fallback": "如用户跳过，使用的兜底值"
    }
  ],

  "warnings": [
    {
      "key": "前提条件",
      "value": "使用的默认值",
      "risk_description": "使用该默认值的潜在风险"
    }
  ]
}
```

## 输出格式（面向用户）

```markdown
【需求确认单】

任务：XXX
类别：YYY → 目标Skill：ZZZ

已确认（N 项）：
  ✅ 维度A：值A
  ✅ 维度B：值B

默认值（M 项，可随时修改）：
  ⚠️ 维度C：值C（默认，conf 0.7）
     示例：[生成示例]

待澄清（K 项，执行中将暂停确认）：
  ❓ 维度D：说明

盲区预警（L 项，已使用默认值）：
  ⚠️ 前提条件E：使用的默认值 — 风险说明

---
回复"确认"即可开始执行。回复"改 [维度名]"可单独修改某项。
```

## 下游Skill消费协议

下游 Skill 在收到确认单后：

1. 从 `confirmed` 读取用户明确提供的值 → 直接使用
2. 从 `defaults` 读取带 confidence 的默认值 → 直接使用
3. 从 `pending` 读取待确认项 → 在执行到对应阶段时暂停并询问
4. 从 `warnings` 读取盲区预警 → 在执行时注意这些前提条件，并在结果中标注风险

下游 Skill 不得：
- 再次询问 confirmed 或 defaults 中已锁定的值
- 以"不确定"为由忽略 defaults 中的值
