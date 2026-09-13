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


def normalize_meta(text):
    """把标题/编号/来源/注标注为「+ 驱动解读」版本。

    全部正则匹配既有行，不依赖某一期的固定文案，重复渲染幂等。
    """
    if "驱动解读）" in text.split("\n", 1)[0]:
        return text
    text = re.sub(
        r"(# 🌅 美股日度复盘简报（晨间版)[^）]*(）)",
        r"\1 · Invest Wiki 产业链段热力 + 驱动解读\2",
        text, count=1,
    )
    text = re.sub(
        r"(\*\*简报编号\*\*：第 \d+ 期（)[^）]*(）)",
        r"\1数据源版 · Invest Wiki 产业链段热力 + 驱动解读\2",
        text, count=1,
    )
    if "Google News RSS" not in text:
        text = re.sub(
            r"(\*\*数据来源\*\*：[^\n]*)",
            r"\1；Google News RSS（驱动解释检索）",
            text, count=1,
        )
    if "驱动解释由 Google News RSS" not in text:
        text = re.sub(
            r"^(> 注：)",
            r"\1驱动解释由 Google News RSS 检索后人工筛选，按高/中/低置信标注，"
            "无明确公开原因的不强行归因；",
            text, count=1, flags=re.M,
        )
    return text


def render(text, drivers):
    text = normalize_meta(text)

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
                # 末列内容会被驱动解释替换，表头同步改名（替换整个末列，不是追加）
                header[-1] = "驱动解读"
                out.append("| " + " | ".join(header) + " |")
                sep = [c.strip() for c in lines[i + 1].strip("|").split("|")]
                sep[-1] = "---"
                out.append("| " + " | ".join(sep) + " |")
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
