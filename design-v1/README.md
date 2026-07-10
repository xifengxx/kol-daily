# 5Factor AI — 金融投资AI助手（网页版效果图）

> 基于PRD文档制作的网页版产品效果图，使用HTML+CSS+JavaScript单文件实现，可直接在浏览器中打开预览。

## 在线访问

部署到 GitHub Pages 后访问：
`https://你的用户名.github.io/仓库名/index.html`

## 本地预览

```bash
# 方式1：直接打开index.html
open index.html

# 方式2：启动本地服务器（推荐，避免iframe跨域问题）
python3 -m http.server 8080
# 然后访问 http://localhost:8080
```

## 页面结构

### 统一入口
- `index.html` — 统一导航入口，包含侧边栏和iframe内容区

### A 行情与数据（3个页面）
- `market-overview.html` — 市场总览（全球14指数 + 涨跌分布 + 行业热力图）
- `stock-detail.html` — 个股行情（K线图 + 技术指标 + 五档盘口）
- `global-market.html` — 全球市场（三大区域 + 汇率 + 商品）
- `watchlist.html` — 自选股（分组筛选 + 五因子表格 + 详情面板）

### B 内容与信息（3个页面）
- `daily-briefing.html` — 每日智能晨报（双版本 + 10热点 + 公告）
- `kol-digest.html` — KOL观点速览（观点主线 + 分歧对照 + 38位KOL）
- `content-manage.html` — 内容管理（日历筛选 + 推送设置）

### C 分析与选股（4个页面）
- `scoring-list.html` — 评分榜单（五因子Top20 + NL选股）
- `stock-deep.html` — 个股深度（四阶段12步分析 + 9模型LLM）
- `sim-trading.html` — 模拟交易（持仓 + 净值曲线 + T+N回撤）
- `strategy-backtest.html` — 策略回测（NL策略 + 回测结果）

### D 产业链与知识（5个页面）
- `industry-chain.html` — 产业链图谱（Treemap/Graph/Sankey/因果传导）
- `sector-analysis.html` — 赛道分析（K线 + 技术面 + 资金面 + 基本面）
- `stock-relation.html` — 个股关联（产业链定位 + 竞争格局）
- `concept-card.html` — 概念卡片（11模块概念百科）
- `knowledge-base.html` — 知识库（4层目录 + 复盘验证）

### E AI编排层（6个页面）
- `workflow.html` — 工作流编排（拖拽 + 触发条件）
- `meeting-minutes.html` — 会议纪要（语音转文字 + 结构化摘要）
- `private-knowledge.html` — 私域知识（PDF上传 + 混合检索）
- `prompt-manage.html` — Prompt管理（8个Skill版本 + A/B测试）
- `multimodal.html` — 多模态（截图分析 + 财报提取 + 语音搜索）
- `ai-chat.html` — AI投研对话（ChatGPT式 + @Skill + 多模型）

### F 社区与协作（3个页面）
- `strategy-square.html` — 策略广场（社区投票 + 夏普排名）
- `notes-share.html` — 笔记分享（投资笔记 + 评论互动）
- `concept-collab.html` — 概念协作（版本历史 + 审核队列）

### G 系统设置（1个页面）
- `settings.html` — 系统设置（账户/五因子/AI模型/数据源/通知等）

## 技术栈

- HTML5 + CSS3 + JavaScript（单文件，无构建步骤）
- Tailwind CSS（CDN）
- ECharts 5.6（CDN）— 数据可视化图表
- Lightweight Charts 4.1（CDN）— K线图
- 所有数据为模拟数据（部分使用真实五因子评分数据）

## 设计规范

- 风格：Stripe金融科技风格（白色画布 + 品牌紫#533afd + 深海军蓝#0d253d）
- 布局：侧边栏220px（深蓝）+ 顶部栏56px（白色）+ 主内容区（弹性）
- 响应式：适配1440px桌面端

## 数据来源

部分页面使用真实数据：
- 五因子评分系统（2026-05-08快照）
- 38位YouTube KOL + 13位Twitter KOL
- 投资知识图谱（74赛道/398公司/572股票映射）
- 全球指数样本数据

## 注意事项

1. 本仓库为产品效果图，非生产代码
2. 图表使用CDN资源，首次加载可能需要等待CDN响应
3. 建议通过本地服务器预览（`python3 -m http.server`），避免iframe `file://` 协议限制

## 许可证

MIT
