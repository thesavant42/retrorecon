/* File: static/dag_explorer.js */
function initDagExplorer(){
  const overlay = document.getElementById('dag-explorer-overlay');
  if(!overlay) return;
  const imgInput = document.getElementById('dag-image');
  const fetchBtn = document.getElementById('dag-fetch-btn');
  const tagsBtn = document.getElementById('dag-tags-btn');
  const closeBtn = document.getElementById('dag-close-btn');
  const output = document.getElementById('dag-output');
  const manifestDiv = document.getElementById('dag-manifest');

  function buildTable(manifest, img){
    const layers = manifest.layers || [];
    let html = '<table class="table url-table w-100"><thead><tr>'+
               '<th>Digest</th><th>Size</th><th>Files</th></tr></thead><tbody>';
    for(const layer of layers){
      const link = `<a href="#" class="layer-link" data-digest="${layer.digest}">${layer.digest}</a>`;
      html += `<tr><td>${link}</td><td>${layer.size || layer.size_bytes || ''}</td><td></td></tr>`;
    }
    html += '</tbody></table>';
    return html;
  }

  async function fetchManifest(){
    const img = imgInput.value.trim();
    if(!img) return;
    const resp = await fetch('/dag/image/' + encodeURIComponent(img));
    if(resp.ok){
      const data = await resp.json();
      manifestDiv.innerHTML = buildTable(data, img);
    } else {
      manifestDiv.textContent = await resp.text();
    }
  }

  async function fetchTags(){
    const img = imgInput.value.trim();
    if(!img) return;
    const repo = img.split(':')[0];
    const resp = await fetch('/dag/repo/' + encodeURIComponent(repo));
    output.textContent = await resp.text();
  }

  fetchBtn.addEventListener('click', fetchManifest);
  tagsBtn.addEventListener('click', fetchTags);
  manifestDiv.addEventListener('click', async ev => {
    const link = ev.target.closest('.layer-link');
    if(!link) return;
    ev.preventDefault();
    const digest = link.dataset.digest;
    const img = imgInput.value.trim();
    if(!digest || !img) return;
    const resp = await fetch(`/dag/layer/${encodeURIComponent(digest)}?image=${encodeURIComponent(img)}`);
    if(resp.ok){
      const data = await resp.json();
      output.textContent = data.files.join('\n');
    }else{
      output.textContent = await resp.text();
    }
  });
  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/dag_explorer'){ history.pushState({}, '', '/'); }
  });
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initDagExplorer);
}else{
  initDagExplorer();
}
