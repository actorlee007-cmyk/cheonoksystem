export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'METHOD_NOT_ALLOWED' });
  }

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    const payload = {
      version: 'CHEONOK_LEAD_API_001',
      received_at: new Date().toISOString(),
      source: body.source || 'cheonoksystem.com',
      type: body.type || 'lead',
      name: body.name || '',
      email: body.email || '',
      contact: body.contact || '',
      country: body.country || '',
      product: body.product || '',
      price: body.price || 0,
      question: body.question || body.message || body.need || '',
      raw: body,
      canon: {
        final_goal: '1000억 시스템',
        monthly_attack_metric: '월 10억',
        revenue_zero: 'CRITICAL',
        hold: 'SAFE_BYPASS',
        spam: 'BLOCK'
      }
    };

    const results = [];

    if (process.env.N8N_WEBHOOK_URL) {
      try {
        const r = await fetch(process.env.N8N_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        results.push({ target: 'n8n', status: r.ok ? 'PASS' : 'HOLD', code: r.status });
      } catch (e) {
        results.push({ target: 'n8n', status: 'HOLD_N8N_FAILED', error: String(e).slice(0, 300) });
      }
    } else {
      results.push({ target: 'n8n', status: 'HOLD_N8N_WEBHOOK_MISSING' });
    }

    if (process.env.CHEONOK_TELEGRAM_BOT_TOKEN && process.env.CHEONOK_TELEGRAM_CHAT_ID) {
      const text = [
        '📩 CHEONOK 신규 리드/결제요청',
        '',
        `유형: ${payload.type}`,
        `이름: ${payload.name || '-'}`,
        `연락처: ${payload.contact || payload.email || '-'}`,
        `국가: ${payload.country || '-'}`,
        `상품: ${payload.product || '-'}`,
        `가격: ${payload.price || 0}`,
        '',
        '내용:',
        payload.question || '-',
        '',
        '판정: PASS_LEAD_CAPTURED / 1000억 시스템 실행 큐 반영'
      ].join('\n');

      try {
        const tg = await fetch(`https://api.telegram.org/bot${process.env.CHEONOK_TELEGRAM_BOT_TOKEN}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: process.env.CHEONOK_TELEGRAM_CHAT_ID,
            text,
            disable_web_page_preview: true
          })
        });
        results.push({ target: 'telegram', status: tg.ok ? 'PASS' : 'HOLD', code: tg.status });
      } catch (e) {
        results.push({ target: 'telegram', status: 'HOLD_TELEGRAM_FAILED', error: String(e).slice(0, 300) });
      }
    } else {
      results.push({ target: 'telegram', status: 'HOLD_TELEGRAM_SECRETS_MISSING' });
    }

    return res.status(200).json({ ok: true, status: 'PASS_LEAD_CAPTURED', payload, results });
  } catch (e) {
    return res.status(500).json({ ok: false, status: 'HOLD_LEAD_API_ERROR', error: String(e).slice(0, 500) });
  }
}
