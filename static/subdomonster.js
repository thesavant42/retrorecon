/* File: static/subdomonster.js */
function initSubdomonster(){
  const overlay = document.getElementById('subdomonster-overlay');
  if(!overlay) return;
  const domainInput = document.getElementById('subdomonster-domain');
  const fetchBtn = document.getElementById('subdomonster-fetch-btn');
  const tableDiv = document.getElementById('subdomonster-table');
  const closeBtn = document.getElementById('subdomonster-close-btn');
  const exportCsvBtn = document.getElementById('subdomonster-export-csv-btn');
  const exportMdBtn = document.getElementById('subdomonster-export-md-btn');
  const sourceRadios = document.getElementsByName('subdomonster-source');
  const apiInput = document.getElementById('subdomonster-api-key');
  let tableData = [];
  let sortField = 'subdomain';
  let sortDir = 'asc';

  function makeResizable(table, key){
    table.style.tableLayout = 'fixed';
    const ths = table.querySelectorAll('th');
    const cols = table.querySelectorAll('col');
    let widths = {};
    try{ widths = JSON.parse(localStorage.getItem(key) || '{}'); }catch{}
    ths.forEach((th, idx) => {
      const id = idx;
      if(widths[id]){
        th.style.width = widths[id];
        if(cols[id]) cols[id].style.width = widths[id];
      }
      const initial = th.style.width || th.offsetWidth + 'px';
      th.style.width = initial;
      if(cols[id]) cols[id].style.width = initial;
      if(th.classList.contains('no-resize')) return;
      const res = document.createElement('div');
      res.className = 'col-resizer';
      th.appendChild(res);
      let startX = 0;
      let startWidth = 0;
      res.addEventListener('mousedown', e => {
        startX = e.pageX;
        startWidth = th.offsetWidth;
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', stop);
        e.preventDefault();
      });
      function onMove(e){
        const w = Math.max(30, startWidth + (e.pageX - startX));
        th.style.width = w + 'px';
        if(cols[id]) cols[id].style.width = w + 'px';
        widths[id] = w + 'px';
      }
      function stop(){
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', stop);
        localStorage.setItem(key, JSON.stringify(widths));
      }
    });
  }

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

  function render(){
    const sorted = tableData.slice().sort((a,b)=>{
      const av = (a[sortField] || '').toString().toLowerCase();
      const bv = (b[sortField] || '').toString().toLowerCase();
      if(av < bv) return sortDir==='asc'? -1:1;
      if(av > bv) return sortDir==='asc'? 1:-1;
      return 0;
    });
    let html = '<table class="table url-table w-100"><colgroup>'+
      '<col/><col/><col/><col/>'+
      '</colgroup><thead><tr>'+
      '<th class="sortable" data-field="subdomain">Subdomain</th>'+
      '<th class="sortable" data-field="domain">Domain</th>'+
      '<th class="sortable" data-field="source">Source</th>'+
      '<th class="sortable" data-field="cdx_indexed">CDXed</th>'+
      '</tr></thead><tbody>';
    for(const r of sorted){
      html += `<tr data-cdx="${r.cdx_indexed?1:0}" data-sub="${r.subdomain}"><td>${r.subdomain}</td><td>${r.domain}</td><td>${r.source}</td><td>${r.cdx_indexed? 'yes':'no'}</td></tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
    const table = tableDiv.querySelector('table');
    table.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', ev => {
        if(ev.target.closest('.col-resizer')) return;
        const field = th.dataset.field;
        if(sortField === field){
          sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          sortField = field;
          sortDir = 'asc';
        }
        render();
      });
    });
    makeResizable(table, 'subdomonster-col-widths');
    table.querySelectorAll('tbody tr').forEach(tr => {
      tr.addEventListener('click', async () => {
        if(tr.dataset.cdx === '0'){
          if(confirm('Send this subdomain to the CDX API?')){
            const sub = tr.dataset.sub;
            const resp = await fetch('/fetch_cdx', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({domain: sub})});
            if(resp.ok){
              await fetch('/mark_subdomain_cdx', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({subdomain: sub})});
              tr.dataset.cdx = '1';
              tr.querySelector('td:last-child').textContent = 'yes';
            } else {
              alert('CDX fetch failed');
            }
          }
        }
      });
    });
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
      tableData = Array.isArray(data) ? data : [];
      render();
    } else {
      alert(await resp.text());
    }
  });

  exportCsvBtn.addEventListener('click', async () => {
    const domain = domainInput.value.trim();
    if(!domain) return;
    const resp = await fetch('/export_subdomains?format=csv&domain=' + encodeURIComponent(domain));
    if(resp.ok){
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = domain + '.csv';
      a.click();
      URL.revokeObjectURL(url);
    } else {
      alert('Export failed');
    }
  });

  exportMdBtn.addEventListener('click', async () => {
    const domain = domainInput.value.trim();
    if(!domain) return;
    const resp = await fetch('/export_subdomains?format=md&domain=' + encodeURIComponent(domain));
    if(resp.ok){
      const text = await resp.text();
      const blob = new Blob([text], {type:'text/markdown'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = domain + '.md';
      a.click();
      URL.revokeObjectURL(url);
    } else {
      alert('Export failed');
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
