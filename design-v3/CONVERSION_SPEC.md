# Design V1 → Design V3 (Apple Stocks 风格) 转换规范

## 设计系统映射

### 颜色替换表（全局CSS变量级别）
| V1 (Stripe) | V3 (Apple) | 用途 |
|-------------|------------|------|
| `#533afd` | `#0071E3` | 强调色/按钮/链接/选中态 |
| `#061b31` | `#1D1D1F` | 主标题/重要文字 |
| `#1a1f36` | `#1D1D1F` | 正文文字 |
| `#64748d` | `#86868B` | 辅助文字/说明 |
| `#f7f8fa` | `#F5F5F7` | 页面背景 |
| `#ffffff` | `#FFFFFF` | 卡片背景（不变） |
| `#e5e7eb` | `#E5E5EA` | 边框/分割线 |
| `#f3f4f6` | `#F2F2F7` | 表头背景/悬停背景 |
| `#dc2626` | `#FF3B30` | A股/港股上涨 |
| `#16a34a` | `#34C759` | A股/港股下跌 |
| `#f59e0b` | `#FF9500` | 警告/风险提示 |
| `#0d253d` | `#FFFFFF` | 侧边栏背景（关键变化） |
| `#8b9cf7` | `#0071E3` | logo彩色部分 |
| `#fafbfc` | `#F5F5F7` | 交替行背景 |
| `#0f172a` | `#1D1D1F` | 深色卡片（K线区域） |

### 字体系统映射
| V1 | V3 |
|----|----|
| 基础 13px | 基础 14px |
| 页面标题 24px 600 | 页面标题 28px 700 |
| 卡片标题 18px 600 | 卡片标题 22px 600 |
| 小节标题 14px 600 | 小节标题 16px 500 |
| 数据大 24px 600 | 数据大 32px 600 |
| 数据中 16px 500 | 数据中 20px 600 |
| 辅助 12px 400 | 辅助 12px 400 |
| 徽章 11px 500 | 徽章 11px 500 |

### 组件样式映射

**卡片**
- V1: `border-radius: 8px`, 多层阴影 `rgba(50,50,93,0.08) 0px 8px 24px...`
- V3: `border-radius: 12px`, `border: 1px solid #E5E5EA`, 阴影 `0 4px 16px rgba(0,0,0,0.08)` 或更轻
- V3 hover: `box-shadow: 0 8px 24px rgba(0,0,0,0.12); transform: translateY(-2px)`

**侧边栏**
- V1: 宽度220px, 背景 `#0d253d`, 文字白色半透明, 选中态紫色背景+左边框
- V3: 宽度240px, 背景 `#FFFFFF`, 边框右边 `1px solid #E5E5EA`, 文字 `#1D1D1F`
- V3 选中态: 背景 `#F0F7FF`, 左侧4px `#0071E3` 竖线, 文字 `#0071E3`
- V3 悬停: 背景 `#F5F5F7`
- V3 分组标题: 12px 600 uppercase, `#86868B`, padding-top: 16px

**顶部导航栏**
- V1: 高度56px, 白色背景, 底部边框 `#e5e7eb`, 搜索框pill形状
- V3: 高度56px, 白色背景, 底部边框 `#E5E5EA`, 搜索框圆角8px高40px背景 `#F5F5F7`

**按钮**
- V1 主按钮: 背景 `#533afd`, 圆角6px, padding 8px 20px
- V3 主按钮: 背景 `#0071E3`, 圆角8px, padding 10px 20px, 字重500
- V3 次要按钮: 背景 `#F5F5F7`, 文字 `#1D1D1F`, 边框 `1px solid #E5E5EA`, 圆角8px

**输入框**
- V1: 背景 `#f7f8fa`, 边框 `#e5e7eb`, 圆角6px/20px(搜索)
- V3: 背景 `#F5F5F7`, 边框 transparent, 圆角8px, focus时边框 `#0071E3` + shadow `0 0 0 3px rgba(0,113,227,0.15)`

**标签/徽章**
- V1: 圆角4px, 各种背景色+文字色组合
- V3: 高度20px, padding 0 8px, 圆角10px(全圆角), 11px 500

**表格**
- V1: 表头背景 `#fafbfc`, 文字 `#64748d`, 12px 600 uppercase
- V3: 表头背景 `#F2F2F7`, 文字 `#86868B`, 12px 500
- V3 行hover: 背景 `#F5F5F7`
- V3 选中行: 左侧4px `#0071E3` 竖线

**Toast/提示**
- V1: 黑色半透明背景
- V3: 黑色背景 `rgba(0,0,0,0.8)`, 圆角12px, padding 12px 20px

### 图标替换
- V1 使用 emoji 图标（如 📊, 📈, 🌍, 🧠, 🎙️, 🗂️, ⭐, 🔍, 💰, 🧬, 🏎️, 🤖, 📝, 🔔）
- V3 使用 Lucide Icons（通过 `<script src="https://unpkg.com/lucide@latest"></script>` + `<i data-lucide="icon-name"></i>`）
- 常见映射：
  - 📊 → `bar-chart-3` / `layout-dashboard`
  - 📈 → `trending-up`
  - 🌍 → `globe`
  - 🧠 → `brain` / `network`
  - 📰 → `newspaper`
  - 🎙️ → `mic`
  - 🗂️ → `folder-open`
  - ⭐ → `star`
  - 🔍 → `search`
  - 💰 → `dollar-sign` / `wallet`
  - 🧬 → `git-branch` / `network`
  - 🏎️ → `zap`
  - 🤖 → `bot`
  - 📝 → `file-text` / `pen-tool`
  - 🔔 → `bell`
  - ⚙️ → `settings`
  - 👤 → `user`
  - 🔧 → `wrench`
  - 📁 → `folder`
  - 📋 → `clipboard-list`
  - 💬 → `message-circle` / `message-square`
  - 📎 → `paperclip`
  - 🏠 → `home`
  - 📚 → `book-open`
  - 🔐 → `lock`
  - ⚡ → `zap`
  - 🎯 → `target`
  - 📉 → `trending-down`
  - 🏆 → `trophy`
  - 🔄 → `refresh-cw`

### 阴影系统替换
- V1: `rgba(50,50,93,0.08) 0px 8px 24px -4px, rgba(0,0,0,0.06) 0px 4px 12px -4px`
- V3: `0 4px 16px rgba(0,0,0,0.08)` (标准) / `0 8px 24px rgba(0,0,0,0.12)` (hover)

### 动画规范
- V1 卡片悬浮: 0.2s ease, 阴影增强 + 微上移 1px
- V3 卡片hover: 0.3s ease, 阴影加深 + translateY(-2px)
- V1 按钮悬浮: 0.15s ease
- V3 按钮hover: 0.2s ease, opacity 0.9
- V3 页面加载: 0.3s fadeIn
- V3 弹窗: 0.3s cubic-bezier(0.16, 1, 0.3, 1)

### 关键CSS类名替换
| V1 | V3 |
|----|----|
| `.sidebar` (深蓝) | `.sidebar` (白色，需重写内部样式) |
| `.card` | `.card` (12px圆角，新阴影) |
| `.btn-primary` | `.btn-primary` (#0071E3背景) |
| `.search-box` (pill) | `.search-input` (圆角8px) |
| `.tag-*` | `.badge-*` (全圆角) |
| `.index-card` | `.card` (统一样式) |
| `.status-dot` | 保持，但颜色用 #FF3B30 |
| `.up` / `.down` | 颜色改为 #FF3B30 / #34C759 |

### HTML结构变化要点
1. **Tailwind 配置**: 在 `<script>` 中定义自定义颜色配置（参考 Design V2）
2. **Lucide 图标**: 在 `<head>` 中加入 `<script src="https://unpkg.com/lucide@latest"></script>`，在页面底部调用 `lucide.createIcons()`
3. **CSS变量**: 将 V1 的 `:root` 变量替换为 V3 的值
4. **字体栈**: 使用 `-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif`
5. **iframe 检测**: 保留 `body.in-iframe` 检测逻辑，隐藏侧边栏和顶部栏
6. **页面标题**: 保持原有的标题文字，但使用新的字体层级

## 注意事项
1. 保持所有页面内容、数据、模拟数据、图表配置、交互逻辑完全不变
2. 保持所有 ECharts 配置和图表数据不变
3. 保持所有 iframe 嵌入逻辑（body.in-iframe）不变
4. 保持所有页面之间的链接关系不变
5. 保持所有 JavaScript 逻辑不变，只改CSS样式和HTML结构
6. 如果 V1 页面没有使用 Lucide，需要添加 Lucide 脚本并替换所有 emoji 图标
7. 如果 V1 页面已经使用 Tailwind，保留 Tailwind CDN 但更新自定义配置
