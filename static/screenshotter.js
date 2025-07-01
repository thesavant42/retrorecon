/* File: static/screenshotter.js */
function initScreenshotter(){
  const overlay = document.getElementById('screenshot-overlay');
  if(!overlay) return;
  const urlInput = document.getElementById('screenshot-url');
  const agentSel = document.getElementById('screenshot-agent');
  const refChk = document.getElementById('screenshot-ref');
  const captureBtn = document.getElementById('screenshot-capture-btn');
  const tableDiv = document.getElementById('screenshot-table');
  const deleteBtn = document.getElementById('screenshot-delete-btn');
  const closeBtn = document.getElementById('screenshot-close-btn');
  const toggleBtn = document.getElementById('screenshot-toggle-btn');
  const logBox = document.getElementById('screenshot-log');
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

  let statusTimer = null;
  let statusDelay = 1000;

  function pollStatus(){
    if(overlay.classList.contains('hidden')){ statusTimer = null; return; }
    fetch('/status')
      .then(r => r.status === 204 ? null : r.json())
      .then(data => {
        if(data && data.code && data.code.startsWith('screenshot')){
          if(window.showStatus) window.showStatus(data.message || data.code);
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

  function makeResizable(table, key){
    if(typeof makeResizableTable === 'function'){
      makeResizableTable(table, key);
    }
  }

  function render(){
    const widths = window.getColWidths ? window.getColWidths('screenshot-col-widths', 7) : {};
    const sorted = tableData.slice().sort((a,b)=>{
      const av = (a[sortField] || '').toString().toLowerCase();
      const bv = (b[sortField] || '').toString().toLowerCase();
      if(av < bv) return sortDir==='asc'? -1:1;
      if(av > bv) return sortDir==='asc'? 1:-1;
      return 0;
    });
    let html = '<table class="table url-table w-100"><colgroup>'+
      `<col class="w-2em"${widths[0]?` style=\"width:${widths[0]}\"`:''}/>`+
      `<col${widths[1]?` style=\"width:${widths[1]}\"`:''}/>`+
      `<col${widths[2]?` style=\"width:${widths[2]}\"`:''}/>`+
      `<col${widths[3]?` style=\"width:${widths[3]}\"`:''}/>`+
      `<col${widths[4]?` style=\"width:${widths[4]}\"`:''}/>`+
      `<col${widths[5]?` style=\"width:${widths[5]}\"`:''}/>`+
      `<col${widths[6]?` style=\"width:${widths[6]}\"`:''}/>`+
      '</colgroup><thead><tr>'+
      `<th class="w-2em checkbox-col no-resize text-center"${widths[0]?` style=\"width:${widths[0]}\"`:''}><input type="checkbox" id="shot-select-all" class="form-checkbox" /></th>`+
      `<th class="sortable" data-field="created_at"${widths[1]?` style=\"width:${widths[1]}\"`:''}>Time</th>`+
      `<th class="sortable" data-field="url"${widths[2]?` style=\"width:${widths[2]}\"`:''}>URL</th>`+
      `<th class="sortable" data-field="status_code"${widths[3]?` style=\"width:${widths[3]}\"`:''}>Status</th>`+
      `<th class="sortable" data-field="ip_addresses"${widths[4]?` style=\"width:${widths[4]}\"`:''}>IPs</th>`+
      `<th class="sortable" data-field="method"${widths[5]?` style=\"width:${widths[5]}\"`:''}>Method</th>`+
      `<th${widths[6]?` style=\"width:${widths[6]}\"`:''}>Thumbnail</th>`+
      '</tr></thead><tbody>';
    for(const row of sorted){
      const img = `<img src="${row.preview}" class="screenshot-thumb"/>`;
      html += `<tr data-id="${row.id}"><td class="checkbox-col"><input type="checkbox" class="row-checkbox" value="${row.id}"/></td>`+
        `<td>${row.created_at}</td>`+
        `<td><div class="cell-content">${row.url}</div></td>`+
        `<td>${row.status_code}</td>`+
        `<td>${row.ip_addresses}</td>`+
        `<td>${row.method}</td>`+
        `<td><a href="${row.file}" target="_blank">${img}</a></td></tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
    tableDiv.querySelectorAll('.screenshot-thumb').forEach(img => {
      img.addEventListener('click', () => {
        img.classList.toggle('thumb-hidden');
      });
    });
    const selAll = document.getElementById('shot-select-all');
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
    makeResizable(table, 'screenshot-col-widths');
  }

  async function loadShots(){
    try{
      const resp = await fetch('/screenshots');
      const data = await resp.json();
      if(Array.isArray(data)) tableData = data; else tableData = [];
      render();
    }catch{}
  }

  captureBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if(!url) return;
    const params = new URLSearchParams({url, agent: agentSel.value, spoof: refChk.checked ? '1':'0'});
    if(debugEnabled) params.set('debug', '1');
    startStatusPolling();
    const resp = await fetch('/tools/screenshot', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    if(resp.ok){
      const data = await resp.json();
      if(debugEnabled && logBox) logBox.value = data.log || '';
      await loadShots();
    } else { alert(await resp.text()); }
  });

  deleteBtn.addEventListener('click', async () => {
    const ids = Array.from(tableDiv.querySelectorAll('.row-checkbox:checked')).map(c=>c.value);
    if(!ids.length) return;
    const params = new URLSearchParams();
    ids.forEach(id => params.append('ids', id));
    await fetch('/delete_screenshots', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    loadShots();
  });

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    stopStatusPolling();
    if(location.pathname === '/tools/screenshotter'){
      history.pushState({}, '', '/');
    }
  });
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });

  if(toggleBtn){
    toggleBtn.addEventListener('click', () => {
      const imgs = tableDiv.querySelectorAll('.screenshot-thumb');
      const anyVisible = Array.from(imgs).some(img => !img.classList.contains('thumb-hidden'));
      imgs.forEach(img => img.classList.toggle('thumb-hidden', anyVisible));
    });
  }

  window.loadScreenshotRows = loadShots;
  window.startScreenshotStatus = startStatusPolling;
  window.stopScreenshotStatus = stopStatusPolling;
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initScreenshotter);
}else{
  initScreenshotter();
}
