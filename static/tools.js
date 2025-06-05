/* File: static/tools.js (revised) */
document.addEventListener('DOMContentLoaded', function() {
  const explodeBtn   = document.getElementById('explodeBtn');
  const mapUrlInput  = document.getElementById('mapUrlInput');
  const resultDiv    = document.getElementById('exploder-results');

  if (!explodeBtn || !mapUrlInput || !resultDiv) return;

  explodeBtn.addEventListener('click', async function(e) {
    e.preventDefault();
    const mapUrl = mapUrlInput.value.trim();
    if (!mapUrl) {
      resultDiv.textContent = 'Please enter a valid .js.map URL.';
      return;
    }

    resultDiv.textContent = 'Loading…';
    try {
      const resp = await fetch(mapUrl);
      if (!resp.ok) {
        resultDiv.textContent = 'Error fetching .js.map: HTTP ' + resp.status;
        return;
      }
      const mapData = await resp.json();
      const sources = mapData.sources || [];
      if (sources.length === 0) {
        resultDiv.textContent = 'No modules found in .js.map.';
        return;
      }
      let html = '<ul style="margin:0; padding-left:1.2em;">';
      sources.forEach(src => {
        html += `<li>${src}</li>`;
      });
      html += '</ul>';
      resultDiv.innerHTML = html;
    } catch (err) {
      console.error(err);
      resultDiv.textContent = 'Unexpected error: ' + err.message;
    }
  });
});
