---
id: pattern-001
category: api
language: unknown
score: 50
tags: [api]
---

## 컨텍스트
파일: sector-analysis.html (Edit 완료)

## 핵심 코드
```unknown
// Init on load — ensure DOM rendered and echarts loaded
function safeInit(fn, id) {
  var el = document.getElementById(id);
  if (!el || el.offsetWidth === 0) { setTimeout(function() { safeInit(fn, id); }, 100); return; }
  fn();
}
setTimeout(function() {
  if (typeof echarts === 'undefined') { setTimeout(arguments.callee, 100); return; }
  safeInit(initRadar, 'radar-sector');
  safeInit(initKline, 'chart-kline');
  safeInit(initCapital, 'chart-capital');
  safeInit(initValueChain, 'chart-value-chain');
  safeInit(initMarketShare, 'chart-market-share');
}, 200);
```

## 태그
- api