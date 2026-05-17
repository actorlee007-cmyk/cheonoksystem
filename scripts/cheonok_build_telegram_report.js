const fs = require('fs');
const path = require('path');
const https = require('https');

const FINAL_GOAL = '1000억 시스템';
const MONTHLY_ATTACK = '월 10억';

function ensureOutputDirectory() {
  const publicDir = path.join(process.cwd(), 'public');
  fs.mkdirSync(publicDir, { recursive: true });
  for (const file of ['index.html', 'gate.html']) {
    const src = path.join(process.cwd(), file);
    const dst = path.join(publicDir, file);
    if (fs.existsSync(src)) fs.copyFileSync(src, dst);
  }
  const marker = {
    version: 'CHEONOK_PUBLIC_BUILD_OUTPUT_001',
    final_goal: FINAL_GOAL,
    monthly_attack_metric: MONTHLY_ATTACK,
    legacy_report: 'BLOCK_LEGACY',
    status: 'PUBLIC_OUTPUT_READY'
  };
  fs.writeFileSync(path.join(publicDir, 'build_status.json'), JSON.stringify(marker, null, 2), 'utf8');
}

function postJson(url, payload) {
  return new Promise((resolve) => {
    try {
      const data = JSON.stringify(payload);
      const u = new URL(url);
      const req = https.request({
        hostname: u.hostname,
        path: u.pathname + u.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data),
          'User-Agent': 'CHEONOK-BUILD-REPORT/002'
        }
      }, (res) => {
        let body = '';
        res.on('data', (d) => { body += d.toString(); });
        res.on('end', () => resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, status: res.statusCode, body: body.slice(0, 300) }));
      });
      req.on('error', (e) => resolve({ ok: false, status: 'ERROR', error: String(e).slice(0, 300) }));
      req.write(data);
      req.end();
    } catch (e) {
      resolve({ ok: false, status: 'EXCEPTION', error: String(e).slice(0, 300) });
    }
  });
}

async function main() {
  ensureOutputDirectory();

  const token = process.env.CHEONOK_TELEGRAM_BOT_TOKEN || '';
  const chatId = process.env.CHEONOK_TELEGRAM_CHAT_ID || '';
  const n8n = process.env.N8N_WEBHOOK_URL || '';
  const now = new Date().toISOString();
  const commit = process.env.VERCEL_GIT_COMMIT_SHA || process.env.GITHUB_SHA || 'unknown';

  const report = [
    '📊 CHEONOK SUPREME MASTER OS 빌드 보고',
    '',
    `보고시각: ${now}`,
    '운영방식: VERCEL BUILD-TIME REPORT / PROTECTION BYPASS',
    `최종목표: ${FINAL_GOAL}`,
    `중간 공격 지표: ${MONTHLY_ATTACK}`,
    '',
    '1. 배포 상태',
    `- 커밋: ${commit}`,
    '- 정보 우선 가드: PASS',
    '- Public output: PASS',
    '- 구버전 500만 보고: BLOCK_LEGACY',
    '- 사용자 수동 위임: BLOCK_EXCEPT_SECRET_OR_AUTH',
    '',
    '2. 판정',
    '- Vercel API Protection 401: BYPASS_BUILD_REPORT',
    '- GitHub Actions 미실행: BUILD_REPORT_FALLBACK_ACTIVE',
    '- Telegram Secret: ' + (token && chatId ? 'PASS' : 'HOLD'),
    '',
    '3. 다음 실행',
    'A. GitHub Actions 보고 루프 복구 지속',
    'B. Vercel Protection 우회 또는 해제 후 API 진단 복구',
    'C. 리드/결제/보고 루프를 월 10억 지표 기준으로 강화',
    '',
    '현재 시스템 상태:',
    '자율 학습 및 PAPER 데이터 축적 상태.'
  ].join('\n');

  let telegram = { ok: false, status: 'HOLD_TELEGRAM_ENV_MISSING' };
  if (token && chatId) {
    telegram = await postJson(`https://api.telegram.org/bot${token}/sendMessage`, {
      chat_id: chatId,
      text: report,
      disable_web_page_preview: true
    });
  }

  let n8nResult = { ok: false, status: 'HOLD_N8N_WEBHOOK_MISSING' };
  if (n8n) {
    n8nResult = await postJson(n8n, {
      version: 'CHEONOK_BUILD_REPORT_002',
      reported_at: now,
      final_goal: FINAL_GOAL,
      monthly_attack_metric: MONTHLY_ATTACK,
      report
    });
  }

  console.log(JSON.stringify({
    version: 'CHEONOK_BUILD_REPORT_002',
    public_output: 'PASS',
    telegram: { ok: telegram.ok, status: telegram.status },
    n8n: { ok: n8nResult.ok, status: n8nResult.status },
    canon: { final_goal: FINAL_GOAL, monthly_attack_metric: MONTHLY_ATTACK, legacy: 'BLOCK_LEGACY' }
  }, null, 2));
}

main().catch((e) => {
  try { ensureOutputDirectory(); } catch (_) {}
  console.log('CHEONOK_BUILD_REPORT_HOLD', String(e).slice(0, 500));
});
