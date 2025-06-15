/* File: static/text_tools.js */
document.addEventListener('DOMContentLoaded', function(){
  const overlay = document.getElementById('text-tools-overlay');
  if(!overlay) return;
  const input = document.getElementById('text-tool-input');
  const closeBtn = document.getElementById('text-tools-close-btn');
  const copyBtn = document.getElementById('text-copy-btn');
  const b64DecodeBtn = document.getElementById('b64-decode-btn');
  const b64EncodeBtn = document.getElementById('b64-encode-btn');
  const urlDecodeBtn = document.getElementById('url-decode-btn');
  const urlEncodeBtn = document.getElementById('url-encode-btn');

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

  closeBtn.addEventListener('click', () => overlay.classList.add('hidden'));
});
