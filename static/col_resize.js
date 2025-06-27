function makeResizableTable(table, key){
  if(!table) return;
  table.style.tableLayout = 'fixed';
  const ths = table.querySelectorAll('th');
  const cols = table.querySelectorAll('col');
  let widths = {};
  try {
    widths = JSON.parse(localStorage.getItem(key) || '{}');
  } catch {}
  if(Object.keys(widths).length !== ths.length){
    widths = {};
  }
  ths.forEach((th, idx) => {
    const id = idx;
    if(widths[id]){
      th.style.width = widths[id];
      if(cols[id]) cols[id].style.width = widths[id];
    }
    const initial = th.style.width || th.offsetWidth + 'px';
    th.style.width = initial;
    if(cols[id]) cols[id].style.width = initial;
    if(th.classList.contains('no-resize')) return;
    const res = document.createElement('div');
    res.className = 'col-resizer';
    th.appendChild(res);
    let startX = 0;
    let startWidth = 0;
    res.addEventListener('mousedown', e => {
      startX = e.pageX;
      startWidth = th.offsetWidth;
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', stop);
      e.preventDefault();
    });
    function onMove(ev){
      const w = Math.max(30, startWidth + (ev.pageX - startX));
      th.style.width = w + 'px';
      if(cols[id]) cols[id].style.width = w + 'px';
      widths[id] = w + 'px';
    }
    function stop(){
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', stop);
      try{ localStorage.setItem(key, JSON.stringify(widths)); }catch{}
    }
  });
}
