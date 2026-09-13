#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch daily news drivers for US briefing heat tables and anomalies."""

import argparse
import datetime
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"


# 查询词表：只放英文主题词，**不含任何时间词**。
#
# 两条实测结论（2026-09-13，Google News RSS）：
#   1. 查询里带日期会显著压低命中——"Kokusai Electric 6525 2026-09-11" 命中 0 条，
#      去掉日期后 "Kokusai Electric 6525 stock" 即有正常结果；日期 token 会被当成
#      字面词去匹配，而不是时间范围。
#   2. 中文名直接 0 命中——"百货商店 stocks market ..." 命中 0 条，
#      换成英文名 "Department Stores stocks" 命中正常。
# 因此：本表只提供「英文主题词」，未覆盖到的条目由 industry_query / segment_query
# 用英文名或 segment_id 兜底，任何路径都不会把中文名或日期塞进查询。
INDUSTRY_QUERY_MAP = {
    "广播电视": "Broadcasting stocks",
    "烟草": "Tobacco stocks",
    "商业设备与耗材": "Business equipment supplies stocks",
    "医疗仪器与耗材": "Medical instruments supplies stocks",
    "消费电子": "Consumer electronics stocks",
    "太阳能": "Solar stocks",
    "科技分销": "Technology distributors stocks",
    "海运": "Marine shipping stocks",
    "油气设备与服务": "Oil gas equipment services stocks",
    "工具与配件制造": "Manufacturing tools accessories stocks",
    "纺织制造": "Textile manufacturing stocks",
    "家居装修": "Home improvement stocks",
    "工业材料": "Industrial materials stocks",
    "铀": "Uranium stocks",
    "抵押REIT": "Mortgage REIT stocks",
    "特殊REIT": "Specialty REIT stocks",
}

SEGMENT_QUERY_MAP = {
    "射频芯片": "RF chip stocks Skyworks Qorvo",
    "模拟芯片": "Analog chip stocks",
    "PCB与IC载板": "PCB IC substrate stocks",
    "光刻胶与湿化学品": "Photoresist wet chemicals semiconductor materials",
    "测试设备": "Semiconductor test equipment stocks",
    "边缘AI": "Edge AI stocks",
    "IC设计服务(Fabless)": "Fabless semiconductor stocks",
    "AI Agent": "AI agent stocks",
    "企业级存储": "Enterprise storage stocks HPE Dell NetApp",
    "CPU(服务器级)": "Server CPU stocks NVIDIA Intel",
    "GPU架构设计": "GPU architecture stocks NVIDIA Intel",
    "GPU": "GPU stocks NVIDIA Intel",
    "服务器电源与UPS": "Server power UPS stocks Vertiv Delta Electronics",
    "AI服务器": "AI server stocks HPE Dell Super Micro",
    "刻蚀设备": "Semiconductor etch equipment stocks Lam Research",
    "DSP与光芯片": "DSP optical chip stocks Lumentum",
}


def ascii_terms(text):
    """从可能中英混排的名称里抽出英文检索词。

    '安森美(onsemi)'   -> 'onsemi'
    'Himax (奇景光电)' -> 'Himax'
    'HPE'              -> 'HPE'
    '纯中文名'          -> ''
    """
    if not text:
        return ""
    cleaned = re.sub(r"[^\x20-\x7E]", " ", text)          # 去掉 CJK 等非 ASCII 字符
    cleaned = re.sub(r"[()\[\]{}<>/\\,;:'\"|&+]", " ", cleaned)
    return " ".join(cleaned.split())


def industry_query(row):
    """行业查询词：优先策展英文主题，否则用 FMP 英文行业名兜底。"""
    name = row.get("industry_zh") or ""
    if name in INDUSTRY_QUERY_MAP:
        return INDUSTRY_QUERY_MAP[name]
    en = (row.get("industry") or "").strip() or ascii_terms(name)
    return f"{en} stocks" if en else ""


def segment_query(row):
    """产业链段查询词：优先策展英文主题，否则由英文 segment_id 兜底。"""
    name = row.get("name") or ""
    if name in SEGMENT_QUERY_MAP:
        return SEGMENT_QUERY_MAP[name]
    slug = " ".join((row.get("segment_id") or "").replace("-", " ").split())
    if slug:
        return f"{slug} stocks"
    en = ascii_terms(name)
    return f"{en} stocks" if en else ""


def anomaly_query(row):
    """异常股查询词：英文名 + 代码 + stock。

    实测 'onsemi ON stock' 命中且高度相关；而带中文名或日期的写法命中 0 条。
    """
    ticker = (row.get("ticker") or "").split(".")[0]
    en = ascii_terms(row.get("name"))
    # 用整词匹配判重，避免子串误判：'ON' 是 'onsemi' 的子串，但并非同一个词，
    # 而实测 'onsemi ON stock' 的命中质量明显优于丢掉代码的 'onsemi stock'。
    if en and ticker and re.search(rf"\b{re.escape(ticker)}\b", en, re.IGNORECASE):
        return f"{en} stock"           # 名称里已含代码，避免 'HPE HPE stock'
    parts = " ".join(p for p in (en, ticker) if p)
    return f"{parts} stock" if parts else ""


def search_google_news(query, limit=10):
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    response = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    root = ET.fromstring(response.text)
    items = []
    for item in root.findall(".//item")[:limit]:
        pub = item.findtext("pubDate") or ""
        source = item.find("source")
        items.append(
            {
                "title": item.findtext("title") or "",
                "link": item.findtext("link") or "",
                "published": pub,
                "source": source.text if source is not None and isinstance(source.text, str) else "",
            }
        )
    return items


def collect_candidates(market_path, heat_path):
    market = json.loads(market_path.read_text(encoding="utf-8"))
    heat = json.loads(heat_path.read_text(encoding="utf-8"))
    target = market.get("target_date") or datetime.date.today().isoformat()

    industries = []
    industry_heat = market.get("modules", {}).get("industry_heat", {})
    for row in industry_heat.get("top", [])[:8] + industry_heat.get("bottom", [])[:8]:
        name = row["industry_zh"]
        industries.append(
            {
                "type": "industry",
                "key": name,
                "display": name,
                "change_pct": row["avg_change_pct"],
                "query": industry_query(row),
            }
        )

    rankable = [x for x in heat["segments"] if x["rankable"]]
    segments = []
    for row in rankable[:8] + list(reversed(rankable[-8:])):
        name = row["name"]
        segments.append(
            {
                "type": "segment",
                "key": row["segment_id"],
                "display": name,
                "change_pct": row["change_equal_weight_pct"],
                "query": segment_query(row),
            }
        )

    anomalies = []
    for row in heat.get("anomalies_pct_5", []):
        ticker = row["ticker"].split(".")[0]
        anomalies.append(
            {
                "type": "anomaly",
                "key": row["ticker"],
                "display": f"{row['name']} ({ticker})",
                "change_pct": row["chg_pct"],
                "query": anomaly_query(row),
            }
        )

    seen = set()
    candidates = []
    for item in industries + segments + anomalies:
        marker = (item["type"], item["key"])
        if marker not in seen:
            candidates.append(item)
            seen.add(marker)
    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--market", type=Path)
    parser.add_argument("--heat", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    args.market = args.market or DATA_DIR / f"us_market_data_{args.date}.json"
    args.heat = args.heat or DATA_DIR / f"industry_chain_heat_{args.date}.json"
    args.out = args.out or DATA_DIR / f"us_drivers_raw_{args.date}.json"

    candidates = collect_candidates(args.market, args.heat)
    results = []
    for i, item in enumerate(candidates, 1):
        if not item.get("query"):
            # 名称无法抽出英文检索词时宁可跳过，也不要发一条注定 0 命中的查询
            results.append({**item, "news": [], "status": "no_query", "error": "无可用英文查询词"})
            print(f"{i}/{len(candidates)} {item['type']} {item['display']}: 跳过（无英文查询词）", flush=True)
            continue
        try:
            news = search_google_news(item["query"])
            status = "ok"
            error = None
        except Exception as exc:
            news = []
            status = "error"
            error = str(exc)[:200]
        results.append({**item, "news": news, "status": status, "error": error})
        print(f"{i}/{len(candidates)} {item['type']} {item['display']}: {len(news)} items", flush=True)

    args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "candidates": len(results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
