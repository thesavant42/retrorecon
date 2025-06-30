/* File: static/text_tools.js */
function initTextTools(){
  const overlay = document.getElementById('text-tools-overlay');
  if(!overlay) return;
  const input = document.getElementById('text-tool-input');
  const closeBtn = document.getElementById('text-tools-close-btn');
  const copyBtn = document.getElementById('text-copy-btn');
  const saveBtn = document.getElementById('text-save-btn');
  const saveNoteBtn = document.getElementById('text-save-note-btn');
  const mdBtn = document.getElementById('text-mdeditor-btn');
  const notesList = document.getElementById('text-notes-list');
  const b64DecodeBtn = document.getElementById('b64-decode-btn');
  const b64EncodeBtn = document.getElementById('b64-encode-btn');
  const urlDecodeBtn = document.getElementById('url-decode-btn');
  const urlEncodeBtn = document.getElementById('url-encode-btn');

  let editingId = null;

  function renderNotes(data){
    if(!notesList) return;
    notesList.innerHTML = '';
    data.forEach(n => {
      const div = document.createElement('div');
      div.className = 'note-item';
      const text = document.createElement('span');
      text.textContent = n.content;
      div.appendChild(text);
      const actions = document.createElement('div');
      actions.className = 'notes-actions';
      const load = document.createElement('a');
      load.href = '#';
      load.className = 'notes-link';
      load.textContent = 'Load';
      load.addEventListener('click', e => {
        e.preventDefault();
        input.value = n.content;
        editingId = n.id;
      });
      const del = document.createElement('a');
      del.href = '#';
      del.className = 'notes-link ml-05';
      del.textContent = 'Delete';
      del.addEventListener('click', e => {
        e.preventDefault();
        if(confirm('Delete note?')){
          fetch('/delete_text_note', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({note_id:n.id})}).then(loadNotes);
        }
      });
      actions.appendChild(load);
      actions.appendChild(del);
      div.appendChild(actions);
      notesList.appendChild(div);
    });
  }

  function loadNotes(){
    if(!notesList) return;
    fetch('/text_notes').then(r=>r.json()).then(renderNotes);
  }

  const initParams = new URLSearchParams(location.search);
  const presetText = initParams.get('text');
  if(presetText) input.value = presetText;

  async function transform(url){
    const text = input.value;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type':'application/x-www-form-urlencoded'},
        body: new URLSearchParams({text})
      });
      const data = await resp.text();
      if(resp.ok){
        input.value = data;
      } else {
        alert(data);
      }
    } catch(err){
      alert('Error: ' + err);
    }
  }

  b64DecodeBtn.addEventListener('click', () => transform('/tools/base64_decode'));
  b64EncodeBtn.addEventListener('click', () => transform('/tools/base64_encode'));
  urlDecodeBtn.addEventListener('click', () => transform('/tools/url_decode'));
  urlEncodeBtn.addEventListener('click', () => transform('/tools/url_encode'));

  copyBtn.addEventListener('click', async () => {
    try{
      await navigator.clipboard.writeText(input.value);
      copyBtn.textContent = 'Copied!';
      setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1000);
    } catch {
      const t = document.createElement('textarea');
      t.value = input.value;
      document.body.appendChild(t);
      t.select();
      document.execCommand('copy');
      document.body.removeChild(t);
    }
  });

  saveBtn.addEventListener('click', () => {
    const blob = new Blob([input.value], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'text.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  saveNoteBtn.addEventListener('click', () => {
    const content = input.value.trim();
    if(!content) return;
    const params = new URLSearchParams({content});
    if(editingId) params.set('note_id', editingId);
    fetch('/text_notes', {
      method: 'POST',
      headers: {'Content-Type':'application/x-www-form-urlencoded'},
      body: params
    }).then(r => {
      if(r.ok){
        saveNoteBtn.textContent = 'Saved!';
        setTimeout(() => { saveNoteBtn.textContent = 'Save Note'; }, 1000);
        editingId = null;
        loadNotes();
      } else {
        r.text().then(t => alert(t));
      }
    });
  });

  if(mdBtn){
    mdBtn.addEventListener('click', () => {
      if(typeof showMarkdownEditor === 'function'){
        showMarkdownEditor(false, input.value);
      }
    });
  }

  closeBtn.addEventListener('click', () => {
    if(typeof hideTextTools === 'function'){
      hideTextTools();
    } else {
      overlay.classList.add('hidden');
      document.body.style.overflow = '';
    }
  });
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });

  loadNotes();
  window.loadTextNotes = loadNotes;
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', initTextTools);
} else {
  initTextTools();
}
