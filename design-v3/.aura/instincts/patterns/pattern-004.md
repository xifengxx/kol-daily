---
id: pattern-004
category: db
language: unknown
score: 50
tags: [db]
---

## 컨텍스트
파일: theme-index.html (Write 완료)

## 핵심 코드
```unknown
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>题材指数 — 5Factor AI</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<script>(function(){if(window.self!==window.top)document.documentElement.classList.add('iframe-embed');})();</script>
<style>
:root {
  --bg: #F5F5F7; --card: #FFFFFF; --border: #E5E5EA;
  --text: #1D1D1F; --text2: #86868B; --accent: #0071E3; --navy: #1D1D1F;
  --up: #FF3B30; --down: #34C759;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.5;
}
html.iframe-embed body { padding: 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }

/* Header */
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 700; color: var(--navy); letter-spacing: -0.02em; }
.page-header p { font-size: 14px; color: var(--text2); margin-top: 4px; }

/* Stat row */
.stat-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 24px; }
.stat-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.stat-card .stat-value { font-size: 24px; font-weight: 700; }
.stat-card .stat-label { font-size: 11px; color: var(--text2); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.03em; }

/* Search + filter */
.filter-bar { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }
.filter-bar input { flex: 1; max-width: 320px; padding: 9px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; background: var(--card); outline: none; font-family: inherit; }
.filter-bar input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(0,113,227,0.12); }
.filter-bar input::placeholder { color: #C7C7CC; }
.filter-chip { padding: 6px 14px; border-radius: 16px; font-size: 12px; font-weight: 500; cursor: pointer; border: 1px solid var(--border); background: var(--card); color: var(--text2); transition: all 0.15s; white-space: nowrap; }
.filter-chip:hover { border-color: var(--accent); color: var(--accent); }
.filter-chip.active { background: var(--accent); color: #fff; border-color: var(--accent); }

/* Theme grid */
.theme-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.theme-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; cursor: pointer; transition: all 0.25s ease; }
.theme-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.08); transform: translateY(-2px); border-color: var(--accent); }
.theme-card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; }
.theme-card-name { font-size: 16px; font-weight: 600; color: var(--text); }
.theme-card-desc { font-size: 12px; color: var(--text2); line-height: 1.6; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
```

## 태그
- db