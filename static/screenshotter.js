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
  let tableData = [];
  let sortField = 'created_at';
  let sortDir = 'desc';

  const initParams = new URLSearchParams(location.search);
  const presetUrl = initParams.get('url');
  if(presetUrl) urlInput.value = presetUrl;

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

  function render(){
    const sorted = tableData.slice().sort((a,b)=>{
      const av = (a[sortField] || '').toString().toLowerCase();
      const bv = (b[sortField] || '').toString().toLowerCase();
      if(av < bv) return sortDir==='asc'? -1:1;
      if(av > bv) return sortDir==='asc'? 1:-1;
      return 0;
    });
    let html = '<table class="table url-table w-100"><colgroup>'+
      '<col class="w-2em"/><col/><col/><col/><col/><col/><col/>'+
      '</colgroup><thead><tr>'+
      '<th class="w-2em checkbox-col no-resize text-center"><input type="checkbox" id="shot-select-all" class="form-checkbox" /></th>'+
      '<th class="sortable" data-field="created_at">Time</th>'+
      '<th class="sortable" data-field="url">URL</th>'+
      '<th class="sortable" data-field="status_code">Status</th>'+
      '<th class="sortable" data-field="ip_addresses">IPs</th>'+
      '<th class="sortable" data-field="method">Method</th>'+
      '<th>Thumbnail</th>'+
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
    const resp = await fetch('/tools/screenshot', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    if(resp.ok){ await loadShots(); } else { alert(await resp.text()); }
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
    if(location.pathname === '/tools/screenshotter'){
      history.pushState({}, '', '/');
    }
  });

  if(toggleBtn){
    toggleBtn.addEventListener('click', () => {
      const imgs = tableDiv.querySelectorAll('.screenshot-thumb');
      const anyVisible = Array.from(imgs).some(img => !img.classList.contains('thumb-hidden'));
      imgs.forEach(img => img.classList.toggle('thumb-hidden', anyVisible));
    });
  }

  loadShots();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initScreenshotter);
}else{
  initScreenshotter();
}
