/* File: static/layerpeek.js */
function initLayerpeek(){
  const overlay = document.getElementById('layerslayer-overlay');
  if(!overlay) return;
  const imageInput = document.getElementById('layerslayer-image');
  const fetchBtn = document.getElementById('layerslayer-fetch-btn');
  const tableDiv = document.getElementById('layerslayer-table');
  const closeBtn = document.getElementById('layerslayer-close-btn');

  function render(data){
    let html = '';
    for(const plat of data){
      html += `<h4>${plat.os}/${plat.architecture}</h4>`;
      html += '<table class="table url-table w-100"><thead><tr><th>Digest</th><th>Size</th><th>Files</th></tr></thead><tbody>';
      for(const layer of plat.layers){
        const files = layer.files.map(f=>`<li>${f}</li>`).join('');
        html += `<tr><td class="w-25em"><div class="cell-content">${layer.digest}</div></td><td>${layer.size}</td><td><ul>${files}</ul></td></tr>`;
      }
      html += '</tbody></table>';
    }
    tableDiv.innerHTML = html;
  }

  fetchBtn.addEventListener('click', async () => {
    const img = imageInput.value.trim();
    if(!img) return;
    const resp = await fetch('/docker_layers?image=' + encodeURIComponent(img));
    if(resp.ok){
      const data = await resp.json();
      render(data);
    } else {
      alert(await resp.text());
    }
  });

  closeBtn.addEventListener('click', () => {
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
