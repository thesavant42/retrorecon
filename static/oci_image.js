function initImagePage(){
  const btn = document.getElementById('image-close-btn');
  if(!btn) return;
  btn.addEventListener('click', () => {
    if(window.history.length > 1){
      window.history.back();
    } else {
      window.location.href = '/';
    }
  });
}
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initImagePage);
}else{
  initImagePage();
}
