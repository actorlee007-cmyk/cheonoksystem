async function telegramProbe() {
  const token = process.env.CHEONOK_TELEGRAM_BOT_TOKEN;
  const chatId = process.env.CHEONOK_TELEGRAM_CHAT_ID;
  if (!token || !chatId) {
    return {
      ok: false,
      status: 'HOLD_TELEGRAM_SECRETS_MISSING',
      has_token: Boolean(token),
      has_chat_id: Boolean(chatId)
    };
  }

  try {
    const text = [
      '✅ CHEONOK MASTER DIAG TEST',
      '',
      '최종목표: 1000억 시스템',
      '중간 공격 지표: 월 10억',
      '텔레그램 환경변수: PASS',
      '구버전 500만 보고: BLOCK_LEGACY',
      '',
      '현재 시스템 상태:',
      '자율 학습 및 PAPER 데이터 축적 상태.'
    ].join('\n');

    const r = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text, disable_web_page_preview: true })
    });

    const body = await r.text().catch(() => '');
    return {
      ok: r.ok,
      status: r.ok ? 'PASS_TELEGRAM_SENT' : 'HOLD_TELEGRAM_API_FAILED',
      code: r.status,
      body: body.slice(0, 500)
    };
  } catch (e) {
    return { ok: false, status: 'HOLD_TELEGRAM_SEND_EXCEPTION', error: String(e).slice(0, 500) };
  }
}

async function n8nProbe(payload) {
  const webhook = process.env.N8N_WEBHOOK_URL;
  if (!webhook) return { ok: false, status: 'HOLD_N8N_WEBHOOK_MISSING', has_webhook: false };
  try {
    const r = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return { ok: r.ok, status: r.ok ? 'PASS_N8N_POSTED' : 'HOLD_N8N_FAILED', code: r.status };
  } catch (e) {
    return { ok: false, status: 'HOLD_N8N_EXCEPTION', error: String(e).slice(0, 500) };
  }
}

export default async function handler(req, res) {
  const now = new Date().toISOString();
  const payload = {
    version: 'CHEONOK_MASTER_DIAG_001',
    checked_at: now,
    final_goal: '1000억 시스템',
    monthly_attack_metric: '월 10억',
    legacy_5m_report: 'BLOCK_LEGACY',
    env_presence: {
      CHEONOK_TELEGRAM_BOT_TOKEN: Boolean(process.env.CHEONOK_TELEGRAM_BOT_TOKEN),
      CHEONOK_TELEGRAM_CHAT_ID: Boolean(process.env.CHEONOK_TELEGRAM_CHAT_ID),
      N8N_WEBHOOK_URL: Boolean(process.env.N8N_WEBHOOK_URL),
      CHEONOK_MANUAL_REVENUE: Boolean(process.env.CHEONOK_MANUAL_REVENUE),
      CHEONOK_MANUAL_LEADS: Boolean(process.env.CHEONOK_MANUAL_LEADS),
      CHEONOK_MANUAL_CHECKOUT: Boolean(process.env.CHEONOK_MANUAL_CHECKOUT),
      CHEONOK_MANUAL_HIGH_TICKET: Boolean(process.env.CHEONOK_MANUAL_HIGH_TICKET)
    },
    routes: {
      home: '/',
      lead: '/api/lead',
      os_status: '/api/os_status',
      cron_master: '/api/cron_master',
      master_diag: '/api/master_diag',
      pay: '/pay',
      consult: '/consult'
    }
  };

  const shouldSend = req.query.send === '1' || req.method === 'POST';
  let telegram = { ok: false, status: 'SKIP_ADD_SEND_1_TO_TEST' };
  let n8n = { ok: false, status: 'SKIP_ADD_SEND_1_TO_TEST' };

  if (shouldSend) {
    telegram = await telegramProbe();
    n8n = await n8nProbe(payload);
  }

  return res.status(200).json({ ok: true, status: 'PASS_MASTER_DIAG_READY', payload, telegram, n8n });
}
