# 代码技术类预设

<!-- @class: 9 -->
<!-- @category: 代码技术 -->
<!-- @skills: 代码审查,README生成,项目文档,CI/CD模板,架构设计,Prompt Lab Notes -->

## 通用维度

- **风格**: 中性 (conf=0.50, 可逆) → display_warning
- **长度**: 中 (conf=0.50, 可逆) → display_warning
- **格式**: 纯文本/Markdown + 代码块 (conf=0.70, 可逆) → skip
- **深度**: 标准 (conf=0.60, 可逆) → skip
- **受众**: 开发者/技术团队 (conf=0.80, 可逆) → skip
- **语言**: 中文+代码 (conf=0.60, 可逆) → skip

## 特色选项

### 代码审查重点 (conf=0.50, 可逆)
- **全维度** (default) — 安全+性能+可维护性均衡
- 安全检查优先（注入/SQL/XSS/权限/敏感信息）
  `"🔴 L45: 字符串拼接构造SQL，存在注入风险。建议参数化查询。"`
- 性能优先（复杂度/内存/IO/N+1问题）
- 可维护性优先（命名/函数长度/圈复杂度/测试覆盖/注释）

### 文档语言 (conf=0.60, 可逆) → skip
- **中文文档+代码块** (default)
- 纯英文文档
- 中英双语注释

### 代码风格参考 (conf=0.60, 可逆) → skip
- **项目已有风格** (default) — 从代码推断
- PEP 8 (Python)
- Google Style Guide
- Airbnb Style Guide
- 不强制特定风格

## 盲区预警

- 安全审查不能替代专业安全审计
- 性能建议基于静态分析，实际瓶颈应通过 profiling 确认
