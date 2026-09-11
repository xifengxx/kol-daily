#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render Invest Wiki 65-segment heat into the US daily briefing."""

import argparse
import json
from pathlib import Path


TOP_N = 8
BOTTOM_N = 8


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
    narrative = [
        "",
        "**结构解读**",
        "",
        f"- **强势端不等于笼统的“AI涨价”**：Top8 分布在封装测试、CMP材料、大模型、封装基板、Fabless、光/DSP芯片、成熟制程和 AI 服务器。"
        f"前三段是 {top_names}，更像是资金在 AI 供给瓶颈、材料耗材和平台模型里做结构性选择。",
        f"- **弱势端集中在 AI 基础设施配套与设备链**：Bottom8 里 {bottom_names} 靠前，说明市场对前期预期较高的算力配套、设备与高估值环节更挑剔；"
        "这与美债利率上行、油价高位压制成长股估值的宏观背景一致。",
        "- **A股映射只作观察，不当作因果传导**：美股段热力为隔夜信号，A股次日还受本地资金面、开盘情绪和个股事件影响。表中映射公司来自 Invest Wiki 的产业角色，不代表每只股票都有相同海外业务敞口。",
    ]

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
        narrative.append(
            "Vertiv 的跌幅需要单独看：它是 AI 数据中心“电力+散热”里的标志性美股，短期大跌可能反映获利了结、资金切换或对高预期配套环节的重新定价；"
            "后续应跟踪公司/行业是否有具体负面消息，而不是机械外推整条散热链。"
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


def render(base_report, heat, output_path):
    text = base_report.read_text(encoding="utf-8")
    text = text.replace(
        "# 🌅 美股日度复盘简报（晨间版 · 行业热力+AI链试运行）",
        "# 🌅 美股日度复盘简报（晨间版 · Invest Wiki 65段产业链热力）",
        1,
    )
    text = text.replace(
        "**数据来源**：",
        "**数据来源**：Invest Wiki 产业链宇宙（v1.0，81原始段→65 canonical段）；",
        1,
    )
    text = text.replace(
        "FMP/Yahoo 产业链行情快照；",
        "Yahoo 产业链行情快照；",
        1,
    )
    text = text.replace(
        "**简报编号**：第 14 期（数据源版 · 行业热力+AI产业链试运行）",
        "**简报编号**：第 14 期（数据源版 · Invest Wiki 65段产业链热力）",
        1,
    )
    text = text.replace(
        "> 注：Infoway 试用 key 已过期（宽度/盘后仍缺并标注）；FMP 指数 ^SOX 未返回（费半改用新浪直连，已校准）。",
        "> 注：Infoway 试用 key 已过期（宽度/盘后仍缺并标注）；FMP 指数 ^SOX 未返回（费半改用新浪直连，已校准）；"
        "产业链热力由 Invest Wiki 65 段宇宙重新计算，不再使用旧版 11 环节清单。",
        1,
    )
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
