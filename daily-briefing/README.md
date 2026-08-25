# 每日财经简报（daily-briefing）

美股日度复盘（早盘版）+ A股港股收盘复盘（收盘版）报告查看模块。

## 使用

打开 `index.html`，选择 **「美股早盘版 / A股收盘版」** + **日期**，即可查看对应报告。

## 报告生成流程

报告由「每日简报实战」系统生成：

1. **本地运行数据脚本**取数 → 生成 JSON 快照（`scripts/fetch_us_market_data.py` / `fetch_a_share_data.py`）
2. **提示词 + 数据快照 + 搜索结果** → 大模型按提示词生成报告 `.md`
3. 报告放入 `reports/{us|cn}/{日期}.md`，并更新 `manifest.json`
4. `git push` 到 gh-pages → GitHub Pages **自动重新部署**

> 完整逻辑见 `docs/03-执行流程/复盘报告执行流程.md`。

## 数据源

| 数据源 | 类型 | 用途 |
|--------|------|------|
| FMP / Infoway / iFinD | 付费 | 行情、板块、宏观日历、资金流 |
| AkShare / 新浪 / 腾讯 | 免费冗余 | 涨停池、龙虎榜、实时兜底 |

密钥通过环境变量配置（`scripts/` 下复制 `.env.example` 为 `.env`），**勿提交真实密钥**。

## 目录

```
daily-briefing/
├── index.html          # 报告查看器（美股/A股 tab + 日期选择）
├── manifest.json       # 可用报告清单（每次新增报告需更新）
├── reports/            # 报告 markdown（查看器读取）
│   ├── us/{日期}.md    # 美股报告
│   └── cn/{日期}.md    # A股+港股报告
├── docs/               # 提示词、数据源调研、执行流程
└── scripts/            # 数据接入脚本
```
