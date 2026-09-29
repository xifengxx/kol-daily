#!/usr/bin/env python3
"""新浪行业板块「成分股等权重」重算。

背景：新浪行业接口(ak.stock_sector_spot)返回的 `涨跌幅` 公式是
「平均涨跌额 ÷ 平均价格」——分子是绝对价格变动、分母是价格水平，量纲不一致，
必被板块内高价股主导，失真可正可负（甚至方向反转）。

本脚本逐一拉取每个新浪行业板块的全部成分股，重算：
  - 等权涨跌幅 = 成分股 changepercent 的算术平均
  - 上涨/下跌/平盘家数
  - 同时保留接口原始值备查

用法:
    python3 scripts/fetch_sector_equalweight.py 2026-09-28 \
        --json-out data/sector_equalweight_2026-09-28.json

注意: 必须在目标交易日收盘后、下一交易日开盘前运行。
成分股快照取自新浪实时接口，盘中运行会拿到当日盘中值。
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone

import akshare as ak

CST = timezone(timedelta(hours=8))


def load_interface_values(path):
    """从取数快照读接口原始板块涨跌幅，作为备查值。"""
    with open(path, encoding="utf-8") as f:
        snap = json.load(f)
    rows = snap["modules"]["sectors"]["data"]
    return {r["label"]: r for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", help="目标交易日 YYYY-MM-DD")
    ap.add_argument("--snapshot", default=None, help="取数快照 JSON（读接口原始值）")
    ap.add_argument("--json-out", required=True)
    ap.add_argument("--raw-out", default=None, help="成分股原始快照落盘路径")
    args = ap.parse_args()

    snap_path = args.snapshot or f"data/a_share_data_{args.date}.json"
    iface = load_interface_values(snap_path)
    labels = list(iface.keys())
    print(f"目标日期 {args.date}，板块数 {len(labels)}", file=sys.stderr)

    out, raw, failed = [], {}, []
    total_stocks = 0
    for i, label in enumerate(labels, 1):
        name = iface[label].get("板块", label)
        try:
            df = ak.stock_sector_detail(sector=label)
        except Exception as e:  # 单个板块失败不致命
            failed.append({"label": label, "板块": name, "error": str(e)})
            continue
        if df is None or df.empty:
            failed.append({"label": label, "板块": name, "error": "empty"})
            continue

        recs = []
        for _, r in df.iterrows():
            try:
                pct = float(r["changepercent"])
            except (TypeError, ValueError):
                continue
            recs.append({
                "code": str(r["code"]),
                "name": str(r["name"]),
                "close": float(r["trade"]) if r["trade"] not in (None, "") else None,
                "pct": pct,
            })
        if not recs:
            failed.append({"label": label, "板块": name, "error": "no valid pct"})
            continue

        raw[label] = recs
        total_stocks += len(recs)
        pcts = [x["pct"] for x in recs]
        out.append({
            "label": label,
            "板块": name,
            "接口涨跌幅": round(float(iface[label]["涨跌幅"]), 4),
            "等权涨跌幅": round(sum(pcts) / len(pcts), 4),
            "上涨": sum(1 for p in pcts if p > 0),
            "下跌": sum(1 for p in pcts if p < 0),
            "平盘": sum(1 for p in pcts if p == 0),
            "成分股数": len(pcts),
        })
        time.sleep(0.15)

    for r in out:
        r["偏差pp"] = round(r["等权涨跌幅"] - r["接口涨跌幅"], 4)

    result = {
        "target_date": args.date,
        "generated_at": datetime.now(CST).isoformat(timespec="seconds"),
        "method": "等权：成分股涨跌幅算术平均；涨跌家数按成分股计",
        "source": "AkShare stock_sector_detail(新浪行业成分股)",
        "sector_count": len(out),
        "stock_count": total_stocks,
        "failed": failed,
        "sectors": sorted(out, key=lambda x: x["等权涨跌幅"], reverse=True),
    }
    if args.raw_out:
        with open(args.raw_out, "w", encoding="utf-8") as f:
            json.dump({"target_date": args.date, "raw": raw}, f,
                      ensure_ascii=False, indent=1)
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"✅ 板块 {len(out)}/{len(labels)}，成分股 {total_stocks} 只 -> {args.json_out}",
          file=sys.stderr)
    if failed:
        print(f"⚠ 失败 {len(failed)} 个板块: {failed}", file=sys.stderr)


if __name__ == "__main__":
    main()
