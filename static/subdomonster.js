/* File: static/subdomonster.js */
function initSubdomonster(){
  const overlay = document.getElementById('subdomonster-overlay');
  if(!overlay) return;
  const domainInput = document.getElementById('subdomonster-domain');
  const fetchBtn = document.getElementById('subdomonster-fetch-btn');
  const tableDiv = document.getElementById('subdomonster-table');
  const closeBtn = document.getElementById('subdomonster-close-btn');

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
    const resp = await fetch('/subdomains', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({domain})});
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
