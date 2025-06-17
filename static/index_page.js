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
});
