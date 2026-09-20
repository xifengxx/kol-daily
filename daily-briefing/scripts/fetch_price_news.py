#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 AI 产业链的价格变动新闻（涨价/提价/调价），落盘为快照。

用法：
  python3 scripts/fetch_price_news.py                          # 今天（北京）
  python3 scripts/fetch_price_news.py 2026-09-19 \
      --json-out data/price_news_2026-09-19.json
  python3 scripts/fetch_price_news.py 2026-09-19 --days 7 --verbose

依赖：pip install requests

这个脚本解决什么问题
--------------------
美股报告第三部分（重要产业新闻）现在是 agent 自己上网搜的——搜什么、搜不搜
涨价，全凭它每次的判断。结果是「撞上了就写（如存储超级周期），撞不上就漏
（如安森美涨价函）」。

本脚本把「不漏」这件事变成确定性的：每次跑批都用**同一组固定查询**扫一遍，
产出 JSON 快照，让 agent 有个明确的信息源可读。

它只做机械的活：查询 → 两道过滤 → 去重 → 按时间窗截断 → 存文件。
**不做任何判断**（哪条重要、值不值得写进报告，交给 agent）。

两道过滤（缺一不可）
--------------------
实测教训：
  - 「散热液冷」查回来的全是数据中心耗水、电费账单
  - 「光模块」查回来的是高盛上调**目标价**（分析师评级 ≠ 涨价）
所以：
  ① 标题必须命中「涨价词」（price increase / 涨价 / 提价 / 调价 …）
  ② 标题不得命中「干扰词」（target price / 目标价 / stock price …）

输出：{target_date, generated_at, modules: {price_news: {status, source, method, data}}}
"""

import argparse
import datetime
import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import requests
except ImportError:
    print("需要 requests：pip install requests", file=sys.stderr)
    sys.exit(1)


# ── 查询清单：按 AI 产业链的价格敏感环节组织，中英各一条 ──────────────
# 只放「料」与「产能」类环节——这些涨价会直接传导到 AI 硬件成本。
# 不要放「液冷」「光模块」这类会被解读成别的意思的宽泛词（实测会跑偏）。
QUERIES = [
    # (品类标签, 语言, 查询词)
    ("存储/HBM",     "zh", "HBM 存储 涨价"),
    ("存储/HBM",     "en", "HBM DRAM NAND price increase"),
    ("先进封装",      "zh", "先进封装 CoWoS 涨价"),
    ("先进封装",      "en", "CoWoS advanced packaging price increase"),
    ("覆铜板/PCB",   "zh", "覆铜板 涨价函"),
    ("覆铜板/PCB",   "en", "CCL copper clad laminate price hike"),
    ("功率半导体",    "zh", "功率半导体 涨价"),
    ("功率半导体",    "en", "power semiconductor price increase"),
    ("模拟芯片",      "zh", "模拟芯片 涨价"),
    ("模拟芯片",      "en", "analog chip price increase"),
    ("被动元件",      "zh", "被动元件 MLCC 涨价"),
    ("被动元件",      "en", "MLCC passive component price increase"),
    ("晶圆代工",      "zh", "晶圆代工 涨价"),
    ("晶圆代工",      "en", "wafer foundry TSMC price increase"),
    ("半导体设备",    "zh", "半导体设备 涨价"),
    ("半导体设备",    "en", "semiconductor equipment price increase"),
    ("硅片/材料",     "zh", "硅片 涨价"),
    ("硅片/材料",     "en", "silicon wafer price increase"),
    ("AI芯片",       "zh", "AI芯片 涨价"),
    ("AI芯片",       "en", "AI chip price increase"),
    ("服务器/整机",   "zh", "服务器 涨价"),
    ("服务器/整机",   "en", "AI server price increase"),
]

# ── 两道过滤 ────────────────────────────────────────────────────────
# ① 必须命中其一（涨价语义）
INCLUDE = [
    # 英文
    "price increase", "price increases", "price hike", "price hikes",
    "price rise", "raises prices", "raise prices", "raised prices",
    "hike prices", "hikes prices", "increase prices", "increases prices",
    "price adjustment", "price surge", "higher prices", "price up",
    # 中文（实测命中质量最好）
    "涨价", "提价", "调价", "涨价函", "价格上调", "上调价格", "涨幅",
]

# ② 命中其一即丢弃（分析师评级、股价、目标价等噪音）
EXCLUDE = [
    "target price", "price target", "stock price", "share price",
    "price forecast", "price prediction", "analyst",
    "目标价", "股价", "评级", "目标股价",
]

UA = "daily-briefing/1.0 (+personal use)"
TIMEOUT = 25
SLEEP_BETWEEN = 1.2          # 查询间隔，避免触发限流


def search_news(query, lang):
    """查 Google News RSS，返回 [{title, link, published, source}]。"""
    hl, gl, ceid = ("zh-CN", "CN", "CN:zh-Hans") if lang == "zh" else ("en-US", "US", "US:en")
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(query)
           + f"&hl={hl}&gl={gl}&ceid={ceid}")
    resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    out = []
    for item in root.findall(".//item"):
        src = item.find("source")
        out.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "published": (item.findtext("pubDate") or "").strip(),
            "source": (src.text.strip() if src is not None and src.text else ""),
        })
    return out


def match_reason(title):
    """返回命中的涨价词；没命中返回 None；命中干扰词直接返回 ('', 'excluded')。"""
    low = title.lower()
    for bad in EXCLUDE:
        if bad in low:
            return None, bad
    for good in INCLUDE:
        if good in low:
            return good, None
    return None, None


def parse_pubdate(s):
    """把 RFC822 的 pubDate 解析成 date；失败返回 None。"""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


def norm_title(title):
    """去重用的规范化标题：去尾部「 - 来源」、统一空白与大小写。"""
    t = re.sub(r"\s+-\s+[^-]{2,40}$", "", title)   # Google News 习惯加「 - 媒体名」
    return re.sub(r"\s+", " ", t).strip().lower()


def main():
    ap = argparse.ArgumentParser(description="扫描 AI 产业链价格变动新闻")
    ap.add_argument("date", nargs="?", help="目标日期 YYYY-MM-DD，默认今天")
    ap.add_argument("--json-out", help="输出路径，省略则打印到 stdout")
    ap.add_argument("--days", type=int, default=3, help="时间窗（天），默认 3")
    ap.add_argument("--verbose", action="store_true", help="打印每条查询的命中情况")
    args = ap.parse_args()

    target = args.date or datetime.date.today().isoformat()
    try:
        target_date = datetime.date.fromisoformat(target)
    except ValueError:
        print(f"[错误] 日期格式不对：{target}", file=sys.stderr)
        sys.exit(2)

    cutoff = target_date - datetime.timedelta(days=args.days)

    print(f"目标日期: {target}  时间窗: {cutoff} 之后  查询数: {len(QUERIES)}", file=sys.stderr)

    raw_hits, errors, stats = [], [], {"excluded": 0, "no_keyword": 0, "too_old": 0, "undated": 0}

    for category, lang, query in QUERIES:
        try:
            items = search_news(query, lang)
        except Exception as exc:
            errors.append(f"{query}: {type(exc).__name__}")
            if args.verbose:
                print(f"  ✗ {category:<10} {query} — {type(exc).__name__}", file=sys.stderr)
            time.sleep(SLEEP_BETWEEN)
            continue

        kept = 0
        for it in items:
            good, bad = match_reason(it["title"])
            if bad:
                stats["excluded"] += 1
                continue
            if not good:
                stats["no_keyword"] += 1
                continue
            pub = parse_pubdate(it["published"])
            if pub is None:
                stats["undated"] += 1
                age = None
            elif pub < cutoff:
                stats["too_old"] += 1
                continue
            else:
                age = (target_date - pub).days
            raw_hits.append({
                "category": category,
                "lang": lang,
                "query": query,
                "matched": good,
                "title": it["title"],
                "link": it["link"],
                "source": it["source"],
                "published": it["published"],
                "pub_date": pub.isoformat() if pub else None,
                "age_days": age,
            })
            kept += 1

        if args.verbose:
            print(f"  {'✓' if kept else '·'} {category:<10} {query:<44} 命中 {kept}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN)

    # 按标题去重，保留最早出现（同一条新闻可能被多个查询捞到）
    seen, items = {}, []
    for h in raw_hits:
        key = norm_title(h["title"])
        if key in seen:
            seen[key]["also_matched"].append(h["category"])
            continue
        h["also_matched"] = []
        seen[key] = h
        items.append(h)

    items.sort(key=lambda x: (x["age_days"] if x["age_days"] is not None else 99,
                              x["category"]))

    by_cat = {}
    for h in items:
        by_cat[h["category"]] = by_cat.get(h["category"], 0) + 1

    data = {
        "days_window": args.days,
        "cutoff_date": cutoff.isoformat(),
        "queries_total": len(QUERIES),
        "queries_failed": len(errors),
        "errors": errors[:10],
        "items_total": len(items),
        "items_by_category": by_cat,
        "filter_stats": stats,
        "items": items,
    }
    snapshot = {
        "target_date": target,
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "modules": {
            "price_news": {
                "status": "ok" if not errors else "partial",
                "source": "Google News RSS",
                "method": ("固定查询组（AI 产业链价格敏感环节，中英各一条）→ "
                           "标题必须命中涨价词且不得命中干扰词 → 按标题去重 → 时间窗截断"),
                "data": data,
            }
        },
    }

    if items:
        cats = "、".join(f"{k} {v}" for k, v in sorted(by_cat.items(), key=lambda x: -x[1]))
        print(f"  ✅ 命中 {len(items)} 条（去重后），按品类：{cats}", file=sys.stderr)
    else:
        print(f"  ⚠ 时间窗内未命中任何涨价新闻（这很可能正常——涨价是月度频率）",
              file=sys.stderr)
    print(f"  过滤掉：干扰词 {stats['excluded']}、无涨价词 {stats['no_keyword']}、"
          f"过期 {stats['too_old']}", file=sys.stderr)
    if errors:
        print(f"  ⚠ {len(errors)} 条查询失败（限流？）", file=sys.stderr)

    text = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"--- 已保存: {out} ---", file=sys.stderr)
    else:
        print(text)

    sys.exit(0)


if __name__ == "__main__":
    main()
