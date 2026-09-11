# 美股产业链热力 + 驱动解读：公共实现方案

**状态**：基线脚本、数据产物和 9/11 报告已提交到 kol-daily。适用报告：美股日度复盘简报第四部分
**对应提示词**：[`美股日度复盘-提示词.md`](https://github.com/xifengxx/kol-daily/blob/gh-pages/daily-briefing/docs/01-提示词/美股日度复盘-提示词.md)  
**产业链数据源仓库**：[xifengxx/invest-wiki](https://github.com/xifengxx/invest-wiki)  
**简报发布仓库**：[xifengxx/kol-daily](https://github.com/xifengxx/kol-daily)
**运行手册**：[`美股产业链热力+驱动解读-数据流与运行手册.md`](./美股产业链热力+驱动解读-数据流与运行手册.md)

**当前线上 universe 快照**：[`chain_universe.json @ 5a32637`](https://github.com/xifengxx/invest-wiki/blob/5a32637/L3-%E7%BD%91%E9%A1%B5%E4%BA%A7%E7%89%A9/chain_universe.json)；**当前 universe 版本**：`2026-09-11.3` / `logic_version=canonical-segments-v2` / `source_hash8=ba099660`

---

## 1. 一句话设计

用 FMP 全市场行业接口算“行业热力”，用产业链 universe JSON 算“产业链段热力”，再用新闻检索给热力表和异常股补“为什么”；所有环节只显示 Top8 / Bottom8，但计算必须覆盖全量产业链段。

---

## 2. 系统边界

- 产业链上游只负责发布带版本号的 `chain_universe.json`。
- 简报侧是消费方，只负责下载、校验、抓行情、计算、检索驱动和渲染报告。
- 技术侧不需要维护或理解产业链图谱的内部工程；当上游发布新的 `chain_universe.json` 后，只需要把 pipeline 配置里的固定 commit URL 更新到新版本。
- 不要抓产业链网页 DOM 当数据源，不要迁入产业链图谱的内部生成逻辑。

---

## 3. 总体数据流

```text
industry_mapping.json + FMP
      ↓ fetch_us_market_data.py
us_market_data_YYYY-MM-DD.json（含行业热力）

chain_universe.json（invest-wiki 固定 commit）+ Yahoo/yfinance
      ↓ fetch_industry_chain_heat.py
industry_chain_heat_YYYY-MM-DD.json

us_market_data + industry_chain_heat
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

## 4. 当前落地状态

| 产物 / 脚本 | 当前状态 | 责任仓库 |
|---|---|---|
| `chain_universe.json` | 已发布到 invest-wiki，commit `5a32637`，包含 version / source hash / source commit / 统计信息。 | invest-wiki |
| `industry_mapping.json` | 已提交到 kol-daily，用于 FMP 英文行业到中文行业映射。 | kol-daily |
| `chain_universe.json` 消费侧快照 | 已提交到 `daily-briefing/scripts/chain_universe.json`，内容对齐上游 commit `5a32637`。 | kol-daily |
| `fetch_us_market_data.py` | 已提交，支持 FMP 全市场行业热力和免费源兜底；不再包含旧 `chain_map.json` 链路。 | kol-daily |
| `fetch_industry_chain_heat.py` | 已提交，负责 universe 行情抓取和 65 段热力计算。 | kol-daily |
| `fetch_daily_drivers.py` | 已提交，日期参数已从固定日期改为必填参数。 | kol-daily |
| `render_industry_chain_report.py` / `render_drivers_report.py` | 已提交，负责热力表和驱动解读列渲染。 | kol-daily |
| 基线数据产物 | 已提交 2026-09-10 交易日的市场快照、产业链热力、驱动原始结果和整理结果。 | kol-daily |
| 基线报告 | 已提交 `2026-09-11-industry-chain-invest-wiki.md` 和驱动解读版报告。 | kol-daily |

---

## 5. 产业链计算规则

### 5.1 数据边界与去重

只消费 `chain_universe.json` 中的 canonical segment。不需要重建或改写这些段；跨赛道重复段合并已经在 universe JSON 中完成。

报告侧计算时遵守以下去重规则：

| 层级 | 规则 |
|---|---|
| 产业链段内 | 同一 ticker 只算一次。 |
| AI算力大赛道汇总 | 所有属于 AI算力的段先合并 ticker，再去重后计算。 |
| 半导体大赛道汇总 | 所有属于半导体的段先合并 ticker，再去重后计算。 |
| 全局汇总 | 所有海外候选股合并 ticker，再去重后计算。 |
| A股 | 只进入 A股映射列，不参与海外热力计算。 |
| 私有 / 未上市 | 排除行情计算；如需出现在产业链中，仅作上下文。 |

### 5.2 计算口径

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

## 6. 行业热力与产业链热力的区别

| 项目 | 行业热力图 | 产业链段热力 |
|---|---|---|
| 数据源 | FMP `industry-performance-snapshot` | 产业链 universe JSON + Yahoo/yfinance 行情 |
| 分类口径 | 交易所官方/行业分类，NASDAQ+NYSE 同名合并 | 自建产业链角色，跨国家、跨市场 |
| 成分股 | FMP 接口只给行业涨跌，免费版不给成分股 | 明确知道每段有哪些公司 |
| 计算 | 行业内成分股等权 | 段内海外成分股等权，市值加权参考 |
| 展示 | Top8 / Bottom8 | Top8 / Bottom8 |
| 解释层 | 行业新闻、代表性公司事件 | 产业链瓶颈、订单、财报、标志性个股 |
| A股 | 无 | 有 A股映射，但只作观察 |

两者不是同一口径，不能互相换算；报告必须分别标注。

---

## 7. 驱动解释层

### 7.1 检索对象

1. FMP 行业热力 Top8 / Bottom8。
2. 产业链 Top8 / Bottom8。
3. 所有 `|chg_pct| >= 5%` 的链内异常股。

### 7.2 流程

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

### 7.3 结构化 schema

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

### 7.4 解释规则

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

## 8. universe 数据契约与同步

### 8.1 版本化快照

`chain_universe.json` 至少包含三类信息：

```json
{
  "version": "universe 版本",
  "logic_version": "计算规则版本",
  "source_commit": "GitHub commit SHA",
  "source_sha256": "内容校验值",
  "stats": {},
  "segments": [],
  "companies": {}
}
```

`segments` 是报告计算的主要输入；每个 segment 至少要有 `segment_id`、`name`、`industry_tags`、`companies`、`n_overseas_candidates`、`n_a_share_mapping` 和 `a_share`。`companies` 用于检查 ticker 是否唯一，以及公司归属哪些段。

`chain_universe.json` 已包含可追溯元数据。kol-daily 不需要长期维护第二份 universe；如果为了回溯需要缓存，可保存为带版本文件名的副本：

```text
daily-briefing/data/universes/
  chain_universe_vYYYY-MM-DD-<source_hash8>.json
chain_universe.json   # 当前生产用 stable 指针/副本
```

每个 universe 至少要有这些元数据：

```json
{
  "version": "YYYY-MM-DD.<n>",
  "built_at": "ISO8601",
  "source_commit": "GitHub commit SHA",
  "source_sha256": "完整 64 位 SHA-256 十六进制字符串",
  "source_hash8": "source_sha256 的前 8 位，仅用于文件名和报告展示",
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

### 8.2 技术环境如何获取数据源

技术环境不要依赖任何 `/Users/...` 本地路径。可选方案：

1. **推荐：从 invest-wiki 固定 commit 拉取 `chain_universe.json`。**
2. 拉取后校验 `version`、`logic_version`、`source_sha256`、`source_commit` 和 `stats`，再进入行情计算。
3. 如果要做离线复算，可把同一 commit 的 JSON 缓存到对象存储或 `daily-briefing/data/universes/`。
4. 后续可做 release/tag，例如 `chain_universe_v1` + checksum，但仓库固定 commit 已经足够作为当前基线。

示例：

```bash
CHAIN_UNIVERSE_URL="https://raw.githubusercontent.com/xifengxx/invest-wiki/5a32637/L3-%E7%BD%91%E9%A1%B5%E4%BA%A7%E7%89%A9/chain_universe.json"
curl -fsSL "$CHAIN_UNIVERSE_URL" -o chain_universe.json
python3 - <<'PY'
import json
d = json.load(open("chain_universe.json"))
print(d["version"], d["logic_version"], d["source_sha256"], d["stats"])
PY
```

### 8.3 推荐同步操作

上游维护者手动重建并发布新 universe 后，kol-daily 只需要把配置中的 `CHAIN_UNIVERSE_URL` 指到新的 fixed commit：

```bash
CHAIN_UNIVERSE_URL="https://raw.githubusercontent.com/xifengxx/invest-wiki/<invest-wiki-commit-sha>/L3-%E7%BD%91%E9%A1%B5%E4%BA%A7%E7%89%A9/chain_universe.json"
```

除这个 URL 外，简报侧不接触产业链图谱的其他工程文件或页面数据。

### 8.4 旧报告是否回算

默认**不回算历史报告**。产业链 universe 变了以后：

- 老报告继续使用当时 universe 的口径；
- 新报告使用最新 universe；
- 如确需回算，必须生成新文件，例如 `YYYY-MM-DD-industry-chain-invest-wiki-uv2.md`，不能覆盖老报告。

当前历史报告只有 `universe_version` 这类粗粒度信息，部分旧版还使用过 11 环节口径；没有完整的 `source_sha256` 和 `logic_version`，所以不能保证逐字节复算。这个限制要写进交接说明：**从新版本开始必须补齐版本元数据，历史报告只作业务参考，不作为可复算基线。**

---

## 9. 技术实现 TODO

### 必做

1. 每次运行前校验 universe 的 `version`、`logic_version`、`source_sha256`、`source_commit`，并把它们写入热力 JSON 和报告。
2. 把渲染脚本的标题替换逻辑重构为显式模板渲染。
3. 统一日期语义：数据文件使用美东交易日，报告文件使用北京时间发布日。

### 建议做

4. 给 `chain_universe.json` 加消费侧校验器：segment 非空、ticker 重复、A/海外归类异常、私有公司误入行情候选都应报警。
5. 驱动解释可先用 Google News RSS，后续替换为新闻 API 时保持 schema 不变。
6. 对缺失行情、市值缺失、数据日期混用生成 warnings 文件，而不是静默忽略。
7. 做一个 dry-run 报表：每段成分股数量、缺失率、是否可排名。

---

## 10. 每日检查清单

| 检查项 | 通过标准 |
|---|---|
| universe 版本 | `CHAIN_UNIVERSE_URL` 指向的固定 commit 是当前应使用的最新发布版本。 |
| universe 元数据 | 报告能说出使用的 universe version / source hash / logic_version。 |
| 交易日 | `us_market_data`、`industry_chain_heat`、`us_drivers` 都对应同一美东交易日。 |
| 段数 | 全量段参与计算；报告只展示 Top8 / Bottom8。 |
| 去重 | 段内和大赛道汇总均按 ticker 去重。 |
| 异常股 | 所有 `|chg_pct| >= 5%` 全量展示。 |
| 驱动解释 | 每条都有置信度；无原因写“暂无明确公开原因”。 |
| A股映射 | 只作次日观察，不参与海外热力计算。 |
| 新文件 | 没有覆盖任何历史报告。 |
| manifest | 新报告在 `us` 数组最前。 |
| 线上验证 | URL 返回 200，关键标题能在页面中找到。 |
