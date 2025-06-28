/* File: static/subdomonster.js */
function initSubdomonster(){
  const overlay = document.getElementById('subdomonster-overlay');
  if(!overlay) return;
  const domainInput = document.getElementById('subdomonster-domain');
  const addBtn = document.getElementById('subdom-add-domain-btn');
  const tableDiv = document.getElementById('subdomonster-table');
  const paginationDiv = document.getElementById('subdomonster-pagination');
  const closeBtn = document.getElementById('subdomonster-close-btn');
  const statusSpan = document.getElementById('subdomonster-status');
  const exportBtn = document.getElementById('subdom-export-btn');
  const exportForm = document.getElementById('subdom-export-form');
  const exportDomainInp = document.getElementById('subdom-export-domain');
  const exportFormatInp = document.getElementById('subdom-export-format');
  const exportQInp = document.getElementById('subdom-export-q');
  const searchInput = document.getElementById('subdomonster-search');
  function cleanTagString(str){
    if(!str) return '';
    const nozw = str.replace(/\u200b/g, '');
    try{
      const arr = JSON.parse(nozw);
      if(Array.isArray(arr)){
        return arr.map(it => {
          const obj = Array.isArray(it) ? it[0] : it;
          return obj && obj.value ? obj.value : '';
        }).join(' ').trim();
      }
    }catch{}
    return nozw;
  }
  let savedTags = [];
  fetch('/saved_tags')
    .then(r => r.ok ? r.json() : {tags: []})
    .then(d => {
      const arr = Array.isArray(d.tags) ? d.tags : [];
      savedTags = arr.map(t => t.name);
        if(searchInput){
        window.subdomSearchTagify = new Tagify(searchInput,{mode:'mix',pattern:/.+/,whitelist:savedTags,
          originalInputValueFormat:v=>v.map(t=>t.value).join(' ')});
      }
    });
  const sourceSel = document.getElementById('subdomonster-source');
  const apiInput = document.getElementById('subdomonster-api-key');
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


  function openCdxImport(sub){
    enqueueCdxImport([sub]);
  }

  const cdxQueue = [];
  let cdxProcessing = false;

  function sanitizeDomain(d){
    return d.replace(/[^A-Za-z0-9_.-]/g, '');
  }

  async function processCdxQueue(){
    if(cdxProcessing) return;
    cdxProcessing = true;
    while(cdxQueue.length){
      const sub = cdxQueue.shift();
      console.debug('cdx import', sub);
      const params = new URLSearchParams({domain: sub, ajax:'1'});
      try{
        await fetch('/fetch_cdx', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
        await fetch('/mark_subdomain_cdx', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({subdomain: sub})});
      }catch(err){
        console.error('cdx queue error', err);
      }
      await new Promise(r=>setTimeout(r,1000));
    }
    cdxProcessing = false;
    if(addBtn) addBtn.click();
  }

  function enqueueCdxImport(list){
    for(const d of list){
      const clean = sanitizeDomain(d);
      if(clean) cdxQueue.push(clean);
    }
    processCdxQueue();
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


  async function fetchSearch(){
    const term = cleanTagString(searchInput.value.trim());
    const domain = domainInput.value.trim();
    const params = new URLSearchParams();
    if(term) params.append('q', term);
    if(domain) params.append('domain', domain);
    const resp = await fetch('/subdomains?' + params.toString());
    if(resp.ok){
      const data = await resp.json();
      tableData = Array.isArray(data.results) ? data.results : data;
    } else {
      tableData = [];
    }
  }

  if(searchInput){
    searchInput.addEventListener('input', async () => {
      searchText = cleanTagString(searchInput.value.trim()).toLowerCase();
      currentPage = 1;
      selectedSubs.clear();
      await fetchSearch();
      render();
      updateSelectionStatus();
    });
  }

  function makeResizable(table, key){
    if(typeof makeResizableTable === 'function'){
      makeResizableTable(table, key);
    }
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

  if(sourceSel){
    sourceSel.addEventListener('change', () => {
      const val = sourceSel.value;
      apiInput.classList.toggle('hidden', val !== 'virustotal');
    });
    // initialize visibility
    apiInput.classList.toggle('hidden', sourceSel.value !== 'virustotal');
  }

  function render(){
    const widths = window.getColWidths ? window.getColWidths('subdomonster-col-widths', 5) : {};
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
      `<col class="w-1-6em checkbox-col"${widths[0]?` style=\"width:${widths[0]}\"`:''}/>`+
      `<col${widths[1]?` style=\"width:${widths[1]}\"`:''}/>`+
      `<col${widths[2]?` style=\"width:${widths[2]}\"`:''}/>`+
      `<col${widths[3]?` style=\"width:${widths[3]}\"`:''}/>`+
      `<col${widths[4]?` style=\"width:${widths[4]}\"`:''}/>`+
      '</colgroup><thead><tr>'+
      `<th class="w-1-6em checkbox-col no-resize text-center"${widths[0]?` style=\"width:${widths[0]}\"`:''}><input type="checkbox" onclick="document.querySelectorAll(\'#subdomonster-table .row-checkbox\').forEach(c=>c.checked=this.checked);selectAll=false;" /></th>`+
      `<th class="sortable" data-field="subdomain"${widths[1]?` style=\"width:${widths[1]}\"`:''}>Subdomain</th>`+
      `<th class="sortable" data-field="domain"${widths[2]?` style=\"width:${widths[2]}\"`:''}>Domain</th>`+
      `<th class="sortable" data-field="source"${widths[3]?` style=\"width:${widths[3]}\"`:''}>Source</th>`+
      `<th class="sortable" data-field="cdx_indexed"${widths[4]?` style=\"width:${widths[4]}\"`:''}>CDXed</th>`+
      '</tr></thead><tbody>';
    for(const r of pageData){
      const encoded = encodeURIComponent(r.subdomain);
      const checked = selectAll || selectedSubs.has(r.subdomain) ? ' checked' : '';
      const tagsHtml = (r.tags || '').split(',').filter(t=>t).map(t=>`<span class="tag-pill">${t}</span>`).join(' ');
      html += `<tr class="url-row-main url-result" data-cdx="${r.cdx_indexed?1:0}" data-sub="${r.subdomain}" data-domain="${r.domain}">`+
        `<td class="text-center"><input type="checkbox" class="row-checkbox" data-sub="${r.subdomain}" data-domain="${r.domain}" value="${r.domain}|${r.subdomain}"${checked} /></td>`+
        `<td><div class="cell-content">${r.subdomain}</div></td>`+
        `<td><div class="cell-content">${r.domain}</div></td>`+
        `<td><div class="cell-content">${r.source}</div></td>`+
        `<td><div class="cell-content">${r.cdx_indexed ? 'yes' : 'no'}</div></td>`+
      `</tr>`+
      `<tr class="url-row-buttons" data-sub="${r.subdomain}" data-domain="${r.domain}">`+
        `<td></td>`+
        `<td colspan="4">`+
          `<div class="url-tools-row nowrap">`+
            `<div class="dropdown d-inline-block">`+
              `<button type="button" class="dropbtn send-btn">Send to ▼</button>`+
              `<div class="dropdown-content">`+
                `<div class="menu-row"><a class="menu-btn" href="/tools/screenshotter?url=${encoded}" target="_blank">Screen Shotter</a></div>`+
                `<div class="menu-row"><a class="menu-btn" href="/tools/httpolaroid?url=${encoded}" target="_blank">HTTPolaroid</a></div>`+
                `<div class="menu-row"><a class="menu-btn" href="/tools/webpack-zip?map_url=${encoded}" target="_blank">Webpack Explode...</a></div>`+
                `<div class="menu-row"><a class="menu-btn" href="/tools/text_tools?text=${encoded}" target="_blank">Text Tools</a></div>`+
                `<div class="menu-row"><a class="menu-btn subdom-search-link" href="#" data-sub="${encoded}">Search</a></div>`+
                `<div class="menu-row"><a class="menu-btn cdx-import-link" href="#" data-sub="${encoded}">Wayback Import</a></div>`+
              `</div>`+
            `</div>`+
            `<button type="button" class="btn explode-btn copy-btn" data-sub="${encoded}" title="Copy">📋 Copy</button>`+
            `<button type="button" class="btn delete-btn" title="Delete">🗑️ Delete</button>`+
            `<button type="button" class="btn ml-05 notes-btn" data-sub="${encoded}">📝 Notes</button>`+
            `<input type="text" class="form-input ml-05 row-tag-input tag-input" placeholder="Tag" size="8" />`+
            `<button type="button" class="btn add-tag-btn" title="Add tag">+</button>`+
            tagsHtml +
          `</div>`+
        `</td>`+
      `</tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
    tableDiv.querySelectorAll('.row-tag-input').forEach(el => {
      new Tagify(el, { maxTags: 1, whitelist: savedTags,
        originalInputValueFormat: v => v.map(t => t.value).join(',') });
    });
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
    table.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const sub = decodeURIComponent(btn.dataset.sub);
        try {
          await navigator.clipboard.writeText(sub);
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = '📋 Copy'; }, 1000);
        } catch {
          const t = document.createElement('textarea');
          t.value = sub;
          document.body.appendChild(t);
          t.select();
          document.execCommand('copy');
          document.body.removeChild(t);
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = '📋 Copy'; }, 1000);
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

    table.querySelectorAll('.add-tag-btn').forEach(btn => {
      btn.addEventListener('click', async ev => {
        ev.stopPropagation();
        const tr = btn.closest('tr');
        if(!tr) return;
        const input = tr.querySelector('.row-tag-input');
        const tag = input ? input.value.trim() : '';
        if(!tag) return;
        const sub = tr.dataset.sub;
        const domain = tr.dataset.domain;
        const params = new URLSearchParams({action:'add_tag', tag, selected:`${domain}|${sub}`});
        const resp = await fetch('/subdomain_action', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:params});
        if(resp.ok){
          input.value = '';
          const data = await resp.json();
          if(data.updated){
            const item = tableData.find(r => r.subdomain===sub);
            if(item){
              item.tags = item.tags ? item.tags + ',' + tag : tag;
            }
            render();
          }
        } else {
          alert('Tag add failed');
        }
      });
    });

    table.querySelectorAll('.notes-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        alert('Notes feature not implemented yet');
      });
    });
    table.querySelectorAll('.cdx-import-link').forEach(link => {
      link.addEventListener('click', (ev) => {
        ev.preventDefault();
        const sub = decodeURIComponent(link.dataset.sub);
        const selected = Array.from(document.querySelectorAll('#subdomonster-table .row-checkbox:checked')).map(c=>c.dataset.sub);
        if(selected.length > 1){
          enqueueCdxImport(selected);
        }else{
          enqueueCdxImport([sub]);
        }
        const row = link.closest('tr');
        const main = row ? row.previousElementSibling : null;
        const target = main || row;
        if(target){
          target.dataset.cdx = '1';
          const cell = target.querySelector('td:nth-child(5)');
          if(cell) cell.textContent = 'yes';
          const item = tableData.find(r => r.subdomain === sub);
          if(item) item.cdx_indexed = true;
        }
      });
    });
    table.querySelectorAll('.subdom-search-link').forEach(link => {
      link.addEventListener('click', ev => {
        ev.preventDefault();
        const sub = decodeURIComponent(link.dataset.sub);
        const box = document.getElementById('searchbox');
        if(box) box.value = sub;
        history.back();
      });
    });

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
    renderPagination(totalPages, sorted.length);
  }

  addBtn.addEventListener('click', async () => {
    const input = prompt('Domain to fetch', domainInput.value.trim());
    const domain = (input || '').trim();
    if(!domain) return;
    domainInput.value = domain;
    const source = sourceSel ? sourceSel.value : 'crtsh';
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


  if(exportBtn && exportForm){
    exportBtn.addEventListener('click', () => {
      const fmt = prompt('Format (md,csv,json)', 'json');
      if(!fmt) return;
      const domain = domainInput.value.trim();
      if(!domain) return;
      if(exportDomainInp) exportDomainInp.value = domain;
      if(exportFormatInp) exportFormatInp.value = fmt;
      if(exportQInp) exportQInp.value = searchInput ? searchInput.value.trim() : '';
      exportForm.submit();
    });
  }



  closeBtn.addEventListener('click', () => {
    history.back();
  });
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });

  window.renderSubdomonster = () => {
    if(tableData.length){
      render();
      updateSelectionStatus();
    }
  };
  window.startSubdomonsterStatus = startStatusPolling;
  window.stopSubdomonsterStatus = stopStatusPolling;
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initSubdomonster);
}else{
  initSubdomonster();
}
