const API_BASE = '/api';

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(pageId).classList.add('active');
}

async function loadSports() {
  try {
    const sports = await apiGet('/sports');
    const container = document.getElementById('sport-list');
    container.innerHTML = '';
    sports.forEach(sport => {
      const btn = document.createElement('button');
      btn.className = 'btn btn-sport';
      btn.innerHTML = `
        <span class="sport-icon">${sport.icon || ''}</span>
        <span class="sport-name">${sport.name}</span>
      `;
      btn.onclick = () => loadSportDetail(sport.id);
      container.appendChild(btn);
    });
  } catch (err) {
    console.error('Failed to load sports:', err);
  }
}

async function loadSportDetail(sportId) {
  try {
    const sport = await apiGet(`/sports/${sportId}`);
    document.getElementById('detail-icon').textContent = sport.icon || '';
    document.getElementById('detail-name').textContent = sport.name;

    const posContainer = document.getElementById('detail-positions');
    posContainer.innerHTML = '';
    sport.positions.forEach(pos => {
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = pos.name;
      posContainer.appendChild(tag);
    });

    const attrContainer = document.getElementById('detail-attributes');
    attrContainer.innerHTML = '';
    sport.attributes.forEach(attr => {
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = attr.name;
      attrContainer.appendChild(tag);
    });

    showPage('sport-detail');
  } catch (err) {
    console.error('Failed to load sport detail:', err);
  }
}

function showRoleSelection(role) {
  showPage('sport-select');
}

document.addEventListener('DOMContentLoaded', () => {
  showPage('home');
  loadSports();
});
