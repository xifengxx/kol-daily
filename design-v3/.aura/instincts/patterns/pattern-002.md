---
id: pattern-002
category: deploy
language: unknown
score: 50
tags: [deploy]
---

## 컨텍스트
파일: sector-analysis.html (Edit 완료)

## 핵심 코드
```unknown
function initValueChain() {
  var dom = document.getElementById('chart-value-chain');
  if (!dom || dom.offsetWidth === 0) return;
  var existing = echarts.getInstanceByDom(dom);
  if (existing) existing.dispose();
  const chart = echarts.init(dom);
```

## 태그
- deploy