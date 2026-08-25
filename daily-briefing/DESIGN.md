# 每日财经简报 · 设计文档（DESIGN.md）

> 本模块视觉设计继承站内「AI产业链图谱」（`industry-chain`）模块，保持站点独立功能模块的设计语言统一。

## 1. 设计来源

| 参考模块 | 参考点 |
|---------|--------|
| AI产业链图谱（industry-chain/index.html） | 布局骨架（左右两栏）、设计令牌、组件样式（侧栏导航 / pill 切换 / 卡片 / 表格） |

## 2. 设计令牌（Design Tokens）

继承 industry-chain 的 CSS 变量：

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#F5F5F7` | 页面背景（浅灰） |
| `--card` | `#FFFFFF` | 卡片 / 侧栏 / 顶栏背景 |
| `--border` | `#E5E5EA` | 边框 |
| `--text` | `#1D1D1F` | 主文字 |
| `--text2` | `#86868B` | 次级文字 |
| `--accent` | `#0071E3` | 主色（Apple 蓝），激活态 / 链接 / 高亮 |
| `--up` | `#FF3B30` | 涨（红） |
| `--down` | `#34C759` | 跌（绿） |
| `--hover` | `#F5F5F7` | hover 背景 |
| `--active` | `rgba(0,113,227,0.10)` | 激活项背景 |

- **字体**：`-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif`
- **圆角**：卡片 12px、小控件 8px、pill 按钮 16px
- **阴影**：hover 时 `0 8px 32px rgba(0,0,0,0.08)`

## 3. 布局结构（左右两栏）

```
┌──────────┬────────────────────────────┐
│  sidebar │  topbar（面包屑）           │
│  220px   ├────────────────────────────┤
│  导航     │  content（报告卡片）        │
│  sticky  │                            │
└──────────┴────────────────────────────┘
```

- **左栏 `.sidebar`**：220px、sticky、全高、右边框分隔 —— 放导航
- **右栏 `.main`**：`flex:1` —— 顶栏 + 内容区

## 4. 组件映射（industry-chain → 每日财经简报）

| industry-chain | 每日财经简报 | 说明 |
|----------------|-------------|------|
| `sidebar-logo` "Invest Wiki" | "每日财经**简报**" | 品牌标识，accent 高亮后缀 |
| `industry-switcher`（AI/半导体 pill） | **美股早盘版 / A股收盘版** pill | 市场切换 |
| `nav-title` "产业链与知识" | "历史报告" | 分节标题 |
| `tree-item`（📄 公司） | **日期项**（2026-08-25） | 报告列表；激活态：`border-left:3px accent` + `--active` 浅蓝底 |
| `topbar .bc` 面包屑 | **市场 > 日期** | 当前位置 |
| `.card` | 报告内容卡片 | 渲染 markdown |
| `.quality-table` | 报告内表格 | 表头大写浅灰、分隔线、hover 背景 |
| `.status-dot` | （可选）报告内状态点 | 涨跌/状态语义 |

## 5. 报告 Markdown 样式规范

- **h2**：19px、`accent` 左边框 4px（与侧栏激活项视觉呼应）
- **h3**：16px 加粗；**h4**：14px
- **表格**：仿 `quality-table`——表头 `--bg` + 2px 下边框 + 大写浅灰；单元格 1px 分隔线；hover 行 `--bg`
- **涨跌色**：报告正文中的 `+X%` / `-X%` 用 `--up` / `--down` 语义（A股习惯红涨绿跌，与 industry-chain 的 `--up:#FF3B30 / --down:#34C759` 一致）
- **blockquote**：`accent` 左边框 + `--text2`
- **数据来源/口径说明**：次级文字 `--text2`

## 6. 响应式

- **≤768px**：侧栏收起为顶部横向选择器，内容单列，报告内边距收紧（20px→16px）
