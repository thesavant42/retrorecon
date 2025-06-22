// JS for main index page
function sanitizeUrl(u){
  try {
    const url = new URL(u, window.location.href);
    if(url.protocol === 'http:' || url.protocol === 'https:'){
      return url.href;
    }
  } catch(e){}
  return null;
}

document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('.url-row-main[data-url]').forEach(row => {
    row.addEventListener('click', () => {
      const raw = row.getAttribute('data-url');
      const url = sanitizeUrl(raw);
      if(url) window.open(url, '_blank');
    });
  });
  document.querySelectorAll('select.tool-select[data-url]').forEach(sel => {
    sel.addEventListener('change', function(){
      const raw = this.getAttribute('data-url');
      const url = sanitizeUrl(raw);
      if(!url){ this.selectedIndex = 0; return; }
      if(typeof handleToolSelect === 'function'){
        handleToolSelect(this, url);
      }
    });
  });

  const exportSel = document.getElementById('url-export-formats');
  const exportForm = document.getElementById('url-export-form');
  const exportFmt = document.getElementById('url-export-format');
  const exportQ = document.getElementById('url-export-q');
  const exportSam = document.getElementById('url-export-sam');
  if(exportSel && exportForm){
    exportSel.addEventListener('change', () => {
      const fmt = exportSel.value;
      if(!fmt) return;
      exportFmt.value = fmt;
      if(exportQ){
        const box = document.getElementById('searchbox');
        exportQ.value = box ? box.value.trim() : '';
      }
      if(exportSam){
        exportSam.value = document.getElementById('select-all-matching-input').value;
      }
      exportForm.querySelectorAll('input[name="id"]').forEach(n => n.remove());
      if(exportSam.value !== 'true'){
        document.querySelectorAll('.row-checkbox:checked').forEach(cb => {
          const inp = document.createElement('input');
          inp.type = 'hidden';
          inp.name = 'id';
          inp.value = cb.value;
          exportForm.appendChild(inp);
        });
      }
      exportForm.submit();
      exportSel.value = '';
    });
  }
});
