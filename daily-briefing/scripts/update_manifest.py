#!/usr/bin/env python3
"""安全更新简报 manifest（us / cn / ai 三类）。

【为什么需要它】
manifest 的更新原本由跑批 agent 直接手改 JSON，而本项目的 manifest 有**两份副本**：
本地 `daily-briefing/manifest.json` 与发布仓库 `kol-daily/daily-briefing/manifest.json`。
两份会各自漂移，只要某一轮跑批拿**过期的那份**当底本重写，就会把另一个任务刚写进去的
条目静默删掉——而 JSON 不会报错，报告文件也还在，只有站点索引悄悄少了它。

2026-10-08 已踩：`1de73c2`（AI 日报 10-08）删掉了 `2220300`（美股第32期）刚加入
`us` 数组的 `2026-10-08-industry-chain-invest-wiki-drivers`，导致该期报告虽已发布、
站点索引里却没有它。提交信息只声称「ai 数组最前插入」，完全看不出删了别人的条目。

【做法】
两份都读 → 取**并集** → 插入/更新新条目 → **两份写回同一内容**。
于是任何一棵树的旧底本都不再可能抹掉另一棵树的新条目，顺带把两棵树的漂移治好。
最后还有一道断言：若合并结果比某一份原本的条目更少，直接报错退出，绝不静默丢条目。

【用法】
    python3 daily-briefing/scripts/update_manifest.py \\
        --cat us \\
        --id 2026-10-08-industry-chain-invest-wiki-drivers \\
        --title "美股 · Invest Wiki 65段产业链热力+驱动解读（周四）"

加 --dry-run 只看结果不落盘。
"""

import argparse
import json
import sys
from pathlib import Path

CATS = ("us", "cn", "ai")


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def dump(path: Path, doc: dict, dry: bool) -> None:
    # 与既有文件保持逐字节一致的格式：2 空格缩进、不转义中文、结尾一个换行
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if dry:
        return
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", required=True, choices=CATS, help="品类：us / cn / ai")
    ap.add_argument("--id", required=True, dest="new_id", help="条目 id（美股为 slug，其他为日期）")
    ap.add_argument("--title", required=True, help="列表里显示的标题")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    here = Path(__file__).resolve()
    daily_dir = here.parent.parent                      # .../daily-briefing
    root = daily_dir.parent                             # 项目根

    candidates = [
        ("本地", daily_dir / "manifest.json"),
        ("发布仓库", root / "kol-daily" / "daily-briefing" / "manifest.json"),
    ]
    targets = [(name, p) for name, p in candidates if p.exists()]
    if not targets:
        print("✗ 找不到任何 manifest.json", file=sys.stderr)
        return 1

    docs = {name: load(p) for name, p in targets}

    # ---- 并集：保持「先出现者优先」的顺序（各文件都是新→旧）----
    ids: list[str] = []
    seen: set[str] = set()
    for name, _ in targets:
        for x in docs[name].get(args.cat) or []:
            if x not in seen:
                seen.add(x)
                ids.append(x)

    # 各份之间缺了哪些条目（漂移），报告出来
    per_file = {name: set(docs[name].get(args.cat) or []) for name, _ in targets}
    union = set(ids)
    for name, _ in targets:
        missing = union - per_file[name]
        if missing:
            print(f"· {name} 少了 {len(missing)} 条，本次一并用并集补回：{sorted(missing)}")

    existed = args.new_id in union
    if existed:
        ids.remove(args.new_id)
    ids.insert(0, args.new_id)

    # ---- 标题：沿用各家已有标题，新条目置顶 ----
    merged_titles: dict[str, str] = {}
    for name, _ in targets:
        for k, v in (docs[name].get(args.cat + "_title") or {}).items():
            merged_titles.setdefault(k, v)
    merged_titles[args.new_id] = args.title

    no_title = [x for x in ids if x not in merged_titles]

    # ---- 落盘（两份同内容）----
    for name, path in targets:
        doc = docs[name]
        before = set(doc.get(args.cat) or [])
        doc[args.cat] = list(ids)
        lost = before - set(ids)
        if lost:
            print(f"✗ {name}：合并结果丢了原文件里的条目 {sorted(lost)}，拒绝写入", file=sys.stderr)
            return 1
        # 新条目的标题插到最前，让标题映射的顺序与 id 列表一致
        rest = {k: v for k, v in merged_titles.items() if k != args.new_id}
        doc[args.cat + "_title"] = {args.new_id: args.title, **rest}
        dump(path, doc, args.dry_run)
        print(f"· {name}：{args.cat} 现有 {len(ids)} 条，首条 {ids[0]}（{'已更新' if existed else '新增'}）")

    if no_title:
        print(f"⚠ 以下条目没有标题映射（站点可能显示为空）：{no_title}", file=sys.stderr)

    print(f"{'[dry-run] ' if args.dry_run else ''}✅ {args.cat} manifest 更新完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
