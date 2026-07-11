# 重构计划：Design V1 → Apple 财经风格 (Design V3)

## 目标
将 Design V1（Stripe 风格）的 27 个 HTML 文件，按照 Design V2（Apple 财经风格）的设计系统进行全面重构，产出 Design V3。

## 核心设计转换规则

### 1. 颜色系统转换
| Stripe (V1) | Apple (V2) | 说明 |
|-------------|------------|------|
| `--sidebar-bg: #0d253d` | `#FFFFFF` | 侧边栏深色 → 白色 |
| `--accent: #533afd` | `#0071E3` | 紫色 → 苹果蓝 |
| `--bg-page: #f7f8fa` | `#F5F5F7` | 浅灰背景 |
| `--border: #e5e7eb` | `#E5E5EA` | 边框色 |
| `--text-primary: #1a1f36` | `#1D1D1F` | 主文字 |
| `--text-secondary: #64748d` | `#86868B` | 次要文字 |
| `--up: #dc2626` | `#FF3B30` | 上涨红 |
| `--down: #16a34a` | `#34C759` | 下跌绿 |
| `--navy: #061b31` | `#1D1D1F` | 深色标题 |
| `--card-bg: #ffffff` | `#FFFFFF` | 卡片白色 |
| `--hover-bg: #f8fafc` | `#F5F5F7` | 悬停背景 |
| `--active-bg: rgba(83,58,253,0.15)` | `#F0F7FF` | 激活背景 |
| 标签背景色 | 使用 Apple 语义色 | 见 DESIGN_SYSTEM.md |

### 2. 圆角转换
- 卡片：`8px` → `12px`
- 按钮：`6px` → `8px`
- 搜索框：`20px`（pill）保持
- 标签/徽章：`4px` → `10px`（全圆角）
- 模态框：`8px` → `16px`

### 3. 阴影与层级转换
- Stripe 多层阴影 → 轻边框为主 (`1px solid #E5E5EA`)
- 卡片 hover：`box-shadow: 0 8px 24px rgba(0,0,0,0.12)` + `transform: translateY(-2px)`
- 移除大部分默认阴影，用边框创造层级

### 4. 字体系统转换
- 字体栈：`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif`
- 页面标题 (H1): `28px 700` 行高 `1.2` 字间距 `-0.02em`
- 板块标题 (H2): `22px 600` 行高 `1.3` 字间距 `-0.01em`
- 卡片标题 (H3): `18px 600` 行高 `1.4`
- 小节标题 (H4): `16px 500` 行高 `1.4`
- 正文 (Body): `14px 400` 行高 `1.6`
- 次要正文 (Body-S): `13px 400` 行高 `1.5`
- 说明文字 (Caption): `12px 400` 行高 `1.4` 字间距 `0.01em`
- 核心数据大字 (Data-L): `32px 600` 行高 `1.1` 字间距 `-0.02em`
- 中等数据 (Data-M): `20px 600` 行高 `1.2`
- 标签 (Label): `11px 500` 行高 `1.3` 字间距 `0.02em`

### 5. 图标系统转换
- 所有 emoji 图标 → Lucide Icons
- 引入 CDN: `<script src="https://unpkg.com/lucide@latest"></script>`
- 使用 `<i data-lucide="icon-name"></i>` 格式
- 图标大小：20px（标准），16px（小），24px（大）
- 图标颜色：继承文字颜色或独立指定

### 6. 侧边栏转换
- 背景：深色 `#0d253d` → 白色 `#FFFFFF`
- 文字：白色 `rgba(255,255,255,0.65)` → 黑色 `#1D1D1F`
- 激活态：紫色背景 + 左边框 → 浅蓝背景 `#F0F7FF` + 蓝色左边框 `#0071E3`
- 悬停态：白色背景 `rgba(255,255,255,0.06)` → 浅灰 `#F5F5F7`
- 分组标题：大写+字间距 → 大写+字间距 `0.05em`，颜色 `#86868B`
- 宽度：220px 保持

### 7. 顶部导航栏转换
- 背景：白色保持
- 高度：56px 保持
- 底部边框：1px solid `#E5E5EA`
- 搜索框：背景 `#F5F5F7`，圆角 8px，高度 40px
- 图标：使用 Lucide 替代 emoji

### 8. 按钮转换
- 主要按钮：背景 `#0071E3`，文字 `#FFFFFF`，圆角 8px，padding 10px 20px
- 次要按钮：背景 `#F5F5F7`，文字 `#1D1D1F`，边框 1px `#E5E5EA`
- 危险按钮：背景 `#FF3B30`，文字 `#FFFFFF`
- 幽灵按钮：背景透明，文字 `#0071E3`
- hover：`opacity 0.9`，过渡 0.2s
- 禁用：`opacity 0.4`

### 9. 表格转换
- 表头：背景 `#F2F2F7`，文字 `#86868B`，12px 500，padding 12px 16px
- 行：padding 14px 16px，border-bottom 1px `#E5E5EA`
- 行 hover：背景 `#F5F5F7`
- 选中行：左侧 4px `#0071E3` 竖线
- 交替行：可选 `#F2F2F7`

### 10. 卡片转换
- 背景：`#FFFFFF`
- 圆角：`12px`
- 边框：`1px solid #E5E5EA`（可选）
- 阴影：`0 4px 16px rgba(0,0,0,0.08)`（可选，用于悬浮）
- 内边距：`24px`
- hover：阴影加深 `0 8px 24px rgba(0,0,0,0.12)`，`transform: translateY(-2px)`，过渡 0.3s ease

### 11. 标签/徽章转换
- 高度：20px，padding 0 8px
- 圆角：10px（全圆角）
- 字体：11px 500
- 类型：primary(`#0071E3`/`#FFFFFF`)、success(`#34C759`/`#FFFFFF`)、warning(`#FF9500`/`#FFFFFF`)、danger(`#FF3B30`/`#FFFFFF`)、neutral(`#F2F2F7`/`#1D1D1F`)

### 12. 动画规范
- 页面加载：0.3s ease-out 淡入
- 卡片 hover：0.3s ease 阴影+位移
- 按钮 hover：0.2s ease 透明度/背景色
- 弹窗出现：0.3s cubic-bezier(0.16, 1, 0.3, 1) fade+scale
- 侧边栏展开：0.3s ease 宽度变化
- 图表加载：0.5s ease 数据动画

## 架构保留
- 保持 V1 的 iframe 主框架架构
- index.html 作为 app shell，iframe 加载子页面
- 子页面保留 `body.in-iframe` 隐藏逻辑
- 所有页面独立单文件 HTML

## 输出目录
`/Users/mac/Claude_projects/5factor_system/deploy-gh-pages/design-v3/`

## 页面映射（27个文件）

| # | V1 文件名 | 说明 | 优先级 |
|---|-----------|------|--------|
| 1 | `index.html` | 主框架（app shell） | P0 |
| 2 | `market-overview.html` | 市场总览 | P0 |
| 3 | `watchlist.html` | 自选股 | P0 |
| 4 | `stock-detail.html` | 个股行情 | P0 |
| 5 | `global-market.html` | 全球市场 | P0 |
| 6 | `daily-briefing.html` | 每日智能晨报 | P0 |
| 7 | `kol-digest.html` | KOL观点 | P0 |
| 8 | `content-manage.html` | 内容管理 | P1 |
| 9 | `scoring-list.html` | 评分榜单 | P0 |
| 10 | `stock-deep.html` | 个股深度 | P0 |
| 11 | `sim-trading.html` | 模拟交易 | P1 |
| 12 | `strategy-backtest.html` | 策略回测 | P1 |
| 13 | `industry-chain.html` | 产业链图谱 | P0 |
| 14 | `sector-analysis.html` | 赛道分析 | P1 |
| 15 | `stock-relation.html` | 个股关联 | P1 |
| 16 | `concept-card.html` | 概念卡片 | P1 |
| 17 | `knowledge-base.html` | 知识库 | P1 |
| 18 | `workflow.html` | 工作流编排 | P2 |
| 19 | `meeting-minutes.html` | 会议纪要 | P2 |
| 20 | `private-knowledge.html` | 私域知识 | P2 |
| 21 | `prompt-manage.html` | Prompt管理 | P2 |
| 22 | `multimodal.html` | 多模态 | P2 |
| 23 | `ai-chat.html` | AI投研对话 | P0 |
| 24 | `strategy-square.html` | 策略广场 | P2 |
| 25 | `notes-share.html` | 笔记分享 | P2 |
| 26 | `concept-collab.html` | 概念协作 | P2 |
| 27 | `settings.html` | 设置 | P0 |

## 执行策略
1. **Stage 1**: 创建 `design-v3` 目录，创建 DESIGN_SYSTEM.md 文档
2. **Stage 2**: 先处理 `index.html` 主框架（手动处理，确保正确）
3. **Stage 3**: 使用 AgentSwarm 并行处理所有 27 个子页面
4. **Stage 4**: 验证和修复

## 注意事项
- 保留所有 V1 的内容、数据结构、交互逻辑
- 仅改变视觉风格和布局细节
- 确保所有 emoji 都被替换为 Lucide Icons
- 确保所有颜色都符合 Apple 设计系统
- 确保响应式断点保持一致（Mobile <640px, Tablet 640-1024px, Desktop >1024px）
- 保持 `body.in-iframe` 的 CSS 规则
- 确保 ECharts 图表颜色也使用 Apple 色板
