// Common JS: clock, slideshow, modal, double-click behaviors
document.addEventListener('DOMContentLoaded', ()=>{
  // Login card double click to toggle gov/farmer
  const loginCard = document.getElementById('loginCard');
  if(loginCard){
    loginCard.addEventListener('dblclick', ()=>{
      const modeInput = document.getElementById('modeInput');
      const farmerForm = document.getElementById('farmerForm');
      const govForm = document.getElementById('govForm');
      const title = document.getElementById('loginTitle');
      if(modeInput.value === 'farmer'){
        modeInput.value = 'government';
        farmerForm.style.display = 'none';
        govForm.style.display = 'block';
        title.textContent = 'Government Login';
      } else {
        modeInput.value = 'farmer';
        farmerForm.style.display = 'block';
        govForm.style.display = 'none';
        title.textContent = 'Farmer Login';
      }
    });
  }

  // Simple clock
  const clock = document.getElementById('clock');
  if(clock){
    function updateClock(){
      const now = new Date();
      const h = String(now.getHours()).padStart(2,'0');
      const m = String(now.getMinutes()).padStart(2,'0');
      const s = String(now.getSeconds()).padStart(2,'0');
      clock.textContent = `${h}:${m}:${s}`;
    }
    setInterval(updateClock,1000); updateClock();
  }

  // farmer list double click to open modal (gov page)
  document.querySelectorAll('.farmer-item').forEach(item=>{
    item.addEventListener('dblclick', async (e)=>{
      const id = item.dataset.id;
      const modal = document.getElementById('govModal');
      const inner = document.getElementById('govModalInner');
      modal.style.display = 'flex';
      inner.innerHTML = '<h3>Loading analytics...</h3>';
      // fetch charts by embedding images
      inner.innerHTML = `<h3>Farmer Analytics</h3>
        <img src="/chart/water/${id}/?t=${Date.now()}" style="width:100%;max-height:240px;object-fit:contain;" />
        <img src="/chart/ph/${id}/?t=${Date.now()}" style="width:100%;max-height:240px;object-fit:contain;" />
        <img src="/chart/temp_humi/${id}/?t=${Date.now()}" style="width:100%;max-height:240px;object-fit:contain;" />`;
    });
  });

  document.querySelectorAll('.close-button').forEach(b=> b.addEventListener('click', ()=>{
    document.querySelectorAll('.modal').forEach(m=> m.style.display='none');
  }));

  window.addEventListener('click', e=>{ document.querySelectorAll('.modal').forEach(m=>{ if(e.target === m) m.style.display='none'; }) });

});
