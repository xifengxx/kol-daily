# AI智能投研助手 — 设计系统规范（Design System）

## 1. 颜色体系（Color System）

### 基础色
| 名称 | 色值 | 用途 |
|------|------|------|
| 主色 Primary | #1D1D1F | 标题、重要文字、深色卡片背景 |
| 辅助色 Secondary | #86868B | 次要信息、说明文字、时间戳 |
| 强调色 Accent | #0071E3 | 链接、按钮、数据高亮、选中态 |
| 背景色 Background | #F5F5F7 | 页面背景、板块底色 |
| 卡片背景 Card | #FFFFFF | 内容区域、带1px #E5E5EA边框 |
| 边框色 Border | #E5E5EA | 分割线、卡片边框、表格边框 |
| 浅灰 Light | #F2F2F7 | 表头背景、悬停背景、标签底色 |

### 语义色（Semantic Colors）
| 名称 | 色值 | 用途 |
|------|------|------|
| 上涨 Red | #FF3B30 | A股/港股涨（中国市场习惯） |
| 下跌 Green | #34C759 | A股/港股跌 |
| 美股上涨 Green | #34C759 | 美股涨（国际市场习惯） |
| 美股下跌 Red | #FF3B30 | 美股跌 |
| 警告 Yellow | #FF9500 | 风险提示、中置信度 |
| 危险 Red | #FF3B30 | 高风险、低置信度、Veto触发 |
| 安全 Green | #34C759 | 高置信度、低风险、推荐态 |
| 中性 Gray | #8E8E93 | 中性情绪、无变化 |
| 信息 Blue | #0071E3 | 信息提示、可点击链接 |

### 图表色板（Chart Palette）
| 序号 | 色值 | 用途 |
|------|------|------|
| 1 | #0071E3 | 主数据系列 |
| 2 | #FF3B30 | 对比系列/跌幅 |
| 3 | #34C759 | 辅助系列/涨幅 |
| 4 | #FF9500 | 第三系列 |
| 5 | #5856D6 | 第四系列 |
| 6 | #AF52DE | 第五系列 |
| 7 | #FF2D55 | 第六系列 |
| 8 | #5AC8FA | 第七系列 |
| 9 | #FFCC00 | 第八系列 |
| 10 | #A2845E | 第十系列 |

## 2. 字体体系（Typography）

### 字体栈
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
```

### 字体层级
| 层级 | 大小 | 字重 | 行高 | 字间距 | 用途 |
|------|------|------|------|--------|------|
| H1 | 28px | 700 | 1.2 | -0.02em | 页面标题 |
| H2 | 22px | 600 | 1.3 | -0.01em | 板块标题 |
| H3 | 18px | 600 | 1.4 | 0 | 卡片标题 |
| H4 | 16px | 500 | 1.4 | 0 | 小节标题 |
| Body | 14px | 400 | 1.6 | 0 | 正文内容 |
| Body-S | 13px | 400 | 1.5 | 0 | 次要正文 |
| Caption | 12px | 400 | 1.4 | 0.01em | 说明文字、时间戳 |
| Data-L | 32px | 600 | 1.1 | -0.02em | 核心数据大字（股价、评分） |
| Data-M | 20px | 600 | 1.2 | 0 | 中等数据（涨幅、指标值） |
| Label | 11px | 500 | 1.3 | 0.02em | 标签、徽章（ uppercase 可选） |

## 3. 间距体系（Spacing）

### 基础单位：4px
| Token | 值 | 用途 |
|-------|-----|------|
| xs | 4px | 紧凑内边距、图标间距 |
| sm | 8px | 按钮内边距、列表项间距 |
| md | 16px | 卡片内边距（小）、元素间距 |
| lg | 24px | 卡片内边距（标准）、板块内部间距 |
| xl | 32px | 板块间距、页面边距 |
| 2xl | 48px | 大板块间距、页面顶部留白 |
| 3xl | 64px | 页面最大间距 |

### 布局规范
- 页面最大宽度：1200px（桌面端），居中
- 移动端边距：16px
- 平板边距：24px
- 桌面边距：32px
- 板块间距：32px（桌面）/ 24px（移动）
- 卡片内边距：24px
- 卡片间距：16px
- 网格：12列，gutter 16px

## 4. 组件规范（Components）

### 导航栏（Top Nav）
- 高度：56px
- 背景：#FFFFFF，底部1px #E5E5EA
- 左侧：产品Logo（24px高）+ 产品名称（16px 600）
- 中间：搜索框（圆角8px，高40px，背景#F5F5F7，placeholder"搜索股票、概念..."）
- 右侧：日期、通知图标、用户头像（32px圆形）
- 固定在顶部，z-index: 100

### 侧边栏（Sidebar）
- 宽度：240px（桌面）/ 64px（收起）
- 背景：#FFFFFF
- 右侧1px #E5E5EA边框
- 菜单项：高度48px，hover背景#F5F5F7，选中态左侧4px #0071E3竖线+文字#0071E3
- 图标：20px，文字14px 500
- 分组标题：12px 600 uppercase，#86868B，padding-top: 16px

### 卡片（Card）
- 背景：#FFFFFF
- 圆角：12px
- 边框：1px solid #E5E5EA（可选）
- 阴影：0 4px 16px rgba(0,0,0,0.08)（可选，用于悬浮卡片）
- 内边距：24px
- hover态：阴影加深 0 8px 24px rgba(0,0,0,0.12)，transform: translateY(-2px)，transition: all 0.3s ease

### 按钮（Button）
- 主要按钮：背景#0071E3，文字#FFFFFF，圆角8px，padding 10px 20px，font 14px 500
- 次要按钮：背景#F5F5F7，文字#1D1D1F，边框1px #E5E5EA，圆角8px
- 危险按钮：背景#FF3B30，文字#FFFFFF
- 幽灵按钮：背景透明，文字#0071E3
- hover：opacity 0.9，transition 0.2s
- 禁用：opacity 0.4，cursor not-allowed

### 标签/徽章（Badge）
- 高度：20px，padding 0 8px
- 圆角：10px（全圆角）
- 字体：11px 500
- 类型：primary(#0071E3/#FFFFFF)、success(#34C759/#FFFFFF)、warning(#FF9500/#FFFFFF)、danger(#FF3B30/#FFFFFF)、neutral(#F2F2F7/#1D1D1F)

### 表格（Table）
- 表头：背景#F2F2F7，文字#86868B，12px 500，padding 12px 16px
- 行：padding 14px 16px，border-bottom 1px #E5E5EA
- 行hover：背景#F5F5F7
- 选中行：左侧4px #0071E3竖线
- 无数据态：居中，图标+文字"暂无数据"

### 输入框（Input）
- 高度：40px，padding 0 14px
- 圆角：8px
- 背景：#F5F5F7
- 边框：1px solid transparent（focus时 #0071E3）
- 字体：14px 400
- focus：背景#FFFFFF，边框#0071E3，shadow 0 0 0 3px rgba(0,113,227,0.15)

### 下拉菜单（Dropdown）
- 背景：#FFFFFF
- 圆角：12px
- 阴影：0 8px 24px rgba(0,0,0,0.15)
- 选项高：40px，padding 0 16px
- 选项hover：背景#F5F5F7

### 模态框/弹窗（Modal）
- 遮罩：rgba(0,0,0,0.4)
- 内容区：背景#FFFFFF，圆角16px，max-width 600px，padding 24px
- 阴影：0 16px 48px rgba(0,0,0,0.2)
- 关闭按钮：右上角，24px，hover旋转90deg
- 动画：fadeIn 0.3s + scale 0.95→1

### 提示/Toast
- 背景：rgba(0,0,0,0.8)（深色）或 #FFFFFF（浅色）
- 圆角：12px
- padding：12px 20px
- 字体：14px 400
- 位置：顶部居中，fixed
- 动画：slideDown 0.3s + fadeIn

## 5. 图表规范（Charts）

### 使用 ECharts 5.6
- 所有图表通过CDN引入：`https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js`
- 图表容器高度：300px（标准），400px（大号），200px（小号）
- 图表背景：transparent（继承卡片背景）
- 图表颜色：使用图表色板

### 雷达图（Radar）
- 5个维度（F1-F5）
- 填充面积：rgba(0,113,227,0.15)
- 线色：#0071E3
- 轴线：#E5E5EA
- 标签：14px #86868B
- 刻度：0-100，每20一个刻度

### K线图（Candlestick）
- 涨：#FF3B30（空心/实心）
- 跌：#34C759（实心）
- MA线：MA5(#0071E3), MA10(#FF9500), MA20(#34C759), MA60(#5856D6)
- 背景：transparent
- 网格线：#F2F2F7
- 提示框：自定义背景#FFFFFF，圆角8px，阴影

### Treemap
- 层级色：L1(#5AC8FA), L2(#0071E3), L3(#5856D6), L4(#AF52DE)
- 边框：1px #FFFFFF
- 标签：12px，#FFFFFF，溢出截断
- 下钻：hover放大，click打开详情

### 桑基图（Sankey）
- 节点：圆角4px，颜色按层级
- 连线：渐变，透明度0.3-0.6
- 标签：12px #86868B

### 力导向图（Graph）
- 节点：圆形，大小按市值/规模
- 连线：按关系类型着色（10色）
- 连线样式：实线（supplies_to）、虚线（leads_to）、点线（competes_with）
- 节点hover：放大+tooltip

### 条形图/柱状图
- 圆角：顶部4px
- 间距：barWidth 60%，barGap 20%
- 背景：transparent
- 网格线：水平#F2F2F7，垂直无

### 折线图
- 线宽：2px
- 点：hover时显示，大小8px
- 面积填充：rgba(0,113,227,0.08)
- 平滑曲线：smooth: true

## 6. 数据展示规范

### 股价展示
- 当前价：Data-L（32px 600），颜色按涨跌
- 涨跌幅：Data-M（20px 600），红色=涨，绿色=跌
- 标签：Caption（12px #86868B），如"最新价"、"今日涨跌"

### 评分展示
- 0-100分：环形进度条或进度条
- 颜色分段：0-30（#FF3B30）、31-60（#FF9500）、61-80（#0071E3）、81-100（#34C759）
- 标签：分数居中，大小24px 600，颜色同分段

### 置信度展示
- 高：绿色圆点 + "高置信度"标签
- 中：黄色圆点 + "中置信度"标签
- 低：红色圆点 + "低置信度"标签
- 位置：卡片右上角

### 情绪展示
- Bullish：#34C759 + 向上箭头
- Bearish：#FF3B30 + 向下箭头
- Neutral：#8E8E93 + 横线
- 共识度：High（>70%）、Medium（40-70%）、Low（<40%）

## 7. 响应式断点

| 断点 | 宽度 | 布局调整 |
|------|------|---------|
| Mobile | < 640px | 单列，侧边栏隐藏，底部导航 |
| Tablet | 640-1024px | 双列，侧边栏可收起 |
| Desktop | > 1024px | 三列，侧边栏展开，完整布局 |

## 8. 动画规范

| 动画 | 时长 | 缓动 | 用途 |
|------|------|------|------|
| 页面加载 | 0.3s | ease-out | 内容淡入 |
| 卡片hover | 0.3s | ease | 阴影+位移 |
| 按钮hover | 0.2s | ease | 透明度/背景色 |
| 弹窗出现 | 0.3s | cubic-bezier(0.16, 1, 0.3, 1) | fade+scale |
| 弹窗消失 | 0.2s | ease-in | fade+scale |
| 侧边栏展开 | 0.3s | ease | 宽度变化 |
| Toast | 0.3s | ease | slideDown+fadeIn |
| 图表加载 | 0.5s | ease | 数据动画 |

## 9. 图标规范

- 使用 Lucide Icons（通过CDN或SVG内联）
- 图标大小：16px（小）、20px（标准）、24px（大）、32px（超大）
- 图标颜色：继承文字颜色，或独立指定
- 图标+文字：间距8px，图标在前

## 10. 模拟数据填充规范

所有设计稿必须使用**逼真的模拟数据**，不可使用"示例数据"、"placeholder"等字样。

### 股票数据
- 股票代码：使用真实代码（如000001.SZ、600519.SH、AAPL、NVDA）
- 股价：合理范围（A股1-1000，美股50-1000）
- 涨跌幅：-10% 到 +10%，保留2位小数
- 市值：以亿/万亿为单位
- PE/PB：合理范围

### 公司数据
- 公司名称：使用真实公司名（如贵州茅台、腾讯控股、英伟达）
- 财务数据：5年收入/利润数据，合理增长趋势
- 业务描述：真实业务，2-3句话

### 新闻/公告
- 标题：真实感标题（如"英伟达Q2财报超预期，数据中心收入创纪录"）
- 来源：真实来源（如"财联社"、"Reuters"、"Bloomberg"）
- 时间：近期日期（如"2025-07-08 10:30"）

### KOL数据
- KOL名称：使用真实知名投资者（如"Cathie Wood"、"Ray Dalio"）
- 观点：合理的市场观点（如"看多AI基础设施"）
- 情绪：bullish/bearish/neutral

### 图表数据
- 趋势合理：涨跌有逻辑，不随机乱画
- 时间范围：K线60日，折线图1年
- 数值范围：符合该标的的历史波动范围
