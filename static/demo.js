/* File: static/demo.js */
function initDemo(){
  const overlay = document.getElementById('demo-overlay');
  if(!overlay) return;
  const select = document.getElementById('demo-select');
  const view = document.getElementById('demo-view');
  const closeBtn = document.getElementById('demo-close-btn');

  async function loadContent(name){
    view.innerHTML = '';
    if(!name) return;
    let url = '';
    if(name === 'index'){ url = '/dynamic/demo/index'; }
    else if(name === 'subdomonster'){ url = '/dynamic/demo/subdomonster'; }
    else if(name === 'screenshotter'){ url = '/dynamic/demo/screenshotter'; }
    else if(name === 'about'){ url = '/dynamic/demo/about'; }
    if(!url) return;
    const resp = await fetch(url);
    const html = await resp.text();
    view.innerHTML = html;
    if(name === 'subdomonster'){
      const script = document.createElement('script');
      script.src = '/static/subdomonster.js';
      document.body.appendChild(script);
    }else if(name === 'screenshotter'){
      const script = document.createElement('script');
      script.src = '/static/screenshotter.js';
      document.body.appendChild(script);
    }else if(name === 'about'){
      const script = document.createElement('script');
      script.src = '/static/help_about.js';
      document.body.appendChild(script);
    }
  }

  select.addEventListener('change', () => loadContent(select.value));
  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/demo'){
      history.pushState({}, '', '/');
    }
  });
}
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initDemo);
}else{
  initDemo();
}
