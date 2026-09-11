# 美股 Invest Wiki 产业链热力 + 驱动解读：公共实现与同步方案

**状态**：方案已跑通本地试运行，待工程化  
**适用报告**：美股日度复盘简报第四部分  
**对应提示词**：[`美股日度复盘-提示词.md`](https://github.com/xifengxx/kol-daily/blob/gh-pages/daily-briefing/docs/01-提示词/美股日度复盘-提示词.md)  
**产业链数据源仓库**：[xifengxx/invest-wiki](https://github.com/xifengxx/invest-wiki)  
**简报发布仓库**：[xifengxx/kol-daily](https://github.com/xifengxx/kol-daily)

**当前线上 universe 快照**：[`L3-网页产物/chain_universe.json @ 5a32637`](https://github.com/xifengxx/invest-wiki/blob/5a32637/L3-%E7%BD%91%E9%A1%B5%E4%BA%A7%E7%89%A9/chain_universe.json)；**当前 universe 版本**：`2026-09-11.3` / `logic_version=canonical-segments-v2` / `source_hash8=ba099660`

---

## 1. 一句话设计

用 FMP 全市场行业接口算“行业热力”，用 Invest Wiki 编译出的产业链宇宙算“产业链段热力”，再用新闻检索给热力表和异常股补“为什么”；所有环节只显示 Top8 / Bottom8，但计算必须覆盖全量产业链段。

---

## 2. 两个仓库的职责

| 仓库 | 职责 | 是否是数据源 |
|---|---|---|
| [invest-wiki](https://github.com/xifengxx/invest-wiki) | L2 词条、产业链定义、公司/股票映射、L3 编译器、`chain_universe.json` 编译与发布 | 是，产业链宇宙的唯一结构数据源 |
| [kol-daily](https://github.com/xifengxx/kol-daily) | 报告数据脚本、行情热力 JSON、驱动 JSON、报告模板与渲染 | 消费方，只应消费固定 commit 的 `chain_universe.json` |

**不要抓 GitHub Pages 网页 DOM 当数据源。**  
应使用 `chain_universe.json` 版本快照。

---

## 3. 总体数据流

```text
Invest Wiki L2 markdown
      ↓ build_wiki_data.py
Invest Wiki L3 wiki_data.json
      ↓ build_chain_universe.py
chain_universe.json（在 invest-wiki 中发布）
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

## 4. 当前落地状态

本节区分“规范”和“已经在线上仓库可用的实现”，避免技术误以为所有脚本都已开源。

| 产物 / 脚本 | 当前状态 | 责任仓库 |
|---|---|---|
| `L3-网页产物/wiki_data.json` | 已在 invest-wiki 仓库跟踪，是可拉取的结构化产物。 | invest-wiki |
| `fetch_us_market_data.py` | 已在 kol-daily 仓库跟踪，但线上版缺少 `industry_heat`、`industry_mapping.json` 和后续新增的免费源兜底；需与本地试运行版合并后再提交。 | kol-daily |
| `chain_universe.json` | 已发布到 invest-wiki，commit `5a32637`，包含 version / source hash / source commit / 统计信息。 | invest-wiki |
| `industry_mapping.json` | FMP 全市场行业名到中文名/科技焦点的映射，目前只在本地试运行目录，尚未提交。 | kol-daily |
| `build_chain_universe.py` | 已提交到 invest-wiki，负责把 `wiki_data.json` 编译成日报 universe。 | invest-wiki |
| `fetch_industry_chain_heat.py` | 本地试运行脚本，尚未提交到 kol-daily。 | kol-daily |
| `fetch_daily_drivers.py` | 本地试运行脚本，尚未提交到 kol-daily。 | kol-daily |
| `render_industry_chain_report.py` / `render_drivers_report.py` | 本地试运行脚本，尚未提交到 kol-daily。 | kol-daily |

因此，本文描述的是**目标工程方案**；在下述脚本迁移并参数化之前，不要把它当成已经完整的线上 pipeline。

---

## 5. 产业链宇宙如何形成

### 5.1 从原始段到 canonical 段

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

### 5.2 公司去重规则

| 层级 | 规则 |
|---|---|
| 产业链段内 | 同一 ticker 只算一次。 |
| AI算力大赛道汇总 | 所有属于 AI算力的段先合并 ticker，再去重后计算。 |
| 半导体大赛道汇总 | 所有属于半导体的段先合并 ticker，再去重后计算。 |
| 全局汇总 | 所有海外候选股合并 ticker，再去重后计算。 |
| A股 | 只进入 A股映射列，不参与海外热力计算。 |
| 私有 / 未上市 | 排除行情计算；如需出现在产业链中，仅作上下文。 |

### 5.3 计算口径

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

## 7. 驱动解释层

### 7.1 检索对象

1. FMP 行业热力 Top8 / Bottom8。
2. Invest Wiki 产业链 Top8 / Bottom8。
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

## 8. Invest Wiki 更新后的同步策略

这是当前最容易出错的地方。用户可能昨天或今天改了产业链地图，但 L3 或简报侧 universe 不一定跟着更新。

### 8.1 先判断改的是哪一层

| 改动内容 | 应该改哪里 | 后续动作 |
|---|---|---|
| 新增公司、修改公司描述、更新股票代码、调整产业段成分 | Invest Wiki L2 markdown | commit L2 → 重建 L3 → 重建 universe |
| 只改了产业链网页 HTML / `wiki_data.json` | 不允许直接作为长期修改 | 必须回写到 L2，否则下次编译会丢 |
| 改了 16 个跨赛道重名的合并规则 | `build_chain_universe.py` 的 `CANONICAL_SEGMENT_ALIASES` | bump universe 逻辑版本，重建 universe |
| 改了 ticker 别名、OTC/ADR、日韩台港股后缀 | `build_chain_universe.py` 的 `TICKER_ALIASES` | bump universe 逻辑版本，重建 universe |
| 改了报告表头、Top8 展示方式、异常股解释列 | 提示词 / 渲染脚本 | 更新提示词和渲染逻辑，不需要重建 universe |
| 改了新闻检索关键词 | `fetch_daily_drivers.py` 的 query map | 只影响后续驱动解释，不影响行情 |

### 8.2 版本化快照

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
  "source_file": "wiki_data.json 的可追溯路径或 raw URL",
  "source_commit": "GitHub commit SHA",
  "source_sha256": "完整 64 位 SHA-256 十六进制字符串",
  "source_hash8": "source_sha256 的前 8 位，仅用于文件名和报告展示",
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

### 8.3 旧报告是否回算

默认**不回算历史报告**。产业链图谱变了以后：

- 老报告继续使用当时 universe 的口径；
- 新报告使用最新 universe；
- 如确需回算，必须生成新文件，例如 `YYYY-MM-DD-industry-chain-invest-wiki-uv2.md`，不能覆盖老报告。

当前历史报告只有 `universe_version` 这类粗粒度信息，部分旧版还使用过 11 环节口径；没有完整的 `source_sha256` 和 `logic_version`，所以不能保证逐字节复算。这个限制要写进交接说明：**从新版本开始必须补齐版本元数据，历史报告只作业务参考，不作为可复算基线。**

### 8.4 技术环境如何获取数据源

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

### 8.5 推荐同步操作（脚本迁移完成后）

```bash
# 1. Invest Wiki 侧：更新 L2 后重建 L3 和 universe
git clone git@github.com:xifengxx/invest-wiki.git
cd invest-wiki
python3 L3-网页产物/build_wiki_data.py
python3 L3-网页产物/build_chain_universe.py
python3 L3-网页产物/validate.py

# 2. 只提交明确产物，禁止 git add -A
git add L3-网页产物/wiki_data.json L3-网页产物/chain_universe.json
git commit -m "feat: 重建产业链 L3 快照"
git push origin master

# 3. kol-daily 侧：把 pipeline 配置里的 CHAIN_UNIVERSE_URL 指到新的 fixed commit
#    <invest-wiki-commit-sha> 是上一步 push 后得到的完整 SHA。
CHAIN_UNIVERSE_URL="https://raw.githubusercontent.com/xifengxx/invest-wiki/<invest-wiki-commit-sha>/L3-%E7%BD%91%E9%A1%B5%E4%BA%A7%E7%89%A9/chain_universe.json"
```

注意：`build_chain_universe.py` 属于 invest-wiki，不需要迁到 kol-daily。kol-daily 的行情/驱动/渲染脚本仍需完成第 9 节迁移，并且每次运行都必须读取固定 commit 的 `chain_universe.json`。

---

## 9. 技术实现 TODO

### 必做

1. 把 `fetch_industry_chain_heat.py`、`fetch_daily_drivers.py` 和两个 render 脚本迁入 kol-daily。
2. 把本地试运行版 `fetch_us_market_data.py` 中的 `industry_heat`、`industry_mapping.json` 和免费源兜底逻辑合并到 kol-daily 现有脚本，迁移前先做代码 review，避免覆盖线上已验证逻辑。
3. 移除脚本里的本地绝对路径和固定日期默认值，把 `TARGET`、`CHAIN_UNIVERSE_URL`、`OUTPUT` 全部参数化。
4. 每次运行前校验 universe 的 `version`、`logic_version`、`source_sha256`、`source_commit`，并把它们写入热力 JSON 和报告。
5. 把渲染脚本的标题替换逻辑重构为显式模板渲染。
6. 报告文件名统一使用美东交易日。

### 建议做

7. 给 `chain_universe.json` 加更强的校验器：ticker 非法、A/海外归类异常、私有公司误入行情候选都应报警。
8. 驱动解释可先用 Google News RSS，后续替换为新闻 API 时保持 schema 不变。
9. 对缺失行情、市值缺失、数据日期混用生成 warnings 文件，而不是静默忽略。
10. 做一个 dry-run 报表：81 原始段 → 65 canonical 段，每段成分股数量、缺失率、是否可排名。

---

## 10. 每日检查清单

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
