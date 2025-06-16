/* File: static/site2zip.js */
function initSite2Zip(){
  const overlay = document.getElementById('sitezip-overlay');
  if(!overlay) return;
  const urlInput = document.getElementById('sitezip-url');
  const agentSel = document.getElementById('sitezip-agent');
  const refChk = document.getElementById('sitezip-ref');
  const captureBtn = document.getElementById('sitezip-capture-btn');
  const tableDiv = document.getElementById('sitezip-table');
  const deleteBtn = document.getElementById('sitezip-delete-btn');
  const closeBtn = document.getElementById('sitezip-close-btn');
  let tableData = [];

  function render(){
    let html = '<table class="table url-table w-100"><thead><tr>'+
      '<th class="checkbox-col no-resize text-center"><input type="checkbox" id="sitezip-select-all" class="form-checkbox" /></th>'+
      '<th>Time</th><th>URL</th><th>Method</th><th>ZIP</th><th>Screenshot</th>'+
      '</tr></thead><tbody>';
    for(const row of tableData){
      const img = `<img src="${row.preview}" class="screenshot-thumb"/>`;
      html += `<tr data-id="${row.id}"><td class="checkbox-col"><input type="checkbox" class="row-checkbox" value="${row.id}"/></td>`+
        `<td>${row.created_at}</td>`+
        `<td><div class="cell-content">${row.url}</div></td>`+
        `<td>${row.method}</td>`+
        `<td><a href="${row.zip}" download>ZIP</a></td>`+
        `<td><a href="${row.preview}" target="_blank">${img}</a></td></tr>`;
    }
    html += '</tbody></table>';
    tableDiv.innerHTML = html;
    const selAll = document.getElementById('sitezip-select-all');
    if(selAll){
      selAll.addEventListener('change', () => {
        tableDiv.querySelectorAll('.row-checkbox').forEach(c => c.checked = selAll.checked);
      });
    }
  }

  async function loadRows(){
    try{
      const resp = await fetch('/sitezips');
      const data = await resp.json();
      tableData = Array.isArray(data) ? data : [];
      render();
    }catch{}
  }

  captureBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if(!url) return;
    const params = new URLSearchParams({url, agent: agentSel.value, spoof_referrer: refChk.checked ? '1':'0'});
    const resp = await fetch('/tools/site2zip', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    if(resp.ok){ await loadRows(); } else { alert(await resp.text()); }
  });

  deleteBtn.addEventListener('click', async () => {
    const ids = Array.from(tableDiv.querySelectorAll('.row-checkbox:checked')).map(c=>c.value);
    if(!ids.length) return;
    const params = new URLSearchParams();
    ids.forEach(id => params.append('ids', id));
    await fetch('/delete_sitezips', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: params});
    loadRows();
  });

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/site2zip'){
      history.pushState({}, '', '/');
    }
  });

  loadRows();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initSite2Zip);
}else{
  initSite2Zip();
}
