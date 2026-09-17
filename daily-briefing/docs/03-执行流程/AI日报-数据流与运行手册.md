# AI 日报：数据流与运行手册

**品类代号**：`ai`
**源站**：[AIHOT](https://aihot.news) ｜ **接入方式**：REST API（匿名只读，无需 Key）
**用途**：个人阅读，非商业。AIHOT 条款允许个人非商业使用；公开镜像/批量再分发需书面授权。

---

## 1. 这个品类与另两个有什么不同

| | 美股晨间版 `us` | A股收盘版 `cn` | **AI 日报 `ai`** |
|---|---|---|---|
| 数据来源 | FMP/新浪/Yahoo 等 | 腾讯/新浪/AkShare 等 | **AIHOT 单一源** |
| 有无休市 | 有 | 有 | **无——周末照出** |
| 发布节奏 | 周二至周六 07:05 | 周一至周五 16:40 | **每天 08:30** |
| 日期口径 | 美东行情日 / 北京发布日**双轨** | 当日 | **单一日期**（源站日期 = 报告日期） |
| 内容来源 | 模型综合多方数据撰写 | 同左 | **源站摘要逐字引用 + 模型点评** |
| 报告编号 | 从 manifest 推断 | 同左 | **按日历推算**（无台账依赖） |

**最容易做错的一点**：把 `us`/`cn` 的「休市则跳过」逻辑带过来。AI 日报**没有休市概念**，判断依据只有「今天是否已生成」和「源站当天有没有日报」，**不是星期几**。

---

## 2. 源站契约

### 2.1 接口

```text
GET https://aihot.news/api/v1/dailies/{YYYY-MM-DD}
GET https://aihot.news/api/v1/dailies          # 最近 30 期索引
GET https://aihot.news/feed/daily.xml          # RSS（兜底，不含结构化字段）
```

- 未知日期返回 **HTTP 404 + RFC7807**（`{"title":"Not found","detail":"No daily report exists for …"}`）——语义干净，可直接判定
- 匿名只读，无需认证；带 `If-None-Match` 可拿 304

### 2.2 响应结构

```jsonc
{
  "schemaVersion": 1,
  "report": {
    "date": "2026-09-17",              // 报告日期（= 我们用的日期）
    "generatedAt": "2026-09-17T00:00:07.147Z",   // UTC，即北京 08:00
    "windowStart": "2026-09-16T00:00:00.000Z",   // 覆盖窗口起（北京 09-16 08:00）
    "windowEnd":   "2026-09-17T00:00:00.000Z",
    "links": { "aihot": "https://aihot.news/daily/2026-09-17" },
    "attribution": { "name": "AIHOT", "url": "..." },
    "lead": null,                       // ⚠️ 实测恒为 null
    "flashes": [],                      // ⚠️ 实测恒为空
    "sections": [
      { "label": "模型发布/更新",
        "items": [
          { "title": "...",
            "summary": "...",           // 源站摘要，61–202 字
            "source": { "name": "X：某账号 (@handle)" },
            "links": { "aihot": "https://aihot.news/items/<item_id>",
                       "original": "https://..." },
            "attribution": { "name": "AIHOT", "url": "..." } }
        ] }
    ]
  }
}
```

### 2.3 已知的固定特征

| 项 | 事实 |
|---|---|
| 章节 | **固定 5 个**：模型发布/更新、产品发布/更新、行业动态、论文研究、技巧与观点 |
| 体量 | 2–5 章节 / **3–16 条**（波动很大） |
| 发布 | 每天北京 **08:00**，**7 天都有**（实测 2026-09-13 周日仍有 6 条） |
| 语言 | **只有中文**；`?lang=en` 返回 **400** | 
| `lead` | 恒为 `null` ——「今日一句话」必须自己写 |
| `flashes` | 恒为 `[]` —— 不要设计依赖它，变非空时口径说明要提示 |

---

## 3. 数据流（三段式 + 一校验）

```text
① fetch_aihot_daily.py <日期> --json-out data/aihot_daily_<日期>.json
       源站摘要逐字落盘（唯一真源）
       ↓
② 模型只写「判断」→ data/_aihot_comments_<日期>.json
       按 item_id 索引的点评（60–200 字）+ 角度 + 置信度
       ↓
③ render_aihot_report.py --snapshot … --comments … --out reports/ai/<日期>.md
       「源站摘要」从快照机械复制；「我的点评」从 comments 注入
       ↓
④ validate_aihot_report.py --report … --snapshot …
       反向逐字断言 + 覆盖率 + 字数 + 章节数
```

### 为什么不让模型直接写报告

需求是「源站摘要**逐字引用**」，这是确定性要求。模型誊抄做不到 100% 保真（尤其 16 条、每期重写一遍），只要改了一个字，「逐字引用」就不成立——这直接违反项目一贯的「禁止编造」纪律。

**让脚本机械复制、模型只提供判断**，与既有的 `render_drivers_report.py` 是同一个模式，不是新架构。

---

## 4. 运行命令

> 所有命令的工作目录都是 `daily-briefing/`。

### 4.1 取数

```bash
python3 scripts/fetch_aihot_daily.py 2026-09-17 \
  --json-out data/aihot_daily_2026-09-17.json
```

退出码：`0` = 拿到当日日报；`1` = 没拿到（`not_found` / `stale` / 出错）。

**落盘前会断言 `report.date == 目标日期`**，不符则标 `status:"stale"`。这是为了堵死「源站延迟时拿到昨天、却挂今天的名字」——本项目最忌讳的静默错误。

### 4.2 写点评（模型产出）

产出 `data/_aihot_comments_<日期>.json`：

```jsonc
{
  "target_date": "2026-09-17",
  "snapshot": "data/aihot_daily_2026-09-17.json",
  "overview": { "text": "<今日一句话，150-200 字>", "confidence": "中" },
  "comments": {
    "<item_id>": {
      "angle": "model",              // model|product|industry|paper|tutorial|opinion
      "comment": "<60-200 字>",
      "confidence": "高|中|低",
      "flags": ["[推测]"]             // 可选
    }
  }
}
```

**`item_id` 取自快照里每个条目的 `item_id` 字段**（即 `links.aihot` 末段）。

> ⚠️ **不能用数组下标、也不能用标题作键**。源站可能在发布后追加条目，下标会整体位移，导致「A 的点评贴到 B 的标题下面」——这种错误读起来完全通顺、内容全错。渲染脚本用 item_id 校验并拦住。

### 4.3 渲染

```bash
python3 scripts/render_aihot_report.py \
  --snapshot data/aihot_daily_2026-09-17.json \
  --comments data/_aihot_comments_2026-09-17.json \
  --out reports/ai/2026-09-17.md
```

### 4.4 校验

```bash
python3 scripts/validate_aihot_report.py \
  --report reports/ai/2026-09-17.md \
  --snapshot data/aihot_daily_2026-09-17.json
```

> `validate_report_data.py --market ai` 不做实际校验（AI 日报没有可对标的实时指数），
> 它会直接指向上面这个专用校验器。

---

## 5. 硬校验规则

### 5.1 渲染脚本（任一不过 → 退出码 2、不写文件）

| # | 规则 | 防的是什么 |
|---|---|---|
| 1 | 快照 `status` 必须是 `ok` | `not_found`/`stale` 时拒绝渲染，防止拿别的日期充数 |
| 2 | 点评里不得出现快照中不存在的 `item_id` | **防条目位移导致点评错位** |
| 3 | 快照每个条目都必须有点评 | 漏条 |
| 4 | 每条点评 60 ≤ 长度 ≤ 200 | 注水与敷衍 |
| 5 | `angle` 必须在六个枚举内 | 角度分派失效 |
| 6 | `overview.text` 非空 | — |

### 5.2 校验脚本（任一不过 → 退出码 1）

| # | 规则 | 防的是什么 |
|---|---|---|
| 1 | 报告里的「源站摘要」序列与快照**逐字一致**（含顺序） | **抓出模型事后 Edit 报告**（「只是润色一下」） |
| 2 | 每条都有「我的点评」 | 覆盖率 |
| 3 | 点评字数 60–200 | 同渲染 |
| 4 | 章节数 = 源站章节数 + 2（今日一句话 + 数据来源） | 丢章节 |
| 5 | 存在 `## 数据来源与口径说明（AIHOT）` | 前端归类依赖它 |

**人工抽检（机器查不了）**：随机挑 2 条点开 `link_original`，确认点评没把「AIHOT 的说法」写成「事实」。

---

## 6. 报告格式硬约束（前端代码依赖）

这些由渲染脚本保证，但改动模板时必须知道：

| 约束 | 原因 |
|---|---|
| 章节用 `##`、条目用 `###` | `parseReport` 按 `^##\s+` 切章；条目用 `###` 才能在右侧目录里保持章级 |
| **每个正文章节标题必须以（AIHOT）结尾** | `classifySection` 靠这个后缀识别本品类（不用中文词，避免与行情报告撞车；源站将来新增章节也仍能正确归类） |
| **来源章节标题必须以「数据来源」开头** | `classifySection` 把它归入 `source`，不进右侧分节目录。**且这一支的判定必须排在 AI 支之前**（否则口径说明会变成正文卡片） |
| `**源站摘要**：` / `**我的点评**：` / `**来源**：` 用**全角冒号、顶格** | 前端 `splitLabeled()` 的正则是 `^\*\*(.+?)\*\*：`，分栏效果零 CSS 改动靠它 |

---

## 7. 边界情况

### 7.1 判断是否该生成（顺序不能乱）

1. **今天是否已有报告**？`reports/ai/<日期>.md` 存在 → **跳过**，不重复跑
2. 不存在 → 取数，看源站当天有没有日报（脚本退出码是否为 0）
3. 源站未发布（`not_found`）→ **重试最多 3 次、间隔 10 分钟**（08:30 → 08:40 → 08:50）
4. 仍无 → **跳过本期**，明确说明「**源站今日未发布日报**」

**绝对不能**降级去用前一天的日报充数。宁可空一期，也不能让内容与日期对不上。

### 7.2 三种特殊情形

| 情形 | 处理 |
|---|---|
| **周末** | 照常生成。源站 7 天都有（实测周日仍有 6 条）。**不要因为「今天是周六」而跳过。** |
| **条目多（16 条）** | 分章节写、写一块追加一次，避免后半段质量下滑 |
| **条目少（3 条）** | **写深，不凑字**。不要为了凑长度把 3 条拆成 9 段——那是注水 |

### 7.3 「技巧与观点」必须逐条判断

这一节**同时装着两类内容**：

- 讲方法、步骤、工具用法 → `tutorial`（侧重：实用性、适用人群、前置条件）
- 讲判断、趋势、批评、立场 → `opinion`（侧重：论据是否成立、与主流看法的分歧）

实测 2026-09-17 该节两条正好一条是观点帖、一条是技巧分享。按章节名一刀切，教程类就拿不到「实用性」角度的点评。

---

## 8. 报告编号

**编号 = (报告日期 − 首期日期) 的日历天数 + 1**，首期日期 = **2026-09-17**。

- 按日期算，**不要从 manifest 数文件**（项目的 us/cn 就是这么算的，已经出过重号）
- 源站某天故障跳过时编号仍然连续
- 由渲染脚本自动计算，写点评时不用管

---

## 9. 发布流程

```bash
cd /Users/mac/每日简报实战/kol-daily
mkdir -p daily-briefing/reports/ai          # 首次需要
cp ../daily-briefing/reports/ai/<日期>.md          daily-briefing/reports/ai/
cp ../daily-briefing/manifest.json                 daily-briefing/
cp ../daily-briefing/data/aihot_daily_<日期>.json  daily-briefing/data/
# 更新 manifest：ai 数组最前插入 <日期>，ai_title[<日期>] = "AI 日报 · N 条"
git add <明确路径>                            # 绝不 git add -A
git pull --rebase origin gh-pages             # 仓库有每 30 分钟的 Actions 同步，会推进远端
git commit && git push origin gh-pages
```

**注意事项**：

- `reports` 在 `sync-local.sh` 的 rsync 排除列表里 → **必须显式 cp**，同步脚本不管它
- manifest 标题写 **`AI 日报 · N 条`**，**不要再带日期**（导航本身已显示日期，重复会导致侧边栏截断）
- 只 `git add` 明确路径。`.aura/` 未进 `.gitignore`，`-A` 会把 agent 日志推到公开仓库（已踩过）

---

## 10. 调度

| 项 | 值 |
|---|---|
| 任务定义 | `scripts/launchd/com.xifengxx.daily-briefing.ai.plist` |
| 触发 | **每天 08:30**（`StartCalendarInterval` 单个 dict，**刻意不写 Weekday**） |
| 手动跑 | `./scripts/daily_briefing_run.sh ai` |
| 日志 | `logs/ai_YYYY-MM-DD_HHMMSS.log`；一句话结论进 `logs/运行汇总.md` |

**看门狗**：目前 **未配置** `watchdog-ai`。AI 日报是 7 天连续，一次静默失败就会缺一期且没有提醒。建议补上（09:00，加一个 case 分支 + 一个 plist 即可）。

---

## 11. 日常检查清单

| 检查项 | 通过标准 |
|---|---|
| 日期一致 | 快照 `target_date` == `report_date` == 报告文件名日期 == manifest key |
| 源站状态 | `status == "ok"`（不是 `stale`/`not_found`） |
| 逐字引用 | `validate_aihot_report.py` 的「逐字一致」为 N/N |
| 点评覆盖 | 每个条目都有点评，字数 60–200 |
| 角度分派 | 无非法 `angle`；「技巧与观点」逐条判断过 |
| 编号 | 与首期日期推算一致 |
| 不覆盖历史 | 没有覆盖任何已有的 `reports/ai/*.md` |
| manifest | `ai` 数组最前是新日期，标题为 `AI 日报 · N 条` |
| 数据纪律 | 无编造的技术参数；推断处标了 `[推测]` |
| 线上 | 报告 URL 返回 200，`?market=ai` 能渲染 |
| 中间产物 | `data/_aihot_comments_*.json` 留在本地，**没有进公开仓库** |
