/* File: static/subdomonster.js */
function initSubdomonster(){
  const overlay = document.getElementById('subdomonster-overlay');
  if(!overlay) return;
  const domainInput = document.getElementById('subdomonster-domain');
  const fetchBtn = document.getElementById('subdomonster-fetch-btn');
  const tableDiv = document.getElementById('subdomonster-table');
  const paginationDiv = document.getElementById('subdomonster-pagination');
  const closeBtn = document.getElementById('subdomonster-close-btn');
  const statusSpan = document.getElementById('subdomonster-status');
  const exportFormatsSel = document.getElementById('subdom-export-formats');
  const exportForm = document.getElementById('subdom-export-form');
  const exportDomainInp = document.getElementById('subdom-export-domain');
  const exportFormatInp = document.getElementById('subdom-export-format');
  const exportQInp = document.getElementById('subdom-export-q');
  const searchInput = document.getElementById('subdomonster-search');
  const sourceRadios = document.getElementsByName('subdomonster-source');
  const apiInput = document.getElementById('subdomonster-api-key');
  const selectModeSel = document.getElementById('subdom-select-mode');
  const bulkTag = document.getElementById('subdom-bulk-tag');
  const addTagBtn = document.getElementById('subdom-add-tag-btn');
  const removeTagBtn = document.getElementById('subdom-remove-tag-btn');
  const clearTagsBtn = document.getElementById('subdom-clear-tags-btn');
  const deleteBtn = document.getElementById('subdom-delete-btn');
  let currentPage = 1;
  let tableData = [];
  const init = document.getElementById('subdomonster-init');
  if(init){
    try{ tableData = JSON.parse(init.textContent); }catch{}
    init.remove();
    currentPage = 1;
  }
  let sortField = 'subdomain';
  let sortDir = 'asc';
  let itemsPerPage = 25;
  let searchText = '';
  let selectAll = false;
  const selectedSubs = new Set();

  let statusTimer = null;
  let statusDelay = 1000;

  function getMatchingCount(){
    const q = searchText;
    if(!q) return tableData.length;
    return tableData.filter(r =>
      r.subdomain.toLowerCase().includes(q) ||
      r.domain.toLowerCase().includes(q) ||
      (r.tags || '').toLowerCase().includes(q)
    ).length;
  }

  function updateSelectionStatus(){
    const count = selectAll ? getMatchingCount() : selectedSubs.size;
    showStatus(count + ' selected');
  }

  function showStatus(msg){
    if(statusSpan){
      statusSpan.textContent = msg;
      setTimeout(() => { if(statusSpan.textContent === msg) statusSpan.textContent = ''; }, 4000);
    }
  }

  function toggleSelectPage(state){
    document.querySelectorAll('#subdomonster-table .row-checkbox').forEach(c => {
      c.checked = state;
      const sub = c.dataset.sub;
      if(state) selectedSubs.add(sub); else selectedSubs.delete(sub);
    });
    selectAll = false;
    if(selectModeSel) selectModeSel.value = state ? 'page' : '';
    updateSelectionStatus();
  }

  function toggleSelectAllMatching(state){
    selectAll = state;
    if(selectModeSel) selectModeSel.value = state ? 'all' : '';
    if(state){
      selectedSubs.clear();
      document.querySelectorAll('#subdomonster-table .row-checkbox').forEach(c => {
        c.checked = true;
        const sub = c.dataset.sub;
        selectedSubs.add(sub);
      });
      showStatus('All matching selected');
    } else {
      selectedSubs.clear();
      document.querySelectorAll('#subdomonster-table .row-checkbox').forEach(c => c.checked=false);
      showStatus('Selection cleared');
    }
    updateSelectionStatus();
  }

  function openCdxImport(sub){
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/fetch_cdx';
    form.target = '_blank';
    const inp = document.createElement('input');
    inp.type = 'hidden';
    inp.name = 'domain';
    inp.value = sub;
    form.appendChild(inp);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    fetch('/mark_subdomain_cdx', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({subdomain: sub})});
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

  if(selectModeSel){
    selectModeSel.addEventListener('change', () => {
      const mode = selectModeSel.value;
      if(mode === 'page') {
        toggleSelectPage(true);
      } else if(mode === 'all') {
        toggleSelectAllMatching(true);
      } else {
        toggleSelectAllMatching(false);
        toggleSelectPage(false);
        document.querySelectorAll('#subdomonster-table .row-checkbox').forEach(c=>c.checked=false);
        selectedSubs.clear();
      }
      updateSelectionStatus();
    });
  }

  if(searchInput){
    searchInput.addEventListener('input', () => {
      searchText = searchInput.value.trim().toLowerCase();
      currentPage = 1;
      selectedSubs.clear();
      render();
      updateSelectionStatus();
    });
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

  function renderPagination(totalPages, totalCount){
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
    html += `<span class="total-count">Total results: ${totalCount}</span>`;
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
    const filtered = searchText ?
      tableData.filter(r =>
        r.subdomain.toLowerCase().includes(searchText) ||
        r.domain.toLowerCase().includes(searchText) ||
        (r.tags || '').toLowerCase().includes(searchText)
      ) :
      tableData;
    const sorted = filtered.slice().sort((a,b)=>{
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
      '<col/><col/><col/><col/><col/><col class="send-col"/>'+
      '</colgroup><thead><tr>'+
      '<th class="w-2em"><input type="checkbox" onclick="document.querySelectorAll(\'#subdomonster-table .row-checkbox\').forEach(c=>c.checked=this.checked);selectAll=false;" /></th>'+
      '<th class="sortable" data-field="subdomain">Subdomain</th>'+
      '<th class="sortable" data-field="domain">Domain</th>'+
      '<th class="sortable" data-field="source">Source</th>'+
      '<th class="sortable" data-field="cdx_indexed">CDXed</th>'+
      '<th>Tags</th>'+
      '<th class="no-resize">Actions:</th>'+
      '</tr></thead><tbody>';
    for(const r of pageData){
      const encoded = encodeURIComponent(r.subdomain);
      const checked = selectAll || selectedSubs.has(r.subdomain) ? ' checked' : '';
      html += `<tr data-cdx="${r.cdx_indexed?1:0}" data-sub="${r.subdomain}" data-domain="${r.domain}">`+
        `<td class="text-center"><input type="checkbox" class="row-checkbox" data-sub="${r.subdomain}" data-domain="${r.domain}" value="${r.domain}|${r.subdomain}"${checked} /></td>`+
        `<td><span class="ml-5px">${r.subdomain}</span></td>`+
        `<td>${r.domain}</td>`+
        `<td>${r.source}</td>`+
        `<td>${r.cdx_indexed? 'yes':'no'}</td>`+
        `<td>${r.tags || ''}</td>`+
        `<td>`+
          `<button type="button" class="btn btn--small delete-btn">x</button> `+
          `<div class="dropdown d-inline-block ml-4px">`+
            `<button type="button" class="dropbtn send-btn">Send to ▼</button>`+
            `<div class="dropdown-content">`+
              `<div class="menu-row"><a class="menu-btn" href="/tools/screenshotter?url=${encoded}" target="_blank">Screen Shotter</a></div>`+
              `<div class="menu-row"><a class="menu-btn" href="/tools/site2zip?url=${encoded}" target="_blank">Site2Zip</a></div>`+
              `<div class="menu-row"><a class="menu-btn" href="/tools/webpack-zip?map_url=${encoded}" target="_blank">Webpack Explode...</a></div>`+
              `<div class="menu-row"><a class="menu-btn" href="/tools/text_tools?text=${encoded}" target="_blank">Text Tools</a></div>`+
              `<div class="menu-row"><a class="menu-btn cdx-import-link" href="#" data-sub="${encoded}">Wayback Import</a></div>`+
            `</div>`+
          `</div>`+
        `</td>`+
      `</tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
    const table = tableDiv.querySelector('table');
    const pageCb = document.getElementById('subdom-page-cb');
    if(pageCb){
      pageCb.checked = pageData.every(r => selectedSubs.has(r.subdomain));
      pageCb.addEventListener('change', () => {
        pageData.forEach(r => {
          if(pageCb.checked) selectedSubs.add(r.subdomain); else selectedSubs.delete(r.subdomain);
        });
        table.querySelectorAll('.row-checkbox').forEach(c => c.checked = pageCb.checked);
        updateSelectionStatus();
      });
    }
    table.querySelectorAll('.row-checkbox').forEach(cb => {
      cb.addEventListener('change', () => {
        const sub = cb.dataset.sub || (cb.closest('tr') ? cb.closest('tr').dataset.sub : '');
        if(cb.checked) selectedSubs.add(sub); else selectedSubs.delete(sub);
        if(pageCb) pageCb.checked = pageData.every(r => selectedSubs.has(r.subdomain));
        updateSelectionStatus();
      });
    });
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
    table.querySelectorAll('.cdx-import-link').forEach(link => {
      link.addEventListener('click', (ev) => {
        ev.preventDefault();
        const sub = decodeURIComponent(link.dataset.sub);
        openCdxImport(sub);
        const row = link.closest('tr');
        if(row){
          row.dataset.cdx = '1';
          const cell = row.querySelector('td:nth-child(5)');
          if(cell) cell.textContent = 'yes';
          const item = tableData.find(r => r.subdomain === sub);
          if(item) item.cdx_indexed = true;
        }
      });
    });

    renderPagination(totalPages, sorted.length);
    const shade = document.getElementById('dropdown-shade');
    table.querySelectorAll('.dropbtn').forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        const item = btn.parentElement;
        const show = !item.classList.contains('show');
        table.querySelectorAll('.dropdown').forEach(d => d.classList.remove('show'));
        if(show){
          item.classList.add('show');
          if(shade) shade.classList.add('show');
        } else {
          if(shade) shade.classList.remove('show');
        }
      });
    });
    renderPagination(totalPages);
  }

  fetchBtn.addEventListener('click', async () => {
    const domain = domainInput.value.trim();
    let source = 'crtsh';
    for(const rb of sourceRadios){ if(rb.checked){ source = rb.value; break; } }
    const params = new URLSearchParams();
    if(domain) params.append('domain', domain);
    params.append('source', source);
    if(source === 'virustotal'){
      const api_key = apiInput.value.trim();
      params.append('api_key', api_key);
      if(!domain) return;
    } else if(source !== 'local' && !domain){
      return;
    }
    showStatus('Fetching...');
    const resp = await fetch('/subdomains', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    if(resp.ok){
      const data = await resp.json();
      tableData = Array.isArray(data) ? data : [];
      currentPage = 1;
      selectedSubs.clear();
      render();
      updateSelectionStatus();
    } else {
      alert(await resp.text());
    }
  });


  if(exportFormatsSel && exportForm){
    exportFormatsSel.addEventListener('change', () => {
      const fmt = exportFormatsSel.value;
      if(!fmt) return;
      const domain = domainInput.value.trim();
      if(!domain) { exportFormatsSel.value = ''; return; }
      if(exportDomainInp) exportDomainInp.value = domain;
      if(exportFormatInp) exportFormatInp.value = fmt;
      if(exportQInp) exportQInp.value = searchInput ? searchInput.value.trim() : '';
      exportForm.submit();
      exportFormatsSel.value = '';
    });
  }

  async function bulkAction(action){
    const selected = Array.from(document.querySelectorAll('#subdomonster-table .row-checkbox:checked')).map(c=>c.value);
    if(!selectAll && selected.length === 0){
      alert('No entries selected');
      return;
    }
    const params = new URLSearchParams();
    params.append('action', action);
    if(selectAll){
      params.append('select_all_matching','true');
      params.append('q', searchInput ? searchInput.value.trim() : '');
      params.append('domain', domainInput.value.trim());
    } else {
      for(const val of selected){ params.append('selected', val); }
    }
    const tag = bulkTag ? bulkTag.value.trim() : '';
    if(tag) params.append('tag', tag);
    const resp = await fetch('/subdomain_action', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:params});
    if(resp.ok){
      const data = await resp.json();
      showStatus('Updated ' + data.updated);
      fetchBtn.click();
    } else {
      alert('Action failed');
    }
  }

  if(addTagBtn){ addTagBtn.addEventListener('click', ()=>bulkAction('add_tag')); }
  if(removeTagBtn){ removeTagBtn.addEventListener('click', ()=>bulkAction('remove_tag')); }
  if(clearTagsBtn){ clearTagsBtn.addEventListener('click', ()=>bulkAction('clear_tags')); }
  if(deleteBtn){ deleteBtn.addEventListener('click', ()=>bulkAction('delete')); }

  closeBtn.addEventListener('click', () => {
    history.back();
  });

  if(tableData.length){
    render();
    updateSelectionStatus();
  }
  window.startSubdomonsterStatus = startStatusPolling;
  window.stopSubdomonsterStatus = stopStatusPolling;
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initSubdomonster);
}else{
  initSubdomonster();
}
