#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch daily news drivers for US briefing heat tables and anomalies."""

import argparse
import datetime
import json
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"


INDUSTRY_QUERY_MAP = {
    "广播电视": "Broadcasting stock market September 2026",
    "烟草": "Tobacco stocks market September 2026",
    "商业设备与耗材": "Business equipment supplies stocks market September 2026",
    "医疗仪器与耗材": "Medical instruments supplies stocks market September 2026",
    "消费电子": "Consumer electronics stocks market September 2026",
    "太阳能": "Solar stocks market September 2026",
    "科技分销": "Technology distributors stocks market September 2026",
    "海运": "Marine shipping stocks market September 2026",
    "油气设备与服务": "Oil gas equipment services stocks market September 2026",
    "工具与配件制造": "Manufacturing tools accessories stocks market September 2026",
    "纺织制造": "Textile manufacturing stocks market September 2026",
    "家居装修": "Home improvement stocks market September 2026",
    "工业材料": "Industrial materials stocks market September 2026",
    "铀": "Uranium stocks market September 2026",
    "抵押REIT": "Mortgage REIT stocks market September 2026",
    "特殊REIT": "Specialty REIT stocks market September 2026",
}

SEGMENT_QUERY_MAP = {
    "射频芯片": "RF chip stocks Skyworks Qorvo market September 2026",
    "模拟芯片": "Analog chip stocks market September 2026",
    "PCB与IC载板": "PCB IC substrate stocks market September 2026",
    "光刻胶与湿化学品": "Photoresist wet chemicals semiconductor materials September 2026",
    "测试设备": "Semiconductor test equipment stocks September 2026",
    "边缘AI": "Edge AI stocks market September 2026",
    "IC设计服务(Fabless)": "Fabless semiconductor stocks market September 2026",
    "AI Agent": "AI agent stocks market September 2026",
    "企业级存储": "Enterprise storage stocks HPE Dell NetApp September 2026",
    "CPU(服务器级)": "Server CPU stocks NVIDIA Intel September 2026",
    "GPU架构设计": "GPU architecture stocks NVIDIA Intel September 2026",
    "GPU": "GPU stocks NVIDIA Intel September 2026",
    "服务器电源与UPS": "Server power UPS stocks Vertiv Delta Electronics September 2026",
    "AI服务器": "AI server stocks HPE Dell Super Micro September 2026",
    "刻蚀设备": "Semiconductor etch equipment stocks Lam Research September 2026",
    "DSP与光芯片": "DSP optical chip stocks Lumentum September 2026",
}


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
                "query": INDUSTRY_QUERY_MAP.get(name, f"{name} stocks market {target}"),
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
                "query": SEGMENT_QUERY_MAP.get(name, f"{name} stocks market {target}"),
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
                "query": f"{row['name']} {ticker} {target}",
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
