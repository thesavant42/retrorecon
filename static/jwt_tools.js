/* File: static/jwt_tools.js */
function initJWTTools(){
  const overlay = document.getElementById('jwt-tools-overlay');
  if(!overlay) return;
  const input = document.getElementById('jwt-tool-input');
  const secret = document.getElementById('jwt-secret');
  const decodeBtn = document.getElementById('jwt-decode-btn');
  const encodeBtn = document.getElementById('jwt-encode-btn');
  const copyBtn = document.getElementById('jwt-copy-btn');
  const saveBtn = document.getElementById('jwt-save-btn');
  const closeBtn = document.getElementById('jwt-close-btn');

  async function call(url, data){
    try{
      const resp = await fetch(url, {
        method:'POST',
        headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body:new URLSearchParams(data)
      });
      const text = await resp.text();
      if(resp.ok){
        input.value = text;
      }else{
        alert(text);
      }
    }catch(err){
      alert('Error: '+err);
    }
  }

  decodeBtn.addEventListener('click', () => {
    call('/tools/jwt_decode', {token: input.value});
  });

  encodeBtn.addEventListener('click', () => {
    call('/tools/jwt_encode', {payload: input.value, secret: secret.value});
  });

  copyBtn.addEventListener('click', async () => {
    try{
      await navigator.clipboard.writeText(input.value);
      copyBtn.textContent = 'Copied!';
      setTimeout(()=>{copyBtn.textContent='Copy';},1000);
    }catch{
      const t=document.createElement('textarea');
      t.value=input.value;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);
    }
  });

  saveBtn.addEventListener('click', () => {
    const blob=new Blob([input.value],{type:'text/plain'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='jwt.txt';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
  });

  closeBtn.addEventListener('click', () => overlay.classList.add('hidden'));
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initJWTTools);
}else{
  initJWTTools();
}
