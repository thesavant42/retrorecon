/* File: static/domain_sort.js */
function initDomainSort(){
  const overlay = document.getElementById('domain-sort-overlay');
  if(!overlay) return;
  const form = document.getElementById('domain-sort-form');
  const outputDiv = document.getElementById('domain-sort-output');
  const exportBtn = document.getElementById('domain-sort-export-btn');
  const closeBtn = document.getElementById('domain-sort-close-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    formData.set('format', 'html');
    const resp = await fetch('/domain_sort', {method:'POST', body: formData});
    outputDiv.innerHTML = await resp.text();
  });

  exportBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    formData.set('format', 'md');
    const resp = await fetch('/domain_sort', {method:'POST', body: formData});
    const text = await resp.text();
    const blob = new Blob([text], {type:'text/markdown'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'domain_tree.md';
    a.click();
    URL.revokeObjectURL(url);
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
