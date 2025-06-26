/* File: static/jwt_tools.js */
function initJWTTools(){
  const overlay = document.getElementById('jwt-tools-overlay');
  if(!overlay) return;
  const input = document.getElementById('jwt-tool-input');
  const secret = document.getElementById('jwt-secret');
  const decodeBtn = document.getElementById('jwt-decode-btn');
  const encodeBtn = document.getElementById('jwt-encode-btn');
  const copyBtn = document.getElementById('jwt-copy-btn');
  const saveBtn = document.getElementById('jwt-save-btn');
  const clearBtn = document.getElementById('jwt-clear-btn');
  const closeBtn = document.getElementById('jwt-close-btn');
  const jarDiv = document.getElementById('jwt-cookie-jar');
  const deleteBtn = document.getElementById('jwt-delete-btn');
  const exportBtn = document.getElementById('jwt-export-btn');
  const editBtn = document.getElementById('jwt-edit-btn');

  let jarData = [];
  let sortField = 'created_at';
  let sortDir = 'desc';

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

  function renderJar(){
    if(!jarDiv) return;
    const sorted = jarData.slice().sort((a,b)=>{
      const av = (a[sortField] || '').toString().toLowerCase();
      const bv = (b[sortField] || '').toString().toLowerCase();
      if(av < bv) return sortDir==='asc'? -1:1;
      if(av > bv) return sortDir==='asc'? 1:-1;
      return 0;
    });
    let html = '<table class="table url-table w-100"><colgroup>'+
      '<col class="w-2em"/><col/><col/><col/><col/><col/><col/>'+
      '</colgroup><thead><tr>'+
      '<th class="w-2em checkbox-col no-resize text-center"><input type="checkbox" id="jwt-select-all" class="form-checkbox" /></th>'+
      '<th class="sortable" data-field="created_at">Time</th>'+
      '<th class="sortable" data-field="issuer">Issuer</th>'+
      '<th class="sortable" data-field="alg">alg</th>'+
      '<th class="sortable" data-field="claims">claims</th>'+
      '<th class="sortable" data-field="notes">Notes</th>'+
      '<th class="sortable" data-field="token">JWT</th>'+
      '</tr></thead><tbody>';
    for(const row of sorted){
      const claims = Array.isArray(row.claims) ? row.claims.join(',') : '';
      html += `<tr data-id="${row.id}"><td class="w-2em checkbox-col"><input type="checkbox" class="row-checkbox" value="${row.id}"/></td>`+
        `<td><div class="cell-content">${row.created_at}</div></td>`+
        `<td><div class="cell-content">${row.issuer||''}</div></td>`+
        `<td><div class="cell-content">${row.alg||''}</div></td>`+
        `<td><div class="cell-content">${claims}</div></td>`+
        `<td><div class="cell-content">${row.notes||''}</div></td>`+
        `<td class="break-all"><div class="cell-content">${row.token}</div></td></tr>`;
    }
    html += '</tbody></table>';
    jarDiv.innerHTML = html;
    const table = jarDiv.querySelector('table');
    jarDiv.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', (ev) => {
        if(ev.target.closest('.col-resizer')) return;
        const field = th.dataset.field;
        if(sortField === field){
          sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        }else{
          sortField = field;
          sortDir = 'asc';
        }
        renderJar();
      });
    });
    const selAll = document.getElementById('jwt-select-all');
    if(selAll){
      selAll.addEventListener('change', () => {
        table.querySelectorAll('.row-checkbox').forEach(c => c.checked = selAll.checked);
      });
    }
    makeResizable(table, 'jwt-col-widths');
  }

  async function loadJar(){
    if(!jarDiv) return;
    try{
      const resp = await fetch('/jwt_cookies');
      const data = await resp.json();
      if(!Array.isArray(data)) return;
      jarData = data;
      renderJar();
    }catch{}
  }

  async function call(url, data, expectJson){
    try{
      const resp = await fetch(url, {
        method:'POST',
        headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body:new URLSearchParams(data)
      });
      if(resp.ok){
          if(expectJson){
            const respData = await resp.json();
          if(respData && respData.error==='no_db'){
              const name = prompt('Enter new database name for JWT log:', 'jwtlog');
              if(name){
                await fetch('/new_db', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({db_name:name}), redirect:'manual'});
              return call(url, data, expectJson);
              }
              return;
          }
          const header = JSON.stringify(respData.header, null, 2);
          const payload = JSON.stringify(respData.payload, null, 2);
          input.value = header + "\n" + payload;
        }else{
          const text = await resp.text();
          input.value = text;
        }
      }else{
        const text = await resp.text();
        alert(text);
      }
    }catch(err){
      alert('Error: '+err);
    }
    loadJar();
  }

  decodeBtn.addEventListener('click', () => {
    call('/tools/jwt_decode', {token: input.value}, true);
  });

  encodeBtn.addEventListener('click', () => {
    call('/tools/jwt_encode', {payload: input.value, secret: secret.value});
  });

  copyBtn.addEventListener('click', async () => {
    try{
      await navigator.clipboard.writeText(input.value);
      copyBtn.textContent = 'Copied!';
      setTimeout(()=>{copyBtn.textContent='Copy';},1000);
    }catch{
      const t=document.createElement('textarea');
      t.value=input.value;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);
    }
  });

  saveBtn.addEventListener('click', () => {
    const blob=new Blob([input.value],{type:'text/plain'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='jwt.txt';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
  });

  clearBtn.addEventListener('click', () => {
    input.value = '';
    secret.value = '';
  });

  if(closeBtn){
    closeBtn.addEventListener('click', () => {
      if(typeof hideJwtTools === 'function'){
        hideJwtTools();
      }else{
        overlay.classList.add('hidden');
        if(location.pathname === '/tools/jwt'){
          history.pushState({}, '', '/');
        }
      }
    });
  }

  function getSelected(){
    return Array.from(jarDiv.querySelectorAll('.row-checkbox:checked')).map(c => c.value);
  }

  if(deleteBtn){
    deleteBtn.addEventListener('click', async () => {
      const ids = getSelected();
      if(!ids.length) return;
      await call('/delete_jwt_cookies', ids.map(id=>['ids',id]));
    });
  }

  if(exportBtn){
    exportBtn.addEventListener('click', async () => {
      const ids = getSelected();
      const params = new URLSearchParams();
      ids.forEach(id => params.append('id', id));
      const resp = await fetch('/export_jwt_cookies?'+params.toString());
      if(resp.ok){
        const data = await resp.json();
        const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
        const url=URL.createObjectURL(blob);
        const a=document.createElement('a');a.href=url;a.download='jwt_cookies.json';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
      }
    });
  }

  if(editBtn){
    editBtn.addEventListener('click', async () => {
      const ids = getSelected();
      if(ids.length!==1) return;
      const row = jarData.find(r=>String(r.id)===ids[0]);
      if(!row) return;
      const notes = prompt('Edit notes:', row.notes||'');
      if(notes===null) return;
      await call('/update_jwt_cookie', {id: row.id, notes});
    });
  }

  loadJar();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initJWTTools);
}else{
  initJWTTools();
}
