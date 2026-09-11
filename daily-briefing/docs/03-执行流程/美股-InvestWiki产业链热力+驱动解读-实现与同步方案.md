# 美股 Invest Wiki 产业链热力 + 驱动解读：公共实现与同步方案

**状态**：方案已跑通本地试运行，待工程化  
**适用报告**：美股日度复盘简报第四部分  
**对应提示词**：[`美股日度复盘-提示词.md`](https://github.com/xifengxx/kol-daily/blob/gh-pages/daily-briefing/docs/01-提示词/美股日度复盘-提示词.md)  
**产业链数据源仓库**：[xifengxx/invest-wiki](https://github.com/xifengxx/invest-wiki)  
**简报发布仓库**：[xifengxx/kol-daily](https://github.com/xifengxx/kol-daily)

---

## 1. 一句话设计

用 FMP 全市场行业接口算“行业热力”，用 Invest Wiki 编译出的产业链宇宙算“产业链段热力”，再用新闻检索给热力表和异常股补“为什么”；所有环节只显示 Top8 / Bottom8，但计算必须覆盖全量产业链段。

---

## 2. 两个仓库的职责

| 仓库 | 职责 | 是否是数据源 |
|---|---|---|
| [invest-wiki](https://github.com/xifengxx/invest-wiki) | L2 词条、产业链定义、公司/股票映射、L3 编译器 | 是，产业链内容源 |
| [kol-daily](https://github.com/xifengxx/kol-daily) | 报告数据脚本、`chain_universe.json`、行情热力 JSON、驱动 JSON、报告模板与渲染 | 消费方，只应消费版本化快照 |

**不要抓 GitHub Pages 网页 DOM 当数据源。**  
应使用 `wiki_data.json` 或进一步编译出的 `chain_universe.json` 版本快照。

---

## 3. 总体数据流

```text
Invest Wiki L2 markdown
      ↓ build_wiki_data.py
Invest Wiki L3 wiki_data.json
      ↓ build_chain_universe.py
chain_universe.json
      ↓ fetch_industry_chain_heat.py
industry_chain_heat_YYYY-MM-DD.json
      ↓ fetch_us_market_data.py
us_market_data_YYYY-MM-DD.json
      ↓ fetch_daily_drivers.py
us_drivers_raw_YYYY-MM-DD.json
      ↓ 人工筛选 / 模型整理，不编造
us_drivers_YYYY-MM-DD.json
      ↓ render_industry_chain_report.py
YYYY-MM-DD-industry-chain-invest-wiki.md
      ↓ render_drivers_report.py
YYYY-MM-DD-industry-chain-invest-wiki-drivers.md
      ↓ manifest.json + GitHub Pages
线上报告
```

---

## 4. 产业链宇宙如何形成

### 4.1 从原始段到 canonical 段

Invest Wiki 有 AI算力和半导体两个大赛道，其中部分产业段名称完全相同，例如：

- 光刻机
- 封装基板材料
- 电子特气
- 薄膜沉积设备
- Chiplet与异构集成
- CPU(服务器级)
- 高纯硅料与硅片
- 检测量测设备
- RISC-V AI芯片
- 刻蚀设备
- 光刻胶与湿化学品
- 高速连接器与铜缆
- 晶圆代工(先进制程)
- EDA与IP核
- 溅射靶材
- FPGA

这些跨赛道重复段合并为同一个 canonical 段；合并结果记录在 `segment.source_slugs`。

### 4.2 公司去重规则

| 层级 | 规则 |
|---|---|
| 产业链段内 | 同一 ticker 只算一次。 |
| AI算力大赛道汇总 | 所有属于 AI算力的段先合并 ticker，再去重后计算。 |
| 半导体大赛道汇总 | 所有属于半导体的段先合并 ticker，再去重后计算。 |
| 全局汇总 | 所有海外候选股合并 ticker，再去重后计算。 |
| A股 | 只进入 A股映射列，不参与海外热力计算。 |
| 私有 / 未上市 | 排除行情计算；如需出现在产业链中，仅作上下文。 |

### 4.3 计算口径

对每个段计算：

```text
等权涨跌幅 = sum(每只有效海外成分股 chg_pct) / 有效成分股数量
市值加权涨跌幅 = sum(chg_pct * USD marketCap) / sum(USD marketCap)
```

主排序口径是**等权**；市值加权只作参考。  
等权能避免 NVIDIA、Apple、TSMC 等超大权重把整段表现盖住；市值加权能观察大权重是否才是驱动来源。

每段还输出：

- `n_overseas_candidates`
- `n_used`
- `n_missing`
- `coverage_pct`
- `rankable`
- `top`
- `bottom`
- `stocks`
- `a_share`

`rankable=true` 的条件是 `n_used >= 2`。样本不足的段不参与排名，但仍保留在 JSON，方便后续补齐。

---

## 5. 行业热力与产业链热力的区别

| 项目 | 行业热力图 | Invest Wiki 产业链段热力 |
|---|---|---|
| 数据源 | FMP `industry-performance-snapshot` | Invest Wiki 自建宇宙 + Yahoo/yfinance 行情 |
| 分类口径 | 交易所官方/行业分类，NASDAQ+NYSE 同名合并 | 自建产业链角色，跨国家、跨市场 |
| 成分股 | FMP 接口只给行业涨跌，免费版不给成分股 | 明确知道每段有哪些公司 |
| 计算 | 行业内成分股等权 | 段内海外成分股等权，市值加权参考 |
| 展示 | Top8 / Bottom8 | Top8 / Bottom8 |
| 解释层 | 行业新闻、代表性公司事件 | 产业链瓶颈、订单、财报、标志性个股 |
| A股 | 无 | 有 A股映射，但只作观察 |

两者不是同一口径，不能互相换算；报告必须分别标注。

---

## 6. 驱动解释层

### 6.1 检索对象

1. FMP 行业热力 Top8 / Bottom8。
2. Invest Wiki 产业链 Top8 / Bottom8。
3. 所有 `|chg_pct| >= 5%` 的链内异常股。

### 6.2 流程

```text
根据热力 JSON 生成检索 query
      ↓ fetch_daily_drivers.py
us_drivers_raw_YYYY-MM-DD.json
      ↓ 人 / 模型筛选，交叉验证时间与对象
us_drivers_YYYY-MM-DD.json
      ↓ render_drivers_report.py
新报告的驱动解读列
```

`fetch_daily_drivers.py` 当前用 Google News RSS 作第一层检索；技术实现可以保留该入口，也可以替换为新闻 API，但输出 schema 必须一致。

### 6.3 结构化 schema

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO8601",
  "method": "Google News RSS + human curation",
  "entries": [
    {
      "type": "industry | segment | anomaly",
      "key": "行业名 / segment_id / TICKER",
      "display": "展示名",
      "confidence": "高 | 中 | 低",
      "driver": "1-2句驱动解释",
      "sources": [
        {
          "title": "新闻标题",
          "source": "媒体名",
          "url": "URL",
          "published": "YYYY-MM-DD"
        }
      ]
    }
  ]
}
```

### 6.4 解释规则

| 置信度 | 判定 |
|---|---|
| 高 | 官方公告、财报、监管文件、权威媒体明确确认，时间和对象匹配。 |
| 中 | 有较强相关线索，但不是完全一对一确认。 |
| 低 | 无明确公开原因，只有泛化报道或情绪推断。 |

没有原因时统一写：

```text
暂无明确公开原因。（置信度：低）
```

禁止编造订单、指引、评级、监管事件、资金流向。  
禁止混淆盘中、盘前、盘后。

---

## 7. Invest Wiki 更新后的同步策略

这是当前最容易出错的地方。用户可能昨天或今天改了产业链地图，但 L3 或简报侧 universe 不一定跟着更新。

### 7.1 先判断改的是哪一层

| 改动内容 | 应该改哪里 | 后续动作 |
|---|---|---|
| 新增公司、修改公司描述、更新股票代码、调整产业段成分 | Invest Wiki L2 markdown | commit L2 → 重建 L3 → 重建 universe |
| 只改了产业链网页 HTML / `wiki_data.json` | 不允许直接作为长期修改 | 必须回写到 L2，否则下次编译会丢 |
| 改了 16 个跨赛道重名的合并规则 | `build_chain_universe.py` 的 `CANONICAL_SEGMENT_ALIASES` | bump universe 逻辑版本，重建 universe |
| 改了 ticker 别名、OTC/ADR、日韩台港股后缀 | `build_chain_universe.py` 的 `TICKER_ALIASES` | bump universe 逻辑版本，重建 universe |
| 改了报告表头、Top8 展示方式、异常股解释列 | 提示词 / 渲染脚本 | 更新提示词和渲染逻辑，不需要重建 universe |
| 改了新闻检索关键词 | `fetch_daily_drivers.py` 的 query map | 只影响后续驱动解释，不影响行情 |

### 7.2 推荐的版本化快照

当前 `chain_universe.json` 是单文件，`version` 固定为 `"1.0"`，不利于追溯。技术实现应升级为：

```text
daily-briefing/data/universes/
  chain_universe_vYYYY-MM-DD-<source_hash8>.json
  chain_universe_vYYYY-MM-DD-<source_hash8>.json
chain_universe.json   # 当前生产用 stable 指针/副本
```

每个 universe 至少要有这些元数据：

```json
{
  "version": "YYYY-MM-DD.<n>",
  "built_at": "ISO8601",
  "source_file": "wiki_data.json 的可追溯路径或 raw URL",
  "source_commit": "GitHub commit SHA",
  "source_sha256": "前 12-16 位 hash",
  "source_generated_at": "L3 编译时间",
  "logic_version": "universe 编译规则版本",
  "stats": {}
}
```

在 `industry_chain_heat_YYYY-MM-DD.json` 和最终报告中都记录：

```text
universe_version
source_sha256
logic_version
target_date
generated_at
```

### 7.3 旧报告是否回算

默认**不回算历史报告**。产业链图谱变了以后：

- 老报告继续使用当时 universe 的口径；
- 新报告使用最新 universe；
- 如确需回算，必须生成新文件，例如 `YYYY-MM-DD-industry-chain-invest-wiki-uv2.md`，不能覆盖老报告。

### 7.4 无法访问本地 Invest Wiki 怎么办

技术环境不要依赖任何 `/Users/...` 本地路径。可选方案：

1. **推荐：把 `chain_universe.json` 作为版本化快照提交到 kol-daily 仓库。**
2. 把 `wiki_data.json` 作为带 hash 的 source snapshot 存入对象存储或 kol-daily 仓库。
3. 从 invest-wiki GitHub raw 拉取，但必须固定 commit SHA，不能永远拉 `main`。
4. 后续可做轻量 release API，例如 `chain_universe_v1.json` + checksum。

---

## 8. 技术实现 TODO

### 必做

1. 把 `build_chain_universe.py` 的 `version` 从硬编码 `"1.0"` 升级为自动生成，并写入 `source_sha256`、`source_commit`、`logic_version`、`built_at`。
2. 把 universe 存为版本化快照，而不是只维护一个会被覆盖的 JSON。
3. 把渲染脚本的标题替换逻辑重构为显式模板渲染。
4. 把 `TARGET`、`UNIVERSE`、`OUTPUT` 全部参数化，禁止脚本里残留固定日期。
5. 报告文件名统一使用美东交易日。

### 建议做

6. 在 L3 编译产物中加入 `generated_at` 和 `source_commit`。
7. 给 `chain_universe.json` 加校验器：段名重复、ticker 非法、A/海外归类异常、私有公司误入行情候选都应报警。
8. 驱动解释可先用 Google News RSS，后续替换为新闻 API 时保持 schema 不变。
9. 对缺失行情、市值缺失、数据日期混用生成 warnings 文件，而不是静默忽略。
10. 做一个 dry-run 报表：81 原始段 → 65 canonical 段，每段成分股数量、缺失率、是否可排名。

---

## 9. 每日检查清单

| 检查项 | 通过标准 |
|---|---|
| Invest Wiki 是否更新 | 如 L2 有更新，必须先重建 L3 和 universe。 |
| universe 版本 | 报告能说出使用的 universe version / source hash。 |
| 交易日 | `us_market_data`、`industry_chain_heat`、`us_drivers` 都对应同一美东交易日。 |
| 段数 | 全量段参与计算；报告只展示 Top8 / Bottom8。 |
| 去重 | 段内和大赛道汇总均按 ticker 去重。 |
| 异常股 | 所有 `|chg_pct| >= 5%` 全量展示。 |
| 驱动解释 | 每条都有置信度；无原因写“暂无明确公开原因”。 |
| A股映射 | 只作次日观察，不参与海外热力计算。 |
| 新文件 | 没有覆盖任何历史报告。 |
| manifest | 新报告在 `us` 数组最前。 |
| 线上验证 | URL 返回 200，关键标题能在页面中找到。 |
