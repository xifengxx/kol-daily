#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch quotes and compute Invest Wiki industry-chain segment heat."""

import datetime
import json
import math
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yfinance as yf


SCRIPT_DIR = Path(__file__).resolve().parent
UNIVERSE_PATH = SCRIPT_DIR / "chain_universe.json"
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data"
QUOTE_CURRENCIES = {"KRW", "JPY", "TWD", "HKD", "EUR", "CHF"}


def _date(value):
    return value.date().isoformat()


def _safe_pct(close, prev_close):
    if not close or not prev_close:
        return None
    return round((float(close) / float(prev_close) - 1) * 100, 2)


def _target_change(series, target):
    close = series.dropna()
    if close.empty:
        return None
    date_index = {_date(idx): idx for idx in close.index}
    used_latest = target not in date_index
    if used_latest:
        target_idx = close.index[-1]
    else:
        target_idx = date_index[target]
    pos = close.index.get_loc(target_idx)
    if pos == 0:
        return None
    prev_idx = close.index[pos - 1]
    return {
        "date": _date(target_idx),
        "close": round(float(close.loc[target_idx]), 4),
        "prev_close": round(float(close.loc[prev_idx]), 4),
        "chg_pct": _safe_pct(close.loc[target_idx], close.loc[prev_idx]),
        "used_latest": used_latest,
    }


def fetch_fx_rates(target):
    rates = {"USD": 1.0}
    symbols = [f"USD{currency}=X" for currency in QUOTE_CURRENCIES]
    frame = yf.download(
        " ".join(symbols),
        start=(datetime.date.fromisoformat(target) - datetime.timedelta(days=8)).isoformat(),
        end=(datetime.date.fromisoformat(target) + datetime.timedelta(days=1)).isoformat(),
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )
    for currency, symbol in zip(QUOTE_CURRENCIES, symbols):
        try:
            close = frame[symbol]["Close"].dropna()
            rates[currency] = float(close.iloc[-1])
        except Exception:
            rates[currency] = None
    return rates


def fetch_market_cap(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        cap = info.get("marketCap")
        currency = info.get("currency")
        if cap is None or currency is None:
            return {"market_cap_local": None, "currency": None, "market_cap_usd": None}
        cap = float(cap)
        return {
            "market_cap_local": round(cap / 1e9, 3),
            "currency": currency,
            "market_cap_usd": cap,
        }
    except Exception:
        return {"market_cap_local": None, "currency": None, "market_cap_usd": None}


def fetch_quotes(candidates, target):
    symbols = [x["ticker"] for x in candidates]
    start = (datetime.date.fromisoformat(target) - datetime.timedelta(days=14)).isoformat()
    end = (datetime.date.fromisoformat(target) + datetime.timedelta(days=1)).isoformat()
    frame = yf.download(
        " ".join(symbols),
        start=start,
        end=end,
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )
    quotes = {}

    def worker(item):
        ticker = item["ticker"]
        try:
            if isinstance(frame.columns, __import__("pandas").MultiIndex) and ticker in frame.columns.get_level_values(0):
                sub = frame[ticker]
            else:
                sub = frame
            change = _target_change(sub["Close"], target)
            base = {
                "ticker": ticker,
                "source": "Yahoo",
                "error": None,
                **change,
            }
        except Exception as exc:
            base = {
                "ticker": ticker,
                "source": "Yahoo",
                "error": str(exc)[:160],
                "date": None,
                "close": None,
                "prev_close": None,
                "chg_pct": None,
                "used_latest": False,
            }
        base.update(fetch_market_cap(ticker))
        return ticker, base

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(worker, item) for item in candidates]
        for i, future in enumerate(as_completed(futures), 1):
            ticker, quote = future.result()
            quotes[ticker] = quote
            if i % 25 == 0:
                print(f"quotes/caps: {i}/{len(candidates)}", flush=True)
            time.sleep(0.02)
    return quotes


def aggregate(stocks):
    valid = [x for x in stocks if x.get("chg_pct") is not None]
    equal = round(statistics.mean(x["chg_pct"] for x in valid), 2) if valid else None
    cap_rows = [x for x in valid if x.get("market_cap_usd")]
    if cap_rows:
        total_cap = sum(float(x["market_cap_usd"]) for x in cap_rows)
        weighted = round(
            sum(float(x["chg_pct"]) * float(x["market_cap_usd"]) for x in cap_rows) / total_cap,
            2,
        )
        cap_coverage = round(len(cap_rows) / len(valid), 2) if valid else 0
    else:
        weighted = None
        cap_coverage = 0
    top = max(valid, key=lambda x: x["chg_pct"]) if valid else None
    bottom = min(valid, key=lambda x: x["chg_pct"]) if valid else None
    return equal, weighted, cap_coverage, top, bottom, len(valid)


def compute_heat(universe, quotes, target):
    quote_by_ticker = {}
    for ticker, comp in universe["companies"].items():
        if not comp["tradable"] or comp["market_guess"] == "CN":
            continue
        q = quotes.get(ticker)
        if not q or q.get("chg_pct") is None:
            continue
        quote_by_ticker[ticker] = {**q, "name": comp["name"]}

    rendered_segments = []
    for seg in universe["segments"]:
        stocks = []
        for comp in seg["companies"]:
            if not comp["in_overseas_heat"]:
                continue
            q = quote_by_ticker.get(comp["ticker"])
            if q:
                stocks.append({**q, "role": "; ".join(comp["roles"]), "rev": comp["rev"]})
        equal, weighted, cap_coverage, top, bottom, n_used = aggregate(stocks)
        n_candidates = len(stocks)
        rendered_segments.append(
            {
                "segment_id": seg["segment_id"],
                "name": seg["name"],
                "industry_tags": seg["industry_tags"],
                "source_slugs": seg["source_slugs"],
                "chain_note": seg["chain_note"],
                "change_equal_weight_pct": equal,
                "change_mcap_weight_pct": weighted,
                "cap_coverage_of_valid": cap_coverage,
                "rank_change_pct": equal,
                "n_overseas_candidates": n_candidates,
                "n_used": n_used,
                "n_missing": n_candidates - n_used,
                "coverage_pct": round(n_used / n_candidates * 100, 1) if n_candidates else 0,
                "rankable": n_used >= 2,
                "top": top,
                "bottom": bottom,
                "stocks": stocks,
                "a_share": seg["a_share"],
            }
        )

    rendered_segments.sort(
        key=lambda x: (
            not x["rankable"],
            x["rank_change_pct"] is None,
            -(x["rank_change_pct"] or -999),
        )
    )
    for i, seg in enumerate(rendered_segments, 1):
        seg["rank"] = i

    track_heat = []
    for industry in ["AI算力", "半导体"]:
        tickers = {}
        for seg in universe["segments"]:
            if industry not in seg["industry_tags"]:
                continue
            for comp in seg["companies"]:
                if comp["in_overseas_heat"]:
                    tickers[comp["ticker"]] = comp
        stocks = [quote_by_ticker[x] for x in tickers if x in quote_by_ticker]
        equal, weighted, cap_coverage, top, bottom, n_used = aggregate(stocks)
        track_heat.append(
            {
                "industry": industry,
                "n_unique_candidates": len(tickers),
                "n_used": n_used,
                "n_missing": len(tickers) - n_used,
                "coverage_pct": round(n_used / len(tickers) * 100, 1) if tickers else 0,
                "change_equal_weight_pct": equal,
                "change_mcap_weight_pct": weighted,
                "cap_coverage_of_valid": cap_coverage,
                "top": top,
                "bottom": bottom,
            }
        )

    all_stocks = list(quote_by_ticker.values())
    _, _, _, top, bottom, n_used = aggregate(all_stocks)
    global_heat = {
        "n_unique_candidates": len({x["ticker"] for x in universe["companies"].values()
                                     if x["tradable"] and x["market_guess"] != "CN"}),
        "n_used": n_used,
        "change_equal_weight_pct": round(statistics.mean(x["chg_pct"] for x in all_stocks), 2) if all_stocks else None,
        "top": top,
        "bottom": bottom,
    }
    anomalies = sorted(
        [x for x in all_stocks if abs(x["chg_pct"]) >= 5],
        key=lambda x: -abs(x["chg_pct"]),
    )
    dates = sorted({x["date"] for x in all_stocks if x.get("date")})
    return {
        "target_date": target,
        "data_dates": dates,
        "date_mixed": len(dates) > 1,
        "source": "Yahoo Finance yfinance",
        "method": (
            "Segment heat uses equal-weight primary and USD market-cap-weighted reference; "
            "duplicate companies are unique per segment but deduplicated for track/global heat."
        ),
        "universe_version": universe["version"],
        "universe_stats": universe["stats"],
        "global_heat": global_heat,
        "track_heat": track_heat,
        "segments": rendered_segments,
        "anomalies_pct_5": anomalies,
        "quotes": quotes,
    }


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "2026-09-09"
    universe_path = Path(sys.argv[2]) if len(sys.argv) > 2 else UNIVERSE_PATH
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else OUTPUT_DIR / f"industry_chain_heat_{target}.json"
    universe = json.loads(universe_path.read_text(encoding="utf-8"))
    candidates = [
        {"ticker": comp["ticker"]}
        for comp in universe["companies"].values()
        if comp["tradable"] and comp["market_guess"] != "CN"
    ]
    print(f"fetching {len(candidates)} overseas tickers for {target}", flush=True)
    quotes = fetch_quotes(candidates, target)
    heat = compute_heat(universe, quotes, target)
    output_path.write_text(json.dumps(heat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    used = sum(1 for x in quotes.values() if x.get("chg_pct") is not None)
    print(
        json.dumps(
            {
                "target": target,
                "candidates": len(candidates),
                "used": used,
                "segments": len(heat["segments"]),
                "rankable_segments": sum(1 for x in heat["segments"] if x["rankable"]),
                "output": str(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
