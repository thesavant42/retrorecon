function initHelpAbout(){
  const overlay = document.getElementById('help-about-overlay');
  if(!overlay) return;
  const closeBtn = document.getElementById('help-about-close-btn');
  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/about'){
      history.pushState({}, '', '/');
    }
  });
}
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initHelpAbout);
}else{
  initHelpAbout();
}
