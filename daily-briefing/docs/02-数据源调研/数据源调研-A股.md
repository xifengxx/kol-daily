# 数据源调研报告：A股每日收盘复盘简报数据覆盖能力

**调研日期**：2026-08-25
**调研目的**：为「A股每日收盘复盘简报」（22-A股日度复盘简报(收盘版)-skill.md）补齐数据缺口，评估三个候选数据源（Infoway / FMP / 同花顺 iFinD）+ 免费替代源（AkShare 等）能否覆盖 A股复盘所需的各项数据。
**方法**：对三个数据源的文档/接口进行调研（Infoway 用已有 key 直接实测 A股；FMP/iFinD 由调研 agent 深挖文档与社区封装）；免费替代源由调研 agent 实测 AkShare/Tushare/Baostock/东财/新浪/腾讯接口；最后整合为"A股复盘所需数据 → 数据源 → 具体接口"对应表。

---

## 目录

1. [A股复盘数据需求清单](#一a股复盘数据需求清单)
2. [数据源一：Infoway A股能力（实测）](#二数据源一infoway-a股能力实测)
3. [数据源二：FMP A股能力](#三数据源二fmp-a股能力)
4. [数据源三：同花顺 iFinD A股能力](#四数据源三同花顺-ifind-a股能力)
5. [免费替代源：AkShare 等](#五免费替代源akshare-等)
6. [整合对应表：数据 → 源 → 接口](#六整合对应表数据--源--接口)
7. [推荐方案](#七推荐方案)
8. [关键数据口径提醒](#八关键数据口径提醒)
9. [调研信息来源](#九调研信息来源)

---

## 一、A股复盘数据需求清单

依据「22-A股日度复盘简报(收盘版)-skill.md」模板与 2026-08-24 实测简报，A股复盘需要以下 12 类数据：

| # | 数据类别 | 在简报中的用途 |
|---|---------|--------------|
| 1 | A股指数行情（上证/深证/创业板/科创50/北证50） | 大盘概况表 |
| 2 | 两市总成交额、量比（放量/缩量） | 资金流向·成交活跃度 |
| 3 | 市场宽度：涨跌家数、涨停/跌停家数、连板股 | 情绪温度计 |
| 4 | 板块/概念涨跌幅（领涨领跌、板块轮动） | 板块热点追踪（10 个热点） |
| 5 | 资金流向：北向资金、主力资金、两融余额、ETF资金流 | 资金流向摘要 |
| 6 | 个股行情与异动、龙虎榜 | 个股要闻精选 |
| 7 | 公司公告（业绩/增减持/并购/IPO） | 重大公告精选 |
| 8 | 宏观政策（央行公开市场操作/逆回购/MLF） | 宏观政策与监管动态 |
| 9 | 宏观数据（CPI/PPI/PMI/社融/LPR，含实际/预期/前值） | 宏观数据解读 |
| 10 | 国际市场（美股指数/原油/黄金/离岸人民币/美元指数） | 国际市场联动 |
| 11 | 港股（恒生指数、南向资金） | 国际市场联动 |
| 12 | 舆情/机构观点（社区热议、研报） | 舆情与市场情绪 |

---

## 二、数据源一：Infoway A股能力（实测）

> 用已有 API key 直接实测（2026-08-25）。

### 2.1 实测结论

| # | 数据类别 | 支持度 | 实测接口 | 实测结果 |
|---|---------|-------|---------|---------|
| 1 | A股指数行情 | ✅ 能取（值需校准） | `POST /stock/v2/batch_kline`，代码 `000001.SH`/`399001.SZ`/`399006.SZ`/`000688.SH` | 全部返回 K线；但**指数值与官方收盘有偏差**（如深证成指报 13687 vs 官方 13794，差 ~0.8%），不能作权威值 |
| 4 | A股板块涨跌 | ✅ 能取 | `GET /common/v2/basic/plate/industry/CN` | 返回 **132 个行业**（含 chg 涨跌幅、rise/fall 家数、total_amount 成交额、market_cap 市值） |
| 3 | A股涨跌家数 | ✅ 能取 | `GET /common/v2/basic/market/breadth/CN` | 返回分档涨跌家数（如 rise 2896+、fall 1453+） |
| 2 | 两市总成交额 | ⚠️ 需自聚合 | 板块/指数 amount 累加 | 无现成"两市总额"，可自算 |
| 5 | 北向/主力/两融/ETF资金流 | ❌ | 无 | Infoway 无资金流端点 |
| 6 | 龙虎榜 | ❌ | 无 | 无 |
| 7 | 公司公告 | ❌ | 仅新闻 WS | 无结构化公告 |
| 8 | 央行公开市场操作 | ❌ | 无 | 无 |
| 9 | 宏观数据 | ❌ | 无 | 无经济日历 |
| 10 | 国际市场 | ✅（美股/商品/加密） | `common/v2/batch_kline` | 美股/原油/黄金/外汇可取（美股调研已验证） |
| 11 | 港股 | ✅ | `stock/batch_trade` 等 | 覆盖港股（文档确认） |
| 12 | 舆情 | ⚠️ | 新闻 WS | 只有快讯流 |

### 2.2 一句话结论

**Infoway（免费档）对 A 股的价值 = 板块涨跌（132 行业）+ 涨跌家数（breadth/CN）两个一手数据**；指数值需与官方校准；北向/主力/两融/龙虎榜/公告/宏观全部缺失。适合做 A股复盘的"补缺源"，不是主源。

---

## 三、数据源二：FMP A股能力

### 3.1 数据源概述

| 项目 | 内容 |
|---|---|
| Base URL | `https://financialmodelingprep.com/stable/{endpoint}`（旧 `api/v3/` 部分下线） |
| 鉴权 | `apikey` 参数 |
| 付费分层 | Free（250 次/天，仅美股 sample）/ Starter $22 / Premium $59 / **Ultimate $149**。**A股/港股需 Ultimate「全球」档，且为延迟数据** |
| A股符号 | 上海 `600519.SS`、深圳 `000001.SZ`、港股 `0700.HK`；上证指数 `000001.SS`、恒生 `^HSI` |

### 3.2 12 类数据逐项结论

| # | 数据类别 | 支持度 | 具体接口 | 备注 |
|---|---------|-------|---------|------|
| 1 | A股指数 | ⚠️ 部分 | `GET /stable/index-quote?symbol=000001.SS` | **只有上证指数**；深证/创业板/科创/北证无覆盖（公开 425 指数中未见） |
| 2 | 两市成交额/量比 | ⚠️ | `batch-exchange-quote?exchange=SHH/SHZ` 自聚合 | 无现成端点，需全量聚合，A股全量需 Ultimate |
| 3 | 涨跌停/宽度/连板 | ❌ | 无 | 无现成；用 screener 统计可行性低 |
| 4 | 板块/概念涨跌 | ❌ | 只有美股 GICS 11 行业 | **A股申万/概念板块无支持** |
| 5 | 资金流向（北向/主力/两融/ETF） | ❌ | 无 | 全部无 |
| 6 | 个股/龙虎榜 | ⚠️ | `quote?symbol=600519.SS`；龙虎榜无 | 个股行情可用（Ultimate，延迟）；**龙虎榜无端点** |
| 7 | 公司公告 | ⚠️ | earnings-calendar / press-releases | A股覆盖弱；**增减持（insider）明确不含A股** |
| 8 | 央行 OMO/MLF | ❌ | 无 | 无 |
| 9 | 宏观数据 | ⚠️ | `economic-calendar?country=CN`（CPI/PPI/PMI 含实际/预期/前值） | **LPR、社融无覆盖**；经济指标序列为中国专属 |
| 10 | 国际市场 | ✅ | `commodities-quote`（原油/黄金）、`forex-quote?symbol=USDCNH`、`quote?symbol=^SPX` | 原油/黄金/离岸人民币/美股明确支持；美元指数 DXY 存疑 |
| 11 | 港股 | ✅ | `index-quote?symbol=^HSI`、`quote?symbol=0700.HK` | 恒指/港股个股支持 |
| 12 | 舆情/机构观点 | ⚠️ | stock-news（英文源）、TipRanks | A股舆情弱；评级/目标价基本为美股 |

### 3.3 一句话结论

**FMP 对 A股 = 只有"上证指数 + 个股 + 恒指 + 国际市场 + CN 宏观日历"约一半，且需 Ultimate 付费档 + 数据延迟；A股特有的深证/创业板、宽度、板块、资金流、龙虎榜、公告、OMO 全部缺失。不适合作为 A股复盘主源。**

---

## 四、数据源三：同花顺 iFinD A股能力

### 4.1 数据源概述

| 项目 | 内容 |
|---|---|
| 调用形态 | SDK（iFinDPy，`THS_iFinDLogin(账号,密码)`）或 HTTP API（`quantapi.51ifind.com/api/v1/`，refresh_token→access_token） |
| 核心函数 | `THS_RQ`(实时)、`THS_HQ`(历史)、`THS_BD`(基础)、`THS_SS`(快照)、`THS_DR`(专题报表含龙虎榜)、`THS_EDB`(经济库)、`THS_WCQuery`(问财)、`THS_ReportQuery`(公告) |
| 权限 | **免费版基本不可用**（单命令上限 1W-10W 条）；试用版历史受限（1月/1年/5年）；**正式版**才有涨停/龙虎榜/北向/两融等盘后数据 |
| 代码 | 上证 `000001.SH`、深成 `399001.SZ`、创业板 `399006.SZ`、科创50 `000688.SH`、北证50 `899050.BJ` |

### 4.2 12 类数据逐项结论

| # | 数据类别 | 支持度 | 具体函数 | 权限 |
|---|---------|-------|---------|------|
| 1 | A股指数 | ✅ | `THS_RQ('000001.SH,...','latest,changeRatio,amount')`；历史 `THS_HQ` | 正式版 |
| 2 | 两市成交额/量比 | ✅ | `amount` 累加；量比 `vol_ratio`/`LB` 指标 | 正式版 |
| 3 | 涨跌/涨跌停家数 | ⚠️ | `THS_RQ('000001.SH','riseCount;fallCount;upLimitCount;downLimitCount')` | 正式版；**连板无现成字段**（需问财 `THS_WCQuery('昨日涨停今日连板')` 或自算） |
| 4 | 板块/概念涨跌 | ✅ | 同花顺行业 `881xxx.TI`、概念 `886xxx`、申万 `801xxx.SL`，用 `THS_RQ/THS_HQ` | 正式版 |
| 5 | 资金流向 | ⚠️ | 主力资金 `THS_RQ(code,'mainNetInflow;...')`；**北向/两融走 `THS_DR` 专题报表**，精确指标代码需 SuperCommand 客户端查询 | 正式版；主力 Level-2 类字段通常收费 |
| 6 | 个股/龙虎榜 | ⚠️ | 个股 `THS_RQ/THS_HQ`；**龙虎榜走 `THS_DR`**，报表代码需客户端查 | 正式版 |
| 7 | 公司公告 | ✅ | `THS_ReportQuery('代码','reportType:901;...')` | 正式版；夜间入库 |
| 8 | 央行 OMO/MLF | ⚠️ | `THS_EDB` 指标 + 新闻解析 | 正式版；无结构化政策日历 |
| 9 | 宏观数据 | ⚠️ | `THS_EDB`（330万+指标，含 CPI/PPI/PMI/社融/利率） | 正式版；**「预期值」未确认提供**，实际值/前值可 |
| 10 | 国际市场 | ✅ | `THS_HQ` 美股 `AAPL.O`、商品/汇率代码 | 正式版；美股次日 06:12 入库 |
| 11 | 港股 | ✅ | `THS_HQ('HSI.HI','00001.HK')`；南向走专题报表 | 正式版 |
| 12 | 舆情/机构观点 | ⚠️ | MCP news 服务、`THS_ReportQuery` | 正式版 |

### 4.3 一句话结论

**iFinD 是 A股/港股原生主场，正式版能覆盖约 9/12 类；但免费版基本不可用、正式版需付费，且北向/两融/龙虎榜/连板的精确指标代码不在公开文档、需登录 SuperCommand 客户端手工配置（落地成本高）。没有 iFinD 付费账号则不建议作为 A股主源。**

---

## 五、免费替代源：AkShare 等

### 5.1 AkShare（开源免费，无需注册）—— 推荐主源

> `pip install akshare`。本质是东财/新浪/腾讯/同花顺/金十等公开接口的封装。MIT 开源。

| # | 数据类别 | 支持度 | 具体函数 | 实测 |
|---|---------|-------|---------|------|
| 1 | A股指数行情 | ✅ | `stock_zh_index_daily_em`、`index_zh_a_hist`；代码 `sh000001`/`sz399001`/`sz399006`/`sh000688`/`bj899050` | ✅ |
| 2 | 两市总成交额 | ✅ | `stock_zh_a_spot()` 的"成交额"求和；量比在东财源 `stock_zh_a_spot_em()` 的"量比"字段 | ✅（量比需东财可达） |
| 3 | 涨跌/涨停/跌停/连板 | ✅ | `stock_market_activity_legu`（涨/涨停/跌停/炸板）；`stock_zt_pool_em(date)`（涨停池+连板数+封板资金+行业）；`stock_zt_pool_dtgc_em`（跌停池）；`stock_zt_pool_previous_em`（昨涨停今表现→晋级率） | ✅ |
| 4 | 板块/概念涨跌 | ✅ | `stock_board_industry_name_em`、`stock_board_concept_name_em`（东财，领涨领跌按涨跌幅排序）；同花顺 `stock_board_industry_summary_ths`；申万 `index_analysis_daily_sw` | ✅（东财需正常网络） |
| 5 | 资金流向 | ✅/⚠️ | 北向 `stock_hsgt_hist_em`、`stock_hsgt_fund_flow_summary_em`；主力 `stock_individual_fund_flow`、`stock_sector_fund_flow_rank`；两融 `stock_margin_sse`、`stock_margin_account_info`；**ETF 资金流需自行估算** | ✅（北向净买额 2024-08-19 起官方停发，只有成交总额） |
| 6 | 个股/龙虎榜 | ✅ | 个股 `stock_zh_a_hist_tx`（腾讯）；**龙虎榜 `stock_lhb_detail_em(start,end)`**（含净买额/上榜原因） | ✅ |
| 7 | 公司公告 | ✅ | `stock_notice_report(symbol='全部',date)`（单日全部公告）；巨潮 `stock_zh_a_disclosure_report_cninfo` | ✅（单日 1557 条） |
| 8 | 央行 OMO/MLF | ⚠️ | `macro_china_central_bank_balance`（央行资产负债表）；**公开市场操作明细无结构化接口，需新闻拼接** | ✅/部分 |
| 9 | 宏观数据 | ✅ | `macro_china_cpi_yearly`（含今值/预测值/前值）、`macro_china_pmi_yearly`、`macro_china_lpr` | ✅ |
| 10 | 国际市场 | ✅ | 新浪直连 `hf_CL`(WTI)/`hf_GC`(黄金)/`gb_$dji`/`gb_ixic`/`fx_susdcny`(人民币)；美元指数用东财 `index_global_hist_em` | ✅ |
| 11 | 港股 | ✅ | 新浪 `rt_hkHSI`(恒指)、`stock_hk_index_daily_sina`；南向 `stock_hsgt_fund_flow_summary_em` | ✅ |
| 12 | 舆情/机构观点 | ✅ | `stock_news_em`(个股新闻)、`stock_research_report_em`(研报+评级+盈利预测)、`stock_news_main_cx`(财新) | ✅ |

**环境坑（接口有效，换环境即可）**：东财 push2 系列在本机被限流（换正常网络）；`py_mini_racer` 在 Python 3.14/Apple Silicon 崩溃（改用 Python 3.9-3.11）。

### 5.2 其他免费源

| 源 | 定位 | 优点 | 限制 |
|----|------|------|------|
| **Baostock** | 免费历史行情 | 全免费无需注册；沪深日线稳定（`query_history_k_data_plus("sh.000001",...)`） | 无涨停池/龙虎榜/北向/板块实时 |
| **Tushare** | 官方 API | 字段严格、限频明确 | 积分制：龙虎榜需 2000 积分、涨停跌停需 5000 积分；免费档每天限额 |
| **东方财富公开 Web** | 免费直连 | `push2`/`push2ex`（涨停池）/`datacenter-web`（龙虎榜/资金流）/`np-anotice`（公告）全部可达 | 按 IP 限流，突发封 IP；无官方文档（逆向） |
| **新浪/腾讯公开接口** | 实时快照兜底 | `hq.sinajs.cn`（A股/美股/商品/汇率/恒指）、`qt.gtimg.cn` 实测全可用；需带 Referer | 限流比东财宽松，需控频 |

---

## 六、整合对应表：数据 → 源 → 接口

| # | A股复盘所需数据 | 首选源 | 具体接口/函数 | 免费/付费 |
|---|---------------|-------|--------------|----------|
| 1 | A股指数行情 | 官方媒体（权威）+ AkShare | `index_zh_a_hist` / `stock_zh_index_daily_em`；Infoway 交叉验证 | 免费 |
| 2 | 两市总成交额、量比 | AkShare | `stock_zh_a_spot()` 求和；量比 `stock_zh_a_spot_em` | 免费 |
| 3 | 涨跌家数/涨停/跌停/连板 | AkShare | `stock_market_activity_legu`、`stock_zt_pool_em`、`stock_zt_pool_dtgc_em` | 免费 |
| 4 | 板块/概念涨跌 | **Infoway**（一手 132 行业）+ AkShare | Infoway `plate/industry/CN`；AkShare `stock_board_industry_name_em` | 免费 |
| 5 | 北向/主力/两融/ETF资金流 | AkShare | `stock_hsgt_fund_flow_summary_em`、`stock_individual_fund_flow`、`stock_margin_sse` | 免费 |
| 6 | 个股/异动/龙虎榜 | AkShare | `stock_zh_a_hist_tx`、`stock_lhb_detail_em` | 免费 |
| 7 | 公司公告 | AkShare | `stock_notice_report(symbol='全部',date)` | 免费 |
| 8 | 央行 OMO/MLF | 新闻（金十/财联社） | `stock_news_main_cx` + 财经媒体检索 | 免费 |
| 9 | 宏观数据（含实际/预期/前值） | AkShare | `macro_china_cpi_yearly`、`macro_china_pmi_yearly`、`macro_china_lpr` | 免费 |
| 10 | 国际市场（美股/原油/黄金/人民币/美元指数） | 新浪直连 / AkShare | `hq.sinajs.cn/list=hf_CL,hf_GC,gb_$dji,fx_susdcny`；东财美元指数 | 免费 |
| 11 | 港股（恒指/南向） | 新浪直连 / AkShare | `rt_hkHSI`、`stock_hk_index_daily_sina`、`stock_hsgt_fund_flow_summary_em` | 免费 |
| 12 | 舆情/机构观点 | AkShare | `stock_news_em`、`stock_research_report_em` | 免费 |

**三商业源在 A股复盘中的角色**：
- **Infoway**：免费档补「板块 132 行业 + 涨跌家数」两个一手数据（已实测可用）
- **FMP**：基本用不上（A股覆盖窄 + 需 Ultimate 付费 + 延迟）
- **iFinD**：无付费账号则跳过；有账号可作 A股深度补充（但指标代码落地成本高）

---

## 七、推荐方案

**主数据源：AkShare（免费开源）** —— 一条依赖覆盖 10/12 类（指数/成交额/涨停池/北向/主力/两融/龙虎榜/公告/宏观/国际/港股/研报）。

**辅助/交叉验证**：
- **Infoway**（已有 key，免费）：板块 132 行业 + 涨跌家数（一手 API）
- **Baostock**：历史日线做数据校验
- **新浪/腾讯直连**：实时快照兜底

**推荐组合架构**：
```
A股复盘数据层
├── AkShare        # 主源：指数/成交额/宽度/资金/龙虎榜/公告/宏观/研报
├── Infoway        # 补缺：板块 132 行业 + 涨跌家数（一手）
├── 新浪直连        # 兜底：美股/原油/黄金/人民币/恒指 实时快照
└── 财经媒体检索    # 补：央行 OMO/MLF、政策文件、舆情话题
```

---

## 八、关键数据口径提醒

1. **北向资金净买额 2024-08-19 起官方停止每日披露**（仅盘后每日总额），所有源（AkShare/iFinD/FMP）拿到的都只有成交总额，报告只能写"前十大活跃股 + 媒体估算"，禁止编造净流入数字——这与优化后提示词的"北向资金口径提醒"一致。
2. **Infoway 的 A股指数值需与官方校准**（实测偏差 ~0.8%），不能作权威值；其板块/涨跌家数可用。
3. **AkShare 部分东财接口有 IP 限流**，`py_mini_racer` 需 Python 3.11 以下——生产环境需注意。
4. **连板股/晋级率**需用 `stock_zt_pool_em` 的"连板数"字段 + `stock_zt_pool_previous_em` 计算，无现成聚合。

---

## 九、调研信息来源

### Infoway（本次实测）
- 文档站：https://docs.infoway.io/ （llms.txt：https://docs.infoway.io/llms.txt）
- 实测接口：`POST /stock/v2/batch_kline`、`GET /common/v2/basic/plate/industry/CN`、`GET /common/v2/basic/market/breadth/CN`

### FMP
- 文档镜像（stable 端点）：https://intelligence.financialmodelingprep.com/developer/docs/stable/
- 公开指数行情页（425 指数，确认 000001.SS/^HSI）：https://site.financialmodelingprep.com/market-indexes
- 公开外汇页（500 对，确认 USDCNH）：https://site.financialmodelingprep.com/currencies
- dayu-agent FMP 集成调研（A股符号/Ultimate 档/内幕不含A股）：https://github.com/noho/dayu-agent/blob/main/docs/fmp_integration_research.md
- Airbyte FMP 连接器（SHH/SHZ 交易所代码）：https://docs.airbyte.com/integrations/sources/financial-modelling

### 同花顺 iFinD
- 官网/帮助中心：https://quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/（含 manual.html / faq.html / deploy.html）
- HTTP API 手册 PDF（含行情/资金流指标名与配额错误码）：http://quantapi.10jqka.com.cn/thsft/iFindService/DataInterfaceWeb/Index/get-File?Marked=863746e5ecd9608b82b406ddbc4fd11a&id=318
- 社区封装（ths_close_price_stock、881 板块代码）：https://github.com/10e9928a/ifind-data

### AkShare / 免费源
- AkShare 官方文档：https://akshare.akfamily.xyz/ ；GitHub：https://github.com/akfamily/akshare
- Tushare 文档：https://tushare.pro/document/2?doc_id=108
- Baostock：https://baostock.com/
- 北向资金口径变化：https://finance.ifeng.com/c/8c9lGjZc39l 、https://finance.sina.com.cn/jjxw/2024-07-27/doc-incfpsmm3457548.shtml
