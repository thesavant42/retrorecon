/* File: static/httpolaroid.js */
function initHttpolaroid(){
  const overlay = document.getElementById('httpolaroid-overlay');
  if(!overlay) return;
  const urlInput = document.getElementById('httpolaroid-url');
  const agentSel = document.getElementById('httpolaroid-agent');
  const refChk = document.getElementById('httpolaroid-ref');
  const harChk = document.getElementById('httpolaroid-har');
  const captureBtn = document.getElementById('httpolaroid-capture-btn');
  const tableDiv = document.getElementById('httpolaroid-table');
  const deleteBtn = document.getElementById('httpolaroid-delete-btn');
  const closeBtn = document.getElementById('httpolaroid-close-btn');
  const toggleBtn = document.getElementById('httpolaroid-toggle-btn');
  const logBox = document.getElementById('httpolaroid-log');
  const debugEnabled = new URLSearchParams(location.search).get('debug') === '1';
  if(logBox && !debugEnabled){
    logBox.style.display = 'none';
  }
  let tableData = [];
  let sortField = 'created_at';
  let sortDir = 'desc';

  const initParams = new URLSearchParams(location.search);
  const presetUrl = initParams.get('url');
  if(presetUrl) urlInput.value = presetUrl;

  function humanReadableSize(size){
    const units = ['B','KB','MB','GB','TB'];
    let i = 0;
    while(size >= 1024 && i < units.length-1){
      size /= 1024;
      i++;
    }
    return size.toFixed(1) + ' ' + units[i];
  }

  function makeResizable(table, key){
    if(typeof makeResizableTable === 'function'){
      makeResizableTable(table, key);
    }
  }

  function render(){
    const sorted = tableData.slice().sort((a,b)=>{
      const av = (a[sortField] || '').toString().toLowerCase();
      const bv = (b[sortField] || '').toString().toLowerCase();
      if(av < bv) return sortDir==='asc'? -1:1;
      if(av > bv) return sortDir==='asc'? 1:-1;
      return 0;
    });
    let html = '<table class="table url-table w-100"><colgroup>'+
      '<col class="w-2em"/><col/><col/><col/><col/><col/><col/><col/><col/><col/>'+
      '</colgroup><thead><tr>'+
      '<th class="w-2em checkbox-col no-resize text-center"><input type="checkbox" id="httpolaroid-select-all" class="form-checkbox" /></th>'+
      '<th class="sortable" data-field="created_at">Time</th>'+
      '<th class="sortable" data-field="url">URL</th>'+
      '<th class="sortable" data-field="status_code">Status</th>'+
      '<th class="sortable" data-field="ip_addresses">IPs</th>'+
      '<th class="sortable" data-field="method">Method</th>'+
      '<th>ZIP</th><th>HAR</th><th class="sortable" data-field="zip_size">Size</th><th>Screenshot</th>'+
      '</tr></thead><tbody>';
    for(const row of sorted){
      const img = `<img src="${row.preview}" class="screenshot-thumb"/>`;
      html += `<tr data-id="${row.id}"><td class="checkbox-col"><input type="checkbox" class="row-checkbox" value="${row.id}"/></td>`+
        `<td>${row.created_at}</td>`+
        `<td><div class="cell-content">${row.url}</div></td>`+
        `<td>${row.status_code}</td>`+
        `<td>${row.ip_addresses}</td>`+
        `<td>${row.method}</td>`+
        `<td><a href="${row.zip}" download>ZIP</a></td>`+
        `<td><a href="${row.har}" target="_blank">HAR</a></td>`+
        `<td>${humanReadableSize(row.zip_size)}</td>`+
        `<td><a href="${row.image}" target="_blank">${img}</a></td></tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
    tableDiv.querySelectorAll('.screenshot-thumb').forEach(img => {
      img.addEventListener('click', () => {
        img.classList.toggle('thumb-hidden');
      });
    });
    const selAll = document.getElementById('httpolaroid-select-all');
    if(selAll){
      selAll.addEventListener('change', () => {
        tableDiv.querySelectorAll('.row-checkbox').forEach(c => c.checked = selAll.checked);
      });
    }
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
    makeResizable(table, 'httpolaroid-col-widths');
  }

  async function loadRows(){
    try{
      const resp = await fetch('/httpolaroids');
      const data = await resp.json();
      tableData = Array.isArray(data) ? data : [];
      render();
    }catch{}
  }

  captureBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if(!url) return;
    const params = new URLSearchParams({url, agent: agentSel.value, spoof_referrer: refChk.checked ? '1':'0'});
    if(harChk && harChk.checked) params.set('har','1');
    if(debugEnabled) params.set('debug', '1');
    const resp = await fetch('/tools/httpolaroid', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    if(resp.ok){
      const data = await resp.json();
      if(debugEnabled && logBox) logBox.value = data.log || '';
      await loadRows();
    } else { alert(await resp.text()); }
  });

  deleteBtn.addEventListener('click', async () => {
    const ids = Array.from(tableDiv.querySelectorAll('.row-checkbox:checked')).map(c=>c.value);
    if(!ids.length) return;
    const params = new URLSearchParams();
    ids.forEach(id => params.append('ids', id));
    await fetch('/delete_httpolaroids', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    loadRows();
  });

  if(toggleBtn){
    toggleBtn.addEventListener('click', () => {
      const imgs = tableDiv.querySelectorAll('.screenshot-thumb');
      const anyVisible = Array.from(imgs).some(img => !img.classList.contains('thumb-hidden'));
      imgs.forEach(img => img.classList.toggle('thumb-hidden', anyVisible));
    });
  }

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/httpolaroid'){
      history.pushState({}, '', '/');
    }
  });
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });

  window.loadHttpolaroidRows = loadRows;
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initHttpolaroid);
}else{
  initHttpolaroid();
}
