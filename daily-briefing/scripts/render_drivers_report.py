#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render a new US briefing with driver explanations without touching the base report."""

import argparse
import json
import re
from pathlib import Path


def load_drivers(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return {entry["type"] + ":" + entry["key"]: entry for entry in data["entries"]}


def add_column_to_table(lines, start, end, header, lookup, keys):
    width = max(line.count("|") for line in lines[start:end])
    lines[start] = lines[start][:-1] + f" {header} |"
    lines[start + 1] = lines[start + 1][:-1] + " --- |"
    for index in range(start + 2, end):
        line = lines[index]
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        key = keys[index - start - 2]
        entry = lookup.get(key)
        if entry:
            cells.append(f"{entry['driver']}（置信度：{entry['confidence']}）")
        else:
            cells.append("暂无明确公开原因（置信度：低）")
        lines[index] = "| " + " | ".join(cells) + " |"


def expand_tables(text, drivers):
    lines = text.splitlines()
    out = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].startswith("|"):
            start = index
            end = start + 2
            while end < len(lines) and lines[end].startswith("|"):
                end += 1
            if len(lines[start]) >= len(lines[start + 1]) and line.count("|") == lines[start + 1].count("|"):
                header = [cell.strip() for cell in line.strip("|").split("|")]
                rows = [
                    [cell.strip() for cell in x.strip("|").split("|")]
                    for x in lines[start + 2:end]
                ]
                if header[:3] == ["方向", "行业", "当日涨跌"]:
                    out.extend([lines[i] for i in range(start, end)])
                    out[-1] = out[-1][:-1] + " 驱动解读 |"
                    out.append(out.pop().replace("| 驱动解读 |", "| --- |"))
                    for row in rows:
                        entry = drivers.get("industry:" + row[1])
                        text_cell = entry["driver"] if entry else "暂无明确公开原因"
                        conf = entry["confidence"] if entry else "低"
                        out.append("| " + " | ".join(row + [f"{text_cell}（置信度：{conf}）"]) + " |")
                    index = end
                    continue
        out.append(line)
        index += 1
    return "\n".join(out)


def render(text, drivers):
    text = text.replace(
        "# 🌅 美股日度复盘简报（晨间版 · Invest Wiki 65段产业链热力）",
        "# 🌅 羁股日度复盘简报（晨间版 · Invest Wiki 65段产业链热力 + 驱动解读）",
    ).replace("羁股", "美股")
    text = text.replace(
        "**简报编号**：第 15 期（数据源版 · Invest Wiki 65段产业链热力）",
        "**简报编号**：第 15 期（数据源版 · Invest Wiki 65段产业链热力 + 驱动解读）",
    )
    text = text.replace(
        "大河财立方等当日收评",
        "大河财立方等当日收评；Google News RSS（驱动解释检索）",
    )
    text = text.replace(
        "> 注：Infoway 试用 key 已过期",
        "> 注：驱动解释由 Google News RSS 检索后人工筛选，按高/中/低置信标注；暂无明确公开原因的低置信条目不强行归因。原始来源记录在本次抓取数据中。Infoway 试用 key 已过期",
    )

    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
            start = i
            end = start + 2
            while end < len(lines) and lines[end].startswith("|"):
                end += 1
            header = [cell.strip() for cell in line.strip("|").split("|")]
            rows = [
                [cell.strip() for cell in x.strip("|").split("|")]
                for x in lines[start + 2:end]
            ]
            if header[:3] == ["方向", "行业", "当日涨跌"]:
                out.append(line)
                out.append(lines[i + 1])
                for row in rows:
                    entry = drivers.get("industry:" + row[1])
                    driver = entry["driver"] if entry else "暂无明确公开原因"
                    conf = entry["confidence"] if entry else "低"
                    row[-1] = f"{driver}（置信度：{conf}）"
                    out.append("| " + " | ".join(row) + " |")
                i = end
                continue
            if header[:2] == ["排名", "产业链段"]:
                out.append(line[:-1] + "| 驱动解读 |")
                out.append(lines[i + 1][:-1] + "| --- |")
                for row in rows:
                    key = next(
                        (entry_key for type_, entry_key, entry in
                         [(e["type"], e["key"], e) for e in drivers.values()]
                         if type_ == "segment" and entry["display"] == row[1]),
                        None,
                    )
                    entry = drivers.get("segment:" + key) if key else None
                    driver = entry["driver"] if entry else "暂无明确公开原因"
                    conf = entry["confidence"] if entry else "低"
                    out.append("| " + " | ".join(row + [f"{driver}（置信度：{conf}）"]) + " |")
                i = end
                continue
            if header[:1] == ["股票"]:
                out.append(line[:-1] + "| 驱动解读 |")
                out.append(lines[i + 1][:-1] + "| --- |")
                for row in rows:
                    ticker = re.search(r"（([^）]+)）", row[0])
                    key = ticker.group(1) if ticker else row[0]
                    entry = drivers.get("anomaly:" + key)
                    driver = entry["driver"] if entry else "暂无明确公开原因"
                    conf = entry["confidence"] if entry else "低"
                    out.append("| " + " | ".join(row + [f"{driver}（置信度：{conf}）"]) + " |")
                i = end
                continue
        out.append(line)
        i += 1
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--drivers", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    drivers = load_drivers(args.drivers)
    text = render(args.base.read_text(encoding="utf-8"), drivers)
    args.out.write_text(text, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
