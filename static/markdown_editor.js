function initMarkdownEditor(){
  const overlay = document.getElementById('markdown-editor-overlay');
  if(!overlay) return;
  const textarea = overlay.querySelector('textarea[name="mdeditor"]');
  const closeBtn = document.getElementById('markdown-editor-close');
  const openBtn = document.getElementById('md-open-btn');
  const saveBtn = document.getElementById('md-save-btn');
  const fileInput = document.getElementById('md-file-input');

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    document.body.style.overflow = '';
  });

  openBtn.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', () => {
    const f = fileInput.files[0];
    if(f){
      f.text().then(t => {
        if(textarea) textarea.value = t;
        if(window.editormd && window.editormd.instances && window.editormd.instances['mdeditor']){
          window.editormd.instances['mdeditor'].setValue(t);
        }
      });
    }
  });

  saveBtn.addEventListener('click', () => {
    const text = textarea.value;
    const blob = new Blob([text], {type:'text/markdown'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'document.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  });

  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', initMarkdownEditor);
} else {
  initMarkdownEditor();
}
