function initHelpReadme(){
  const overlay = document.getElementById('help-readme-overlay');
  if(!overlay) return;
  const closeBtn = document.getElementById('help-readme-close-btn');
  const backBtn = document.getElementById('help-readme-back-btn');
  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    if(location.pathname === '/tools/readme'){
      history.pushState({}, '', '/');
    }
  });
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && !overlay.classList.contains('hidden')){
      closeBtn.click();
    }
  });
  backBtn.addEventListener('click', () => {
    overlay.scrollTo({top:0, behavior:'smooth'});
  });
}
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initHelpReadme);
}else{
  initHelpReadme();
}
