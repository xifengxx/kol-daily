#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 AI 日报：逐字断言 + 覆盖率 + 字数。

用法：
  python3 scripts/validate_aihot_report.py \
      --report reports/ai/2026-09-17.md \
      --snapshot data/aihot_daily_2026-09-17.json

为什么需要它
------------
渲染脚本已经保证了「源站摘要逐字复制」。但报告写出后，agent 仍可能出于
「只是润色一下」的自我合理化去 Edit 报告文件——那样「原文摘要」四个字就
不再成立，而这正是项目一贯防的「编造」。

所以这里做**反向断言**：报告里出现的每一段源站摘要，必须能在快照里找到
完全一致的字符串。这道校验能抓出任何事后改写。
"""

import argparse
import json
import re
import sys
from pathlib import Path

MIN_LEN = 60
MAX_LEN = 200

CONF_SUFFIX = re.compile(r"（置信度：[^）]*）\s*$")


def die(msg):
    print(f"[校验未通过] {msg}", file=sys.stderr)
    sys.exit(1)


def parse_report(md):
    """抽出每条：标题 / 源站摘要 / 我的点评。"""
    items, cur, sections = [], None, 0
    for line in md.splitlines():
        if line.startswith("## "):
            sections += 1
        elif line.startswith("### "):
            if cur:
                items.append(cur)
            cur = {"title": line[4:].strip(), "summary": None, "comment": None}
        elif cur is not None:
            if line.startswith("**源站摘要**："):
                cur["summary"] = line[len("**源站摘要**："):].strip()
            elif line.startswith("**我的点评**："):
                raw = line[len("**我的点评**："):].strip()
                cur["comment"] = CONF_SUFFIX.sub("", raw).strip()
    if cur:
        items.append(cur)
    return items, sections


def main():
    ap = argparse.ArgumentParser(description="校验 AI 日报")
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--snapshot", required=True, type=Path)
    args = ap.parse_args()

    if not args.report.exists():
        die(f"报告不存在：{args.report}")
    if not args.snapshot.exists():
        die(f"快照不存在：{args.snapshot}")

    md = args.report.read_text(encoding="utf-8")
    snap = json.loads(args.snapshot.read_text(encoding="utf-8"))
    module = snap["modules"]["aihot_daily"]
    data = module["data"]

    if module["status"] != "ok":
        die(f"快照 status={module['status']}，不应据此发布报告")

    items, sections = parse_report(md)
    expected = [it for sec in data["sections"] for it in sec["items"]]

    print(f"报告 {args.report.name}：{sections} 个 ## 章节 / {len(items)} 条；"
          f"快照：{data['section_count']} 章节 / {data['item_count']} 条")

    # ① 逐字断言：报告里的摘要序列必须与快照完全一致（含顺序）
    exp_summaries = [it["summary"] for it in expected]
    got_summaries = [it["summary"] for it in items]
    if len(got_summaries) != len(exp_summaries):
        die(f"条目数不一致：报告 {len(got_summaries)} 条，快照 {len(exp_summaries)} 条")
    for i, (a, b) in enumerate(zip(got_summaries, exp_summaries)):
        if a != b:
            die(f"第 {i + 1} 条「源站摘要」与快照不一致（被改写过）\n"
                f"  报告：{a[:80]}\n  快照：{b[:80]}")

    # ② 覆盖率：每条都要有点评，且不能为空
    for i, it in enumerate(items, 1):
        if not it["comment"]:
            die(f"第 {i} 条缺「我的点评」：{it['title'][:40]}")

    # ③ 字数区间
    bad = [(i, len(it["comment"]), it["title"][:30])
           for i, it in enumerate(items, 1)
           if not (MIN_LEN <= len(it["comment"]) <= MAX_LEN)]
    if bad:
        detail = "\n".join(f"  第 {i} 条 {n} 字：{t}" for i, n, t in bad)
        die(f"点评字数越界（要求 {MIN_LEN}-{MAX_LEN}）：\n{detail}")

    # ④ 章节数
    # 报告里的 ## 含「今日一句话」与「数据来源」两个非源站章节
    expect_sections = data["section_count"] + 2
    if sections != expect_sections:
        die(f"章节数不符：报告 {sections}，预期 {expect_sections}"
            f"（源站 {data['section_count']} + 今日一句话 + 数据来源）")

    # ⑤ 来源章节必须存在且带 AIHOT 后缀（前端据此归类）
    if "## 数据来源与口径说明（AIHOT）" not in md:
        die("缺少「## 数据来源与口径说明（AIHOT）」章节——前端将无法正确归类")

    lens = [len(it["comment"]) for it in items]
    print(f"  ✅ 逐字一致 {len(items)}/{len(items)}")
    print(f"  ✅ 点评完整，字数 {min(lens)}–{max(lens)} 字（区间 {MIN_LEN}-{MAX_LEN}）")
    print(f"  ✅ 章节 {sections} 个、来源章节齐备")
    print("校验通过")


if __name__ == "__main__":
    main()
