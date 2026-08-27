#!/bin/bash
# 本地-only 模块同步：按 sync-config.json 的 local_modules 从本地源复制到 kol-daily 并推送 gh-pages。
# 用于源项目不在 GitHub 上的模块（daily-briefing 等）。GitHub 源模块走 GitHub Actions，勿用此脚本。
#
# 用法:
#   ./sync-local.sh            # 实际同步（复制 → git add → commit → push）
#   ./sync-local.sh --dry-run  # 只显示将同步什么，不提交
set -euo pipefail
cd "$(dirname "$0")"

DRY=""
[ "${1:-}" = "--dry-run" ] && DRY="-n"

python3 - "$DRY" <<'PYEOF'
import datetime
import json
import os
import subprocess
import sys

dry = sys.argv[1] == "-n"
config = json.load(open("sync-config.json", encoding="utf-8"))
repo = os.getcwd()
changed = []

for m in config.get("local_modules", []):
    name = m["name"]
    src = m["source_dir"]
    tgt = os.path.join(repo, m["target_dir"])
    excludes = m.get("exclude", [])
    print(f"[{name}] {src} -> {m['target_dir']}")
    if not os.path.isdir(src):
        print(f"  ⚠ 源目录不存在: {src}（跳过）")
        continue
    os.makedirs(tgt, exist_ok=True)

    args = ["rsync", "-a", "--checksum", "--itemize-changes"]
    if dry:
        args.append("-n")
    for e in excludes:
        args += ["--exclude", e]
    args += [os.path.join(src, ""), tgt.rstrip("/") + "/"]
    r = subprocess.run(args, capture_output=True)
    if r.returncode != 0:
        print(f"  ⚠ rsync 失败: {r.stderr.decode('utf-8', errors='replace').strip()}")
        continue
    out = r.stdout.decode("utf-8", errors="replace")
    lines = [l for l in out.splitlines() if l and not l.startswith(".")]
    if lines:
        changed.append(m["target_dir"])
        for l in lines[:6]:
            print(f"  {l}")
        if len(lines) > 6:
            print(f"  ... 共 {len(lines)} 项变更")
    else:
        print("  无变化")

if not changed:
    print("无变化，无需提交。")
    sys.exit(0)
if dry:
    print(f"（dry-run）以下模块有变化，未提交: {sorted(set(changed))}")
    sys.exit(0)

subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(
    ["git", "commit", "-m", f"sync: 本地模块同步 {len(changed)} 个 - {datetime.date.today().isoformat()}"],
    check=True,
)
subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
print(f"✓ 已提交并推送 {len(changed)} 个模块")
PYEOF
