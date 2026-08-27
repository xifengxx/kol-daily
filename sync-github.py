#!/usr/bin/env python3
"""GitHub 源模块自动同步（供 GitHub Actions 调用，也可本地运行）。

按 sync-config.json 的 github_modules 从公开仓库拉取最新文件，
有变化则提交并推送 gh-pages。零密钥：仅适用于公开仓库源。

用法:
  python3 sync-github.py            # 同步 + 提交 + 推送
  python3 sync-github.py --dry-run  # 只检查差异，不提交不推送
"""
import json
import os
import subprocess
import sys
import urllib.request
from urllib.parse import quote

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(REPO_ROOT, "sync-config.json"), encoding="utf-8") as f:
        return json.load(f)


def raw_url(repo, branch, path):
    """构建 raw.githubusercontent.com URL，路径分段做 UTF-8 百分号编码（支持中文目录）。"""
    quoted = "/".join(quote(seg) for seg in path.split("/"))
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{quoted}"


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kol-daily-sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def git(*args):
    subprocess.run(
        ["git", *args], check=True, cwd=REPO_ROOT, capture_output=True, text=True
    )


def main():
    dry_run = "--dry-run" in sys.argv
    config = load_config()
    modules = config.get("github_modules", [])
    changed = []

    for m in modules:
        target = os.path.join(REPO_ROOT, m["target"])
        url = raw_url(m["repo"], m["branch"], m["path"])
        print(f"[{m['name']}] {url}")
        try:
            content = download(url)
        except Exception as e:
            print(f"  ⚠ 下载失败: {e}（跳过）")
            continue
        if os.path.exists(target):
            with open(target, "rb") as f:
                if f.read() == content:
                    print("  无变化")
                    continue
        if not dry_run:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(content)
        print(f"  ✓ 有变化 -> {m['target']}")
        changed.append(m["target"])

    if not changed:
        print("全部模块无变化，无需提交。")
        return 0
    if dry_run:
        print(f"（dry-run）将更新 {len(changed)} 个文件，未提交。")
        return 0

    # GitHub Actions checkout 默认 detached HEAD，先回到 gh-pages 分支再提交
    try:
        git("checkout", "-B", "gh-pages", "origin/gh-pages")
    except subprocess.CalledProcessError:
        git("checkout", "-B", "gh-pages")

    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("add", "--", *changed)
    git("commit", "-m", "sync: 自动更新模块数据 " + __import__("datetime").date.today().isoformat())
    git("push", "origin", "gh-pages")
    print(f"✓ 已提交并推送 {len(changed)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
