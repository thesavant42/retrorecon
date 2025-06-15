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
  const clearBtn = document.getElementById('jwt-clear-btn');
  const closeBtn = document.getElementById('jwt-close-btn');
  const warnDiv = document.getElementById('jwt-warning');
  const expDiv = document.getElementById('jwt-exp');
  const jarDiv = document.getElementById('jwt-cookie-jar');

  async function loadJar(){
    if(!jarDiv) return;
    try{
      const resp = await fetch('/jwt_cookies');
      const data = await resp.json();
      if(!Array.isArray(data)) return;
      let html = '<table class="table w-100"><tr><th>Time</th><th>Issuer</th><th>alg</th><th>claims</th><th>Notes</th><th>JWT</th></tr>';
      for(const row of data){
        const claims = Array.isArray(row.claims) ? row.claims.join(',') : '';
        html += `<tr><td>${row.created_at}</td><td>${row.issuer||''}</td><td>${row.alg||''}</td><td>${claims}</td><td>${row.notes||''}</td><td class="break-all">${row.token}</td></tr>`;
      }
      html += '</table>';
      jarDiv.innerHTML = html;
    }catch{}
  }

  async function call(url, data, expectJson){
    try{
      const resp = await fetch(url, {
        method:'POST',
        headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body:new URLSearchParams(data)
      });
      if(resp.ok){
          if(expectJson){
            const respData = await resp.json();
          if(respData && respData.error==='no_db'){
              const name = prompt('Enter new database name for JWT log:', 'jwtlog');
              if(name){
                await fetch('/new_db', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({db_name:name}), redirect:'manual'});
              return call(url, data, expectJson);
              }
              return;
          }
          const header = JSON.stringify(respData.header, null, 2);
          const payload = JSON.stringify(respData.payload, null, 2);
          input.value = header + "\n" + payload;
          if(expDiv){
            if(respData.exp_readable){
              expDiv.textContent = 'exp: ' + respData.exp_readable;
              expDiv.classList.remove('hidden');
              expDiv.classList.toggle('valid', !respData.expired);
              expDiv.classList.toggle('expired', respData.expired);
            }else{
              expDiv.classList.add('hidden');
            }
          }
          if(warnDiv){
            const msgs = [];
            if(respData.alg_warning){ msgs.push('Weak algorithm'); }
            if(respData.key_warning){ msgs.push('Weak key'); }
            if(msgs.length){
              warnDiv.textContent = msgs.join(' / ');
              warnDiv.classList.remove('hidden');
            }else{
              warnDiv.classList.add('hidden');
            }
          }
        }else{
          const text = await resp.text();
          input.value = text;
        }
      }else{
        const text = await resp.text();
        alert(text);
      }
    }catch(err){
      alert('Error: '+err);
    }
    loadJar();
  }

  decodeBtn.addEventListener('click', () => {
    call('/tools/jwt_decode', {token: input.value}, true);
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

  clearBtn.addEventListener('click', () => {
    input.value = '';
    secret.value = '';
    if(warnDiv) warnDiv.classList.add('hidden');
    if(expDiv) expDiv.classList.add('hidden');
  });

  closeBtn.addEventListener('click', () => overlay.classList.add('hidden'));

  loadJar();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initJWTTools);
}else{
  initJWTTools();
}
