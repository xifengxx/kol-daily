#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 AIHOT（aihot.news）当日 AI 日报，落盘为快照。

用法：
  python3 scripts/fetch_aihot_daily.py                      # 今天（北京时间）
  python3 scripts/fetch_aihot_daily.py 2026-09-17 \
      --json-out data/aihot_daily_2026-09-17.json
  python3 scripts/fetch_aihot_daily.py 2026-09-17 --raw     # 只打印不落盘

依赖：pip install requests

设计要点
--------
1. **按日期取，不用 /latest**。源站 `/api/v1/dailies/{date}` 对不存在的日期返回
   404（RFC7807 格式），语义干净。用 /latest 则可能在源站延迟时静默拿到**昨天**
   的日报，而输出文件却叫今天的名字——这是最危险的一类错误，必须从源头堵死。
2. **落盘前断言 `report.date == target_date`**。不等则标 `status: "stale"`，
   渲染脚本会拒绝执行。宁可空一天，也不让昨天的内容冒充今天。
3. **item_id 用 `links.aihot` 的末段**，不用数组下标。源站可能在 08:00 发布后
   追加条目，下标整体位移会让「A 的点评贴到 B 的标题下」。

输出结构（沿用项目既有信封）：
  {target_date, generated_at, modules: {aihot_daily: {status, source, data, detail}}}
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("需要 requests：pip install requests", file=sys.stderr)
    sys.exit(1)


API_BASE = "https://aihot.news/api/v1/dailies"
SITE_BASE = "https://aihot.news"
UA = "daily-briefing/1.0 (+personal use)"
TIMEOUT = 25


def fetch_daily(target):
    """按日期取日报。

    返回 (status, payload, detail)：
      status ∈ ok | not_found | stale | error
    payload 为源站顶层响应（含 schemaVersion 与 report）。
    """
    url = f"{API_BASE}/{target}"
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
    except Exception as exc:                                  # 网络异常
        return "error", None, f"{type(exc).__name__}: {exc}"

    if resp.status_code == 404:
        return "not_found", None, "源站当日无日报（HTTP 404）"
    if resp.status_code != 200:
        return "error", None, f"HTTP {resp.status_code}: {resp.text[:160]}"

    try:
        payload = resp.json()
    except Exception as exc:
        return "error", None, f"响应不是 JSON：{exc}"

    report = payload.get("report")
    if not isinstance(report, dict):
        return "error", None, "响应缺少 report 字段"

    actual = report.get("date")
    if actual != target:
        # 源站返回的不是我们要的那一天——绝不将就
        return "stale", payload, f"源站返回日期 {actual}，与目标 {target} 不符"

    return "ok", payload, None


def item_id_of(item, fallback_index):
    """item_id = links.aihot 的末段；取不到时用序号兜底并标注。"""
    links = item.get("links") or {}
    aihot = (links.get("aihot") or "").rstrip("/")
    if aihot:
        seg = aihot.split("/")[-1]
        if seg:
            return seg, aihot
    return f"idx-{fallback_index}", ""


def build_data(report, schema_version):
    """把源站 report 摊平成快照 data 段，并附三个防呆字段。"""
    sections_out = []
    item_index = {}
    counter = 0

    for sec in report.get("sections") or []:
        items_out = []
        for raw in sec.get("items") or []:
            counter += 1
            item_id, aihot_url = item_id_of(raw, counter)
            src = raw.get("source") or {}
            links = raw.get("links") or {}
            summary = raw.get("summary") or ""
            entry = {
                "item_id": item_id,
                "title": raw.get("title") or "",
                "summary": summary,                 # ← 逐字保存，永不改写
                "summary_len": len(summary),
                "source_name": src.get("name") or "",
                "link_aihot": aihot_url or links.get("aihot") or "",
                "link_original": links.get("original") or "",
                "attribution": raw.get("attribution") or {},
            }
            items_out.append(entry)
            item_index[item_id] = {
                "section_label": sec.get("label") or "",
                "title": entry["title"],
            }
        sections_out.append({"label": sec.get("label") or "", "items": items_out})

    lead = report.get("lead")
    flashes = report.get("flashes") or []

    return {
        "report_date": report.get("date"),
        "generated_at_source": report.get("generatedAt"),
        "window_start": report.get("windowStart"),
        "window_end": report.get("windowEnd"),
        "schema_version": schema_version,
        "source_url": ((report.get("links") or {}).get("aihot")) or "",
        "attribution": report.get("attribution") or {},
        "section_count": len(sections_out),
        "item_count": counter,
        # 三个防呆字段：源站若悄悄改结构，这里能看出来，而不是静默丢内容
        "lead_present": lead is not None,
        "flashes_count": len(flashes),
        "sections": sections_out,
        "item_index": item_index,
    }


def main():
    parser = argparse.ArgumentParser(description="抓取 AIHOT 当日 AI 日报")
    parser.add_argument("date", nargs="?", help="目标日期 YYYY-MM-DD，默认今天（北京）")
    parser.add_argument("--json-out", help="输出路径，省略则打印到 stdout")
    args = parser.parse_args()

    target = args.date or datetime.date.today().isoformat()
    try:
        datetime.date.fromisoformat(target)
    except ValueError:
        print(f"[错误] 日期格式不对：{target}（应为 YYYY-MM-DD）", file=sys.stderr)
        sys.exit(2)

    print(f"目标日期: {target}  (源站 {API_BASE}/{target})", file=sys.stderr)
    status, payload, detail = fetch_daily(target)

    data = None
    if payload:
        report = payload.get("report") or {}
        data = build_data(report, payload.get("schemaVersion"))

    module = {
        "status": status,
        "source": f"AIHOT {API_BASE}/{target}",
        "detail": detail,
        "data": data,
    }

    snapshot = {
        "target_date": target,
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "modules": {"aihot_daily": module},
    }

    # 图标：ok / not_found / stale / error 各一行提示，便于无人值守时看日志判断
    if status == "ok":
        data = module["data"]
        print(f"  ✅ 抓到 {data['section_count']} 章节 / {data['item_count']} 条"
              f"（源站生成于 {data['generated_at_source']}）", file=sys.stderr)
    elif status == "not_found":
        print(f"  ⚠ 源站当日未发布日报：{detail}", file=sys.stderr)
    elif status == "stale":
        print(f"  ❌ 日期不符：{detail}", file=sys.stderr)
    else:
        print(f"  ❌ 抓取失败：{detail}", file=sys.stderr)

    text = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"--- 已保存: {out} ---", file=sys.stderr)
    else:
        print(text)

    # 退出码：只有 ok 才算成功，方便上层脚本直接判断
    sys.exit(0 if status == "ok" else 1)


if __name__ == "__main__":
    main()
