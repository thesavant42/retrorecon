let simplemde = null;

function initMarkdownEditor(){
  const overlay = document.getElementById('markdown-editor-overlay');
  if(!overlay) return;
  const textarea = overlay.querySelector('#mdeditor-textarea');
  const closeBtn = document.getElementById('markdown-editor-close');
  const openBtn = document.getElementById('md-open-btn');
  const saveBtn = document.getElementById('md-save-btn');
  const fileInput = document.getElementById('md-file-input');
  const fileList = document.getElementById('md-file-list');

  function ensureEditor(){
    if(!simplemde && window.SimpleMDE){
      const underline = {
        name: 'underline',
        action: function customUnderline(editor){
          const cm = editor.codemirror;
          const selectedText = cm.getSelection();
          cm.replaceSelection(`<u>${selectedText}</u>`);
        },
        className: 'fa fa-underline',
        title: 'Underline'
      };
      simplemde = new SimpleMDE({
        element: textarea,
        autoDownloadFontAwesome: false,
        spellChecker: false,
        toolbar: [
          'bold',
          'italic',
          'strikethrough',
          underline,
          '|',
          'heading-1',
          'heading-2',
          'heading-3',
          '|',
          'quote',
          'unordered-list',
          'ordered-list',
          '|',
          'link',
          'image',
          '|',
          'preview',
          'side-by-side',
          'fullscreen',
          '|',
          'guide'
        ]
      });
      window.simplemde = simplemde;
    }
  }

  function loadFiles(){
    if(!fileList) return;
    fetch('/markdown_files').then(r=>r.json()).then(files => {
      fileList.innerHTML = '';
      files.forEach(name => {
        const item = document.createElement('div');
        item.className = 'md-file-item';
        item.textContent = name;
        item.addEventListener('click', () => {
          fetch('/markdown_file/' + encodeURIComponent(name))
            .then(r=>r.text())
            .then(t => {
              if(textarea) textarea.value = t;
              if(simplemde){
                simplemde.value(t);
              }
            });
        });
        fileList.appendChild(item);
      });
    });
  }
  window.loadMdFiles = loadFiles;

  function refreshEditor(){
    if(simplemde){
      const body = overlay.querySelector('.md-editor-body');
      const h = body ? body.clientHeight || 700 : 700;
      simplemde.codemirror.setSize('100%', h);
      simplemde.codemirror.refresh();
    }
  }
  window.refreshMdEditor = refreshEditor;

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
        if(simplemde){
          simplemde.value(t);
        }
      });
    }
  });

  saveBtn.addEventListener('click', () => {
    const text = simplemde ? simplemde.value() : textarea.value;
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

  ensureEditor();
  refreshEditor();
  loadFiles();
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', initMarkdownEditor);
} else {
  initMarkdownEditor();
}
