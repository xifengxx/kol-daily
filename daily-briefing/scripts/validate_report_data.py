#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日复盘报告 - 数据校验脚本
==============================
对「美股日度复盘」/「A股收盘复盘」报告里的关键数据点，用权威源做多源比对，
标出「报告值 vs 权威参考值」的差异，避免口径/数据不准。

数据源（均实测可用）：
  美股指数/费半：新浪 hq.sinajs.cn（gb_$dji/ixic/inx/$sox，休市显示收盘）
  港股指数：新浪 rt_hk（规范字段 [6]现价 [8]涨跌幅）
  A股指数：akshare 腾讯K线（stock_zh_index_daily_tx）
  市场宽度：akshare stock_market_activity_legu（上涨/涨停/跌停/两市总成交额）
  涨停池：akshare stock_zt_pool_em

用法：
  python3 validate_report_data.py --market us --report ../reports/us/2026-09-02.md
  python3 validate_report_data.py --market cn --report ../reports/cn/2026-09-02.md
  python3 validate_report_data.py --market us --date 2026-09-01
"""
import re, sys, os, argparse
import requests
import akshare as ak
import warnings
warnings.filterwarnings("ignore")

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}

# ---------- 权威源：指数 ----------
def sina_quote(codes):
    """新浪实时快照，返回 {key: [字段...]}"""
    r = requests.get("https://hq.sinajs.cn/list=" + codes, headers=SINA_HEADERS, timeout=10)
    r.encoding = "gbk"
    out = {}
    for line in r.text.strip().splitlines():
        if "=" in line and '"' in line:
            k = line.split("=")[0].split("_")[-1]
            out[k] = line.split('"')[1].split(",")
    return out

def fetch_us_indices():
    """美股指数权威(新浪,休市=收盘)。返回 {名称: {'close':, 'pct':}}"""
    q = sina_quote("gb_$dji,gb_ixic,gb_inx,gb_$sox")
    res = {}
    for key, name in [("$dji", "道琼斯"), ("ixic", "纳斯达克"), ("inx", "标普"), ("$sox", "费城半导体")]:
        a = q.get(key, [])
        try:
            res[name] = {"close": float(a[1]), "pct": float(a[3])}
        except (ValueError, IndexError):
            pass
    return res

def fetch_hk_indices():
    """港股指数权威(新浪 rt_hk, 规范字段 [6]现价 [8]涨跌幅)。返回 {名称: {close,pct}}"""
    res = {}
    try:
        r = requests.get("https://hq.sinajs.cn/list=rt_hkHSI,rt_hkHSCEI,rt_hkHSTECH", headers=SINA_HEADERS, timeout=10)
        r.encoding = "gbk"
        mapping = {"HSI": ("恒生指数", 6, 8), "HSCEI": ("恒生国企", 6, 8), "HSTECH": ("恒生科技", 6, 8)}
        for line in r.text.strip().splitlines():
            if "=" in line and '"' in line:
                key = line.split("=")[0].split("_")[-1]  # rt_hkHSI -> HSI
                if key in mapping:
                    name, ci, cpi = mapping[key]
                    a = line.split('"')[1].split(",")
                    if len(a) > 8:
                        res[name] = {"close": float(a[ci]), "pct": float(a[cpi])}
    except Exception:
        pass
    return res

def fetch_cn_indices():
    """A股指数权威(腾讯K线)。返回 {名称: {close,pct}}"""
    syms = {"上证指数": "sh000001", "深证成指": "sz399001", "创业板指": "sz399006", "科创50": "sh000688", "北证50": "bj899050"}
    res = {}
    for name, sym in syms.items():
        try:
            df = ak.stock_zh_index_daily_tx(symbol=sym)
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else None
            close = float(last["close"])
            pct = round((close / float(prev["close"]) - 1) * 100, 2) if prev is not None else None
            res[name] = {"close": close, "pct": pct}
        except Exception:
            pass
    return res

def fetch_breadth():
    """市场宽度权威(乐咕)。返回 {上涨,涨停,跌停,两市总成交额}"""
    try:
        df = ak.stock_market_activity_legu()
        row = df.iloc[-1]
        return {k: row.get(k) for k in ["上涨", "涨停", "跌停", "炸板", "两市总成交额", "中位涨幅"]}
    except Exception:
        return {}

# ---------- 报告提取 ----------
def extract_report_values(report_path):
    """从报告 markdown 提取关键数据，返回 {指标: {值类别}}。"""
    txt = open(report_path, encoding="utf8").read()
    vals = {}
    # 指数表：| 名称 | 点位 | 涨跌幅 | ...（提取名称/点位/涨跌幅）
    for line in txt.splitlines():
        if line.strip().startswith("|") and not re.match(r"\|\s*:?-+", line.strip()):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                name = cells[0]
                close = cells[1]
                pct = cells[2]
                # 匹配已知指数名（含点位+涨跌幅的表格行）
                known = ["上证指数", "深证成指", "创业板指", "科创50", "北证50",
                         "道琼斯", "标普", "纳斯达克", "费城半导体", "罗素",
                         "恒生指数", "恒生国企", "恒生科技"]
                if any(k in name for k in known):
                    if re.search(r"[\d,]+\.\d{2}", close) and re.search(r"[+-]?\d+\.\d+%", pct or ""):
                        vals.setdefault(name, {})
                        vals[name]["close"] = close
                        vals[name]["pct"] = pct
    return vals

def to_num(s):
    if not s: return None
    return float(str(s).replace(",", "").replace("%", "").replace("+", ""))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", choices=["us", "cn"], default="us")
    ap.add_argument("--report", help="报告 .md 路径")
    ap.add_argument("--date", help="日期(用于拼默认路径)")
    args = ap.parse_args()
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # daily-briefing
    if not args.report and args.date:
        args.report = os.path.join(base, "reports", args.market, args.date + ".md")
    if not args.report or not os.path.exists(args.report):
        print("❌ 报告路径无效:", args.report); sys.exit(1)

    print(f"=== 校验报告: {args.report} ({args.market}) ===")
    report_vals = extract_report_values(args.report)
    # 取权威参考
    if args.market == "us":
        ref = fetch_us_indices()
    else:
        ref = fetch_cn_indices()
        ref.update(fetch_hk_indices())
    breadth = fetch_breadth()

    # 比对指数
    print("\n【指数点位/涨跌幅】报告 vs 权威参考")
    mism = 0
    matched = 0
    for name, rv in report_vals.items():
        # 匹配权威参考
        ref_name = None
        for k, v in ref.items():
            if k in name or name in k:
                ref_name = k; break
        if not ref_name:
            continue
        rc = ref[ref_name]["close"]
        rp = ref[ref_name]["pct"]
        rep_close = to_num(rv.get("close"))
        rep_pct = to_num(rv.get("pct"))
        c_diff = abs((rep_close or 0) - rc) if rc else 999
        p_diff = abs((rep_pct or 0) - rp) if rp is not None else 999
        ok = c_diff < 10 and p_diff < 0.3
        flag = "✅ 一致" if ok else "⚠️ 差异"
        if ok: matched += 1
        else: mism += 1
        print(f"  {name:12} 报告 {rv.get('close','?')}/{rv.get('pct','?')} | 权威 {rc}/{rp}% | {flag} (点位差{c_diff:.1f} 涨跌差{p_diff:.2f})")
    print(f"\n  ✅一致 {matched} | ⚠️差异 {mism}")

    # 市场宽度（A股报告都涉及）
    if breadth:
        print("\n【市场宽度】权威(乐咕)")
        print(f"  上涨{breadth.get('上涨')} 涨停{breadth.get('涨停')} 跌停{breadth.get('跌停')} 两市总成交{breadth.get('两市总成交额')}")
    print("\n说明：点位差<10且涨跌差<0.3%视为一致；超出为口径/数据差异，需人工确认（技术常犯：用盘中/半日数据当收盘）。")

if __name__ == "__main__":
    main()
