/* File: static/domain_sort.js */
function initDomainSort(){
  const overlay = document.getElementById('domain-sort-overlay');
  if(!overlay) return;
  const form = document.getElementById('domain-sort-form');
  const outputDiv = document.getElementById('domain-sort-output');
  const exportBtn = document.getElementById('domain-sort-export-btn');
  const closeBtn = document.getElementById('domain-sort-close-btn');

  const importInput = document.getElementById('domain-import-input');
  const importBtn = document.getElementById('domain-import-btn');

  outputDiv.addEventListener('click', (e) => {
    if(e.target.classList.contains('domain-sort-toggle')){
      e.preventDefault();
      const id = e.target.dataset.target;
      const el = document.getElementById(id);
      if(el){ el.open = !el.open; }
    }
  });

  function setStatus(msg){
    if(window.showStatus) window.showStatus(msg);
  }

  async function refresh(){
    const resp = await fetch('/domain_sort', {method:'POST'});
    outputDiv.innerHTML = await resp.text();
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    formData.set('format', 'html');
    setStatus('Processing...');
    const resp = await fetch('/domain_sort', {method:'POST', body: formData});
    outputDiv.innerHTML = await resp.text();
    setStatus(resp.ok ? 'List imported successfully.' : 'Upload failed.');
    document.dispatchEvent(new Event('domainDataChanged'));
  });

  if(importBtn && importInput){
    importBtn.addEventListener('click', async () => {
      const domain = importInput.value.trim().toLowerCase();
      if(!domain) return;
      importInput.value = '';
      setStatus('Importing...');
      for(const src of ['crtsh','virustotal']){
        const params = new URLSearchParams({domain, source: src});
        await fetch('/subdomains', {method:'POST', body: params});
      }
      setStatus('Import complete.');
      await refresh();
      document.dispatchEvent(new Event('domainDataChanged'));
    });
  }

  document.addEventListener('domainDataChanged', () => {
    refresh();
  });

  exportBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    formData.set('format', 'md');
    setStatus('Processing...');
    const resp = await fetch('/domain_sort', {method:'POST', body: formData});
    const text = await resp.text();
    const blob = new Blob([text], {type:'text/markdown'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'domain_tree.md';
    a.click();
    URL.revokeObjectURL(url);
    setStatus(resp.ok ? 'Markdown exported.' : 'Export failed.');
  });

  closeBtn.addEventListener('click', () => {
    history.back();
  });

  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', initDomainSort);
}else{
  initDomainSort();
}
