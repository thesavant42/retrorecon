/* File: static/layerpeek.js */
function initLayerpeek(){
  console.log('[Layerpeek] initializing');
  const overlay = document.getElementById('layerslayer-overlay');
  if(!overlay){
    console.warn('[Layerpeek] overlay element not found');
    return;
  }
  const imageInput = document.getElementById('layerslayer-image');
  const fetchBtn = document.getElementById('layerslayer-fetch-btn');
  const tableDiv = document.getElementById('layerslayer-table');
  const infoDiv = document.getElementById('layerslayer-info');
  const consoleDiv = document.getElementById('layerslayer-console');
  const closeBtn = document.getElementById('layerslayer-close-btn');
  const statusSpan = document.getElementById('layerslayer-status');

  function logStatus(msg){
    if(!consoleDiv) return;
    consoleDiv.textContent += msg + '\n';
    consoleDiv.scrollTop = consoleDiv.scrollHeight;
  }

  let statusTimer = null;
  let statusDelay = 1000;
  function pollStatus(){
    if(overlay.classList.contains('hidden')){ statusTimer = null; return; }
    fetch('/status')
      .then(r => r.status === 204 ? null : r.json())
      .then(data => {
        if(data && data.code && data.code.startsWith('layerpeek')){
          logStatus(data.message || data.code);
          statusDelay = 1000;
        }else{
          statusDelay = Math.min(statusDelay * 2, 3000);
        }
        statusTimer = setTimeout(pollStatus, statusDelay);
      })
      .catch(() => { statusTimer = setTimeout(pollStatus, 5000); });
  }

  function startPolling(){
    consoleDiv.textContent = '';
    if(!statusTimer) pollStatus();
  }

  function makeResizable(table, key){
    if(typeof makeResizableTable === 'function'){
      makeResizableTable(table, key);
    }
  }

  function render(data){
    console.log('[Layerpeek] rendering data', data);
    const plats = Array.isArray(data) ? data : data.platforms;
    let headerHtml = '';
    if(!Array.isArray(data)){
      const ownerUrl = `https://hub.docker.com/u/${data.owner}`;
      const repoUrl = `https://hub.docker.com/r/${data.owner}/${data.repo}/tags`;
      const manifestUrl = `https://hub.docker.com/layers/${data.owner}/${data.repo}/${data.tag}/images/${data.manifest}`;
      headerHtml = `Owner: <a href="${ownerUrl}" target="_blank">${data.owner}</a> | ` +
                   `Image: <a href="${repoUrl}" target="_blank">${data.repo}</a> | ` +
                   `Tag: <a href="${repoUrl}" target="_blank">${data.tag}</a> | ` +
                   `Manifest: <a href="${manifestUrl}" target="_blank">${data.manifest}</a>`;
    }
    infoDiv.innerHTML = headerHtml;
    let html = '';
    for(const plat of plats){
      console.log('[Layerpeek] platform', plat.os, plat.architecture);
      html += `<h4>${plat.os}/${plat.architecture}</h4>`;
      html += '<table class="table url-table w-100"><colgroup><col/><col class="w-6em"/><col/><col class="w-6em"/></colgroup><thead><tr><th>Digest</th><th>Size</th><th>Files</th><th>Download</th></tr></thead><tbody>';
      for(const layer of plat.layers){
        console.log('[Layerpeek] layer', layer.digest);
        const files = layer.files.map(f=>`<li>${f}</li>`).join('');
        const filesHtml = `<details><summary>${layer.files.length} files</summary><ul>${files}</ul></details>`;
        html += `<tr><td class="w-25em"><div class="cell-content">${layer.digest}</div></td><td>${layer.size}</td><td>${filesHtml}</td><td><a href="${layer.download}">Get</a></td></tr>`;
      }
      html += '</tbody></table>';
    }
    tableDiv.innerHTML = html;
    tableDiv.querySelectorAll('table').forEach(t => makeResizable(t, 'layerpeek-col-widths'));
  }

  fetchBtn.addEventListener('click', async () => {
    const img = imageInput.value.trim();
    if(!img) return;
    console.log('[Layerpeek] fetch layers for', img);
    startPolling();
    fetchBtn.disabled = true;
    const oldText = fetchBtn.textContent;
    if(statusSpan) statusSpan.textContent = 'Fetching...';
    try {
      const resp = await fetch('/docker_layers?image=' + encodeURIComponent(img));
      if(resp.ok){
        const data = await resp.json();
        render(data);
      } else {
        console.error('[Layerpeek] server responded', resp.status);
        let msg;
        try {
          const err = await resp.json();
          msg = err.details ? `${err.error}: ${err.details}` : err.error;
        } catch {
          msg = await resp.text();
        }
        console.error('[Layerpeek] error', msg);
        alert(msg);
      }
    } catch(err){
      console.error('[Layerpeek] fetch failed', err);
      alert('Error: ' + err);
    } finally {
      fetchBtn.disabled = false;
      fetchBtn.textContent = oldText;
      if(statusSpan) statusSpan.textContent = '';
    }
  });

  closeBtn.addEventListener('click', () => {
    console.log('[Layerpeek] closing overlay');
    overlay.classList.add('hidden');
    if(statusTimer){
      clearTimeout(statusTimer);
      statusTimer = null;
    }
    if(location.pathname === '/tools/layerpeek'){
      history.pushState({}, '', '/');
    }
  });
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initLayerpeek);
}else{
  initLayerpeek();
}
