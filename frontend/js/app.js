const API_BASE = '/api';
let currentSports = [];

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
    }

    showPage('page-dashboard');
  } catch (err) {
    clearToken();
    showPage('page-home');
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
