const API_BASE = '/api';
let currentSports = [];
let currentTeamId = null;
let currentUserRole = null;

function getToken() {
  return localStorage.getItem('traintime_token');
}

function setToken(token) {
  localStorage.setItem('traintime_token', token);
}

function clearToken() {
  localStorage.removeItem('traintime_token');
}

async function apiGet(path) {
  const headers = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (res.status === 401) { clearToken(); showPage('page-home'); throw new Error('Sessao expirada'); }
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `API error: ${res.status}`); }
  return res.json();
}

async function apiPost(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', headers, body: JSON.stringify(body) });
  if (res.status === 401) { clearToken(); showPage('page-home'); throw new Error('Sessao expirada'); }
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `API error: ${res.status}`); }
  return res.json();
}

async function apiPut(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { method: 'PUT', headers, body: JSON.stringify(body) });
  if (res.status === 401) { clearToken(); showPage('page-home'); throw new Error('Sessao expirada'); }
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `API error: ${res.status}`); }
  return res.json();
}

async function apiDelete(path) {
  const headers = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE', headers });
  if (res.status === 401) { clearToken(); showPage('page-home'); throw new Error('Sessao expirada'); }
  if (!res.ok && res.status !== 204) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `API error: ${res.status}`); }
  return res.status === 204 ? null : res.json();
}

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(pageId).classList.add('active');
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  el.textContent = message;
  el.style.display = 'block';
}

function hideError(elementId) {
  document.getElementById(elementId).style.display = 'none';
}

function goToRegister(role) {
  if (role === 'athlete') {
    loadSportsForRegister();
    showPage('page-register-athlete');
  } else {
    loadSportsForCoach();
    showPage('page-register-coach');
  }
}

async function loadSportsForRegister() {
  try {
    const sports = await apiGet('/sports');
    currentSports = sports;
    const select = document.getElementById('reg-athlete-sport');
    select.innerHTML = '<option value="">Selecione...</option>';
    sports.forEach(s => {
      select.innerHTML += `<option value="${s.id}">${s.icon || ''} ${s.name}</option>`;
    });
  } catch (err) {
    console.error('Failed to load sports:', err);
  }
}

async function loadPositionsForRegister(sportId) {
  const posSelect = document.getElementById('reg-athlete-position');
  if (!sportId) {
    posSelect.innerHTML = '<option value="">Selecione o esporte primeiro</option>';
    return;
  }
  try {
    const positions = await apiGet(`/sports/${sportId}/positions`);
    posSelect.innerHTML = '<option value="">Selecione...</option>';
    positions.forEach(p => {
      posSelect.innerHTML += `<option value="${p.id}">${p.name}</option>`;
    });
  } catch (err) {
    console.error('Failed to load positions:', err);
  }
}

async function loadSportsForCoach() {
  try {
    const sports = await apiGet('/sports');
    currentSports = sports;
    const container = document.getElementById('reg-coach-sports');
    container.innerHTML = '';
    sports.forEach(s => {
      container.innerHTML += `
        <div class="checkbox-item">
          <input type="checkbox" id="coach-sport-${s.id}" value="${s.id}">
          <label for="coach-sport-${s.id}">${s.icon || ''} ${s.name}</label>
        </div>
      `;
    });
  } catch (err) {
    console.error('Failed to load sports:', err);
  }
}

async function handleLogin(e) {
  e.preventDefault();
  hideError('login-error');
  const btn = document.getElementById('login-btn');
  btn.disabled = true;
  btn.textContent = 'Entrando...';
  try {
    const data = await apiPost('/auth/login', {
      email: document.getElementById('login-email').value,
      password: document.getElementById('login-password').value,
    });
    setToken(data.access_token);
    await loadDashboard();
  } catch (err) {
    showError('login-error', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Entrar';
  }
}

async function handleRegisterAthlete(e) {
  e.preventDefault();
  hideError('register-athlete-error');
  const btn = document.getElementById('register-athlete-btn');
  btn.disabled = true;
  btn.textContent = 'Criando...';
  try {
    await apiPost('/auth/register/athlete', {
      name: document.getElementById('reg-athlete-name').value,
      email: document.getElementById('reg-athlete-email').value,
      password: document.getElementById('reg-athlete-password').value,
      sport_id: parseInt(document.getElementById('reg-athlete-sport').value),
      position_id: parseInt(document.getElementById('reg-athlete-position').value),
    });
    const loginData = await apiPost('/auth/login', {
      email: document.getElementById('reg-athlete-email').value,
      password: document.getElementById('reg-athlete-password').value,
    });
    setToken(loginData.access_token);
    await loadDashboard();
  } catch (err) {
    showError('register-athlete-error', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Criar Conta';
  }
}

async function handleRegisterCoach(e) {
  e.preventDefault();
  hideError('register-coach-error');
  const btn = document.getElementById('register-coach-btn');
  const checked = document.querySelectorAll('#reg-coach-sports input[type="checkbox"]:checked');
  const sportIds = Array.from(checked).map(c => parseInt(c.value));
  if (sportIds.length === 0) {
    showError('register-coach-error', 'Selecione pelo menos um esporte');
    return;
  }
  btn.disabled = true;
  btn.textContent = 'Criando...';
  try {
    await apiPost('/auth/register/coach', {
      name: document.getElementById('reg-coach-name').value,
      email: document.getElementById('reg-coach-email').value,
      password: document.getElementById('reg-coach-password').value,
      sport_ids: sportIds,
    });
    const loginData = await apiPost('/auth/login', {
      email: document.getElementById('reg-coach-email').value,
      password: document.getElementById('reg-coach-password').value,
    });
    setToken(loginData.access_token);
    await loadDashboard();
  } catch (err) {
    showError('register-coach-error', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Criar Conta';
  }
}

function handleLogout() {
  clearToken();
  showPage('page-home');
}

async function loadDashboard() {
  try {
    const user = await apiGet('/auth/me');
    currentUserRole = user.role;
    document.getElementById('dashboard-greeting').textContent = `Ola, ${user.name}`;

    if (user.role === 'athlete') {
      document.getElementById('dashboard-role').textContent = 'Perfil: Atleta';
      document.getElementById('dashboard-athlete').style.display = 'block';
      document.getElementById('dashboard-coach').style.display = 'none';
      try {
        const profile = await apiGet('/athletes/me');
        document.getElementById('dash-sport').textContent = profile.sport ? `${profile.sport.icon || ''} ${profile.sport.name}` : '-';
        document.getElementById('dash-position').textContent = profile.position ? profile.position.name : '-';
      } catch (e) {
        document.getElementById('dash-sport').textContent = '-';
        document.getElementById('dash-position').textContent = '-';
      }
      try {
        const attrs = await apiGet('/athletes/me/attributes');
        const container = document.getElementById('dash-attributes');
        container.innerHTML = '';
        if (attrs.length === 0) {
          container.innerHTML = '<span class="tag" style="opacity:0.5">Nenhum atributo avaliado</span>';
        } else {
          attrs.forEach(a => {
            container.innerHTML += `<span class="tag">${a.attribute_name}: ${a.value}</span>`;
          });
        }
      } catch (e) {
        document.getElementById('dash-attributes').innerHTML = '<span class="tag" style="opacity:0.5">Nenhum atributo</span>';
      }
      await loadAthleteTeams();
    } else if (user.role === 'coach') {
      document.getElementById('dashboard-role').textContent = 'Perfil: Treinador';
      document.getElementById('dashboard-athlete').style.display = 'none';
      document.getElementById('dashboard-coach').style.display = 'block';
      try {
        const profile = await apiGet('/coaches/me');
        const container = document.getElementById('dash-coach-sports');
        container.innerHTML = '';
        if (profile.sports.length === 0) {
          container.innerHTML = '<span class="tag" style="opacity:0.5">Nenhum esporte selecionado</span>';
        } else {
          profile.sports.forEach(s => {
            container.innerHTML += `<span class="tag">${s.icon || ''} ${s.name}</span>`;
          });
        }
      } catch (e) {
        document.getElementById('dash-coach-sports').innerHTML = '<span class="tag" style="opacity:0.5">Nenhum esporte</span>';
      }
      await loadCoachTeams();
    }

    showPage('page-dashboard');
  } catch (err) {
    clearToken();
    showPage('page-home');
  }
}

async function loadCoachTeams() {
  try {
    const teams = await apiGet('/teams');
    const container = document.getElementById('dash-coach-teams');
    const noTeams = document.getElementById('dash-no-teams');
    container.innerHTML = '';
    if (teams.length === 0) {
      container.style.display = 'none';
      noTeams.style.display = 'block';
    } else {
      container.style.display = 'flex';
      noTeams.style.display = 'none';
      teams.forEach(t => {
        container.innerHTML += `
          <div class="team-card" onclick="openTeam(${t.id})">
            <div class="team-card-info">
              <span class="team-card-name">${t.name}</span>
              <span class="team-card-meta">${t.athlete_count} atleta${t.athlete_count !== 1 ? 's' : ''}</span>
            </div>
            <span class="team-card-icon">${t.sport.icon || ''}</span>
          </div>
        `;
      });
    }
  } catch (e) {
    console.error('Failed to load coach teams:', e);
  }
}

async function loadAthleteTeams() {
  try {
    const teams = await apiGet('/athletes/me/teams');
    const container = document.getElementById('dash-athlete-teams');
    container.innerHTML = '';
    if (teams.length === 0) {
      container.innerHTML = '<p class="empty-text">Voce nao participa de nenhuma equipe ainda.</p>';
    } else {
      teams.forEach(t => {
        container.innerHTML += `
          <div class="team-card" onclick="openTeam(${t.id})">
            <div class="team-card-info">
              <span class="team-card-name">${t.name}</span>
              <span class="team-card-meta">Treinador: ${t.coach_name}</span>
            </div>
            <span class="team-card-icon">${t.sport.icon || ''}</span>
          </div>
        `;
      });
    }
  } catch (e) {
    console.error('Failed to load athlete teams:', e);
  }
}

function showCreateTeam() {
  const select = document.getElementById('team-sport');
  select.innerHTML = '<option value="">Selecione...</option>';
  currentSports.forEach(s => {
    select.innerHTML += `<option value="${s.id}">${s.icon || ''} ${s.name}</option>`;
  });
  document.getElementById('team-name').value = '';
  hideError('create-team-error');
  showPage('page-create-team');
}

async function handleCreateTeam(e) {
  e.preventDefault();
  hideError('create-team-error');
  try {
    const data = await apiPost('/teams', {
      name: document.getElementById('team-name').value,
      sport_id: parseInt(document.getElementById('team-sport').value),
    });
    await openTeam(data.id);
  } catch (err) {
    showError('create-team-error', err.message);
  }
}

async function openTeam(teamId) {
  currentTeamId = teamId;
  try {
    const team = await apiGet(`/teams/${teamId}`);
    document.getElementById('team-detail-name').textContent = team.name;
    document.getElementById('team-detail-sport').textContent = `${team.sport.icon || ''} ${team.sport.name}`;

    const isCoach = currentUserRole === 'coach';
    document.getElementById('team-detail-actions').style.display = isCoach ? 'flex' : 'none';
    document.getElementById('btn-add-athlete').style.display = isCoach ? 'inline-flex' : 'none';

    const athletesContainer = document.getElementById('team-athletes');
    const noAthletes = document.getElementById('team-no-athletes');
    athletesContainer.innerHTML = '';

    if (team.athletes.length === 0) {
      athletesContainer.style.display = 'none';
      noAthletes.style.display = 'block';
    } else {
      athletesContainer.style.display = 'flex';
      noAthletes.style.display = 'none';
      team.athletes.forEach(a => {
        const removeBtn = isCoach ? `<button class="btn-remove" onclick="handleRemoveAthlete(${a.id})">Remover</button>` : '';
        athletesContainer.innerHTML += `
          <div class="athlete-card">
            <div class="athlete-card-info">
              <span class="athlete-card-name">${a.name}</span>
              <span class="athlete-card-pos">${a.position_name || '-'}</span>
            </div>
            ${removeBtn}
          </div>
        `;
      });
    }

    showPage('page-team-detail');
  } catch (err) {
    console.error('Failed to open team:', err);
  }
}

function showEditTeam() {
  document.getElementById('edit-team-name').value = document.getElementById('team-detail-name').textContent;
  hideError('edit-team-error');
  showPage('page-edit-team');
}

async function handleEditTeam(e) {
  e.preventDefault();
  hideError('edit-team-error');
  try {
    await apiPut(`/teams/${currentTeamId}`, {
      name: document.getElementById('edit-team-name').value,
    });
    await openTeam(currentTeamId);
  } catch (err) {
    showError('edit-team-error', err.message);
  }
}

async function handleDeleteTeam() {
  if (!confirm('Tem certeza que deseja excluir esta equipe?')) return;
  try {
    await apiDelete(`/teams/${currentTeamId}`);
    await loadDashboard();
  } catch (err) {
    console.error('Failed to delete team:', err);
  }
}

async function showAddAthlete() {
  try {
    const team = await apiGet(`/teams/${currentTeamId}`);
    const compatible = await apiGet(`/athletes/compatible?sport_id=${team.sport.id}`);
    const container = document.getElementById('compatible-athletes');
    const noCompatible = document.getElementById('no-compatible');
    container.innerHTML = '';

    if (compatible.length === 0) {
      container.style.display = 'none';
      noCompatible.style.display = 'block';
    } else {
      container.style.display = 'flex';
      noCompatible.style.display = 'none';
      compatible.forEach(a => {
        container.innerHTML += `
          <div class="athlete-select-item">
            <div class="athlete-card-info">
              <span class="athlete-card-name">${a.name}</span>
              <span class="athlete-card-pos">${a.position_name || '-'}</span>
            </div>
            <button class="btn-small btn-primary" onclick="handleAddAthlete(${a.id})">Adicionar</button>
          </div>
        `;
      });
    }

    showPage('page-add-athlete');
  } catch (err) {
    console.error('Failed to load compatible athletes:', err);
  }
}

async function handleAddAthlete(athleteId) {
  try {
    await apiPost(`/teams/${currentTeamId}/athletes/${athleteId}`);
    await openTeam(currentTeamId);
  } catch (err) {
    console.error('Failed to add athlete:', err);
  }
}

async function handleRemoveAthlete(athleteId) {
  if (!confirm('Remover este atleta da equipe?')) return;
  try {
    await apiDelete(`/teams/${currentTeamId}/athletes/${athleteId}`);
    await openTeam(currentTeamId);
  } catch (err) {
    console.error('Failed to remove athlete:', err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (token) {
    loadDashboard();
  } else {
    showPage('page-home');
  }
});
