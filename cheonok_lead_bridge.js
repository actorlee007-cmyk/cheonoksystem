/* CHEONOK Lead Bridge 001
   Purpose: route homepage fortune/subscription/consulting events through /api/lead
   Canon: 1000억 시스템 / 월 10억 중간 공격지표 / revenue 0 = CRITICAL
*/
(function () {
  const API = '/api/lead';

  async function sendLead(payload) {
    const body = {
      source: 'cheonoksystem.com/homepage',
      received_from: location.href,
      final_goal: '1000억 시스템',
      monthly_attack_metric: '월 10억',
      ...payload
    };

    try {
      const r = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await r.json().catch(() => ({}));
      console.log('[CHEONOK_LEAD_BRIDGE]', data);
      return { ok: r.ok, data };
    } catch (e) {
      console.warn('[CHEONOK_LEAD_BRIDGE_HOLD]', e);
      return { ok: false, error: String(e) };
    }
  }

  function getLang() {
    return document.documentElement.getAttribute('data-lang') || 'ko';
  }

  function patchSubscribe() {
    const original = window.doSubscribe;
    window.doSubscribe = async function () {
      const emailEl = document.getElementById('subEmail');
      const msg = document.getElementById('subMsg');
      const email = emailEl ? emailEl.value.trim() : '';

      if (!email || !email.includes('@')) {
        alert('올바른 이메일을 입력해주세요');
        return;
      }

      const result = await sendLead({
        type: 'subscription_lead',
        email,
        contact: email,
        country: getLang().toUpperCase(),
        product: 'Daily Fortune + AI Tips Free Subscribe',
        price: 0,
        question: '무료 구독 신청 / 매일 운세 + AI 자동화 팁'
      });

      if (msg) {
        msg.style.display = 'block';
        msg.textContent = result.ok
          ? '✅ 구독 접수 완료. CHEONOK 시스템에 리드가 기록되었습니다.'
          : '✅ 구독 접수 완료. 네트워크 연결은 HOLD 상태로 기록됩니다.';
      }
      if (emailEl) emailEl.value = '';

      if (typeof original === 'function') {
        try { original.__cheonok_wrapped || original(); } catch (e) {}
      }
    };
    window.doSubscribe.__cheonok_patched = true;
  }

  function patchSaju() {
    const original = window.analyzeSaju;
    window.analyzeSaju = async function () {
      if (typeof original === 'function') {
        try { original(); } catch (e) { console.warn('[CHEONOK_ORIGINAL_SAJU_HOLD]', e); }
      }

      const date = document.getElementById('sajuDate')?.value || '';
      const time = document.getElementById('sajuTime')?.value || '';
      if (!date) return;

      await sendLead({
        type: 'fortune_analysis_lead',
        country: getLang().toUpperCase(),
        product: 'AI 운세·타로 미니 리포트',
        price: 9900,
        question: `무료 사주 분석 실행: birth=${date}, time=${time || 'unknown'}`
      });
    };
    window.analyzeSaju.__cheonok_patched = true;
  }

  function addConsultBridge() {
    document.querySelectorAll('a[href^="mailto:"]').forEach((a) => {
      if (a.dataset.cheonokBridge) return;
      a.dataset.cheonokBridge = '1';
      a.addEventListener('click', () => {
        sendLead({
          type: 'consulting_click',
          contact: a.getAttribute('href').replace('mailto:', ''),
          country: getLang().toUpperCase(),
          product: 'AI 매출 시스템 진단 프로젝트',
          price: 3000000,
          question: '컨설팅 문의 CTA 클릭'
        });
      });
    });
  }

  function addRevenueWidget() {
    if (document.getElementById('cheonokRevenueWidget')) return;
    const box = document.createElement('div');
    box.id = 'cheonokRevenueWidget';
    box.style.cssText = 'position:fixed;right:18px;bottom:18px;z-index:9999;background:rgba(5,8,15,.94);border:1px solid rgba(212,175,55,.35);color:#f0ead6;border-radius:16px;padding:14px 14px 12px;max-width:310px;box-shadow:0 18px 50px rgba(0,0,0,.35);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;';
    box.innerHTML = `
      <div style="font-size:12px;color:#d4af37;font-weight:800;margin-bottom:6px;">CHEONOK 1000억 OS</div>
      <div style="font-size:13px;line-height:1.55;color:#f0ead6;">매출 0은 CRITICAL. 지금 리드·결제요청·고액상담으로 연결합니다.</div>
      <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
        <button id="cheonokMiniLead" style="border:0;border-radius:10px;background:#d4af37;color:#000;padding:8px 10px;font-weight:800;cursor:pointer;">무료진단</button>
        <button id="cheonokHighTicket" style="border:1px solid rgba(212,175,55,.35);border-radius:10px;background:transparent;color:#f0ead6;padding:8px 10px;font-weight:800;cursor:pointer;">300만 진단</button>
        <button id="cheonokCloseWidget" style="border:0;border-radius:10px;background:rgba(255,255,255,.08);color:#f0ead6;padding:8px 10px;cursor:pointer;">닫기</button>
      </div>`;
    document.body.appendChild(box);

    document.getElementById('cheonokMiniLead')?.addEventListener('click', () => {
      document.getElementById('saju')?.scrollIntoView({ behavior: 'smooth' });
      sendLead({
        type: 'free_diagnosis_widget_click',
        product: '무료진단',
        price: 0,
        question: '1000억 OS 위젯: 무료진단 클릭'
      });
    });

    document.getElementById('cheonokHighTicket')?.addEventListener('click', () => {
      sendLead({
        type: 'high_ticket_widget_click',
        product: 'AI 매출 시스템 진단 프로젝트',
        price: 3000000,
        question: '1000억 OS 위젯: 300만 원 진단 프로젝트 관심 클릭'
      });
      location.href = 'mailto:admin@cheonoksystem.com?subject=CHEONOK%20300%EB%A7%8C%EC%9B%90%20AI%20%EB%A7%A4%EC%B6%9C%20%EC%A7%84%EB%8B%A8%20%EB%AC%B8%EC%9D%98';
    });

    document.getElementById('cheonokCloseWidget')?.addEventListener('click', () => box.remove());
  }

  function boot() {
    patchSubscribe();
    patchSaju();
    addConsultBridge();
    addRevenueWidget();
    sendLead({
      type: 'homepage_visit',
      country: getLang().toUpperCase(),
      product: 'CHEONOK Global Revenue OS',
      price: 0,
      question: '홈페이지 방문 / 리드 브릿지 활성화'
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
