/* File: static/dag_explorer.js */
function initDagExplorer(){
  const overlay = document.getElementById('dag-explorer-overlay');
  if(!overlay) return;
  const imgInput = document.getElementById('dag-image');
  const fetchBtn = document.getElementById('dag-fetch-btn');
  const tagsBtn = document.getElementById('dag-tags-btn');
  const closeBtn = document.getElementById('dag-close-btn');
  const output = document.getElementById('dag-output');

  async function fetchManifest(){
    const img = imgInput.value.trim();
    if(!img) return;
    const resp = await fetch('/dag/image/' + encodeURIComponent(img));
    output.textContent = await resp.text();
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
