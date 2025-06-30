/* File: static/domain_summary.js */
function initDomainSummary(){
  const overlay = document.getElementById('domain-summary-overlay');
  if(!overlay) return;
  const closeBtn = document.getElementById('domain-summary-close-btn');
  const totalDomains = document.getElementById('summary-total-domains');
  const totalHosts = document.getElementById('summary-total-hosts');
  const topList = document.getElementById('summary-top-list');
  const lonelyList = document.getElementById('summary-lonely-list');

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
    if(location.pathname === '/tools/domain_summary'){
      history.pushState({}, '', '/');
    }
  });

  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });

  loadSummary();
  setInterval(loadSummary, 5000);
  window.loadDomainSummary = loadSummary;
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initDomainSummary);
}else{
  initDomainSummary();
}
