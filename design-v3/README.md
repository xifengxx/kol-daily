# Design V3 — Apple Stocks App 风格转换说明

## 概述

本目录包含将 **Design V1 (Stripe 风格)** 转换为 **Design V3 (Apple 财经/Stocks App 风格)** 的完整结果。

- **源目录**: `design-v1/` — 基于 Stripe 设计系统（深海军蓝侧边栏 + 品牌紫强调色）
- **目标目录**: `design-v3/` — 基于 Apple 财经设计系统（白色侧边栏 + 蓝色强调色）
- **参考风格**: `design-v2/` — Apple Stocks App 风格原型（提供设计规范参考）

---

## 转换内容

### 已转换文件（27个）

| 类别 | 文件 |
|------|------|
| **统一入口** | `index.html` |
| **行情与数据** | `market-overview.html`, `stock-detail.html`, `global-market.html`, `watchlist.html` |
| **内容与信息** | `daily-briefing.html`, `kol-digest.html`, `content-manage.html` |
| **分析与选股** | `scoring-list.html`, `stock-deep.html`, `sim-trading.html`, `strategy-backtest.html` |
| **产业链与知识** | `industry-chain.html`, `sector-analysis.html`, `stock-relation.html`, `concept-card.html`, `knowledge-base.html` |
| **AI编排层** | `workflow.html`, `meeting-minutes.html`, `private-knowledge.html`, `prompt-manage.html`, `multimodal.html`, `ai-chat.html` |
| **社区与协作** | `strategy-square.html`, `notes-share.html`, `concept-collab.html` |
| **系统** | `settings.html` |

---

## 设计系统变更对照

### 颜色体系

| 元素 | V1 (Stripe) | V3 (Apple) |
|------|-------------|------------|
| 强调色 | `#533afd` 品牌紫 | `#0071E3` Apple蓝 |
| 主文字 | `#061b31` 深海军蓝 | `#1D1D1F` 近黑 |
| 辅助文字 | `#64748d` | `#86868B` |
| 页面背景 | `#f7f8fa` | `#F5F5F7` |
| 卡片边框 | `#e5e7eb` | `#E5E5EA` |
| 浅灰背景 | `#f3f4f6` | `#F2F2F7` |
| 上涨(A股) | `#dc2626` 红 | `#FF3B30` Apple红 |
| 下跌(A股) | `#16a34a` 绿 | `#34C759` Apple绿 |
| 警告 | `#f59e0b` | `#FF9500` Apple橙 |
| 侧边栏背景 | `#0d253d` 深蓝 | `#FFFFFF` 白色 |

### 组件样式

| 组件 | V1 (Stripe) | V3 (Apple) |
|------|-------------|------------|
| **卡片圆角** | 8px | 12px |
| **卡片阴影** | 多层蓝紫阴影 | `0 4px 16px rgba(0,0,0,0.08)` |
| **卡片hover** | 微上移1px | 上移2px + 阴影加深 |
| **侧边栏宽度** | 220px | 240px |
| **侧边栏样式** | 深蓝背景，白色文字 | 白色背景，黑色文字，右边框 |
| **选中态** | 紫色背景+左边框 | 浅蓝背景 `#F0F7FF` + 蓝色左边框 |
| **按钮圆角** | 6px | 8px |
| **搜索框** | Pill形状(20px圆角) | 圆角8px，高40px |
| **标签圆角** | 4px | 10px(全圆角) |
| **页面标题** | 24px 600 | 28px 700 |
| **卡片标题** | 18px 600 | 22px 600 |

### 图标系统

| V1 (Emoji) | V3 (Lucide Icons) |
|------------|-------------------|
| 📊 | `layout-dashboard` / `bar-chart-3` |
| 📈 | `trending-up` |
| 🌍 | `globe` |
| 🧠 | `brain` |
| 📰 | `newspaper` |
| 🎙️ | `mic` |
| ⭐ | `star` |
| 🔍 | `search` |
| 💰 | `wallet` |
| 🧬 | `git-branch` |
| 🤖 | `bot` |
| 🔔 | `bell` |
| ⚙️ | `settings` |
| 📝 | `file-text` |
| 🏆 | `trophy` |
| ⚡ | `zap` |
| 🎯 | `target` |
| 👥 | `users` |
| 🔗 | `link` |
| ☰ | `menu` |
| ◀ | `panel-left-close` |
| ▼ | `chevron-down` |

---

## 保留未变的内容

以下所有内容**完全保留**，未做任何修改：

- ✅ 所有页面结构、布局、模块划分
- ✅ 所有模拟数据（股价、指数、K线数据、新闻等）
- ✅ 所有 ECharts 图表配置和数据
- ✅ 所有 Lightweight Charts K线图配置
- ✅ 所有 JavaScript 交互逻辑（Tab切换、展开/折叠、搜索等）
- ✅ 所有 iframe 嵌入检测逻辑（`body.in-iframe`）
- ✅ 所有页面之间的链接关系
- ✅ 所有响应式断点和移动端适配
- ✅ 所有 Tailwind CDN 和 ECharts CDN 引用

---

## 使用方式

```bash
# 方式1：直接打开入口页面
open /Users/mac/Claude_projects/5factor_system/deploy-gh-pages/design-v3/index.html

# 方式2：启动本地服务器（推荐，避免iframe跨域问题）
cd /Users/mac/Claude_projects/5factor_system/deploy-gh-pages/design-v3
python3 -m http.server 8080
# 然后访问 http://localhost:8080/index.html
```

---

## 文件位置

```
/Users/mac/Claude_projects/5factor_system/deploy-gh-pages/
├── design-v1/          # 原始 Stripe 风格（保留）
├── design-v2/          # Apple 风格参考原型（保留）
├── design-v3/          # ✅ 本次转换结果（Apple 风格）
│   ├── index.html      # 统一入口
│   ├── market-overview.html
│   ├── stock-detail.html
│   ├── ... (共27个文件)
│   └── README.md       # 本文件
└── prototypes/         # DeepSeek 融合风格（保留）
```

---

*转换日期: 2025年*  
*转换工具: Python 批量脚本*  
*设计风格参考: Apple Stocks App / design-v2*
