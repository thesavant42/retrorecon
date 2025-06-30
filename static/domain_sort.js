/* File: static/domain_sort.js */
function initDomainSort(){
  const overlay = document.getElementById('domain-sort-overlay');
  if(!overlay) return;
  const form = document.getElementById('domain-sort-form');
  const outputDiv = document.getElementById('domain-sort-output');
  const closeBtn = document.getElementById('domain-sort-close-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const resp = await fetch('/domain_sort', {method:'POST', body: formData});
    outputDiv.innerHTML = await resp.text();
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
