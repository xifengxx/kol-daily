#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由「AIHOT 快照 + 点评 JSON」渲染 AI 日报。

用法：
  python3 scripts/render_aihot_report.py \
      --snapshot data/aihot_daily_2026-09-17.json \
      --comments data/_aihot_comments_2026-09-17.json \
      --out reports/ai/<日期>.md

分工（这是本脚本存在的唯一理由）
--------------------------------
- **源站摘要由脚本从快照逐字复制**，agent 没有改写的机会；
- **点评由 agent 写在 comments JSON 里**，脚本只负责注入。

模型誊抄做不到逐字保真，而「原文摘要」这四个字只有在真的逐字时才成立。
这与项目既有的 render_drivers_report.py 是同一个模式。

硬校验（任一不过 → 非零退出、不写文件）
----------------------------------------
1. 快照 status 必须是 ok（not_found / stale 一律拒绝渲染）
2. comments 里出现快照中不存在的 item_id → 报错（防「下标位移导致点评错位」）
3. 快照中每个条目都必须有点评 → 报错（缺哪条报哪条）
4. 每条点评长度必须在 [MIN_LEN, MAX_LEN]
5. angle 必须在枚举内
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


# 每条点评的字数区间。下限是「信息量约束」而非「凑字约束」——
# 目的是机器可判定地排除「值得关注」「有待观察」这类空话。
MIN_LEN = 60
MAX_LEN = 200

# 点评角度枚举。章节名只作默认值：源站的「技巧与观点」一个章节里
# 同时装着教程（tutorial）和观点（opinion），必须逐条判断。
ANGLES = {
    "model": "模型类",
    "product": "产品类",
    "industry": "行业类",
    "paper": "论文类",
    "tutorial": "教程类",
    "opinion": "观点类",
}

# 首期日期：报告编号 = (报告日期 − 首期日期).days + 1
# 按日历推算而非数文件——AI 日报是唯一 7 天连续的品类，日期语义更准确，
# 且源站故障缺一天时编号仍然连续。
FIRST_ISSUE = datetime.date(2026, 9, 17)

WEEKDAY_CN = "一二三四五六日"


def die(msg, code=2):
    print(f"[渲染中止] {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path, what):
    p = Path(path)
    if not p.exists():
        die(f"{what}不存在：{p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"{what}解析失败：{exc}")


def resolve_number(date_str):
    """报告编号 = 距首期的日历天数 + 1。"""
    d = datetime.date.fromisoformat(date_str)
    return (d - FIRST_ISSUE).days + 1


def check_comments(snapshot_data, comments):
    """渲染前把所有硬约束检查完，避免写出半成品。"""
    items = {}
    for sec in snapshot_data["sections"]:
        for it in sec["items"]:
            items[it["item_id"]] = it

    cmts = comments.get("comments") or {}

    unknown = sorted(set(cmts) - set(items))
    if unknown:
        die("点评里出现快照中不存在的 item_id（很可能发生了条目位移）：\n  "
            + "\n  ".join(unknown))

    missing = [i for i in items if i not in cmts]
    if missing:
        die(f"有 {len(missing)} 条没有点评，缺：\n  " + "\n  ".join(missing))

    for item_id, c in cmts.items():
        text = (c.get("comment") or "").strip()
        n = len(text)
        if n < MIN_LEN or n > MAX_LEN:
            die(f"点评长度越界（{n} 字，要求 {MIN_LEN}-{MAX_LEN}）：{items[item_id]['title'][:30]}")
        angle = c.get("angle")
        if angle not in ANGLES:
            die(f"angle 非法（{angle!r}，应为 {sorted(ANGLES)}）：{items[item_id]['title'][:30]}")

    overview = (comments.get("overview") or {}).get("text", "").strip()
    if not overview:
        die("缺少 overview.text（今日一句话）")


def to_beijing(iso):
    """把源站的 UTC ISO 串转成北京时间可读格式。

    源站给的是 `2026-09-16T00:00:00.000Z` 这种原始串，直接贴进报告又长又难读，
    还会把头部元信息挤成三行。转成「09-16 08:00」既短又符合读者的时间直觉。
    """
    if not iso:
        return "—"
    try:
        s = iso.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        bj = dt.astimezone(ZoneInfo("Asia/Shanghai"))
        return bj.strftime("%m-%d %H:%M")
    except Exception:
        return str(iso)


def truncate(text, limit=72):
    """截断过长的来源名，尽量在自然边界断开。

    源站有些来源名很长（实测 50+ 字，形如「X：人名（头衔） (@handle)」），
    直接按字数硬切会把括号或 @handle 切成半个，看起来像坏了。
    """
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in (" ", "（", "(", "·", "・", "，", "：", ":"):
        pos = cut.rfind(sep)
        if pos > limit * 0.6:
            cut = cut[:pos]
            break
    return cut.rstrip("（(·・，：: ") + "…"


def render_item(index, item, comment):
    lines = [f"### {index}. {item['title']}", ""]
    # 逐字引用，不删改
    lines.append(f"**源站摘要**：{item['summary']}")
    lines.append("")
    lines.append(f"**我的点评**：{comment['comment'].strip()}"
                 f"（置信度：{comment.get('confidence', '中')}）")
    lines.append("")

    src = truncate(item.get("source_name") or "未标注来源")
    links = []
    if item.get("link_original"):
        links.append(f"[原始出处]({item['link_original']})")
    if item.get("link_aihot"):
        links.append(f"[AIHOT 条目]({item['link_aihot']})")
    lines.append(f"**来源**：{src}" + (" · " + " · ".join(links) if links else ""))
    lines.append("")
    return lines


def render(snapshot, comments):
    data = snapshot["modules"]["aihot_daily"]["data"]
    status = snapshot["modules"]["aihot_daily"]["status"]
    if status != "ok":
        die(f"快照 status={status}，拒绝渲染（{snapshot['modules']['aihot_daily'].get('detail') or ''}）。"
            "源站当日未发布时应当跳过本期，而不是拿别的日期充数。")

    date_str = data["report_date"]
    d = datetime.date.fromisoformat(date_str)
    number = resolve_number(date_str)
    cmts = comments["comments"]
    overview = comments["overview"]

    out = []
    out.append(f"# 🤖 AI 日报（AIHOT）")
    out.append("")
    out.append(f"**日期**：{date_str}（周{WEEKDAY_CN[d.weekday()]}）")
    out.append(f"**简报编号**：AI 日报第 {number} 期")
    out.append(f"**本期条目**：{data['section_count']} 个章节 / {data['item_count']} 条")
    out.append(f"**数据来源**：AIHOT（[aihot.news]({data.get('source_url') or 'https://aihot.news'})）"
               "当日 AI 日报；「源站摘要」栏逐字引用，未做改写")
    out.append(f"**覆盖窗口**：{to_beijing(data.get('window_start'))} → "
               f"{to_beijing(data.get('window_end'))}（北京时间）")
    out.append("")

    # 口径说明。lead / flashes 的实际情况来自防呆字段，不靠猜
    out.append("> **口径说明（先读）**")
    out.append("> 1. 「源站摘要」栏**逐字引用**源站字段，未删改一字；链接指向 AIHOT 条目页与原始出处。")
    out.append("> 2. 「我的点评」栏为**模型生成**，非源站内容；角度按条目类别自适应，附置信度。")
    out.append("> 3. **AIHOT 本身是对原始出处的二次摘要**——「源站摘要」已是二转手。"
               "要核实细节请点「原始出处」。")
    if data.get("lead_present"):
        out.append("> 4. 源站本期提供了导语 `lead`，下方「今日一句话」已参考；其余仍为本报告自撰。")
    else:
        out.append("> 4. 源站本期导语 `lead` 为空（该字段近期恒为空），「今日一句话」为本报告自撰。")
    if data.get("flashes_count"):
        out.append(f"> 5. 源站本期有 {data['flashes_count']} 条快讯（`flashes`），"
                   "本报告当前**未纳入**，需查阅源站。")
    out.append("")
    out.append("---")
    out.append("")

    out.append("## 〇、今日一句话（AI 圈核心洞察）")
    out.append("")
    out.append(overview["text"].strip()
               + f"（置信度：{overview.get('confidence', '中')}）")
    out.append("")
    out.append("---")
    out.append("")

    # 章节标题统一带（AIHOT）后缀：前端 classifySection 靠它识别本品类
    for si, sec in enumerate(data["sections"], 1):
        out.append(f"## {'〇一二三四五六七八九十'[si] if si <= 10 else si}、{sec['label']}（AIHOT）")
        out.append("")
        for ii, item in enumerate(sec["items"], 1):
            out.extend(render_item(ii, item, cmts[item["item_id"]]))
        out.append("---")
        out.append("")

    # 末尾来源章节：标题必须以「数据来源」开头，前端据此归入 source 分类、不进目录
    out.append("## 数据来源与口径说明（AIHOT）")
    out.append("")
    out.append(f"- **源站**：AIHOT（[aihot.news](https://aihot.news)）"
               f" · 当日日报：[{data.get('source_url') or ''}]({data.get('source_url') or ''})")
    out.append(f"- **覆盖窗口**：{to_beijing(data.get('window_start'))} → "
               f"{to_beijing(data.get('window_end'))}（北京时间）")
    out.append(f"- **源站生成时间**：{to_beijing(data.get('generated_at_source'))}（北京时间）")
    out.append(f"- **抽取字段**：`title` / `summary` / `source.name` / `links`；"
               f"schemaVersion={data.get('schema_version')}、章节 {data['section_count']} 个、"
               f"条目 {data['item_count']} 条")
    out.append("- **版权**：内容版权归各原始出处与 AIHOT 所有；本报告仅作个人阅读用途，"
               "不用于商业分发。")
    out.append("- **本报告生成方式**：源站摘要由脚本从快照逐字复制，点评由模型撰写，"
               "渲染脚本对长度与覆盖率做硬校验。")
    out.append("")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="渲染 AI 日报")
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--comments", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    snapshot = load_json(args.snapshot, "快照")
    comments = load_json(args.comments, "点评")

    if snapshot["modules"]["aihot_daily"]["status"] == "ok":
        check_comments(snapshot["modules"]["aihot_daily"]["data"], comments)

    text = render(snapshot, comments)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(str(args.out))


if __name__ == "__main__":
    main()
