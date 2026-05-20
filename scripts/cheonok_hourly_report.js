const fs = require('fs');
const path = require('path');

const now = new Date();
const stamp = now.toISOString().replace(/[:.]/g, '-');
const outDir = path.join(process.cwd(), 'reports', 'hourly');
fs.mkdirSync(outDir, { recursive: true });

const report = {
  generatedAt: now.toISOString(),
  mode: 'CHEONOK_HOURLY_CLOUD_CONTROL',
  safety: {
    PAPER_ONLY: true,
    LIVE_TRADE: 'BLOCKED',
    CAPITAL_SCALE: 'BLOCKED',
    KIS_ORDER_GATE: 'BLOCKED'
  },
  chain: {
    exposure: 'BUILDING',
    click: 'BLOCK',
    lead: 'BLOCK',
    payment: 'BUILDING',
    delivery: 'BUILDING',
    repeatPurchase: 'BLOCK'
  },
  billionaireCapitalGate: {
    highestPriority: 'AI Revenue System Diagnosis',
    fastest5MRoute: ['300000 KRW x 17', '1000000 KRW x 5', '3000000 KRW x 2'],
    nextCapitalAction: 'Publish one public CTA and capture the first lead.'
  },
  adaptiveRouter: {
    selectedLenses: ['billionaire', 'operator', 'programmer', 'sales', 'psychology', 'risk'],
    rule: 'Checklist is audit only; adaptive lens weighting is primary.'
  },
  nextEvidenceStandard: 'public CTA URL OR one lead OR one verified payment proof'
};

const md = `# CHEONOK Hourly Cloud Control Report\n\nGenerated: ${report.generatedAt}\n\n## Safety\n- PAPER_ONLY TRUE\n- LIVE_TRADE BLOCKED\n- CAPITAL_SCALE BLOCKED\n- KIS_ORDER_GATE BLOCKED\n\n## Revenue Chain\n- Exposure: ${report.chain.exposure}\n- Click: ${report.chain.click}\n- Lead: ${report.chain.lead}\n- Payment: ${report.chain.payment}\n- Delivery: ${report.chain.delivery}\n- Repeat Purchase: ${report.chain.repeatPurchase}\n\n## Billionaire Capital Gate\n- Priority: ${report.billionaireCapitalGate.highestPriority}\n- Fastest 5M: ${report.billionaireCapitalGate.fastest5MRoute.join(' / ')}\n- Next action: ${report.billionaireCapitalGate.nextCapitalAction}\n\n## Adaptive Router\n- Lenses: ${report.adaptiveRouter.selectedLenses.join(', ')}\n- Rule: ${report.adaptiveRouter.rule}\n\n## Next Evidence Standard\n${report.nextEvidenceStandard}\n`;

fs.writeFileSync(path.join(outDir, `CHEONOK_HOURLY_${stamp}.md`), md, 'utf8');
fs.writeFileSync(path.join(outDir, `CHEONOK_HOURLY_${stamp}.json`), JSON.stringify(report, null, 2), 'utf8');
console.log(md);
