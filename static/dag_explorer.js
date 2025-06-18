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

  const SPEC_LINKS = {
    'application/vnd.docker.distribution.manifest.v2+json':
      'https://github.com/opencontainers/image-spec/blob/main/manifest.md',
    'application/vnd.docker.image.rootfs.diff.tar.gzip':
      'https://github.com/opencontainers/image-spec/blob/main/layer.md',
    'application/vnd.docker.container.image.v1+json':
      'https://github.com/opencontainers/image-spec/blob/main/config.md'
  };

  function escapeHtml(str){
    return str.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }

  function humanReadableSize(size){
    const units = ['B','KB','MB','GB','TB'];
    let i = 0;
    while(size >= 1024 && i < units.length-1){
      size /= 1024;
      i++;
    }
    return size.toFixed(1) + ' ' + units[i];
  }

  function linkMediaType(mt){
    const url = SPEC_LINKS[mt];
    const text = escapeHtml(mt);
    return url ? `<a class="mt" href="${url}">${text}</a>` : text;
  }

  function renderLayer(layer, repo){
    const mt = String(layer.mediaType || '');
    const digest = String(layer.digest || '');
    const size = Number(layer.size || layer.size_bytes || 0);
    const digestLink = `<a href="/fs/${repo}@${digest}?mt=${encodeURIComponent(mt)}&size=${size}" class="mt layer-link" data-digest="${digest}">${escapeHtml(digest)}</a>`;
    const sizeLink = `<a href="/size/${repo}@${digest}?mt=${encodeURIComponent(mt)}&size=${size}"><span title="${humanReadableSize(size)}">${size}</span></a>`;
    return '{<br>'+
      `<div class="indent">"mediaType": "${linkMediaType(mt)}",</div>`+
      `<div class="indent">"digest": "${digestLink}",</div>`+
      `<div class="indent">"size": ${sizeLink}</div>`+
      '}';
  }

  function renderObj(obj, repo){
    if(Array.isArray(obj)){
      const lines = ['['];
      obj.forEach((v,i) => {
        const comma = i < obj.length - 1 ? ',' : '';
        lines.push(`<div class="indent">${renderObj(v, repo)}${comma}</div>`);
      });
      lines.push(']');
      return lines.join('<br>');
    }
    if(obj && typeof obj === 'object'){
      const keys = Object.keys(obj);
      const lines = ['{'];
      keys.forEach((k,i) => {
        const v = obj[k];
        const comma = i < keys.length - 1 ? ',' : '';
        let valueHtml;
        if(k === 'layers' && Array.isArray(v)){
          const arr = ['['];
          v.forEach((layer,j) => {
            arr.push(`<div class="indent">${renderLayer(layer, repo)}</div>` + (j < v.length-1 ? ' ,' : ''));
          });
          arr.push(']');
          valueHtml = arr.join('<br>');
        } else if(k === 'mediaType' && typeof v === 'string'){
          valueHtml = `"${linkMediaType(v)}"`;
        } else {
          valueHtml = renderObj(v, repo);
        }
        lines.push(`<div class="indent">"${escapeHtml(k)}": ${valueHtml}${comma}</div>`);
      });
      lines.push('}');
      return lines.join('<br>');
    }
    if(typeof obj === 'string'){
      return `"${escapeHtml(obj)}"`;
    }
    return escapeHtml(JSON.stringify(obj));
  }

  function parseRepo(image){
    const ref = image.split('@')[0];
    let repo = ref.split(':')[0];
    if(!repo.includes('/')) repo = 'library/' + repo;
    return repo;
  }

  function renderManifest(manifest, image){
    const repo = parseRepo(image);
    return renderObj(manifest, repo);
  }

  async function fetchManifest(){
    const img = imgInput.value.trim();
    if(!img) return;
    const resp = await fetch('/dag/image/' + encodeURIComponent(img));
    if(resp.ok){
      const data = await resp.json();
      manifestDiv.innerHTML = renderManifest(data, img);
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
