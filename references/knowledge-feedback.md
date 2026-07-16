# 知识回流协议（未来平台层实现）

本 Skill 自身不执行存储和修改。以下协议声明信息对齐完成后，平台层可执行的持久化操作。

---

## 触发器

任务正常完成后触发（用户确认"满意"或下游 Skill 返回成功）。

## 回流数据

### 1. 置信度更新

对本次任务中使用到的每条默认选项：

| 本次行为 | 调整 |
|---------|------|
| 用户确认（未改） | confidence += adjustment_factor.confirm |
| 用户主动修改为 X | confidence += adjustment_factor.overridden |
| 用户未提及（使用了默认值但未显式确认） | confidence 不变 |

所有 confidence 值 clamp 到 [min, max] 范围。

### 2. 新领域模板记录

如果本次任务类型不在现有的 12 大类中：

```json
{
  "task_type": "从用户原始请求中提取的任务标签",
  "derived_from": "最接近的12大类之一或'novel'",
  "first_used": "ISO日期",
  "use_count": 1,
  "fields": {
    "风格": "本次实际使用的值",
    "长度": "本次实际使用的值",
    ...
  }
}
```

新领域初始置信度 seed = 0.5（单次样本，不可过高）。

### 3. 模式漂移检测

触发条件：某个字段的 conf 已到达 max(0.95)，但用户连续 3 次手动改为同一备选值。

处理：将 conf 重置为 0.50，切换默认值为备选值，记录迁移日志。

## 存储位置

由平台层负责。Skill 不指定具体存储实现。推荐的存储格式：
- 键值对：`info-align:{user_id}:confidence:{field_key}`
- 文档型：`info-align:{user_id}:domain-templates`

## 不负责的事情

- 不负责实际存储（Skill 无持久化能力）
- 不负责跨会话读取（由 Agent 框架在 Skill 启动时注入）
- 不负责修改自己的文件（SKILL.md 是只读的）
- 不处理多用户/多租户（平台层职责）
