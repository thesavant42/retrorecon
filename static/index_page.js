// JS for main index page
function sanitizeUrl(u){
  try {
    let raw = (u || '').trim();
    if(!raw) return null;
    // Prepend http:// if scheme is missing
    if(!/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(raw)){
      raw = 'http://' + raw;
    }
    const url = new URL(raw);
    if(url.protocol === 'http:' || url.protocol === 'https:'){
      return url.href;
    }
  } catch(e){}
  return null;
}

// ----- Theme Engine -----
function applyTheme({bg, text, accent, border, fontFamily}){
  const root = document.documentElement;
  root.style.setProperty('--color-bg', bg || '#000');
  root.style.setProperty('--color-text', text || '#fff');
  root.style.setProperty('--color-accent', accent || '#0af');
  root.style.setProperty('--color-border', border || '#888');
  root.style.setProperty('--font-family-base', fontFamily || 'monospace');
  root.style.setProperty('--font-main', fontFamily || 'monospace');
}

function loadTheme(){
  try{
    const t = JSON.parse(localStorage.getItem('retroTheme') || '{}');
    if(Object.keys(t).length){ applyTheme(t); }
  }catch{}
}

function saveTheme(t){
  localStorage.setItem('retroTheme', JSON.stringify(t));
}

function getLastDb(){
  try{
    return localStorage.getItem('retroLastDb') || '';
  }catch(e){
    return '';
  }
}

function saveLastDb(name){
  try{
    if(name){
      localStorage.setItem('retroLastDb', name);
    }
  }catch(e){}
}

// Apply stored theme on load
loadTheme();

async function initTagInputs(){
  // Tagify removed; no initialization needed
}

function autoloadLastDb(current){
  if(current && current !== '(none)' && current !== 'UNSAVED'){
    saveLastDb(current);
    return;
  }
  const last = getLastDb();
  if(!last) return;
  const selector = document.getElementById('load-saved-db-bar-select');
  if(selector){
    const found = Array.from(selector.options).some(opt => opt.value === last);
    if(!found){
      try{ localStorage.removeItem('retroLastDb'); }catch(e){}
      return;
    }
  }
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/load_saved_db';
  const inp = document.createElement('input');
  inp.type = 'hidden';
  inp.name = 'db_file';
  inp.value = last;
  form.appendChild(inp);
  document.body.appendChild(form);
  form.submit();
}

document.addEventListener('DOMContentLoaded', function(){
  autoloadLastDb(document.body.dataset.db);
  initTagInputs();
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
      if(fmt === 'db'){
        exportSel.value = '';
        const nm = prompt('Enter database name:', 'waybax');
        if(nm){
          const enc = encodeURIComponent(nm.trim());
          window.location = '/save_db?name=' + enc;
        }
        return;
      }
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

  const saveThemeBtn = document.getElementById('save-theme-btn');
  if(saveThemeBtn){
    saveThemeBtn.addEventListener('click', () => {
      const theme = {
        bg: document.getElementById('bg-color-input').value,
        text: document.getElementById('text-color-input').value,
        accent: document.getElementById('accent-color-input').value,
        border: document.getElementById('border-color-input').value,
        fontFamily: document.getElementById('font-family-select').value
      };
      applyTheme(theme);
      saveTheme(theme);
    });
  }

  // Close dropdown menus when a menu item is selected
  document.querySelectorAll('.dropdown-content').forEach(menu => {
    menu.addEventListener('click', ev => {
      if (ev.target.closest('a, button, input[type="submit"]')) {
        if (typeof closeMenus === 'function') closeMenus();
      }
    });
    menu.addEventListener('change', ev => {
      if (ev.target.closest('select')) {
        if (typeof closeMenus === 'function') closeMenus();
      }
    });
  });
});
