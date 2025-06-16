document.addEventListener('DOMContentLoaded', function(){
  const openapiUrl = document.getElementById('openapi-url');
  const loadBtn = document.getElementById('load-openapi');
  const epSelect = document.getElementById('endpoint-select');
  const form = document.getElementById('api-request-form');
  const methodSel = document.getElementById('method');
  const urlInput = document.getElementById('request-url');
  const headersInput = document.getElementById('headers');
  const bodyInput = document.getElementById('body');
  const respPre = document.getElementById('response-display');
  const expReq = document.getElementById('export-request');
  const expResp = document.getElementById('export-response');

  if(loadBtn){
    loadBtn.addEventListener('click', async ()=>{
      if(!openapiUrl.value) return;
      const resp = await fetch('/api_client/openapi?url='+encodeURIComponent(openapiUrl.value));
      const data = await resp.json();
      epSelect.innerHTML = '';
      data.forEach(ep => {
        const opt = document.createElement('option');
        opt.value = ep.method + ' ' + ep.path;
        opt.textContent = ep.method + ' ' + ep.path;
        epSelect.appendChild(opt);
      });
    });
  }

  if(epSelect){
    epSelect.addEventListener('change', ()=>{
      const val = epSelect.value.split(' ');
      if(val.length>=2){
        methodSel.value = val[0];
        urlInput.value = val.slice(1).join(' ');
      }
    });
  }

  if(form){
    form.addEventListener('submit', async e=>{
      e.preventDefault();
      const params = new URLSearchParams();
      params.append('method', methodSel.value);
      params.append('url', urlInput.value);
      params.append('headers', headersInput.value);
      params.append('body', bodyInput.value);
      const resp = await fetch('/api_client/send', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:params});
      const data = await resp.json();
      respPre.textContent = JSON.stringify(data, null, 2);
    });
  }

  function saveText(filename, text){
    const blob = new Blob([text], {type:'text/plain'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  }

  if(expReq){
    expReq.addEventListener('click', ()=>{
      const reqData = [methodSel.value + ' ' + urlInput.value, headersInput.value, '', bodyInput.value].join('\n');
      saveText('request.txt', reqData);
    });
  }

  if(expResp){
    expResp.addEventListener('click', ()=>{
      saveText('response.json', respPre.textContent);
    });
  }
});
