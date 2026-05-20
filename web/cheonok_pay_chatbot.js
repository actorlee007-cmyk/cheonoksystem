(() => {
  const PAY = {
    mini: 'https://www.paypal.com/ncp/payment/P6E4ZM2PHKKES',
    deep: 'https://www.paypal.com/ncp/payment/5F26FX28QQS6U',
    ceo: 'https://www.paypal.com/ncp/payment/KJPM4FJBJXPE6',
    os: 'https://www.paypal.com/ncp/payment/394P6QWWX3Y8G',
    form: 'https://docs.google.com/forms/d/e/1FAIpQLSfcZ27sYNP-TOFhtzQmCe2dd4d453Es1ih_7c42xDHlWWP-Qw/viewform'
  };

  const products = [
    { id: 'free', label: '무료진단', price: 'Free', desc: '링크 하나로 병목 미리보기', url: PAY.form, tone: 'gold' },
    { id: 'mini', label: 'Mini Report', price: '$7', desc: '핵심 문제 1개 + 다음 방향', url: PAY.mini, tone: 'soft' },
    { id: 'ceo', label: 'CEO Diagnosis', price: '$69', desc: '7일 실행 로드맵', url: PAY.ceo, tone: 'green' },
    { id: 'os', label: 'Operator OS', price: '$299', desc: 'AI 운영 구조 진단', url: PAY.os, tone: 'dark' },
    { id: 'b2b', label: 'B2B Inquiry', price: '₩300k+', desc: '고가진단·구축 상담', url: PAY.form, tone: 'blue' }
  ];

  const style = document.createElement('style');
  style.textContent = `
    .cpay-fab{position:fixed;right:18px;bottom:18px;z-index:9999;border:0;border-radius:999px;padding:15px 18px;background:#111827;color:white;font-weight:950;box-shadow:0 18px 48px rgba(0,0,0,.28);cursor:pointer;letter-spacing:-.03em}.cpay-fab span{color:#f1c75c}.cpay-box{position:fixed;right:18px;bottom:78px;width:min(390px,calc(100vw - 28px));max-height:min(720px,calc(100vh - 100px));overflow:auto;background:#fffdf8;color:#111827;border:1px solid #e5d7c2;border-radius:26px;box-shadow:0 26px 80px rgba(0,0,0,.26);z-index:9999;display:none;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Noto Sans KR',sans-serif;letter-spacing:-.03em}.cpay-box.open{display:block}.cpay-head{background:linear-gradient(135deg,#101827,#1b2b42);color:white;padding:18px;border-radius:24px 24px 0 0}.cpay-head b{display:block;font-size:18px}.cpay-head p{margin:6px 0 0;color:rgba(255,255,255,.76);font-size:13px;line-height:1.45}.cpay-body{padding:15px}.cpay-msg{background:#f7f1e8;border:1px solid #e5d7c2;border-radius:17px;padding:12px;margin-bottom:10px;font-size:14px;line-height:1.55}.cpay-products{display:grid;gap:9px}.cpay-card{border:1px solid #e5d7c2;background:white;border-radius:18px;padding:13px;display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center}.cpay-card b{display:block;font-size:15px}.cpay-card small{display:block;color:#667085;margin-top:4px;line-height:1.35}.cpay-card em{font-style:normal;font-weight:950;color:#c28b1b}.cpay-card a{display:inline-flex;justify-content:center;align-items:center;border-radius:13px;padding:10px 12px;background:#12a66a;color:white;text-decoration:none;font-weight:950;white-space:nowrap}.cpay-card a.gold{background:linear-gradient(135deg,#c28b1b,#f1c75c);color:#111}.cpay-card a.dark{background:#111827}.cpay-card a.blue{background:#2454d8}.cpay-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.cpay-actions button,.cpay-actions a{border:1px solid #e5d7c2;background:#fff;border-radius:14px;padding:11px;text-align:center;font-weight:850;text-decoration:none;color:#111827;cursor:pointer}.cpay-bank{background:#f8f4ff;border:1px solid #c4b5fd;color:#4c1d95;border-radius:16px;padding:12px;margin-top:11px;font-size:13px;line-height:1.55}.cpay-foot{font-size:11px;color:#94a3b8;line-height:1.45;margin-top:11px}.cpay-close{float:right;border:0;background:rgba(255,255,255,.12);color:white;border-radius:999px;width:30px;height:30px;cursor:pointer}@media(max-width:560px){.cpay-fab{left:14px;right:14px;bottom:14px}.cpay-box{left:14px;right:14px;bottom:74px;width:auto}.cpay-actions{grid-template-columns:1fr}.cpay-card{grid-template-columns:1fr}}`;
  document.head.appendChild(style);

  const fab = document.createElement('button');
  fab.className = 'cpay-fab';
  fab.innerHTML = '<span>Pay</span> 도와드릴까요?';

  const box = document.createElement('div');
  box.className = 'cpay-box';
  box.innerHTML = `
    <div class="cpay-head"><button class="cpay-close" type="button">×</button><b>CHEONOK 결제 도우미</b><p>고민이 있으면 무료진단부터, 빠른 실행안이 필요하면 $69 CEO 진단부터 시작하세요.</p></div>
    <div class="cpay-body">
      <div class="cpay-msg">무엇을 선택해야 할지 모르겠다면 <b>무료진단</b>을 누르세요. 이미 문제와 링크가 정리되어 있으면 <b>$69 CEO Diagnosis</b>가 가장 빠릅니다.</div>
      <div class="cpay-products">${products.map(p => `<div class="cpay-card"><div><b>${p.label} <em>${p.price}</em></b><small>${p.desc}</small></div><a class="${p.tone === 'gold' ? 'gold' : p.tone === 'dark' ? 'dark' : p.tone === 'blue' ? 'blue' : ''}" href="${p.url}" target="_blank" rel="noopener" data-product="${p.id}">${p.id === 'free' || p.id === 'b2b' ? '신청' : '결제'}</a></div>`).join('')}</div>
      <div class="cpay-bank"><b>원화 계좌이체</b><br>카카오뱅크 3333-15-4116074 이현진<br>입금 후 무료진단 폼에 입금자명 + 상품명을 남겨주세요.</div>
      <div class="cpay-actions"><a href="${PAY.form}" target="_blank" rel="noopener">무료진단 폼 열기</a><button type="button" id="cpayRecommend">추천받기</button></div>
      <div class="cpay-foot">매출 보장, 투자·법률·의료 자문은 제공하지 않습니다. 결제 전 무료진단으로 적합도를 먼저 확인할 수 있습니다.</div>
    </div>`;

  document.body.appendChild(fab);
  document.body.appendChild(box);

  function openBox(){ box.classList.add('open'); }
  function closeBox(){ box.classList.remove('open'); }
  fab.addEventListener('click', () => box.classList.toggle('open'));
  box.querySelector('.cpay-close').addEventListener('click', closeBox);
  box.querySelector('#cpayRecommend').addEventListener('click', () => {
    const msg = box.querySelector('.cpay-msg');
    msg.innerHTML = '추천 기준: <b>처음이면 무료진단</b> → 문제를 알고 있으면 <b>$69 CEO Diagnosis</b> → 운영 구조 전체가 막혔으면 <b>$299 Operator OS</b> → 회사/고객 반복 구조는 <b>B2B 상담</b>입니다.';
    openBox();
  });

  box.querySelectorAll('a[data-product]').forEach(a => {
    a.addEventListener('click', () => {
      try {
        fetch('/api/lead', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ source:'pay_chatbot', type:'payment_click', product:a.dataset.product, ts:new Date().toISOString() }) });
      } catch(e) {}
    });
  });

  setTimeout(() => { if (!sessionStorage.getItem('cheonok_pay_opened')) { openBox(); sessionStorage.setItem('cheonok_pay_opened','1'); } }, 4500);
})();
