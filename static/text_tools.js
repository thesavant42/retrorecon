/* File: static/text_tools.js */
function initTextTools(){
  const overlay = document.getElementById('text-tools-overlay');
  if(!overlay) return;
  const input = document.getElementById('text-tool-input');
  const closeBtn = document.getElementById('text-tools-close-btn');
  const copyBtn = document.getElementById('text-copy-btn');
  const saveBtn = document.getElementById('text-save-btn');
  const saveNoteBtn = document.getElementById('text-save-note-btn');
  const b64DecodeBtn = document.getElementById('b64-decode-btn');
  const b64EncodeBtn = document.getElementById('b64-encode-btn');
  const urlDecodeBtn = document.getElementById('url-decode-btn');
  const urlEncodeBtn = document.getElementById('url-encode-btn');

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
    fetch('/text_notes', {
      method: 'POST',
      headers: {'Content-Type':'application/x-www-form-urlencoded'},
      body: new URLSearchParams({content})
    }).then(r => {
      if(r.ok){
        saveNoteBtn.textContent = 'Saved!';
        setTimeout(() => { saveNoteBtn.textContent = 'Save Note'; }, 1000);
      } else {
        r.text().then(t => alert(t));
      }
    });
  });

  closeBtn.addEventListener('click', () => overlay.classList.add('hidden'));
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', initTextTools);
} else {
  initTextTools();
}
