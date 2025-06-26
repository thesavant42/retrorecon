/* File: static/oci_explorer.js */
function initRegistryExplorer(){
  const overlay = document.getElementById('registry-explorer-overlay');
  if(!overlay) return;
  const imageInput = document.getElementById('registry-image');
  const fetchBtn = document.getElementById('registry-fetch-btn');
  const closeBtn = document.getElementById('registry-close-btn');
  const tableDiv = document.getElementById('registry-table');
  const infoDiv = document.getElementById('registry-info');
  const bkTableBody = document.getElementById('registry-bookmark-table-body');
  const bkAddCurrentBtn = document.getElementById('registry-add-bookmark-btn');

  function escapeHtml(str){
    return str.replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));
  }

  function loadBookmarks(){
    try{ return JSON.parse(localStorage.getItem('ociBookmarks')||'[]'); }catch{ return []; }
  }
  function saveBookmarks(arr){
    localStorage.setItem('ociBookmarks', JSON.stringify(arr));
  }
  function renderBookmarks(){
    if(!bkTableBody) return;
    const bks = loadBookmarks();
    bkTableBody.innerHTML = bks.map((b,i)=>
      `<tr data-idx="${i}"><td><a class="mt" href="${b.addr}">${escapeHtml(b.addr)}</a></td>`+
      `<td>${escapeHtml(b.note||'')}</td>`+
      `<td class="bookmark-actions"><button type="button" class="btn btn--small edit-btn">Edit</button>`+
      `<button type="button" class="btn btn--small delete-btn">X</button></td></tr>`
    ).join('');
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

  function attachSort(table){
    const tbody = table.querySelector('tbody');
    table.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', ev => {
        if(ev.target.closest('.col-resizer')) return;
        const idx = Array.from(th.parentNode.children).indexOf(th);
        const dir = th.dataset.sort === 'asc' ? 'desc' : 'asc';
        th.dataset.sort = dir;
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort((a,b)=>{
          const av = a.children[idx].textContent.trim();
          const bv = b.children[idx].textContent.trim();
          const nA = parseInt(av.replace(/[^0-9]/g,''));
          const nB = parseInt(bv.replace(/[^0-9]/g,''));
          if(!isNaN(nA) && !isNaN(nB)){
            return dir==='asc'? nA-nB : nB-nA;
          }
          return dir==='asc'? av.localeCompare(bv):bv.localeCompare(av);
        });
        rows.forEach(r=>tbody.appendChild(r));
      });
    });
  }

  function buildTables(plats, img, manifestDigest){
    let html = '';
    for(const plat of plats){
      const label = (plat.os || plat.architecture)
        ? `${plat.os || '?'} / ${plat.architecture || '?'}`
        : 'Unknown platform';
      html += `<h4>${label}</h4>`;
      html += '<table class="table url-table w-100"><colgroup>'+
               '<col class="digest-col"/><col class="w-6em"/><col/>'+
               '<col class="w-6em download-col"/><col class="w-6em delete-col"/>'+
               '</colgroup><thead><tr>'+
               '<th class="sortable" data-field="digest">Digest</th>'+
               '<th class="sortable" data-field="size">Size</th>'+
               '<th>Files</th>'+
               '<th class="text-center no-resize">Download</th>'+
               '<th class="text-center no-resize">Delete</th>'+
               '</tr></thead><tbody>';
      for(const layer of plat.layers){
        const files = layer.files.map(f=>{
          const p = f.split('/').map(encodeURIComponent).join('/');
          const imgEnc = img.split('/').map(encodeURIComponent).join('/');
          const href = manifestDigest
            ? `/layers/${imgEnc}@${manifestDigest}/${p}`
            : `/layers/${imgEnc}/${p}`;
          return `<li><a class="mt" href="${href}" target="_blank">${f}</a></li>`;
        }).join('');
        const filesHtml = `<details><summary>${layer.files.length} files</summary><ul>${files}</ul></details>`;
        const dlink = `/download_layer?image=${encodeURIComponent(img)}&digest=${encodeURIComponent(layer.digest)}`;
        html += `<tr><td><div class="cell-content">${layer.digest}</div></td>`+
                `<td>${layer.size}</td><td>${filesHtml}</td>`+
                `<td class="text-center"><a href="${dlink}">Get</a></td>`+
                `<td class="text-center"><button type="button" class="btn delete-entry-btn">X</button></td></tr>`;
      }
      html += '</tbody></table>';
    }
    return html;
  }

  function render(data){
    const ownerUrl = `https://hub.docker.com/u/${data.owner}`;
    const repoUrl = `https://hub.docker.com/r/${data.owner}/${data.repo}/tags`;
    const manifestUrl = `https://hub.docker.com/layers/${data.owner}/${data.repo}/${data.tag}/images/${data.manifest}`;
    infoDiv.innerHTML = `Owner: <a href="${ownerUrl}" target="_blank">${data.owner}</a> | `+
                        `Image: <a href="${repoUrl}" target="_blank">${data.repo}</a> | `+
                        `Tag: <a href="${repoUrl}" target="_blank">${data.tag}</a> | `+
                        `Manifest: <a href="${manifestUrl}" target="_blank">${data.manifest}</a>`;
    let html = '';
    const imgRef = `${data.owner}/${data.repo}:${data.tag}`;
    if(data.results){
      for(const m of data.methods){
        html += `<h3>${m}</h3>`;
        html += buildTables(data.results[m], imgRef, data.manifest);
      }
    } else {
      html = buildTables(data.platforms, imgRef, data.manifest);
    }
    tableDiv.innerHTML = html;
    tableDiv.querySelectorAll('table').forEach(t=>{ attachSort(t); makeResizable(t,'registry-col-widths'); });
  }

  tableDiv.addEventListener('click', ev => {
    const btn = ev.target.closest('.delete-entry-btn');
    if(btn){
      const row = btn.closest('tr');
      if(row) row.remove();
    }
  });

  if(bkAddCurrentBtn){
    bkAddCurrentBtn.addEventListener('click', () => {
      const addr = imageInput.value.trim();
      if(!addr) return;
      const bks = loadBookmarks();
      if(!bks.find(b => b.addr === addr)){
        bks.push({addr, note: ''});
        saveBookmarks(bks);
        renderBookmarks();
      }
    });
  }
  if(bkTableBody){
    bkTableBody.addEventListener('click', ev => {
      const row = ev.target.closest('tr');
      if(!row) return;
      const idx = Number(row.dataset.idx);
      const bks = loadBookmarks();
      if(ev.target.classList.contains('edit-btn')){
        const note = prompt('Edit note', bks[idx].note||'');
        if(note===null) return;
        bks[idx].note = note;
        saveBookmarks(bks);
        renderBookmarks();
      }else if(ev.target.classList.contains('delete-btn')){
        bks.splice(idx,1);
        saveBookmarks(bks);
        renderBookmarks();
      }
    });
  }

  renderBookmarks();

  fetchBtn.addEventListener('click', async () => {
    const img = imageInput.value.trim();
    if(!img) return;
    const url = '/oci_explorer_api?image=' + encodeURIComponent(img);
    fetchBtn.disabled = true;
    const oldText = fetchBtn.textContent;
    fetchBtn.textContent = 'Fetching...';
    try{
      const resp = await fetch(url);
      if(resp.ok){
        const data = await resp.json();
        render(data);
      } else {
        alert(await resp.text());
      }
    }catch(err){ alert('Error: '+err); }
    finally{ fetchBtn.disabled=false; fetchBtn.textContent=oldText; }
  });

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/oci_explorer'){
      history.pushState({}, '', '/');
    }
  });
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initRegistryExplorer);
}else{
  initRegistryExplorer();
}
