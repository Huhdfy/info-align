# 商业报告类预设

<!-- @class: 1 -->
<!-- @category: 商业报告 -->
<!-- @skills: 深度报告,行业研究,尽调,投决备忘录,市场速览,业绩快评,晨会纪要,财务分析,资产配置,基金分析,可比公司分析,研报摘要,债券募集,招股书,并购方案,退出分析,路演材料,读年报,商业写作,桌面调研,调研纪要,访谈纪要,咨询报告,预算分析,标竿对比,风险评估,筛项目,方案框架 -->

## 通用维度

<!-- @通用维度 -->

<!-- @option: 风格 -->
<!-- @confidence: 0.85 @reversible: true @strategy: skip -->
- **风格**: 正式
  `"本报告从行业格局、商业模式、财务表现三个维度对标的公司进行深度分析。"`

<!-- @option: 长度 -->
<!-- @confidence: 0.70 @reversible: true @strategy: skip -->
- **长度**: 长 (>800字)
  `覆盖多维度、含数据表格、结论+建议`

<!-- @option: 格式 -->
<!-- @confidence: 0.80 @reversible: true @strategy: skip -->
- **格式**: 结构化报告
  `标题层级、数据表格、风险提示、附录引用`

<!-- @option: 深度 -->
<!-- @confidence: 0.60 @reversible: true @strategy: display_warning -->
- **深度**: 深度分析
  `多源交叉验证、量化分析、前瞻判断`

<!-- @option: 受众 -->
<!-- @confidence: 0.70 @reversible: false @strategy: display -->
- **受众**: 管理层/专业投资者
  `假定读者具备行业和财务知识`

<!-- @option: 语言 -->
<!-- @confidence: 0.80 @reversible: true @strategy: skip -->
- **语言**: 中文

## 特色选项

<!-- @option: 报告体例 -->
<!-- @confidence: 0.50 @reversible: true @strategy: display_warning -->
### 报告体例
- **券商研报体例** (default)
  `"1. 行业空间与竞争格局\n2. 商业模式与护城河\n3. 财务分析与盈利预测\n4. 估值与投资建议\n5. 风险提示"`
- **咨询报告体例**
  `"核心发现：XX行业正经历从规模驱动到效率驱动的结构性转变…\n建议A：优先投入研发以构建技术壁垒…"`
- **内部汇报体例**
  `"当前市场格局：三家头部企业占据65%市场份额…\n下一步行动：建议Q3启动A/B测试"`
- **监管报送体例**
  `按证监会/银保监会模板`

<!-- @option: 估值方法 -->
<!-- @confidence: 0.50 @reversible: true @strategy: display_warning -->
### 估值方法引用（仅投研类）
- **不涉及估值** (default)
- PE/PB/PS 相对估值
- DCF 绝对估值
- 可比公司分析

<!-- @option: 数据颗粒度 -->
<!-- @confidence: 0.50 @reversible: true @strategy: display_warning -->
### 数据颗粒度
- **年度趋势** (default)
- 季度拆解
- 月度追踪
- 周度快照

<!-- @option: 风险标注 -->
<!-- @confidence: 0.40 @reversible: true @strategy: display_warning -->
### 风险标注方式（尽调/投决专属）
- **红/黄/绿 三色** (default)
  `"🔴 客户集中度风险：前五大客户占比78%，最大客户占比35%"`
- 等级 1-5 评分
- 仅文字描述

<!-- @option: 图表 -->
<!-- @confidence: 0.50 @reversible: true @strategy: display_warning -->
### 图表要求
- **嵌入数据表格+文字分析** (default)
  `"| 年份 | 营收(亿) | YoY | 净利润(亿) | 净利率 |\n| 2023 | 45.2 | +12% | 8.1 | 17.9% |"`
- 仅文字描述，不制表
- 需生成可视化图表描述

## 盲区预警

<!-- @option: 数据来源 @strategy: warning -->
- 数据来源: 默认使用公开市场数据
- 预测假设: 估值中增长率/WACC使用行业均值，标注为估算
- 时效性: 结论基于截至生成日期的公开信息
