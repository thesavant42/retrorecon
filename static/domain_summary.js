/* File: static/domain_summary.js */
function initDomainSummary(){
  const overlay = document.getElementById('domain-summary-overlay');
  if(!overlay) return;
  const closeBtn = document.getElementById('domain-summary-close-btn');
  const totalDomains = document.getElementById('summary-total-domains');
  const totalHosts = document.getElementById('summary-total-hosts');
  const topList = document.getElementById('summary-top-list');
  const lonelyList = document.getElementById('summary-lonely-list');
  const domainInput = document.getElementById('subdomain-import-domain');
  const sourceSel = document.getElementById('subdom-source');
  const apiInput = document.getElementById('subdom-api');
  const fetchBtn = document.getElementById('subdom-fetch-btn');
  const statusSpan = document.getElementById('subdom-status');

  let statusTimer = null;
  let statusDelay = 1000;
  let summaryTimer = null;

  function showStatus(msg){
    if(window.showStatus){
      window.showStatus(msg);
    } else if(statusSpan){
      statusSpan.textContent = msg;
      setTimeout(() => { if(statusSpan.textContent === msg) statusSpan.textContent = ''; }, 4000);
    }
  }

  function pollStatus(){
    if(overlay.classList.contains('hidden')){ statusTimer = null; return; }
    fetch('/status')
      .then(r => r.status === 204 ? null : r.json())
      .then(data => {
        if(data && data.code && data.code.startsWith('subdomonster')){
          showStatus(data.message || data.code);
          statusDelay = 1000;
        } else {
          statusDelay = Math.min(statusDelay * 2, 3000);
        }
        statusTimer = setTimeout(pollStatus, statusDelay);
      })
      .catch(() => { statusTimer = setTimeout(pollStatus, 5000); });
  }

  function startStatusPolling(){ if(!statusTimer) pollStatus(); }
  function stopStatusPolling(){ if(statusTimer){ clearTimeout(statusTimer); statusTimer = null; } }

  function startSummaryUpdates(){
    if(summaryTimer) return;
    loadSummary();
    summaryTimer = setInterval(loadSummary, 5000);
  }

  function stopSummaryUpdates(){
    if(summaryTimer){
      clearInterval(summaryTimer);
      summaryTimer = null;
    }
  }

  async function loadSummary(){
    try{
      const resp = await fetch('/domain_summary.json');
      if(!resp.ok) return;
      const data = await resp.json();
      totalDomains.textContent = data.total_domains;
      totalHosts.textContent = data.total_hosts;
      topList.innerHTML = '';
      data.top_subdomains.forEach(([d,c])=>{
        const li = document.createElement('li');
        li.textContent = `${d} (${c})`;
        topList.appendChild(li);
      });
      lonelyList.innerHTML = '';
      data.lonely_subdomains.forEach(([d,c])=>{
        const li = document.createElement('li');
        li.textContent = `${d} (${c})`;
        lonelyList.appendChild(li);
      });
    }catch{}
  }

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    document.body.style.overflow = '';
    stopSummaryUpdates();
    stopStatusPolling();
    if(location.pathname === '/tools/domain_summary'){
      history.pushState({}, '', '/');
    }
  });

  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });

  if(fetchBtn){
    fetchBtn.addEventListener('click', async () => {
      const domain = domainInput ? domainInput.value.trim() : '';
      const source = sourceSel ? sourceSel.value : 'crtsh';
      if(source !== 'local' && !domain) return;
      const params = new URLSearchParams({source});
      if(domain) params.set('domain', domain);
      if(apiInput && apiInput.value.trim()) params.set('api_key', apiInput.value.trim());
      startStatusPolling();
      try{
        const resp = await fetch('/subdomains', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:params});
        if(resp.ok){
          await loadSummary();
        } else {
          showStatus(await resp.text());
        }
      }catch(err){
        console.error('import failed', err);
      }
    });
  }

  window.loadDomainSummary = startSummaryUpdates;
  window.startDomainSummary = startSummaryUpdates;
  window.stopDomainSummary = () => { stopSummaryUpdates(); stopStatusPolling(); };
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initDomainSummary);
}else{
  initDomainSummary();
}
