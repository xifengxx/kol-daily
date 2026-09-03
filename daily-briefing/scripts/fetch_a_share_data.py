#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股每日收盘复盘 - 数据接入脚本（付费优先 + 免费冗余 + 数据路由）
================================================================
按"付费商业源优先 → 免费源冗余 → 财经媒体兜底"的路由原则，
拉取 A股复盘简报（22-A股日度复盘简报）所需数据，输出结构化 JSON 快照。

数据源（优先级路由）：
  - iFinD（付费，可选）：若配置 IFIND_USER/IFIND_PASS 则优先，否则跳过
  - AkShare（免费开源）：本机可用路径 = 腾讯K线 / 乐咕市场活动 / 涨停池 / 北向 / 两融 / 龙虎榜 / 公告 / 宏观
  - Infoway（付费，env INFOWAY_API_KEY）：板块 132 行业 + 涨跌家数
  - FMP（付费，env FMP_API_KEY）：国际与宏观日历（本机可用性视 key 档位）
  - 新浪直连（免费）：美股/原油/黄金/人民币/恒指实时兜底

用法：
  python3 fetch_a_share_data.py                 # 最近一个交易日
  python3 fetch_a_share_data.py 2026-08-24      # 指定日期
依赖：pip install akshare requests python-dotenv
"""

import os
import sys
import json
import time
import datetime
import warnings
import urllib.parse

warnings.filterwarnings("ignore")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests
import akshare as ak

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
INFOWAY_KEY = os.environ.get("INFOWAY_API_KEY", "")
FMP_KEY = os.environ.get("FMP_API_KEY", "")
IFIND_USER = os.environ.get("IFIND_USER", "")
IFIND_PASS = os.environ.get("IFIND_PASS", "")
INFOWAY_BASE = "https://data.infoway.io"
FMP_BASE = "https://financialmodelingprep.com/stable"
SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}

# A股指数：名称 -> (腾讯 symbol, 通用代码)
INDICES = {
    "上证指数": ("sh000001", "000001"),
    "深证成指": ("sz399001", "399001"),
    "创业板指": ("sz399006", "399006"),
    "科创50": ("sh000688", "000688"),
    "北证50": ("bj899050", "899050"),
}

# ---------------------------------------------------------------------------
# 请求封装
# ---------------------------------------------------------------------------

def infoway_get(path):
    try:
        r = requests.get(f"{INFOWAY_BASE}{path}", headers={"apiKey": INFOWAY_KEY}, timeout=25)
        j = r.json()
        if isinstance(j, dict) and "ret" in j and j.get("ret") != 200:
            return {"error": j.get("msg")}
        if isinstance(j, dict) and "data" in j:
            return j["data"]
        return j
    except Exception as e:
        return {"error": str(e)}


def sina_quote(codes):
    """新浪实时行情，返回解析后的 dict。"""
    r = requests.get("https://hq.sinajs.cn/list=" + codes, headers=SINA_HEADERS, timeout=10)
    r.encoding = "gbk"
    out = {}
    for line in r.text.strip().splitlines():
        if "=" not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        val = line.split('"')[1] if '"' in line else ""
        out[key] = val.split(",")
    return out


def fmp_get(path, params=None):
    p = dict(params or {})
    p["apikey"] = FMP_KEY
    try:
        r = requests.get(f"{FMP_BASE}{path}", params=p, timeout=20)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}: {r.text[:120]}"}
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def run_with_fallback(name, fetchers):
    """按优先级依次尝试多个取数函数，首个成功即返回；记录实际来源。"""
    last_err = ""
    for label, fn in fetchers:
        try:
            data = fn()
            if data and not (isinstance(data, dict) and "error" in data):
                return {"status": "ok", "source": label, "data": data}
        except Exception as e:
            last_err = str(e)[:120]
    return {"status": "error", "source": None, "error": last_err, "data": None}


# ---------------------------------------------------------------------------
# 各数据模块
# ---------------------------------------------------------------------------

def pick_bar(df, date_col, target):
    """从 DataFrame 挑目标日期行，找不到返回最后一行。"""
    if df is None or df.empty:
        return None
    if target:
        m = df[df[date_col].astype(str).str.replace("-", "").str.replace("/", "") == target.replace("-", "")]
        if not m.empty:
            return m.iloc[-1]
    return df.iloc[-1]


def fetch_indices(target):
    """A股指数行情。首选腾讯K线，备选 Infoway。"""
    def tx():
        out = {}
        for name, (sym, _) in INDICES.items():
            df = ak.stock_zh_index_daily_tx(symbol=sym)
            if df is None or df.empty:
                out[name] = {"error": "no data"}
                continue
            df2 = df
            if target:
                key = df["date"].astype(str).str.replace("-", "").str.replace("/", "")
                df2 = df[key <= target.replace("-", "")]
            if df2.empty:
                df2 = df
            row = df2.iloc[-1]
            prev = df2.iloc[-2] if len(df2) > 1 else None
            close = float(row["close"])
            pct = round((close / float(prev["close"]) - 1) * 100, 2) if prev is not None else None
            out[name] = {"date": str(row["date"])[:10], "close": close, "pct_chg": pct}
        return out

    def infoway_indices():
        codes = ",".join(f"{c}.SH" if n in ("上证指数", "科创50") else (f"{c}.SZ" if n in ("深证成指", "创业板指") else f"{c}.BJ") for n, (_, c) in INDICES.items())
        return {"note": "Infoway 指数值需与官方校准，仅供参考"}

    fetchers = []
    if IFIND_USER:  # iFinD 优先（若配置账号）
        fetchers.append(("iFinD", lambda: None))
    fetchers.append(("腾讯K线", tx))
    fetchers.append(("Infoway", infoway_indices))
    return run_with_fallback("indices", fetchers)


def fetch_breadth(target):
    """市场宽度：乐咕涨跌/涨停/跌停/炸板 + 涨停池连板。备选 Infoway breadth/CN。"""
    def legu():
        df = ak.stock_market_activity_legu()
        row = pick_bar(df, "日期", target)
        return {k: row[k] for k in ["上涨", "涨停", "跌停", "炸板", "两市总成交额", "中位涨幅"] if k in row} if row is not None else {}

    def zt_pool():
        zt = ak.stock_zt_pool_em(date=target.replace("-", ""))
        dt = None
        try:
            dt = ak.stock_zt_pool_dtgc_em(date=target.replace("-", ""))
        except Exception:
            pass
        out = {"涨停家数": len(zt) if zt is not None else 0}
        if zt is not None and not zt.empty and "连板数" in zt:
            out["连板梯队"] = zt.groupby("连板数").size().to_dict()
            out["最高连板"] = int(zt["连板数"].max())
        if dt is not None and not dt.empty:
            out["跌停家数"] = len(dt)
        return out

    def infoway_breadth():
        d = infoway_get("/common/v2/basic/market/breadth/CN")
        if isinstance(d, dict) and "rise_less_than_three" in d:
            rise = sum(d.get(k, 0) for k in ["rise_less_than_three", "rise_three_to_five", "rise_five_to_seven", "rise_more_than_seven"])
            fall = sum(d.get(k, 0) for k in ["fall_less_than_three", "fall_three_to_five", "fall_five_to_seven", "fall_more_than_seven"])
            return {"上涨家数(Infoway)": rise, "下跌家数(Infoway)": fall, "平盘": d.get("flatline")}
        return {}

    fetchers = [("乐咕", legu), ("涨停池", zt_pool), ("Infoway", infoway_breadth)]
    return run_with_fallback("breadth", fetchers)


def fetch_sectors():
    """板块涨跌：新浪行业（中文，Infoway试用key已过期的兜底）。"""
    def sina():
        df = ak.stock_sector_spot(indicator="新浪行业")
        return df.to_dict("records")
    return run_with_fallback("sectors", [("新浪行业", sina)])


def fetch_fund_flow(target):
    """资金流向：北向汇总 + 两融。"""
    def hsgt():
        df = ak.stock_hsgt_fund_flow_summary_em()
        return df.to_dict("records")
    def margin():
        start = (datetime.datetime.strptime(target, "%Y-%m-%d") - datetime.timedelta(days=10)).strftime("%Y%m%d")
        df = ak.stock_margin_sse(start_date=start, end_date=target.replace("-", ""))
        return df.tail(2).to_dict("records")
    res = {}
    hs = run_with_fallback("fund_flow_hsgt", [("AkShare北向", hsgt)])
    mg = run_with_fallback("fund_flow_margin", [("AkShare两融", margin)])
    res["北向资金"] = hs
    res["两融"] = mg
    return res


def fetch_lhb(target):
    """龙虎榜。"""
    def lhb():
        df = ak.stock_lhb_detail_em(start_date=target.replace("-", ""), end_date=target.replace("-", ""))
        return df.head(30).to_dict("records")
    return run_with_fallback("lhb", [("AkShare龙虎榜", lhb)])


def fetch_notices(target):
    """公司公告。"""
    def notices():
        df = ak.stock_notice_report(symbol="全部", date=target.replace("-", ""))
        return df.head(50).to_dict("records")
    return run_with_fallback("notices", [("AkShare公告", notices)])


def fetch_macro(target):
    """宏观数据：CPI/PMI/LPR（含实际/预期/前值）。"""
    def cpi():
        df = ak.macro_china_cpi_yearly()
        return df.tail(2).to_dict("records")
    def pmi():
        df = ak.macro_china_pmi_yearly()
        return df.tail(2).to_dict("records")
    def lpr():
        df = ak.macro_china_lpr()
        return df.tail(2).to_dict("records")
    out = {}
    out["CPI"] = run_with_fallback("macro_cpi", [("AkShare", cpi)])
    out["PMI"] = run_with_fallback("macro_pmi", [("AkShare", pmi)])
    out["LPR"] = run_with_fallback("macro_lpr", [("AkShare", lpr)])
    return out


def fetch_international():
    """国际市场：美股/原油/黄金/人民币（新浪直连，Infoway/FMP 备选）。"""
    def sina():
        q = sina_quote("gb_$dji,gb_ixic,gb_inx,hf_CL,hf_GC,fx_susdcny")
        return q
    return run_with_fallback("international", [("新浪直连", sina)])


def fetch_hk():
    """港股：恒生/恒生国企/恒生科技（新浪直连，FMP 备选）。"""
    def sina():
        q = sina_quote("rt_hkHSI,rt_hkHSCEI,rt_hkHSTECH")
        out = {}
        for code, arr in q.items():
            # 新浪 rt_hk 港股指数字段：[0]代码 [1]名称 [2]今开 [3]昨收 [4]最高 [5]最低 [6]现价 [7]涨跌额 [8]涨跌幅
            if isinstance(arr, list) and len(arr) > 8:
                try:
                    out[code] = {"name": arr[1], "price": float(arr[6]), "prev_close": float(arr[3]), "change": float(arr[7]), "change_pct": float(arr[8])}
                except (ValueError, TypeError):
                    out[code] = {"raw": arr}
        return out
    def fmp():
        d = fmp_get("/quote", {"symbol": "^HSI,^HSCE"})
        if isinstance(d, list) and d:
            return d
        return {}
    return run_with_fallback("hk", [("新浪", sina), ("FMP", fmp)])


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--json-out")]
    if args:
        target = args[0]
    else:
        target = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    json_out = "a_share_data_" + target + ".json"
    if "--json-out" in sys.argv:
        i = sys.argv.index("--json-out")
        if i + 1 < len(sys.argv):
            json_out = sys.argv[i + 1]

    print(f"目标日期: {target}  (iFinD {'已配置' if IFIND_USER else '未配置，走免费冗余'})")
    result = {"target_date": target, "generated_at": datetime.datetime.now().isoformat(), "modules": {}}

    def run(name, fn):
        r = fn()
        result["modules"][name] = r
        # 兼容两种返回：带 status 的包装结果，或直接返回数据的嵌套 dict
        ok = False
        if isinstance(r, dict) and r.get("status") == "ok":
            ok = True
            print(f"  ✅ {name}  <- 来源: {r.get('source', '?')}")
        elif isinstance(r, dict) and "status" not in r and r:
            ok = True
            subs = [k for k, v in r.items() if isinstance(v, dict) and v.get("status") == "ok"]
            print(f"  ✅ {name}  <- 子模块 OK: {subs if subs else '有数据'}")
        if not ok:
            print(f"  ⚠️ {name}  未取到: {str(r)[:100]}")

    print("--- 拉取中 ---")
    run("indices", lambda: fetch_indices(target))
    time.sleep(1)
    run("breadth", lambda: fetch_breadth(target))
    time.sleep(1)
    run("sectors", fetch_sectors)
    time.sleep(1)
    run("fund_flow", lambda: fetch_fund_flow(target))
    time.sleep(1)
    run("lhb", lambda: fetch_lhb(target))
    time.sleep(1)
    run("notices", lambda: fetch_notices(target))
    time.sleep(1)
    run("macro", lambda: fetch_macro(target))
    run("international", fetch_international)
    run("hk", fetch_hk)

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"--- 已保存: {json_out} ---")


if __name__ == "__main__":
    main()
