/* File: static/subdomonster.js */
function initSubdomonster(){
  const overlay = document.getElementById('subdomonster-overlay');
  if(!overlay) return;
  const domainInput = document.getElementById('subdomonster-domain');
  const fetchBtn = document.getElementById('subdomonster-fetch-btn');
  const scrapeBtn = document.getElementById('subdomonster-scrape-btn');
  const tableDiv = document.getElementById('subdomonster-table');
  const paginationDiv = document.getElementById('subdomonster-pagination');
  const closeBtn = document.getElementById('subdomonster-close-btn');
  const statusSpan = document.getElementById('subdomonster-status');
  const exportCsvBtn = document.getElementById('subdomonster-export-csv-btn');
  const exportMdBtn = document.getElementById('subdomonster-export-md-btn');
  const sourceRadios = document.getElementsByName('subdomonster-source');
  const apiInput = document.getElementById('subdomonster-api-key');
  let tableData = [];
  const init = document.getElementById('subdomonster-init');
  if(init){
    try{ tableData = JSON.parse(init.textContent); }catch{}
    init.remove();
    currentPage = 1;
  }
  let sortField = 'subdomain';
  let sortDir = 'asc';
  let currentPage = 1;
  let itemsPerPage = 25;

  let statusTimer = null;
  let statusDelay = 1000;

  function showStatus(msg){
    if(statusSpan){
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

  function startStatusPolling(){
    if(statusSpan) statusSpan.textContent = '';
    if(!statusTimer) pollStatus();
  }

  function stopStatusPolling(){
    if(statusTimer){
      clearTimeout(statusTimer);
      statusTimer = null;
    }
  }

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

  function renderPagination(totalPages){
    if(!paginationDiv) return;
    let html = '<div class="pagination">';
    html += '<select id="subdom-items" class="form-select menu-btn">';
    [10,25,50,100].forEach(n => {
      const sel = n === itemsPerPage ? ' selected' : '';
      html += `<option value="${n}"${sel}>${(''+n).padStart(2,'0')}</option>`;
    });
    html += '</select>';
    html += `<span class="page-info">Page ${currentPage} of ${totalPages}</span>`;
    if(currentPage>1){
      html += `<a href="#" data-p="1" class="pagination-arrow" aria-label="First">&laquo;&laquo;</a>`;
      html += `<a href="#" data-p="${currentPage-1}" class="pagination-arrow" aria-label="Prev">&laquo;</a>`;
    }
    let start = currentPage - 2 > 2 ? currentPage - 2 : 1;
    let end = currentPage + 2 < totalPages - 1 ? currentPage + 2 : totalPages;
    if(start>1){
      html += `<a href="#" data-p="1">1</a>`;
      if(start>2) html += '<span>...</span>';
    }
    for(let p=start; p<=end; p++){
      if(p===currentPage) html += `<strong>${p}</strong>`;
      else html += `<a href="#" data-p="${p}">${p}</a>`;
    }
    if(end<totalPages){
      if(end<totalPages-1) html += '<span>...</span>';
      html += `<a href="#" data-p="${totalPages}">${totalPages}</a>`;
    }
    if(currentPage<totalPages){
      html += `<a href="#" data-p="${currentPage+1}" class="pagination-arrow" aria-label="Next">&raquo;</a>`;
      html += `<a href="#" data-p="${totalPages}" class="pagination-arrow" aria-label="Last">&raquo;&raquo;</a>`;
    }
    html += '</div>';
    paginationDiv.innerHTML = html;
    const sel = document.getElementById('subdom-items');
    if(sel){
      sel.addEventListener('change', ()=>{
        itemsPerPage = parseInt(sel.value,10);
        currentPage = 1;
        render();
      });
    }
    paginationDiv.querySelectorAll('a[data-p]').forEach(a=>{
      a.addEventListener('click', e=>{
        e.preventDefault();
        currentPage = parseInt(a.dataset.p,10);
        render();
      });
    });
  }

  for(const rb of sourceRadios){
    rb.addEventListener('change', () => {
      const val = rb.value;
      if(rb.checked){
        apiInput.classList.toggle('hidden', val !== 'virustotal');
      }
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
    const totalPages = Math.max(1, Math.ceil(sorted.length / itemsPerPage));
    if(currentPage > totalPages) currentPage = totalPages;
    const pageData = sorted.slice((currentPage-1)*itemsPerPage, (currentPage-1)*itemsPerPage + itemsPerPage);
    let html = '<table class="table url-table w-100"><colgroup>'+
      '<col/><col/><col/><col/><col class="send-col"/>'+
      '</colgroup><thead><tr>'+
      '<th class="sortable" data-field="subdomain">Subdomain</th>'+
      '<th class="sortable" data-field="domain">Domain</th>'+
      '<th class="sortable" data-field="source">Source</th>'+
      '<th class="sortable" data-field="cdx_indexed">CDXed</th>'+
      '<th class="no-resize">Send</th>'+
      '</tr></thead><tbody>';
    for(const r of pageData){
      html += `<tr data-cdx="${r.cdx_indexed?1:0}" data-sub="${r.subdomain}" data-domain="${r.domain}"><td>${r.subdomain}</td><td>${r.domain}</td><td>${r.source}</td><td>${r.cdx_indexed? 'yes':'no'}</td><td><button type="button" class="btn btn--small delete-btn">x</button> <button type="button" class="btn send-btn">Send!</button></td></tr>`;
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
    table.querySelectorAll('.send-btn').forEach(btn => {
      btn.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        const tr = btn.closest('tr');
        if(tr && tr.dataset.cdx === '0'){
          if(confirm('Send this subdomain to the CDX API?')){
            const sub = tr.dataset.sub;
            const resp = await fetch('/fetch_cdx', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({domain: sub})});
            if(resp.ok){
              await fetch('/mark_subdomain_cdx', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({subdomain: sub})});
              tr.dataset.cdx = '1';
              tr.querySelector('td:nth-child(4)').textContent = 'yes';
            } else {
              alert('CDX fetch failed');
            }
          }
        }
      });
    });
    table.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        const tr = btn.closest('tr');
        if(tr && confirm('Delete this subdomain?')){
          const sub = tr.dataset.sub;
          const domain = tr.dataset.domain;
          const resp = await fetch('/delete_subdomain', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({domain, subdomain: sub})});
          if(resp.ok){
            tableData = tableData.filter(r => r.subdomain !== sub);
            render();
          } else {
            alert('Delete failed');
          }
        }
      });
    });
    renderPagination(totalPages);
  }

  fetchBtn.addEventListener('click', async () => {
    const domain = domainInput.value.trim();
    let source = 'crtsh';
    for(const rb of sourceRadios){ if(rb.checked){ source = rb.value; break; } }
    if(source === 'local'){
      const body = new URLSearchParams();
      if(domain) body.append('domain', domain);
      const resp = await fetch('/scrape_subdomains', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body});
      if(resp.ok){
        const q = domain ? ('?domain=' + encodeURIComponent(domain)) : '';
        const r = await fetch('/subdomains' + q);
        if(r.ok){
          const data = await r.json();
          tableData = Array.isArray(data) ? data : [];
          currentPage = 1;
          render();
        } else {
          alert(await r.text());
        }
      } else {
        alert('Scrape failed');
      }
      return;
    }
    if(!domain) return;
    const api_key = apiInput.value.trim();
    const resp = await fetch('/subdomains', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({domain, source, api_key})});
    if(resp.ok){
      const data = await resp.json();
      tableData = Array.isArray(data) ? data : [];
      currentPage = 1;
      render();
    } else {
      alert(await resp.text());
    }
  });

  scrapeBtn.addEventListener('click', async () => {
    const domain = domainInput.value.trim();
    const body = new URLSearchParams();
    if(domain) body.append('domain', domain);
    const resp = await fetch('/scrape_subdomains', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body});
    if(resp.ok){
      const q = domain ? ('?domain=' + encodeURIComponent(domain)) : '';
      const r = await fetch('/subdomains' + q);
      if(r.ok){
        const data = await r.json();
        tableData = Array.isArray(data) ? data : [];
        currentPage = 1;
        render();
      } else {
        fetchBtn.click();
      }
    } else {
      alert('Scrape failed');
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
    stopStatusPolling();
    if(location.pathname === '/tools/subdomonster'){
      history.pushState({}, '', '/');
    }
  });

  if(tableData.length){
    render();
  }
  window.startSubdomonsterStatus = startStatusPolling;
  window.stopSubdomonsterStatus = stopStatusPolling;
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initSubdomonster);
}else{
  initSubdomonster();
}
