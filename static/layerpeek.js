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
  const closeBtn = document.getElementById('layerslayer-close-btn');

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
      html += '<table class="table url-table w-100"><thead><tr><th>Digest</th><th>Size</th><th>Files</th><th>Download</th></tr></thead><tbody>';
      for(const layer of plat.layers){
        console.log('[Layerpeek] layer', layer.digest);
        const files = layer.files.map(f=>`<li>${f}</li>`).join('');
        const filesHtml = `<details><summary>${layer.files.length} files</summary><ul>${files}</ul></details>`;
        html += `<tr><td class="w-25em"><div class="cell-content">${layer.digest}</div></td><td>${layer.size}</td><td>${filesHtml}</td><td><a href="${layer.download}">Get</a></td></tr>`;
      }
      html += '</tbody></table>';
    }
    tableDiv.innerHTML = html;
  }

  fetchBtn.addEventListener('click', async () => {
    const img = imageInput.value.trim();
    if(!img) return;
    console.log('[Layerpeek] fetch layers for', img);
    fetchBtn.disabled = true;
    const oldText = fetchBtn.textContent;
    fetchBtn.textContent = 'Fetching...';
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
    }
  });

  closeBtn.addEventListener('click', () => {
    console.log('[Layerpeek] closing overlay');
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/layerpeek'){
      history.pushState({}, '', '/');
    }
  });
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initLayerpeek);
}else{
  initLayerpeek();
}
