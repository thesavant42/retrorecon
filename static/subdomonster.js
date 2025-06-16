/* File: static/subdomonster.js */
function initSubdomonster(){
  const overlay = document.getElementById('subdomonster-overlay');
  if(!overlay) return;
  const domainInput = document.getElementById('subdomonster-domain');
  const fetchBtn = document.getElementById('subdomonster-fetch-btn');
  const tableDiv = document.getElementById('subdomonster-table');
  const closeBtn = document.getElementById('subdomonster-close-btn');
  const sourceRadios = document.getElementsByName('subdomonster-source');
  const apiInput = document.getElementById('subdomonster-api-key');

  for(const rb of sourceRadios){
    rb.addEventListener('change', () => {
      apiInput.classList.toggle('hidden', rb.value !== 'virustotal' || !rb.checked);
    });
  }
  // initialize visibility
  (function(){
    let active = Array.from(sourceRadios).find(r=>r.checked);
    if(active){
      apiInput.classList.toggle('hidden', active.value !== 'virustotal');
    }
  })();

  function render(rows){
    let html = '<table class="table url-table w-100"><thead><tr>'+
      '<th>Subdomain</th><th>Domain</th><th>Source</th>'+
      '</tr></thead><tbody>';
    for(const r of rows){
      html += `<tr><td>${r.subdomain}</td><td>${r.domain}</td><td>${r.source}</td></tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
  }

  fetchBtn.addEventListener('click', async () => {
    const domain = domainInput.value.trim();
    if(!domain) return;
    let source = 'crtsh';
    for(const rb of sourceRadios){ if(rb.checked){ source = rb.value; break; } }
    const api_key = apiInput.value.trim();
    const resp = await fetch('/subdomains', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({domain, source, api_key})});
    if(resp.ok){
      const data = await resp.json();
      render(data);
    } else {
      alert(await resp.text());
    }
  });

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/subdomonster'){
      history.pushState({}, '', '/');
    }
  });
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initSubdomonster);
}else{
  initSubdomonster();
}
