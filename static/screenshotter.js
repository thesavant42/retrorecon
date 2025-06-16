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
  let tableData = [];

  function render(){
    let html = '<table class="table url-table w-100"><thead><tr>'+
      '<th class="checkbox-col no-resize text-center"><input type="checkbox" id="shot-select-all" class="form-checkbox" /></th>'+
      '<th>Time</th><th>URL</th><th>Method</th><th>Thumbnail</th>'+
      '</tr></thead><tbody>';
    for(const row of tableData){
      const img = `<img src="${row.preview}" class="screenshot-thumb"/>`;
      html += `<tr data-id="${row.id}"><td class="checkbox-col"><input type="checkbox" class="row-checkbox" value="${row.id}"/></td>`+
        `<td>${row.created_at}</td>`+
        `<td><div class="cell-content">${row.url}</div></td>`+
        `<td>${row.method}</td>`+
        `<td><a href="${row.file}" target="_blank">${img}</a></td></tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
    const selAll = document.getElementById('shot-select-all');
    if(selAll){
      selAll.addEventListener('change', () => {
        tableDiv.querySelectorAll('.row-checkbox').forEach(c => c.checked = selAll.checked);
      });
    }
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

  loadShots();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initScreenshotter);
}else{
  initScreenshotter();
}
