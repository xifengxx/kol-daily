#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render Invest Wiki 65-segment heat into the US daily briefing."""

import argparse
import json
import re
from pathlib import Path


TOP_N = 8
BOTTOM_N = 8

# 报告标题/编号里统一使用的口径描述（改口径时只改这一处）
# 注意：不要带括号，标题/编号本身已有一层括号，再嵌会变成「（…（…））」
CHAIN_TITLE_SUFFIX = "Invest Wiki 产业链段热力 65段全量计算"


def pct(value):
    return "—" if value is None else f"{value:+.2f}%"


def stock_text(stock, limit=2):
    if not stock:
        return "—"
    rows = stock if isinstance(stock, list) else [stock]
    return "、".join(f"{x['name']} {x['chg_pct']:+.2f}%" for x in rows[:limit])


def a_share_text(segment, limit=4):
    if not segment.get("a_share"):
        return "—"
    return "、".join(x["name"] for x in segment["a_share"][:limit])


def segment_row(segment):
    top = stock_text(segment.get("top"), 1)
    bottom = stock_text(segment.get("bottom"), 1)
    return (
        f"| {segment['rank']} | {segment['name']} | "
        f"{pct(segment['change_equal_weight_pct'])} | "
        f"{pct(segment['change_mcap_weight_pct'])} | "
        f"{top} / {bottom} | {a_share_text(segment)} |"
    )


def build_chain_section(heat):
    rankable = [x for x in heat["segments"] if x["rankable"]]
    top = rankable[:TOP_N]
    bottom = list(reversed(rankable[-BOTTOM_N:]))
    unrankable = [x for x in heat["segments"] if not x["rankable"]]
    anomalies = heat.get("anomalies_pct_5", [])

    stats = heat["universe_stats"]
    header = [
        "### 2. Invest Wiki 产业链段热力（65段全量计算版）",
        "",
        "> 口径：使用 Invest Wiki 产业链宇宙，原始 81 段合并跨赛道重名后为 "
        f"{stats['canonical_segments']} 个 canonical 段；海外候选 {stats['overseas_quote_candidates']} 只，"
        f"有效行情 {heat['global_heat']['n_used']} 只。段内同一 ticker 去重；AI算力/半导体和全局汇总再按 ticker 去重。"
        "排名以**海外成分股等权涨跌**为主，USD 市值加权为参考；A股只作次日映射观察，不参与海外热力计算。",
        "",
        f"> 覆盖：AI算力 {heat['track_heat'][0]['n_used']}/{heat['track_heat'][0]['n_unique_candidates']} 只、"
        f"半导体 {heat['track_heat'][1]['n_used']}/{heat['track_heat'][1]['n_unique_candidates']} 只；"
        f"有效样本≥2 的 {len(rankable)} 段参与排名，{len(unrankable)} 段因样本不足保留但不排名。"
        f"数据日期：美东 {heat['target_date']}。FMP 免费版行业接口不返回成分股，因此下表用 Invest Wiki 的段内代表股补足个股线索。",
        "",
        "**AI算力 / 半导体大赛道汇总**",
        "",
        "| 赛道 | 等权热力 | 市值加权 | 领涨 → 领跌 | 覆盖率 |",
        "|---|---:|---:|---|---:|",
    ]
    for track in heat["track_heat"]:
        header.append(
            f"| {track['industry']} | {pct(track['change_equal_weight_pct'])} | "
            f"{pct(track['change_mcap_weight_pct'])} | "
            f"{stock_text(track.get('top'), 1)} → {stock_text(track.get('bottom'), 1)} | "
            f"{track['coverage_pct']}% |"
        )

    header.extend(
        [
            "",
            "**Top8（最强产业链段）**",
            "",
            "| 排名 | 产业链段 | 等权 | 市值加权 | 领涨 / 领跌 | A股映射 |",
            "|---:|---|---:|---:|---|---|",
        ]
    )
    header.extend(segment_row(x) for x in top)
    header.extend(
        [
            "",
            "**Bottom8（最弱产业链段）**",
            "",
            "| 排名 | 产业链段 | 等权 | 市值加权 | 领涨 / 领跌 | A股映射 |",
            "|---:|---|---:|---:|---|---|",
        ]
    )
    header.extend(segment_row(x) for x in bottom)

    top_names = "、".join(x["name"] for x in top[:3])
    bottom_names = "、".join(x["name"] for x in bottom[:3])
    strongest = top[0] if top else None
    # bottom 是 reversed(rankable[-8:])，故 bottom[0] 才是跌幅最大的一端
    weakest = bottom[0] if bottom else None

    narrative = [
        "",
        "**结构解读**",
        "",
        "> 本节全部由当日数据生成；具体涨跌原因见驱动解读列，不做无数据支撑的归因。",
        "",
    ]
    if strongest and weakest:
        narrative.append(
            f"- **强势端**：Top8 由 {top_names} 领前；等权涨幅居首的是 {strongest['name']}"
            f"（{pct(strongest['change_equal_weight_pct'])}）。"
        )
        narrative.append(
            f"- **弱势端**：Bottom8 里 {bottom_names} 靠前；等权跌幅最大的是 {weakest['name']}"
            f"（{pct(weakest['change_equal_weight_pct'])}）。"
        )

    # 口径提示：只在 Top8 内确实存在明显背离时才写，避免套话
    divergent = [
        s for s in top
        if s.get("change_equal_weight_pct") is not None
        and s.get("change_mcap_weight_pct") is not None
        and abs(s["change_equal_weight_pct"] - s["change_mcap_weight_pct"]) >= 1.0
    ]
    if divergent:
        d = max(divergent, key=lambda s: abs(
            s["change_equal_weight_pct"] - s["change_mcap_weight_pct"]))
        narrative.append(
            f"- **口径提示**：Top8 中等权与市值加权背离最大的是 {d['name']}"
            f"（等权 {pct(d['change_equal_weight_pct'])} vs 市值加权 {pct(d['change_mcap_weight_pct'])}），"
            "说明该段涨跌主要由小市值成分股贡献、龙头相对走平。两个口径不可互相换算，"
            "本表以等权为主排序、市值加权仅作参考。"
        )

    narrative.append(
        "- **A股映射只作观察，不当作因果传导**：美股段热力为隔夜信号，A股次日还受本地资金面、开盘情绪和个股事件影响。"
        "表中映射公司来自 Invest Wiki 的产业角色，不代表每只股票都有相同海外业务敞口。"
    )

    if anomalies:
        narrative.extend(
            [
                "",
                "**链内异常股（|涨跌幅|≥5%）**",
                "",
                "| 股票 | 涨跌幅 | 所属/角色提示 |",
                "|---|---:|---|",
            ]
        )
        role_by_ticker = {}
        for segment in heat["segments"]:
            for stock in segment["stocks"]:
                role_by_ticker.setdefault(stock["ticker"], set()).add(segment["name"])
            for stock in segment.get("a_share", []):
                pass
        for stock in anomalies:
            roles = "、".join(sorted(role_by_ticker.get(stock["ticker"], []))[:2]) or "跨段/行情来源"
            narrative.append(
                f"| {stock['name']}（{stock['ticker']}） | {stock['chg_pct']:+.2f}% | {roles} |"
            )
        narrative.append("")
        biggest = max(anomalies, key=lambda s: abs(s["chg_pct"]))
        narrative.append(
            f"上表按 |涨跌幅| 全量列出，波动最大的是 {biggest['name']}（{biggest['ticker']}）"
            f"{biggest['chg_pct']:+.2f}%。单只成分股的异动不宜机械外推为整条产业链的方向；"
            "其具体原因见驱动解读列，无明确公开原因时按低置信标注，不强行归因。"
        )

    return "\n".join(header + narrative)


def replace_chain_subsection(text, chain_section):
    marker = "### 2. AI 产业链环节热力"
    start = text.find(marker)
    if start < 0:
        marker = "### 2. Invest Wiki 产业链段热力"
        start = text.find(marker)
    if start < 0:
        raise ValueError("chain subsection marker not found")
    next_marker = text.find("\n### 3.", start)
    if next_marker < 0:
        next_marker = text.find("\n## 五、", start)
    if next_marker < 0:
        raise ValueError("end marker not found")
    return text[:start] + chain_section + "\n\n" + text[next_marker + 1:]


def normalize_meta(text, heat):
    """把 base 报告的标题/编号/来源/注改成与当日 heat 一致的通用表述。

    全部用正则匹配既有行，不依赖某一期的固定文案；重复渲染是幂等的。
    """
    stats = heat["universe_stats"]
    n_src = stats["source_segments"]
    n_seg = stats["canonical_segments"]

    # 标题：任意「晨间版 · xxx」都归一，不写死旧标题
    text = re.sub(
        r"(# 🌅 美股日度复盘简报（晨间版)[^）]*(）)",
        rf"\1 · {CHAIN_TITLE_SUFFIX}\2",
        text, count=1,
    )
    # 简报编号：保留期号数字，只规范化括号内的版本描述
    text = re.sub(
        r"(\*\*简报编号\*\*：第 \d+ 期（)[^）]*(）)",
        rf"\1数据源版 · {CHAIN_TITLE_SUFFIX}\2",
        text, count=1,
    )
    # 数据来源：用负向先行断言只看「这一行」，避免被正文里同名表述误判为已处理
    text = re.sub(
        r"\*\*数据来源\*\*：(?!Invest Wiki)",
        f"**数据来源**：Invest Wiki 产业链宇宙（{n_src} 原始段 → {n_seg} canonical 段）；",
        text, count=1,
    )
    # 口径注：追加一句说明。用 [ \t]* 而非 \s*（否则会吃掉行尾空行）；
    # 用负向先行断言保证重复渲染不会叠加同一句。
    text = re.sub(
        r"^(> 注：(?!.*不再使用旧版 11 环节清单).*?)。?[ \t]*$",
        rf"\1；产业链热力改由 Invest Wiki {n_seg} 段宇宙计算，不再使用旧版 11 环节清单。",
        text, count=1, flags=re.M,
    )
    return text


def render(base_report, heat, output_path):
    text = base_report.read_text(encoding="utf-8")
    text = normalize_meta(text, heat)
    text = replace_chain_subsection(text, build_chain_section(heat))
    output_path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--heat", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    heat = json.loads(args.heat.read_text(encoding="utf-8"))
    render(args.base, heat, args.out)
    print(args.out)


if __name__ == "__main__":
    main()
