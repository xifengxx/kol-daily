# 数据源调研报告：FFD（Findesk）数据覆盖能力

**调研日期**：2026-08-29
**调研目的**：评估 FFD（Findesk，同花顺 iFinD 金融数据平台）能否作为每日复盘（美股 + A股）的**备用数据源**，尤其补齐此前缺口：A股板块/概念涨跌幅（含科技概念）、资金流、两融、龙虎榜、分钟K、全球市场。
**方法**：完整阅读 FFD 智能体 API 文档（`https://ffd.findesk.cn/ffd-api-docs-agent.txt`，883 行）+ 用试用 key 实测 `public-capabilities` 能力目录（298KB）+ 探测权限边界（`tree`/`indicators`/`concepts/catalog`）。

---

## 一、FFD 是什么

- **同花顺（iFinD/Findesk）金融数据平台**，Base `https://ffd.findesk.cn`，FastAPI 后端，同时是一个 **MCP 服务器**（`contract_version: mcp-0.7.49`，正式基线 85 项 MCP 工具）。
- 官网主打「金融研究工作台」：**L2 十档盘口、实时快照、秒级/分钟K线、集合竞价、ETF 盘中估值、资金流、两融**。
- 智能体（Claude 等）接入是**第二主入口**，用于自然语言任务拆解、字段查找、复杂工作流；Python SDK 是普通 Python 用户主入口；REST 供自有系统/其他语言。

### 接入三入口
| 入口 | 用法 | 适用 |
|------|------|------|
| **Python SDK**（主） | `data.login(api_key=...)` + `data.query(function=..., codes, indicators, start_date, end_date, options)` | 普通脚本 |
| **MCP 工具**（85个 `ffd_*`） | Agent 通过 MCP 协议调 `ffd_*` | AI 智能体 |
| **REST** | `/api/market-data/*`、`/api/historical/*`、`/api/templates/*`（自然语言 query 模板） | 自有系统/其他语言 |

### 鉴权
- Base URL `https://ffd.findesk.cn`；所有接口用同一个 API Key。
- REST 请求头：`Authorization: Bearer YOUR_FFD_API_KEY`；SDK：`data.login(api_key=os.getenv("FFD_API_KEY"))`。
- **Key 只放环境变量/请求头**，不进 body/query/日志。

---

## 二、对 A股复盘 12 类数据覆盖（对照《数据源调研-A股.md》需求清单）

| # | 数据类别 | 能否 | FFD 入口/接口 | 说明 |
|---|---------|------|--------------|------|
| 1 | A股指数行情 | ✅ | `data.query(function="history"/"realtime_quote", codes="000001.SH", indicators=...)` | 上证/深证/创业板/科创/北证 |
| 2 | 两市成交/量比 | ✅ | `data.query(history, indicators="amt,vol_ratio")` / `ffd_market_daily` | |
| 3 | 市场宽度/涨跌停/连板 | ✅ | `ffd_market_breadth`（宽度）；**`ffd_limit_pool`**（每日涨停池/炸板池/跌停池完整导出） | 专用工具含连板/封板率/相关概念 |
| 4 | **板块/概念涨跌幅** | ✅ | **`POST /api/templates/sector-concept-fund-flow-rank`**（含"板块净额、**涨跌幅**、流入家数占比"）；`concepts`/`industries` catalog+members；`ffd_industry_history` | ★ 科技概念（CPO/算力/半导体）；成分覆盖率≥90%才发布 |
| 5 | 资金流（北向/主力/两融/ETF） | ✅ | `ffd_money_flow` / `.../moneyflow-continuity`（主力）；`.../margin`（两融）；`etf-money-flow` | 个股/全市场/行业/概念；北向口径需确认 |
| 6 | 个股异动/龙虎榜 | ✅ | `.../dragon-tiger`、`dragon-tiger-seats`（**逐营业部席位**） | |
| 7 | 公司公告 | ✅ | 公告原文与详情（`/api/historical/company-events`、公告模块） | |
| 8 | 宏观政策（央行OMO） | ✅ | `ffd_macro_data` | |
| 9 | 宏观数据（CPI/PPI/PMI/社融/LPR） | ✅ | `ffd_macro_data` / `ffd_global_macro_series` | 实际/预期/前值需按字段核实 |
| 10 | 国际市场（美股/原油/黄金/汇率） | ✅/⚠️ | `ffd_global_market_quote`、`ffd_global_index_data`、`ffd_crypto_market_*`；美股 `AAPL.O` | **美股仅日线/分钟，无实时权限**；原油/黄金期货 |
| 11 | 港股（恒指/南向） | ✅ | `history`/`intraday`（`0700.HK`）；`ffd_global_market` | |
| 12 | 舆情/研报 | ✅ | 全球新闻库（`sectors`/`news`）、研报库 | |

---

## 三、对美股复盘覆盖（补充）

| 数据 | 能否 | 接口 | 说明 |
|------|------|------|------|
| 美股指数/个股日线·分钟 | ✅ | `data.query(history/intraday, "AAPL.O")` | 分钟按北京时间传入；**当前无美股实时权限** |
| 全球指数/行情/宏观/新闻 | ✅ | `ffd_global_index_data`、`ffd_global_market_quote/bars`、`ffd_global_macro_series` | |
| 美债 | ⚠️ | 期货 `.CBT`（美债期货） | 直接收益率序列需确认 |
| 期权 | ✅/⚠️ | `ffd_options`（境内）；美股期权未形成生产证据（零扣费关闭） | |
| 费城半导体等指数 | ✅ | 全球指数行情 | 补齐 `^SOX` |

---

## 四、关键接口示例（可直接复用）

```python
# ① 历史行情（日线）
from ffd import data
data.login(api_key=os.getenv("FFD_API_KEY"))
result = data.query(function="history", codes="600519.SH",
                    indicators="open,high,low,close,volume,amt",
                    start_date="2026-06-01", end_date="2026-06-04", options="CPS:1")
```

```python
# ② 行业/概念板块资金流 + 涨跌幅（A股板块全景可用）
import requests, os
resp = requests.post("https://ffd.findesk.cn/api/templates/sector-concept-fund-flow-rank",
    headers={"Authorization": f"Bearer {os.getenv('FFD_API_KEY')}"},
    json={"query": "今日行业主力资金净流入排名", "market": "stock", "limit": 20}, timeout=60)
print(resp.json())
```

- 概念/行业目录：`GET /api/historical/concepts/catalog`、`.../industries/catalog`、`members`
- 涨停池：`ffd_limit_pool`（专用工具）
- 两融：`POST /api/market-microstructure/margin`；龙虎榜逐席位：`POST /api/market-microstructure/dragon-tiger-seats`

---

## 五、权限 / 计费（实测边界）

- ✅ **`GET /api/v1/catalog/public-capabilities`**：试用 key 能访问（298KB，列出全部能力/工具/rest_endpoints）。
- ❌ **`tree` / `indicators` → 401「无效的登录凭证」**；**`/api/historical/concepts/catalog` → 503** —— **试用 key 取不到真实数据，需正式授权 / 更高套餐**（或走 MCP 终端）。
- **扣点规则**：搜索/身份/基础档案/风险信号 2 点；申报事件/所有权/观察 5 点；标准化财务/公共采购 10 点；当日全量导出每 1000 行 1 点；**参数错误/权限拦截/服务失败净扣 0**。
- 试用注册赠送 5 万数据点。

---

## 六、对项目的价值与缺口

### 价值（能补齐此前缺口）
- ★ **A股板块/概念涨跌幅**（科技概念：CPO/算力/半导体/低空经济）—— 正是我们「板块涨跌全景图」要的，且是**同花顺权威数据**。
- **资金流（行业/概念/全市场）、两融、龙虎榜（逐席位）、涨停池/炸板/跌停、分钟K** —— 补强。
- **全球市场/指数/宏观/新闻/研报/财务/估值/一致预期** —— 补全。

### 缺口 / 局限
1. **板块"涨跌幅"在资金流模板**（`sector-concept-fund-flow-rank`）取，**没有独立的"板块行情"工具**（`ffd_industry_history` 是专题报表）；且**成分股有效资金流覆盖率≥90% 才发布**，否则缺。
2. **美股无实时权限**（仅日线/分钟）；美股期权未验证。
3. **数据计费/扣点**；试用 key 只够看目录（真实查询被 401/503 拦），需**正式授权 key**。
4. 部分 iFinD 板块指标需**客户端指标码**（如 p03291 板块成分、p03321 板块ID、p03374 板块进出记录）。
5. **不得混用接口口径**：区分历史行情 / 实时快照 / 分钟 / 基本面 / 资金 / 公告新闻 / 专题；缺失字段保持 `null` 并披露，不补零、不把部分覆盖当完整。

---

## 七、推荐 / 结论

- **FFD 是现有最优的备用数据源**（同花顺体系、覆盖板块/概念/资金流/两融/龙虎榜/分钟K/全球），能补「数据源调研-A股.md」里多数缺口，也能增强美股复盘。
- **要用起来需要**：① **正式授权的 API Key**（试用只够看目录）；② **接入方式**：Python SDK 或 MCP（配给 Claude Code）或 REST 模板。
- **若接入**：A股板块涨跌幅图用 `sector-concept-fund-flow-rank`；指数/个股行情用 `data.query(function="history")`；涨停池用 `ffd_limit_pool`；两融/龙虎榜用 `market-microstructure/*`。

---

## 八、信息来源

- FFD 智能体 API 文档：`https://ffd.findesk.cn/ffd-api-docs-agent.txt`（883 行，机器可读版）
- 能力契约实测：`GET /api/v1/catalog/public-capabilities`（298KB，列出 85 工具 + 63 REST 端点）
- 试用 key 权限实测：`tree`/`indicators` → 401；`concepts/catalog` → 503；`public-capabilities` → 200
- Findesk 官网：`https://www.findesk.cn`（金融研究工作台能力文案）
