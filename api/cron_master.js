const FINAL_GOAL_KRW = 100000000000;
const MONTHLY_ATTACK_KRW = 1000000000;

function won(n) {
  return '₩' + Number(n || 0).toLocaleString('ko-KR');
}

function envNumber(name) {
  const value = Number(process.env[name] || 0);
  return Number.isFinite(value) ? value : 0;
}

async function sendTelegram(text) {
  const token = process.env.CHEONOK_TELEGRAM_BOT_TOKEN;
  const chatId = process.env.CHEONOK_TELEGRAM_CHAT_ID;
  if (!token || !chatId) {
    return { ok: false, status: 'HOLD_TELEGRAM_SECRETS_MISSING' };
  }

  const chunks = [];
  for (let i = 0; i < text.length; i += 3500) chunks.push(text.slice(i, i + 3500));
  const results = [];
  for (const chunk of chunks) {
    const r = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text: chunk, disable_web_page_preview: true })
    });
    results.push({ ok: r.ok, status: r.status, body: await r.text().catch(() => '') });
  }
  return { ok: results.every(x => x.ok), status: results.every(x => x.ok) ? 'PASS_TELEGRAM_SENT' : 'HOLD_TELEGRAM_FAILED', results };
}

async function postN8n(payload) {
  const webhook = process.env.N8N_WEBHOOK_URL;
  if (!webhook) return { ok: false, status: 'HOLD_N8N_WEBHOOK_MISSING' };
  try {
    const r = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return { ok: r.ok, status: r.status };
  } catch (e) {
    return { ok: false, status: 'HOLD_N8N_POST_FAILED', error: String(e).slice(0, 300) };
  }
}

export default async function handler(req, res) {
  const now = new Date();
  const revenue = envNumber('CHEONOK_MANUAL_REVENUE');
  const leads = envNumber('CHEONOK_MANUAL_LEADS');
  const checkout = envNumber('CHEONOK_MANUAL_CHECKOUT');
  const highTicket = envNumber('CHEONOK_MANUAL_HIGH_TICKET');
  const reverseCases = envNumber('CHEONOK_REVERSE_CASES');
  const globalTests = envNumber('CHEONOK_GLOBAL_TESTS');
  const contentPublished = envNumber('CHEONOK_CONTENT_PUBLISHED');
  const monthlyGap = Math.max(MONTHLY_ATTACK_KRW - revenue, 0);
  const finalGap = Math.max(FINAL_GOAL_KRW - revenue, 0);

  const report = [
    '📊 CHEONOK SUPREME MASTER OS 보고',
    '',
    `보고시각: ${now.toISOString()}`,
    '운영방식: VERCEL CRON MASTER / PC OFF SAFE',
    '최종목표: 1000억 시스템',
    '중간 공격 지표: 월 10억',
    '',
    '1. 현재 매출 상태',
    `- 리드: ${leads}`,
    `- 결제요청: ${checkout}`,
    `- 고액제안: ${highTicket}`,
    `- 매출: ${won(revenue)}`,
    `- 월 10억 부족분: ${won(monthlyGap)}`,
    `- 1000억 부족분: ${won(finalGap)}`,
    '',
    '2. 판정',
    `- 매출 0: ${revenue <= 0 ? 'CRITICAL' : 'PASS'}`,
    `- 리드 0: ${leads <= 0 ? 'CRITICAL' : 'PASS'}`,
    `- 결제요청 0: ${checkout <= 0 ? 'CRITICAL' : 'PASS'}`,
    `- 고액제안 0: ${highTicket <= 0 ? 'HOLD_TO_ACTION' : 'PASS'}`,
    '- 구버전 500만 보고: BLOCK_LEGACY',
    '- 무단 자동결제/스팸: BLOCK',
    '',
    '3. 자율 실행 큐',
    `- 돈 번 사례 역추적: ${reverseCases}`,
    `- 글로벌 테스트: ${globalTests}`,
    `- 콘텐츠 발행: ${contentPublished}`,
    '',
    '4. 다음 1시간 실행',
    'A. 저마찰 리드 10건 또는 결제요청 1건',
    'B. 300만 원 AI 매출 시스템 진단 제안 1건',
    'C. JoCoding/TikTok/Shorts 도구 1개를 상품·결제·보고 루프로 변환',
    'D. 10개국 광고 소재 후보 생성',
    '',
    '현재 시스템 상태:',
    '자율 학습 및 PAPER 데이터 축적 상태.'
  ].join('\n');

  const payload = {
    version: 'CHEONOK_VERCEL_CRON_MASTER_001',
    reported_at: now.toISOString(),
    final_goal_krw: FINAL_GOAL_KRW,
    monthly_attack_krw: MONTHLY_ATTACK_KRW,
    metrics: { revenue, leads, checkout, highTicket, reverseCases, globalTests, contentPublished, monthlyGap, finalGap },
    report
  };

  const telegram = await sendTelegram(report);
  const n8n = await postN8n(payload);

  return res.status(200).json({ ok: true, status: 'PASS_CRON_MASTER_EXECUTED', telegram, n8n, payload });
}
