#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股日度复盘简报 - 数据接入脚本
=================================
读取 FMP + Infoway 两个数据源，拉取"美股日度复盘简报"所需的缺失数据，
输出结构化 JSON 快照（可直接作为上下文喂给大模型生成简报）。

数据源与密钥（从环境变量或 .env 读取，不硬编码）：
  - FMP_API_KEY      https://financialmodelingprep.com/stable/
  - INFOWAY_API_KEY  https://data.infoway.io   (HTTP header apiKey)

用法：
  python3 fetch_us_market_data.py                 # 取最近一个美股交易日的当日数据
  python3 fetch_us_market_data.py 2026-08-21      # 取指定日期的数据（该日作为"当日"）
  python3 fetch_us_market_data.py --json-out path # 指定 JSON 输出路径

输出：
  - us_market_data_YYYY-MM-DD.json  结构化数据快照
  - 终端打印每个模块 成功/失败 状态
"""

import os
import sys
import json
import time
import datetime
import statistics

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
FMP_KEY = os.environ.get("FMP_API_KEY", "")
INFOWAY_KEY = os.environ.get("INFOWAY_API_KEY", "")
FMP_BASE = "https://financialmodelingprep.com/stable"
INFOWAY_BASE = "https://data.infoway.io"

# 简报模板要用的标的
M7 = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
M7_INFOWAY = [s + ".US" for s in M7]
INDICES_FMP = ["^GSPC", "^IXIC", "^DJI", "^SOX", "^RUT"]   # 标普/纳指/道指/费半/罗素
INDICES_INFOWAY = "US500,US30,US2000,VIX,DXY,ES,NQ"          # 标普/道指/罗素/VIX/美元指数/E-mini期货
COMMODITIES_INFOWAY = "XAUUSD,CL,BZ,GC"                       # 黄金现货/WTI/布伦特/黄金期货

# ---------------------------------------------------------------------------
# 请求封装
# ---------------------------------------------------------------------------

def fmp_get(path, params=None):
    """FMP stable 端点 GET。失败时返回 {'error': ...}。"""
    p = dict(params or {})
    p["apikey"] = FMP_KEY
    try:
        r = requests.get(f"{FMP_BASE}{path}", params=p, timeout=25)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}: {r.text[:150]}"}
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def _infoway_request(method, url, **kwargs):
    """Infoway 请求，带 429 限流重试（免费档限流较紧）。"""
    for attempt in range(5):
        r = requests.request(method, url, timeout=30, **kwargs)
        if r.status_code == 429:
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}: {r.text[:150]}"}
        try:
            return r.json()
        except Exception:
            return {"error": r.text[:200]}
    return {"error": "429 after retries"}


def infoway_get(path):
    """Infoway GET。兼容两类响应：
    带 ret 包装的（如 kline/batch_trade）与直接返回 data 的（如 breadth/temperature）。"""
    j = _infoway_request("GET", f"{INFOWAY_BASE}{path}", headers={"apiKey": INFOWAY_KEY})
    if isinstance(j, dict) and "error" in j:
        return j
    if isinstance(j, dict) and "ret" in j and j.get("ret") != 200:
        return {"error": j.get("msg")}
    if isinstance(j, dict) and "data" in j:
        return j["data"]
    return j


def infoway_kline(market, codes, kline_type=8, kline_num=25):
    """Infoway 批量 K线。market ∈ {stock, common, crypto}，codes 为逗号分隔字符串。"""
    j = _infoway_request(
        "POST",
        f"{INFOWAY_BASE}/{market}/v2/batch_kline",
        headers={"apiKey": INFOWAY_KEY, "Content-Type": "application/json"},
        json={"codes": codes, "klineType": kline_type, "klineNum": kline_num},
    )
    if isinstance(j, dict) and "error" in j:
        return j
    if isinstance(j, dict) and "ret" in j and j.get("ret") != 200:
        return {"error": j.get("msg")}
    return j.get("data")


def pick_bar_by_date(resp_list, target_date):
    """从 K线 respList 里挑目标日期那根；找不到则返回最新一根。"""
    if not resp_list:
        return None
    for bar in resp_list:
        try:
            if datetime.datetime.fromtimestamp(int(bar["t"])).strftime("%Y-%m-%d") == target_date:
                return bar
        except Exception:
            continue
    return resp_list[0]


# ---------------------------------------------------------------------------
# 各数据模块
# ---------------------------------------------------------------------------

def fetch_fmp_indices_eod(target):
    """FMP：三大指数 + 费半 + 罗素 收盘与成交量（含量比计算）。

    [数据取值规范 - 务必遵守]
    - 指数点位：以本模块 FMP `historical-price-eod/full` 为权威收盘，勿用 WebSearch 媒体摘要、勿写"XX 附近"估算。
    - 费城半导体 ^SOX：免费档取不到（返回 None）→ 用 Yahoo `^SOX` 或新浪 `gb_$sox` 补。
    - Infoway 指数为"等权口径"，数值与 FMP 加权略异（如标普等权 -0.09% vs 加权 -0.26%），引用须标注口径，勿混用。
    - VIX 免费档取不到（^VIX 为付费端点）。"""
    out = {"status": "ok", "indices": {}, "note": ""}
    start = (datetime.datetime.strptime(target, "%Y-%m-%d") - datetime.timedelta(days=40)).strftime("%Y-%m-%d")
    for sym in INDICES_FMP:
        d = fmp_get("/historical-price-eod/full", {"symbol": sym, "from": start, "to": target})
        if isinstance(d, list) and d:
            rows = [x for x in d if isinstance(x, dict) and x.get("date")]
            rows.sort(key=lambda x: x["date"])  # 升序
            idx = next((i for i, x in enumerate(rows) if x["date"] == target), None)
            if idx is None:
                today, prev = rows[-1], rows[-21:-1]
            else:
                today, prev = rows[idx], rows[max(0, idx - 20):idx]
            vols = [x.get("volume") or 0 for x in prev if x.get("volume")]
            avg20 = statistics.mean(vols) if vols else None
            vol_ratio = round(today.get("volume", 0) / avg20, 2) if avg20 else None
            out["indices"][sym] = {
                "date": today.get("date"),
                "close": today.get("close"),
                "volume": today.get("volume"),
                "vol_ratio_20d": vol_ratio,
            }
        else:
            out["indices"][sym] = {"error": d if isinstance(d, dict) else "no data"}
    failed = [s for s, v in out["indices"].items() if "error" in v]
    if failed:
        out["status"] = "partial"
        out["note"] = f"失败(多为付费端点): {failed}"
    return out


def fetch_fmp_sectors(target):
    """FMP：sector-performance-snapshot 按日期聚合出 11 大行业涨跌幅。"""
    d = fmp_get("/sector-performance-snapshot", {"date": target})
    if not isinstance(d, list):
        return {"status": "error", "error": d, "sectors": []}
    agg = {}
    for row in d:
        s = row.get("sector")
        chg = row.get("averageChange")
        if s is None or chg is None:
            continue
        agg.setdefault(s, []).append(chg)
    sectors = [{"sector": s, "avg_change_pct": round(statistics.mean(v), 2), "n_exchanges": len(v)}
               for s, v in agg.items()]
    sectors.sort(key=lambda x: -x["avg_change_pct"])
    return {"status": "ok", "sectors": sectors}


def fetch_fmp_treasuries(target):
    """FMP：美债收益率 2Y/10Y/30Y（以及全期限）。"""
    start = (datetime.datetime.strptime(target, "%Y-%m-%d") - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    d = fmp_get("/treasury-rates", {"from": start, "to": target})
    if not isinstance(d, list) or not d:
        return {"status": "error", "error": d, "rates": {}}
    today = d[-1] if d[-1].get("date") == target else d[0]
    return {"status": "ok", "rates": today}


def fetch_fmp_crypto():
    """FMP：比特币价格（免费）。"""
    d = fmp_get("/quote", {"symbol": "BTCUSD"})
    if isinstance(d, list) and d:
        q = d[0]
        return {"status": "ok", "btc_usd": {"price": q.get("price"), "change_pct": q.get("changePercentage"),
                                             "volume": q.get("volume")}}
    return {"status": "error", "error": d}


def fetch_infoway_breadth():
    """Infoway：市场宽度（涨跌家数）。"""
    d = infoway_get("/common/v2/basic/market/breadth/US")
    if isinstance(d, dict) and "rise_less_than_three" in d:
        return {"status": "ok", "breadth": d}
    return {"status": "error", "error": d}


def fetch_infoway_temperature():
    """Infoway：市场温度/情绪（自研指标，非 CNN Fear & Greed，取 US）。"""
    d = infoway_get("/common/v2/basic/market/temperature?market=US")
    if isinstance(d, dict) and isinstance(d.get("list"), list):
        us = next((x for x in d["list"] if x.get("market") == "US"), d["list"][0])
        return {"status": "ok", "temperature": {k: us.get(k) for k in ("temp", "temp_intro", "valuation", "sentiment", "updated_at")}}
    return {"status": "error", "error": d}


def fetch_infoway_kline_block(market, codes, target, label):
    """Infoway：批量 K线 → {代码: {date, open, high, low, close, chg_pct, volume, amount}}。"""
    d = infoway_kline(market, codes)
    if not isinstance(d, list):
        return {"status": "error", "error": d, "items": {}}
    items = {}
    for item in d:
        sym = item.get("s")
        rl = item.get("respList") or []
        bar = pick_bar_by_date(rl, target)
        if bar is None:
            items[sym] = {"error": "no bar"}
            continue
        items[sym] = {
            "date": datetime.datetime.fromtimestamp(int(bar["t"])).strftime("%Y-%m-%d"),
            "open": float(bar.get("o")), "high": float(bar.get("h")),
            "low": float(bar.get("l")), "close": float(bar.get("c")),
            "chg_pct": bar.get("pc"), "chg": bar.get("pca"),
            "volume": float(bar.get("v")), "amount": float(bar.get("vw")),
        }
    return {"status": "ok", "items": items}


def fetch_infoway_afterhours(tickers):
    """Infoway：最新实时成交（含盘前/盘后快照）。
    注意：返回的是**当前时点**的最新成交，不是历史某日的盘后数据；
    用于"今日盘前异动"参考，或与目标日 K 线收盘价对比看盘后跳空。"""
    d = infoway_get(f"/stock/batch_trade/{tickers}")
    if not isinstance(d, list):
        return {"status": "error", "error": d, "trades": {}}
    trades = {}
    for x in d:
        ts = x.get("t")
        try:
            ts_str = datetime.datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S") if int(ts) > 1e12 else datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts_str = str(ts)
        trades[x.get("s")] = {"price": x.get("p"), "volume": x.get("v"), "ts": ts_str}
    return {"status": "ok", "note": "实时快照(非历史盘后)", "trades": trades}


# ---------------------------------------------------------------------------
# 新浪兜底源（Infoway 试用 key 过期后，M7 个股 / 商品改用新浪直连）
# ---------------------------------------------------------------------------

def _sina_head(codes):
    """新浪实时快照 → {key:[字段...]}"""
    import requests as _rq
    r = _rq.get("https://hq.sinajs.cn/list=" + codes, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
    r.encoding = "gbk"
    out = {}
    for line in r.text.strip().splitlines():
        if "=" in line and '"' in line:
            k = line.split("=")[0].split("_")[-1]
            out[k] = line.split('"')[1].split(",")
    return out

def fetch_m7_sina():
    """M7 个股（新浪美股，[1]现价 [2]涨跌幅）。Infoway 过期后兜底。"""
    m = {"nvda": "NVDA.US", "aapl": "AAPL.US", "msft": "MSFT.US", "goog": "GOOGL.US",
         "amzn": "AMZN.US", "meta": "META.US", "tsla": "TSLA.US"}
    q = _sina_head("gb_nvda,gb_aapl,gb_msft,gb_goog,gb_amzn,gb_meta,gb_tsla")
    items = {}
    for code, us in m.items():
        a = q.get(code, [])
        if len(a) > 3:
            try:
                items[us] = {"close": float(a[1]), "chg_pct": float(a[2])}
            except ValueError:
                items[us] = {"close": a[1], "chg_pct": a[2]}
    return {"status": "ok" if items else "error", "source": "新浪", "items": items}

def fetch_commodities_sina():
    """商品（原油/黄金，新浪 hf_）。Infoway 过期后兜底。"""
    q = _sina_head("hf_CL,hf_OIL,hf_GC")
    items = {}
    for code, name in [("CL", "WTI原油"), ("OIL", "布伦特原油"), ("GC", "黄金")]:
        a = q.get(code, [])
        if a:
            try:
                items[name] = {"close": float(a[0])}
            except ValueError:
                items[name] = {"close": a[0]}
    return {"status": "ok" if items else "error", "source": "新浪", "items": items}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--json-out")]
    if args:
        target = args[0]
    else:
        # 默认取最近一个交易日（东八区今天若为非交易日则往前找，简单取"今天-1天再对齐到工作日"）
        target = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    json_out = "us_market_data_" + target + ".json"

    # 从 argv 解析 --json-out
    if "--json-out" in sys.argv:
        i = sys.argv.index("--json-out")
        if i + 1 < len(sys.argv):
            json_out = sys.argv[i + 1]

    print(f"目标日期: {target}")
    if not FMP_KEY:
        print("[错误] 未设置 FMP_API_KEY")
        sys.exit(1)
    # Infoway 试用 key 可能已过期：不强制要求，M7/商品/等用新浪/FMP 兜底，宽度/温度/盘后若无替代标[待核实]

    result = {"target_date": target, "generated_at": datetime.datetime.now().isoformat(), "modules": {}}

    def run(name, fn):
        try:
            r = fn()
        except Exception as e:
            result["modules"][name] = {"status": "error", "error": str(e)[:200]}
            print(f"  ❌ {name}  异常: {str(e)[:120]}")
            return
        result["modules"][name] = r
        status = r.get("status", "?")
        mark = {"ok": "✅", "partial": "⚠️", "error": "❌"}.get(status, "❓")
        detail = ""
        if name == "fmp_indices_eod" and isinstance(r.get("indices"), dict):
            detail = " ".join(f"{k}:{v.get('close')}({v.get('vol_ratio_20d')}x)" for k, v in r["indices"].items())
        elif name == "fmp_sectors" and r.get("sectors"):
            detail = ", ".join(f"{s['sector']} {s['avg_change_pct']}%" for s in r["sectors"][:6])
        elif name == "infoway_kline_stocks":
            detail = ", ".join(f"{k}:{v.get('close')}({v.get('chg_pct')})" for k, v in r.get("items", {}).items())
        elif name == "infoway_kline_common":
            detail = ", ".join(f"{k}:{v.get('close')}({v.get('chg_pct')})" for k, v in r.get("items", {}).items())
        print(f"  {mark} {name} {detail}")

    print("--- 拉取中 ---")
    run("fmp_indices_eod", lambda: fetch_fmp_indices_eod(target))
    run("fmp_sectors", lambda: fetch_fmp_sectors(target))
    run("fmp_treasuries", lambda: fetch_fmp_treasuries(target))
    run("fmp_crypto", fetch_fmp_crypto)
    # Infoway 免费档限流较紧：每个调用之间留间隔
    run("infoway_breadth", fetch_infoway_breadth)
    time.sleep(1.5)
    run("infoway_temperature", fetch_infoway_temperature)
    time.sleep(1.5)
    run("infoway_kline_stocks", lambda: fetch_m7_sina())
    time.sleep(0.3)
    run("infoway_kline_common", lambda: fetch_commodities_sina())
    time.sleep(0.3)
    run("infoway_afterhours", lambda: fetch_infoway_afterhours(",".join(M7_INFOWAY)))

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"--- 已保存: {json_out} ---")


if __name__ == "__main__":
    main()
