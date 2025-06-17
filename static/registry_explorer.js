/* File: static/registry_explorer.js */
function initRegistryExplorer(){
  const overlay = document.getElementById('registry-explorer-overlay');
  if(!overlay) return;
  const imageInput = document.getElementById('registry-image');
  const methodChecks = overlay.querySelectorAll('input[name="registry-method"]');
  const fetchBtn = document.getElementById('registry-fetch-btn');
  const closeBtn = document.getElementById('registry-close-btn');
  const tableDiv = document.getElementById('registry-table');
  const infoDiv = document.getElementById('registry-info');

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

  function buildTables(plats, img){
    let html = '';
    for(const plat of plats){
      html += `<h4>${plat.os}/${plat.architecture}</h4>`;
      html += '<table class="table url-table w-100"><colgroup>'+
               '<col/><col class="w-6em"/><col/><col class="w-6em"/>'+
               '</colgroup><thead><tr>'+
               '<th class="sortable" data-field="digest">Digest</th>'+
               '<th class="sortable" data-field="size">Size</th>'+
               '<th>Files</th><th>Download</th>'+
               '</tr></thead><tbody>';
      for(const layer of plat.layers){
        const files = layer.files.map(f=>`<li>${f}</li>`).join('');
        const filesHtml = `<details><summary>${layer.files.length} files</summary><ul>${files}</ul></details>`;
        const dlink = `/download_layer?image=${encodeURIComponent(img)}&digest=${encodeURIComponent(layer.digest)}`;
        html += `<tr><td class="w-25em"><div class="cell-content">${layer.digest}</div></td>`+
                `<td>${layer.size}</td><td>${filesHtml}</td>`+
                `<td><a href="${dlink}">Get</a></td></tr>`;
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
        html += buildTables(data.results[m], imgRef);
      }
    } else {
      html = buildTables(data.platforms, imgRef);
    }
    tableDiv.innerHTML = html;
    tableDiv.querySelectorAll('table').forEach(t=>{ attachSort(t); makeResizable(t,'registry-col-widths'); });
  }

  fetchBtn.addEventListener('click', async () => {
    const img = imageInput.value.trim();
    if(!img) return;
    const methods = Array.from(methodChecks).filter(c=>c.checked).map(c=>c.value);
    let url = '/registry_explorer?image=' + encodeURIComponent(img);
    if(methods.length === 1){
      url += '&method=' + encodeURIComponent(methods[0]);
    }else if(methods.length > 1){
      url += '&methods=' + methods.map(encodeURIComponent).join(',');
    }
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
    if(location.pathname === '/tools/registry_viewer'){
      history.pushState({}, '', '/');
    }
  });
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initRegistryExplorer);
}else{
  initRegistryExplorer();
}
