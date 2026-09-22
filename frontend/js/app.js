const API_BASE = '/api';
let currentSports = [];
let currentTeamId = null;
let currentWorkoutId = null;
let currentWorkoutExerciseId = null;
let currentExerciseSportId = null;
let currentExerciseId = null;
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
  const target = document.getElementById(pageId);
  target.classList.add('active');
  const header = document.getElementById('app-header');
  const isAuth = target.classList.contains('page--auth');
  document.body.classList.toggle('app-shell', !isAuth);
  header.hidden = isAuth;
}

function initials(name) {
  if (!name) return 'U';
  return name.trim().split(/\s+/).slice(0, 2).map(n => n[0]).join('').toUpperCase();
}

function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function emptyStateHTML(icon, title, text, btnHTML = '') {
  return `
    <span class="empty-icon" aria-hidden="true">${icon}</span>
    <span class="empty-title">${title}</span>
    <span class="empty-text">${text}</span>
    ${btnHTML}
  `;
}

function skeletonCards(count) {
  let html = '';
  for (let i = 0; i < count; i++) {
    html += `
      <div class="skeleton skeleton-card">
        <div class="skeleton-img"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line skeleton-line--sm"></div>
      </div>
    `;
  }
  return html;
}

function renderAppHeader(user) {
  document.getElementById('header-avatar').textContent = initials(user.name);
  document.getElementById('header-name').textContent = `Olá, ${(user.name || '').split(' ')[0] || 'Usuário'}`;
  document.getElementById('header-role').textContent = user.role === 'coach' ? 'Treinador' : 'Atleta';
}

function toggleUserMenu(event) {
  event.stopPropagation();
  const menu = document.getElementById('user-dropdown');
  const btn = document.getElementById('btn-user-menu');
  const open = menu.hidden;
  menu.hidden = !open;
  btn.setAttribute('aria-expanded', String(open));
}

function closeUserMenu(event) {
  if (event && event.target instanceof Element && event.target.closest('.user-menu')) return;
  const menu = document.getElementById('user-dropdown');
  const btn = document.getElementById('btn-user-menu');
  if (!menu.hidden) {
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
  }
}
document.addEventListener('click', closeUserMenu);

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
    renderAppHeader(user);

    document.getElementById('menu-attributes').style.display = user.role === 'athlete' ? 'flex' : 'none';
    document.getElementById('menu-exercises').style.display = user.role === 'coach' ? 'flex' : 'none';

    document.getElementById('sidebar-name').textContent = user.name;
    document.getElementById('sidebar-avatar').textContent = initials(user.name);

    const teamsGrid = document.getElementById('dash-teams-grid');
    const teamsLoading = document.getElementById('dash-teams-loading');
    const teamsEmpty = document.getElementById('dash-teams-empty');
    const teamsError = document.getElementById('dash-teams-error');
    teamsGrid.innerHTML = '';
    teamsEmpty.innerHTML = '';
    teamsError.innerHTML = '';
    teamsEmpty.hidden = true;
    teamsError.hidden = true;
    teamsLoading.innerHTML = skeletonCards(3);

    const isAthlete = user.role === 'athlete';
    document.getElementById('hero-quote-text').textContent = isAthlete
      ? 'O progresso começa com um bom treino.'
      : 'Disciplina é o que transforma objetivo em resultado.';
    document.getElementById('sidebar-quote').textContent = isAthlete
      ? 'Cada treino é um passo mais perto do seu objetivo.'
      : 'Grandes resultados vêm de grandes planejamentos.';
    document.getElementById('sidebar-role').textContent = isAthlete ? 'Atleta' : 'Treinador';
    document.getElementById('dashboard-role').textContent = isAthlete ? 'Perfil Atleta' : 'Perfil Treinador';
    document.getElementById('sidebar-subtitle').textContent = isAthlete ? 'Seu esporte e atributos' : 'Esportes que trabalha';
    document.getElementById('teams-section-title').textContent = isAthlete ? 'Minhas Equipes' : 'Suas Equipes';
    document.getElementById('dashboard-welcome').textContent = isAthlete
      ? 'Vamos treinar? Seu esforço de hoje constrói seu resultado de amanhã.'
      : 'Bem-vindo ao seu painel de controle. Gerencie equipes, treinos e acompanhe seus atletas.';

    const first = (user.name || '').split(' ')[0] || '';
    document.getElementById('dashboard-greeting').textContent = `Olá, ${first} 👋`;

    try {
      const [teams, workouts, sports, profile, attributes] = await Promise.all([
        isAthlete ? apiGet('/athletes/me/teams') : apiGet('/teams'),
        apiGet('/workouts'),
        apiGet('/sports'),
        isAthlete ? apiGet('/athletes/me') : apiGet('/coaches/me'),
        isAthlete ? apiGet('/athletes/me/attributes') : Promise.resolve([]),
      ]);
      currentSports = sports;

      const workoutCounts = {};
      let scheduledCount = 0;
      workouts.forEach(w => {
        workoutCounts[w.team_id] = (workoutCounts[w.team_id] || 0) + 1;
        if (w.status === 'scheduled') scheduledCount++;
      });

      teamsLoading.innerHTML = '';
      if (teams.length === 0) {
        renderTeamsEmpty(isAthlete);
      } else {
        renderTeamsGrid(isAthlete, teams, workoutCounts);
      }

      renderSidebar(isAthlete, profile, attributes);
      renderMainCards(isAthlete, teams.length, scheduledCount, workouts.length);
      renderPhases();
    } catch (err) {
      teamsLoading.innerHTML = '';
      teamsError.innerHTML = `
        <span class="error-icon" aria-hidden="true">⚠️</span>
        <strong>Não foi possível carregar seus dados.</strong>
        <p>Tente novamente.</p>
        <button class="btn btn-secondary btn-sm" onclick="loadDashboard()">Tentar novamente</button>
      `;
      teamsError.hidden = false;
    }

    showPage('page-dashboard');
  } catch (err) {
    clearToken();
    showPage('page-home');
  }
}

function renderTeamsGrid(isAthlete, teams, workoutCounts) {
  const grid = document.getElementById('dash-teams-grid');
  grid.innerHTML = '';
  const AVATAR_FACES = ['🧑', '👩', '🧔', '👱'];
  teams.forEach((t, i) => {
    const count = workoutCounts[t.id] || 0;
    const countText = `${count} treino${count !== 1 ? 's ativos' : ' ativo'}`;
    const athleteText = isAthlete
      ? (t.coach_name ? `Coach: ${t.coach_name}` : t.sport.name)
      : `${t.sport.name} · ${t.athlete_count || 0} atleta${(t.athlete_count || 0) === 1 ? '' : 's'}`;
    const isNew = isAthlete ? false : isNewTeam(t.created_at);
    const badge = isNew ? '<span class="badge badge--new">Nova</span>' : '';
    const icon = t.sport.icon || '🏅';
    const avatarCount = isAthlete ? 0 : (t.athlete_count || 0);
    let avatars = '';
    if (avatarCount > 0) {
      const show = Math.min(avatarCount, 3);
      let stack = '';
      for (let a = 0; a < show; a++) {
        stack += `<i>${AVATAR_FACES[a % AVATAR_FACES.length]}</i>`;
      }
      const extra = avatarCount - show;
      stack += extra > 0 ? `<b>+${extra}</b>` : `<b>${avatarCount}</b>`;
      avatars = `<div class="team-avatars" aria-label="${avatarCount} atleta${avatarCount !== 1 ? 's' : ''}">${stack}</div>`;
    } else if (isAthlete) {
      avatars = '';
    }
    grid.innerHTML += `
      <article class="team-grid-card" onclick="openTeam(${t.id})" role="button" tabindex="0" onkeydown="if(event.key==='Enter'||event.key===' ')openTeam(${t.id})">
        <div class="team-visual team-visual--${i % 2 ? 'purple' : 'blue'}">
          <span class="team-visual-icon" aria-hidden="true">${icon}</span>
        </div>
        <div class="team-body">
          <div class="team-title">
            <span class="ticon" aria-hidden="true">${icon}</span>
            <div class="team-title-info">
              <strong>${t.name}</strong>${badge}
              <small>${athleteText}</small>
            </div>
            <svg class="team-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </div>
          <p class="team-meta">📅 ${countText}</p>
          ${avatars}
        </div>
      </article>
    `;
  });
}

function isNewTeam(createdAt) {
  if (!createdAt) return false;
  const created = new Date(createdAt);
  if (isNaN(created.getTime())) return false;
  const days = (Date.now() - created.getTime()) / 86400000;
  return days >= 0 && days <= 7;
}

function renderTeamsEmpty(isAthlete) {
  const empty = document.getElementById('dash-teams-empty');
  empty.hidden = false;
  empty.innerHTML = isAthlete
    ? emptyStateHTML('👥', 'Você ainda não participa de equipes', 'Quando um treinador adicionar você a uma equipe, ela aparecerá aqui.')
    : emptyStateHTML('👥', 'Nenhuma equipe ainda', 'Crie sua primeira equipe para começar a organizar seus atletas.',
        '<button class="btn btn-primary btn-sm" onclick="showCreateTeam()">+ Criar equipe</button>');
}

function renderSidebar(isAthlete, profile, attributes) {
  const block = document.getElementById('sidebar-block');
  block.innerHTML = '';
  if (isAthlete) {
    const sport = profile.sport ? `${profile.sport.icon || '🏐'} ${profile.sport.name}` : 'Não definido';
    const position = profile.position ? profile.position.name : 'Não definido';
    block.innerHTML += `
      <div class="sidebar-item"><span class="sidebar-item-icon" aria-hidden="true">${profile.sport ? (profile.sport.icon || '🏐') : '🏐'}</span><span>${profile.sport ? profile.sport.name : 'Esporte'}</span><span class="sidebar-item-arrow">→</span></div>
      <div class="sidebar-item"><span class="sidebar-item-icon" aria-hidden="true">🎯</span><span>${position}</span><span class="sidebar-item-arrow">→</span></div>
    `;
    const list = attributes.slice(0, 4);
    list.forEach(a => {
      block.innerHTML += `
        <div class="sidebar-item">
          <span>${a.attribute_name}</span>
          <b style="color:var(--accent-blue-2)">${a.value}</b>
        </div>
      `;
    });
  } else {
    const sports = profile.sports || [];
    if (sports.length === 0) {
      block.innerHTML = '<p class="empty-text">Nenhum esporte selecionado.</p>';
    } else {
      sports.forEach(s => {
        block.innerHTML += `
          <div class="sidebar-item">
            <span class="sidebar-item-icon" aria-hidden="true">${s.icon || '🏅'}</span>
            <span>${s.name}</span>
            <span class="sidebar-item-arrow">→</span>
          </div>
        `;
      });
    }
  }

  document.getElementById('sidebar-actions').innerHTML = `
    <button class="btn btn-secondary btn-sm" onclick="showProfileEdit()">Editar perfil</button>
    ${isAthlete
      ? '<button class="btn btn-secondary btn-sm" onclick="showAttributesEdit()">Avaliar atributos</button>'
      : '<button class="btn btn-secondary btn-sm" onclick="openExerciseLibrary()">Biblioteca de exercícios</button>'}
  `;
}

function renderMainCards(isAthlete, teamCount, scheduledCount, totalWorkouts) {
  const container = document.getElementById('main-cards');
  const teamsBtn = `<button class="btn btn-secondary btn-sm" onclick="scrollToSection('dash-teams-section')">Ver equipes →</button>`;

  if (isAthlete) {
    container.innerHTML = `
      <div class="main-card main-card--featured">
        <span class="main-card-icon" aria-hidden="true">📅</span>
        <span class="main-card-count">${totalWorkouts}</span>
        <h3 class="main-card-title">Meus Treinos</h3>
        <p class="main-card-desc">Seus treinos das equipes, em um só lugar.</p>
        <button class="btn btn-primary btn-sm" onclick="openAthleteWorkoutsPage()">Ver treinos →</button>
      </div>
      <div class="main-card">
        <span class="main-card-icon" aria-hidden="true">👥</span>
        <span class="main-card-count">${teamCount}</span>
        <h3 class="main-card-title">Minhas Equipes</h3>
        <p class="main-card-desc">Visualize as equipes que você participa.</p>
        ${teamsBtn}
      </div>
      <div class="main-card main-card--locked">
        <span class="main-card-icon" aria-hidden="true">📈</span>
        <h3 class="main-card-title">Meu Progresso</h3>
        <p class="main-card-desc">Acompanhe sua evolução nos treinos e atributos.</p>
        <span class="badge-coming">🔒 Em breve</span>
      </div>
    `;
  } else {
    container.innerHTML = `
      <div class="main-card">
        <span class="main-card-icon" aria-hidden="true">👥</span>
        <span class="main-card-count">${teamCount}</span>
        <h3 class="main-card-title">Minhas Equipes</h3>
        <p class="main-card-desc">Visualize e gerencie suas equipes de treinamento.</p>
        ${teamsBtn}
      </div>
      <div class="main-card main-card--featured">
        <span class="main-card-icon" aria-hidden="true">📅</span>
        <span class="main-card-count">${scheduledCount}</span>
        <h3 class="main-card-title">Treinos</h3>
        <p class="main-card-desc">Crie e gerencie seus treinos de forma simples e organizada.</p>
        <button class="btn btn-primary btn-sm" onclick="scrollToSection('dash-teams-section')">Ver treinos →</button>
      </div>
      <div class="main-card main-card--locked">
        <span class="main-card-icon" aria-hidden="true">📊</span>
        <h3 class="main-card-title">Performance</h3>
        <p class="main-card-desc">Acompanhe a evolução dos seus atletas.</p>
        <span class="badge-coming">🔒 Em breve</span>
      </div>
    `;
  }
}

function renderPhases() {
  const phases = [
    { n: 1, label: 'Fundação', done: true },
    { n: 2, label: 'Usuários', done: true },
    { n: 3, label: 'Equipes', done: true },
    { n: 4, label: 'Treinos', done: true },
    { n: 5, label: 'Exercícios', done: true },
    { n: 6, label: 'Execução', done: false, current: true },
    { n: 7, label: 'Performance', done: false },
  ];
  document.getElementById('phase-steps').innerHTML = phases.map(p => `
    <li class="${p.done ? 'done' : p.current ? 'current' : ''}">
      <i aria-hidden="true">${p.done ? '✓' : p.current ? '●' : '○'}</i>
      <span>Fase ${p.n}<small>${p.label}</small></span>
    </li>
  `).join('');
}

async function openAthleteWorkoutsPage() {
  await loadAthleteWorkouts();
  showPage('page-athlete-workouts');
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
    document.getElementById('team-detail-icon').textContent = team.sport.icon || '🏐';
    document.getElementById('team-detail-sport').textContent = `${team.sport.icon || ''} ${team.sport.name}`;

    const isCoach = currentUserRole === 'coach';
    document.getElementById('team-detail-actions').style.display = isCoach ? 'flex' : 'none';
    document.getElementById('btn-add-athlete').style.display = isCoach ? 'inline-flex' : 'none';

    const athletesContainer = document.getElementById('team-athletes');
    const noAthletes = document.getElementById('team-no-athletes');
    athletesContainer.innerHTML = '';

    if (team.athletes.length === 0) {
      athletesContainer.style.display = 'none';
      noAthletes.style.display = 'flex';
      noAthletes.innerHTML = emptyStateHTML('👤', 'Nenhum atleta na equipe', 'Adicione atletas compatíveis com o esporte para montar seu elenco.');
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

    loadTeamWorkoutsPreview(teamId);
  } catch (err) {
    console.error('Failed to open team:', err);
  }
}

async function loadTeamWorkoutsPreview(teamId) {
  try {
    const workouts = await apiGet(`/workouts?team_id=${teamId}`);
    const container = document.getElementById('team-workouts-preview');
    container.innerHTML = '';
    const recent = workouts.slice(0, 3);
    if (recent.length === 0) {
      container.innerHTML = '<p class="empty-text">Nenhum treino ainda.</p>';
    } else {
      recent.forEach(w => {
        const date = new Date(w.scheduled_at);
        const dateStr = date.toLocaleDateString('pt-BR');
        container.innerHTML += `
          <div class="workout-card" onclick="openWorkout(${w.id})">
            <span class="workout-card-title">${w.title}</span>
            <div class="workout-card-meta">
              <span>${dateStr}</span>
              <span class="workout-status workout-status-${w.status}">${w.status === 'scheduled' ? 'Agendado' : w.status === 'completed' ? 'Concluido' : 'Cancelado'}</span>
            </div>
          </div>
        `;
      });
    }
  } catch (e) {
    console.error('Failed to load workouts preview:', e);
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
      noCompatible.style.display = 'flex';
      noCompatible.innerHTML = emptyStateHTML('👥', 'Nenhum atleta compatível', 'Cadastre um atleta para este esporte e ele aparecerá aqui.');
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

async function openTeamWorkouts() {
  try {
    const workouts = await apiGet(`/workouts?team_id=${currentTeamId}`);
    const container = document.getElementById('team-workouts-list');
    const noWorkouts = document.getElementById('team-no-workouts');
    const team = await apiGet(`/teams/${currentTeamId}`);
    document.getElementById('workouts-team-name').textContent = `${team.name} - Treinos`;
    document.getElementById('btn-create-workout').style.display = currentUserRole === 'coach' ? 'inline-flex' : 'none';

    container.innerHTML = '';
    if (workouts.length === 0) {
      container.style.display = 'none';
      noWorkouts.style.display = 'flex';
      noWorkouts.innerHTML = emptyStateHTML('📅', 'Nenhum treino ainda', currentUserRole === 'coach'
        ? 'Crie o primeiro treino desta equipe para começar.'
        : 'Quando um treinador criar treinos para esta equipe, eles aparecerão aqui.');
    } else {
      container.style.display = 'flex';
      noWorkouts.style.display = 'none';
      workouts.forEach(w => {
        const date = new Date(w.scheduled_at);
        const dateStr = date.toLocaleDateString('pt-BR');
        const timeStr = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        container.innerHTML += `
          <div class="workout-card" onclick="openWorkout(${w.id})">
            <span class="workout-card-title">${w.title}</span>
            <div class="workout-card-meta">
              <span>${dateStr} - ${timeStr}</span>
              ${w.duration_minutes ? `<span>${w.duration_minutes} min</span>` : ''}
              <span class="workout-status workout-status-${w.status}">${w.status === 'scheduled' ? 'Agendado' : w.status === 'completed' ? 'Concluido' : 'Cancelado'}</span>
            </div>
          </div>
        `;
      });
    }

    showPage('page-team-workouts');
  } catch (err) {
    console.error('Failed to load workouts:', err);
  }
}

function showCreateWorkout() {
  document.getElementById('workout-title').value = '';
  document.getElementById('workout-description').value = '';
  document.getElementById('workout-date').value = '';
  document.getElementById('workout-time').value = '';
  document.getElementById('workout-duration').value = '';
  hideError('create-workout-error');
  showPage('page-create-workout');
}

async function handleCreateWorkout(e) {
  e.preventDefault();
  hideError('create-workout-error');
  const date = document.getElementById('workout-date').value;
  const time = document.getElementById('workout-time').value;
  const scheduledAt = `${date}T${time}:00`;
  try {
    await apiPost('/workouts', {
      team_id: currentTeamId,
      title: document.getElementById('workout-title').value,
      description: document.getElementById('workout-description').value || null,
      scheduled_at: scheduledAt,
      duration_minutes: document.getElementById('workout-duration').value ? parseInt(document.getElementById('workout-duration').value) : null,
    });
    await openTeamWorkouts();
  } catch (err) {
    showError('create-workout-error', err.message);
  }
}

async function openWorkout(workoutId) {
  currentWorkoutId = workoutId;
  try {
    const workout = await apiGet(`/workouts/${workoutId}`);
    document.getElementById('workout-detail-title').textContent = workout.title;
    document.getElementById('workout-detail-team').textContent = `Equipe: ${workout.team.name}`;

    const isCoach = currentUserRole === 'coach';
    document.getElementById('workout-detail-actions').style.display = isCoach ? 'flex' : 'none';

    const statusMap = { scheduled: 'Agendado', completed: 'Concluido', cancelled: 'Cancelado' };
    const statusEl = document.getElementById('workout-detail-status');
    statusEl.textContent = statusMap[workout.status] || workout.status;
    statusEl.className = `profile-value workout-status workout-status-${workout.status}`;

    const date = new Date(workout.scheduled_at);
    document.getElementById('workout-detail-date').textContent = date.toLocaleDateString('pt-BR');
    document.getElementById('workout-detail-time').textContent = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    document.getElementById('workout-detail-duration').textContent = workout.duration_minutes ? `${workout.duration_minutes} minutos` : '-';
    document.getElementById('workout-detail-desc').textContent = workout.description || '-';

    await loadWorkoutExercises(workoutId);
    showPage('page-workout-detail');
  } catch (err) {
    console.error('Failed to open workout:', err);
  }
}

function showEditWorkout() {
  document.getElementById('edit-workout-title').value = document.getElementById('workout-detail-title').textContent;
  document.getElementById('edit-workout-description').value = document.getElementById('workout-detail-desc').textContent === '-' ? '' : document.getElementById('workout-detail-desc').textContent;
  const duration = document.getElementById('workout-detail-duration').textContent;
  document.getElementById('edit-workout-duration').value = duration === '-' ? '' : parseInt(duration);
  hideError('edit-workout-error');
  showPage('page-edit-workout');
}

async function handleEditWorkout(e) {
  e.preventDefault();
  hideError('edit-workout-error');
  const date = document.getElementById('edit-workout-date').value;
  const time = document.getElementById('edit-workout-time').value;
  const scheduledAt = `${date}T${time}:00`;
  try {
    await apiPut(`/workouts/${currentWorkoutId}`, {
      title: document.getElementById('edit-workout-title').value,
      description: document.getElementById('edit-workout-description').value || null,
      scheduled_at: scheduledAt,
      duration_minutes: document.getElementById('edit-workout-duration').value ? parseInt(document.getElementById('edit-workout-duration').value) : null,
      status: document.getElementById('edit-workout-status').value,
    });
    await openWorkout(currentWorkoutId);
  } catch (err) {
    showError('edit-workout-error', err.message);
  }
}

async function handleDeleteWorkout() {
  if (!confirm('Tem certeza que deseja excluir este treino?')) return;
  try {
    await apiDelete(`/workouts/${currentWorkoutId}`);
    await openTeamWorkouts();
  } catch (err) {
    console.error('Failed to delete workout:', err);
  }
}

async function loadAthleteWorkouts() {
  try {
    const workouts = await apiGet('/workouts');
    const container = document.getElementById('athlete-workouts-list');
    const noWorkouts = document.getElementById('athlete-no-workouts');
    container.innerHTML = '';
    if (workouts.length === 0) {
      container.style.display = 'none';
      noWorkouts.style.display = 'flex';
      noWorkouts.innerHTML = emptyStateHTML('📅', 'Nenhum treino disponível', 'Quando um treinador publicar treinos para suas equipes, eles aparecerão aqui.');
    } else {
      container.style.display = 'flex';
      noWorkouts.style.display = 'none';
      workouts.forEach(w => {
        const date = new Date(w.scheduled_at);
        const dateStr = date.toLocaleDateString('pt-BR');
        const timeStr = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        container.innerHTML += `
          <div class="workout-card" onclick="openAthleteWorkout(${w.id})">
            <span class="workout-card-title">${w.title}</span>
            <div class="workout-card-meta">
              <span class="workout-team-label">${w.team_name}</span>
              <span>${dateStr} - ${timeStr}</span>
              ${w.duration_minutes ? `<span>${w.duration_minutes} min</span>` : ''}
              <span class="workout-status workout-status-${w.status}">${w.status === 'scheduled' ? 'Agendado' : w.status === 'completed' ? 'Concluido' : 'Cancelado'}</span>
            </div>
          </div>
        `;
      });
    }
  } catch (e) {
    console.error('Failed to load athlete workouts:', e);
  }
}

async function openAthleteWorkout(workoutId) {
  currentWorkoutId = workoutId;
  try {
    const workout = await apiGet(`/workouts/${workoutId}`);
    document.getElementById('ath-workout-detail-title').textContent = workout.title;
    document.getElementById('ath-workout-detail-team').textContent = `Equipe: ${workout.team.name}`;

    const statusMap = { scheduled: 'Agendado', completed: 'Concluido', cancelled: 'Cancelado' };
    const statusEl = document.getElementById('ath-workout-detail-status');
    statusEl.textContent = statusMap[workout.status] || workout.status;
    statusEl.className = `profile-value workout-status workout-status-${workout.status}`;

    const date = new Date(workout.scheduled_at);
    document.getElementById('ath-workout-detail-date').textContent = date.toLocaleDateString('pt-BR');
    document.getElementById('ath-workout-detail-time').textContent = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    document.getElementById('ath-workout-detail-duration').textContent = workout.duration_minutes ? `${workout.duration_minutes} minutos` : '-';

    loadWorkoutExercisesForAthlete(workoutId);
    showPage('page-athlete-workout-detail');
  } catch (err) {
    console.error('Failed to open athlete workout:', err);
  }
}

async function loadWorkoutExercisesForAthlete(workoutId) {
  try {
    const wes = await apiGet(`/workouts/${workoutId}/exercises`);
    const container = document.getElementById('ath-workout-exercises-list');
    const noExercises = document.getElementById('ath-workout-no-exercises');
    container.innerHTML = '';
    if (wes.length === 0) {
      container.style.display = 'none';
      noExercises.style.display = 'flex';
      noExercises.innerHTML = emptyStateHTML('🏋️', 'Nenhum exercício neste treino', 'Os exercícios deste treino ainda não foram definidos pelo treinador.');
    } else {
      container.style.display = 'flex';
      noExercises.style.display = 'none';
      wes.forEach(we => {
        container.innerHTML += renderExerciseCard(we, false);
      });
    }
  } catch (e) {
    console.error('Failed to load athlete exercises:', e);
  }
}

function exerciseTypeLabel(type) {
  const map = { repetitions: 'Repetições', duration: 'Duração', distance: 'Distância', mixed: 'Misto' };
  return map[type] || type || 'Exercício';
}

function formatDuration(seconds) {
  if (seconds == null) return '';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m > 0) return s > 0 ? `${m}min ${s}s` : `${m}min`;
  return `${s}s`;
}

function renderExerciseCard(we, isCoach) {
  const params = [];
  if (we.sets) params.push(`${we.sets}× séries`);
  if (we.repetitions) params.push(`${we.repetitions} reps`);
  const dur = formatDuration(we.duration_seconds);
  if (dur) params.push(`⏱ ${dur}`);
  if (we.distance_meters) params.push(`${we.distance_meters}m`);
  if (we.rest_seconds) params.push(`Descanso ${we.rest_seconds}s`);

  const actionsHtml = isCoach ? `
    <div class="exercise-card-actions">
      <button class="btn-icon" onclick="showEditWorkoutExercise(${we.id})" title="Editar" aria-label="Editar exercício">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </button>
      <button class="btn-icon btn-icon--danger" onclick="handleDeleteWorkoutExercise(${we.id})" title="Excluir" aria-label="Excluir exercício">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
      </button>
    </div>
  ` : '';

  return `
    <div class="exercise-card">
      <span class="exercise-number" aria-hidden="true">${String(we.order).padStart(2, '0')}</span>
      <div class="exercise-card-main">
        <div class="exercise-card-header">
          <div>
            <span class="exercise-card-name">${we.exercise.name}</span>
            <span class="exercise-card-type">${exerciseTypeLabel(we.exercise.exercise_type)}</span>
          </div>
          ${actionsHtml}
        </div>
        <div class="exercise-card-params">
          ${params.length ? params.map(p => `<span class="exercise-param">${p}</span>`).join('') : '<span class="exercise-param">Sem parâmetros</span>'}
        </div>
        ${we.notes ? `<span class="exercise-note">${we.notes}</span>` : ''}
      </div>
    </div>
  `;
}

async function loadWorkoutExercises(workoutId) {
  try {
    const wes = await apiGet(`/workouts/${workoutId}/exercises`);
    const container = document.getElementById('workout-exercises-list');
    const noExercises = document.getElementById('workout-no-exercises');
    const isCoach = currentUserRole === 'coach';
    document.getElementById('btn-add-workout-exercise').style.display = isCoach ? 'inline-flex' : 'none';

    container.innerHTML = '';
    if (wes.length === 0) {
      container.style.display = 'none';
      noExercises.style.display = 'flex';
      noExercises.innerHTML = emptyStateHTML('🏋️', 'Nenhum exercício neste treino', 'Adicione exercícios compatíveis para montar a ficha deste treino.');
    } else {
      container.style.display = 'flex';
      noExercises.style.display = 'none';
      wes.forEach(we => {
        container.innerHTML += renderExerciseCard(we, isCoach);
      });
    }
  } catch (e) {
    console.error('Failed to load workout exercises:', e);
  }
}

async function showAddWorkoutExercise() {
  try {
    const workout = await apiGet(`/workouts/${currentWorkoutId}`);
    currentExerciseSportId = workout.team.sport_id;
    const exercises = await apiGet(`/exercises?sport_id=${currentExerciseSportId}`);
    const container = document.getElementById('compatible-exercises');
    const noExercises = document.getElementById('no-compatible-exercises');
    container.innerHTML = '';
    if (exercises.length === 0) {
      container.style.display = 'none';
      noExercises.style.display = 'flex';
      noExercises.innerHTML = emptyStateHTML('🏋️', 'Nenhum exercício disponível', 'Cadastre exercícios para este esporte para adicioná-los ao treino.');
    } else {
      container.style.display = 'flex';
      noExercises.style.display = 'none';
      exercises.forEach(e => {
        container.innerHTML += `
          <div class="exercise-select-item" onclick="showConfigureExercise(${e.id}, '${e.name}')">
            <div class="exercise-select-info">
              <span class="exercise-select-name">${e.name}</span>
              <span class="exercise-select-type">${e.exercise_type}</span>
            </div>
            <span style="color:var(--text-secondary)">+</span>
          </div>
        `;
      });
    }
    showPage('page-add-workout-exercise');
  } catch (e) {
    console.error('Failed to load compatible exercises:', e);
  }
}

function showConfigureExercise(exerciseId, exerciseName) {
  currentExerciseId = exerciseId;
  document.getElementById('configure-exercise-title').textContent = `Configurar: ${exerciseName}`;
  document.getElementById('we-order').value = '1';
  document.getElementById('we-sets').value = '';
  document.getElementById('we-repetitions').value = '';
  document.getElementById('we-duration').value = '';
  document.getElementById('we-distance').value = '';
  document.getElementById('we-rest').value = '';
  document.getElementById('we-notes').value = '';
  hideError('configure-exercise-error');
  showPage('page-configure-exercise');
}

async function handleAddWorkoutExercise(e) {
  e.preventDefault();
  hideError('configure-exercise-error');
  const data = {
    exercise_id: currentExerciseId,
    order: parseInt(document.getElementById('we-order').value),
    sets: document.getElementById('we-sets').value ? parseInt(document.getElementById('we-sets').value) : null,
    repetitions: document.getElementById('we-repetitions').value ? parseInt(document.getElementById('we-repetitions').value) : null,
    duration_seconds: document.getElementById('we-duration').value ? parseInt(document.getElementById('we-duration').value) : null,
    distance_meters: document.getElementById('we-distance').value ? parseFloat(document.getElementById('we-distance').value) : null,
    rest_seconds: document.getElementById('we-rest').value ? parseInt(document.getElementById('we-rest').value) : null,
    notes: document.getElementById('we-notes').value || null,
  };
  try {
    await apiPost(`/workouts/${currentWorkoutId}/exercises`, data);
    await openWorkout(currentWorkoutId);
  } catch (err) {
    showError('configure-exercise-error', err.message);
  }
}

async function showEditWorkoutExercise(weId) {
  currentWorkoutExerciseId = weId;
  try {
    const wes = await apiGet(`/workouts/${currentWorkoutId}/exercises`);
    const we = wes.find(w => w.id === weId);
    if (!we) return;
    document.getElementById('edit-we-order').value = we.order;
    document.getElementById('edit-we-sets').value = we.sets || '';
    document.getElementById('edit-we-repetitions').value = we.repetitions || '';
    document.getElementById('edit-we-duration').value = we.duration_seconds || '';
    document.getElementById('edit-we-distance').value = we.distance_meters || '';
    document.getElementById('edit-we-rest').value = we.rest_seconds || '';
    document.getElementById('edit-we-notes').value = we.notes || '';
    hideError('edit-workout-exercise-error');
    showPage('page-edit-workout-exercise');
  } catch (e) {
    console.error('Failed to load workout exercise:', e);
  }
}

async function handleEditWorkoutExercise(e) {
  e.preventDefault();
  hideError('edit-workout-exercise-error');
  const data = {
    order: parseInt(document.getElementById('edit-we-order').value),
    sets: document.getElementById('edit-we-sets').value ? parseInt(document.getElementById('edit-we-sets').value) : null,
    repetitions: document.getElementById('edit-we-repetitions').value ? parseInt(document.getElementById('edit-we-repetitions').value) : null,
    duration_seconds: document.getElementById('edit-we-duration').value ? parseInt(document.getElementById('edit-we-duration').value) : null,
    distance_meters: document.getElementById('edit-we-distance').value ? parseFloat(document.getElementById('edit-we-distance').value) : null,
    rest_seconds: document.getElementById('edit-we-rest').value ? parseInt(document.getElementById('edit-we-rest').value) : null,
    notes: document.getElementById('edit-we-notes').value || null,
  };
  try {
    await apiPut(`/workouts/${currentWorkoutId}/exercises/${currentWorkoutExerciseId}`, data);
    await openWorkout(currentWorkoutId);
  } catch (err) {
    showError('edit-workout-exercise-error', err.message);
  }
}

async function handleDeleteWorkoutExercise(weId) {
  if (!confirm('Remover este exercicio do treino?')) return;
  try {
    await apiDelete(`/workouts/${currentWorkoutId}/exercises/${weId}`);
    await openWorkout(currentWorkoutId);
  } catch (e) {
    console.error('Failed to delete workout exercise:', e);
  }
}

function showCreateExercise() {
  document.getElementById('exercise-name').value = '';
  document.getElementById('exercise-description').value = '';
  document.getElementById('exercise-type').value = 'repetitions';
  hideError('create-exercise-error');
  showPage('page-create-exercise');
}

async function handleCreateExercise(e) {
  e.preventDefault();
  hideError('create-exercise-error');
  try {
    const exercise = await apiPost('/exercises', {
      name: document.getElementById('exercise-name').value,
      description: document.getElementById('exercise-description').value || null,
      sport_id: currentExerciseSportId,
      exercise_type: document.getElementById('exercise-type').value,
    });
    showConfigureExercise(exercise.id, exercise.name);
  } catch (err) {
    showError('create-exercise-error', err.message);
  }
}

function showSuccess(elementId, message) {
  const el = document.getElementById(elementId);
  el.textContent = message;
  el.style.display = 'block';
}

function hideSuccess(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.style.display = 'none';
}

// ========== PROFILE EDIT ==========

async function showProfileEdit() {
  hideError('profile-edit-error');
  hideSuccess('profile-edit-success');
  const isAthlete = currentUserRole === 'athlete';
  document.getElementById('profile-edit-title').textContent = isAthlete ? 'Editar Perfil do Atleta' : 'Editar Perfil do Treinador';
  document.getElementById('profile-edit-sport-group').style.display = isAthlete ? 'block' : 'none';
  document.getElementById('profile-edit-position-group').style.display = isAthlete ? 'block' : 'none';
  document.getElementById('profile-edit-sports-group').style.display = isAthlete ? 'none' : 'block';
  document.getElementById('profile-edit-name').value = document.getElementById('sidebar-name').textContent;
  try {
    const sports = currentSports.length ? currentSports : await apiGet('/sports');
    if (isAthlete) {
      const profile = await apiGet('/athletes/me');
      const sportSel = document.getElementById('profile-edit-sport');
      sportSel.innerHTML = '<option value="">Nenhum</option>' + sports.map(s => `<option value="${s.id}">${s.icon || ''} ${s.name}</option>`).join('');
      sportSel.value = profile.sport ? profile.sport.id : '';
      await loadProfilePositions(profile.sport ? profile.sport.id : null, profile.position ? profile.position.id : null);
    } else {
      const profile = await apiGet('/coaches/me');
      const container = document.getElementById('profile-edit-coach-sports');
      const owns = new Set((profile.sports || []).map(s => s.id));
      container.innerHTML = sports.map(s => `
        <div class="checkbox-item">
          <input type="checkbox" id="profile-coach-sport-${s.id}" value="${s.id}" ${owns.has(s.id) ? 'checked' : ''}>
          <label for="profile-coach-sport-${s.id}">${s.icon || ''} ${s.name}</label>
        </div>
      `).join('');
    }
    showPage('page-profile-edit');
  } catch (err) {
    showError('profile-edit-error', err.message);
  }
}

async function loadProfilePositions(sportId, selectedPositionId) {
  const posSel = document.getElementById('profile-edit-position');
  if (!sportId) {
    posSel.innerHTML = '<option value="">Nenhuma posição</option>';
    return;
  }
  try {
    const positions = await apiGet(`/sports/${sportId}/positions`);
    posSel.innerHTML = '<option value="">Nenhuma posição</option>' + positions.map(p =>
      `<option value="${p.id}" ${p.id === selectedPositionId ? 'selected' : ''}>${p.name}</option>`
    ).join('');
  } catch (err) {
    console.error('Failed to load positions:', err);
  }
}

async function onProfileSportChange() {
  const sportVal = document.getElementById('profile-edit-sport').value;
  await loadProfilePositions(sportVal ? parseInt(sportVal, 10) : null, null);
}

async function handleProfileEdit(e) {
  e.preventDefault();
  hideError('profile-edit-error');
  hideSuccess('profile-edit-success');
  const btn = document.getElementById('profile-edit-btn');
  const name = document.getElementById('profile-edit-name').value;
  const finish = () => {
    btn.disabled = false;
    btn.textContent = 'Salvar';
  };
  if (currentUserRole !== 'athlete') {
    const checked = document.querySelectorAll('#profile-edit-coach-sports input[type="checkbox"]:checked');
    const sportIds = Array.from(checked).map(c => parseInt(c.value, 10));
    if (sportIds.length === 0) {
      showError('profile-edit-error', 'Selecione pelo menos um esporte');
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Salvando...';
    try {
      await apiPut('/coaches/me', { name, sport_ids: sportIds });
      showSuccess('profile-edit-success', 'Perfil atualizado com sucesso.');
      await loadDashboard();
    } catch (err) {
      showError('profile-edit-error', err.message);
    } finally {
      finish();
    }
    return;
  }
  const sportVal = document.getElementById('profile-edit-sport').value;
  const posVal = document.getElementById('profile-edit-position').value;
  const sportId = sportVal ? parseInt(sportVal, 10) : null;
  const positionId = sportId && posVal ? parseInt(posVal, 10) : null;
  btn.disabled = true;
  btn.textContent = 'Salvando...';
  try {
    await apiPut('/athletes/me', { name, sport_id: sportId, position_id: positionId });
    showSuccess('profile-edit-success', 'Perfil atualizado com sucesso.');
    await loadDashboard();
  } catch (err) {
    showError('profile-edit-error', err.message);
  } finally {
    finish();
  }
}

// ========== ATHLETE ATTRIBUTES ==========

let currentAttributesSportId = null;

async function showAttributesEdit() {
  hideError('attributes-edit-error-msg');
  hideSuccess('attributes-edit-success');
  const loading = document.getElementById('attributes-edit-loading');
  const errBox = document.getElementById('attributes-edit-error');
  loading.innerHTML = skeletonCards(3);
  errBox.style.display = 'none';
  document.getElementById('attributes-form-wrap').style.display = 'none';
  try {
    const profile = await apiGet('/athletes/me');
    if (!profile.sport) {
      loading.innerHTML = '';
      errBox.innerHTML = emptyStateHTML('🎯', 'Nenhum esporte definido', 'Defina um esporte no seu perfil para avaliar seus atributos.',
        '<button class="btn btn-primary btn-sm" onclick="showProfileEdit()">Editar perfil</button>');
      errBox.style.display = 'flex';
      return;
    }
    const [catalog, values] = await Promise.all([
      apiGet(`/sports/${profile.sport.id}/attributes`),
      apiGet('/athletes/me/attributes'),
    ]);
    currentAttributesSportId = profile.sport.id;
    const valueMap = {};
    values.forEach(v => { valueMap[v.attribute_id] = v.value; });
    loading.innerHTML = '';
    const fields = document.getElementById('attributes-fields');
    fields.innerHTML = catalog.map(a => {
      const val = valueMap[a.id] != null ? valueMap[a.id] : 50;
      return `
        <div class="attribute-field">
          <div class="attribute-field-head">
            <span class="attribute-name">${a.name}</span>
            <output class="attribute-value" id="attr-output-${a.id}" for="attr-input-${a.id}">${val}</output>
          </div>
          <input type="range" class="attribute-range" id="attr-input-${a.id}" min="0" max="100" step="1" value="${val}" oninput="document.getElementById('attr-output-${a.id}').value = this.value">
        </div>
      `;
    }).join('');
    document.getElementById('attributes-form-wrap').style.display = 'block';
    showPage('page-attributes-edit');
  } catch (err) {
    loading.innerHTML = '';
    errBox.innerHTML = `
      <span class="error-icon" aria-hidden="true">⚠️</span>
      <strong>Não foi possível carregar seus atributos.</strong>
      <p>${err.message}</p>
      <button class="btn btn-secondary btn-sm" onclick="showAttributesEdit()">Tentar novamente</button>
    `;
    errBox.style.display = 'flex';
  }
}

async function handleAttributesEdit(e) {
  e.preventDefault();
  hideError('attributes-edit-error-msg');
  hideSuccess('attributes-edit-success');
  const btn = document.getElementById('attributes-save-btn');
  btn.disabled = true;
  btn.textContent = 'Salvando...';
  try {
    const catalog = await apiGet(`/sports/${currentAttributesSportId}/attributes`);
    const attributes = catalog.map(a => ({
      attribute_id: a.id,
      value: parseInt(document.getElementById(`attr-input-${a.id}`).value, 10),
    }));
    await apiPut('/athletes/me/attributes', { attributes });
    showSuccess('attributes-edit-success', 'Avaliação salva com sucesso.');
    await loadDashboard();
  } catch (err) {
    showError('attributes-edit-error-msg', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Salvar avaliação';
  }
}

// ========== EXERCISE LIBRARY (coach) ==========

let currentCoachId = null;
let libraryEditExerciseId = null;

function librarySportName(sportId) {
  const s = currentSports.find(x => x.id === sportId);
  return s ? `${s.icon || ''} ${s.name}` : 'Esporte';
}

function hideLibraryFeedback() {
  document.getElementById('library-feedback').style.display = 'none';
}

function showLibraryFeedback(message) {
  const el = document.getElementById('library-feedback');
  el.textContent = message;
  el.style.display = 'block';
}

async function openExerciseLibrary() {
  hideLibraryFeedback();
  hideError('lib-exercise-form-error');
  try {
    const profile = await apiGet('/coaches/me');
    currentCoachId = profile.id;
    const sports = profile.sports || [];
    const filter = document.getElementById('library-sport-filter');
    filter.innerHTML = '<option value="">Todos os esportes</option>' + sports.map(s =>
      `<option value="${s.id}">${s.icon || ''} ${s.name}</option>`).join('');
    const sportSel = document.getElementById('lib-exercise-sport');
    sportSel.innerHTML = sports.map(s =>
      `<option value="${s.id}">${s.icon || ''} ${s.name}</option>`).join('');
    document.getElementById('library-sport-filter').value = '';
  } catch (err) {
    showLibraryFeedback(err.message);
  }
  await loadExerciseLibrary();
  showPage('page-exercise-library');
}

async function loadExerciseLibrary() {
  const loading = document.getElementById('library-exercises-loading');
  const list = document.getElementById('library-exercises-list');
  const noExercises = document.getElementById('library-no-exercises');
  loading.innerHTML = skeletonCards(3);
  list.style.display = 'none';
  noExercises.style.display = 'none';
  const sportId = document.getElementById('library-sport-filter').value;
  try {
    const exercises = await apiGet(`/exercises${sportId ? `?sport_id=${sportId}` : ''}`);
    loading.innerHTML = '';
    list.innerHTML = '';
    if (exercises.length === 0) {
      list.style.display = 'none';
      noExercises.style.display = 'flex';
      noExercises.innerHTML = emptyStateHTML('🏋️', 'Nenhum exercício encontrado', 'Crie exercícios para montar sua biblioteca reutilizável de treinos.',
        '<button class="btn btn-primary btn-sm" onclick="showLibraryForm(\'create\')">+ Novo exercício</button>');
      return;
    }
    list.style.display = 'flex';
    exercises.forEach(ex => {
      const mine = currentCoachId != null && ex.created_by === currentCoachId;
      const actions = mine ? `
        <div class="exercise-card-actions">
          <button class="btn-icon" onclick="showLibraryForm('edit', ${ex.id})" title="Editar" aria-label="Editar exercício">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="btn-icon btn-icon--danger" onclick="handleLibraryDeleteExercise(${ex.id})" title="Excluir" aria-label="Excluir exercício">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>` : '';
      list.innerHTML += `
        <div class="exercise-select-item library-row">
          <div class="exercise-select-info">
            <span class="exercise-select-name">${ex.name}</span>
            <span class="exercise-select-type">${exerciseTypeLabel(ex.exercise_type)} · ${librarySportName(ex.sport_id)}${mine ? '' : ' · outro treinador'}</span>
          </div>
          ${actions}
        </div>
      `;
    });
  } catch (err) {
    loading.innerHTML = '';
    list.style.display = 'none';
    noExercises.style.display = 'none';
    showLibraryFeedback(`Não foi possível carregar os exercícios: ${err.message}`);
  }
}

async function showLibraryForm(mode, exerciseId) {
  hideError('lib-exercise-form-error');
  hideLibraryFeedback();
  const form = document.getElementById('library-exercise-form');
  if (!mode) {
    form.style.display = 'none';
    return;
  }
  libraryEditExerciseId = mode === 'edit' ? exerciseId : null;
  document.getElementById('lib-exercise-name').value = '';
  document.getElementById('lib-exercise-description').value = '';
  document.getElementById('lib-exercise-type').value = 'repetitions';
  document.getElementById('lib-exercise-sport-group').style.display = mode === 'create' ? 'block' : 'none';
  document.getElementById('lib-exercise-sport').required = mode === 'create';
  document.getElementById('library-form-title').textContent = mode === 'edit' ? 'Editar exercício' : 'Novo exercício';
  document.getElementById('lib-exercise-form-btn').textContent = mode === 'edit' ? 'Salvar alterações' : 'Criar exercício';
  if (mode === 'edit') {
    try {
      const ex = await apiGet(`/exercises/${exerciseId}`);
      document.getElementById('lib-exercise-name').value = ex.name;
      document.getElementById('lib-exercise-description').value = ex.description || '';
      document.getElementById('lib-exercise-type').value = ex.exercise_type;
    } catch (err) {
      showLibraryFeedback(err.message);
      return;
    }
  }
  form.style.display = 'block';
  form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function handleLibraryExerciseForm(e) {
  e.preventDefault();
  hideError('lib-exercise-form-error');
  hideLibraryFeedback();
  const btn = document.getElementById('lib-exercise-form-btn');
  btn.disabled = true;
  const name = document.getElementById('lib-exercise-name').value;
  const description = document.getElementById('lib-exercise-description').value || null;
  const exerciseType = document.getElementById('lib-exercise-type').value;
  try {
    if (libraryEditExerciseId) {
      await apiPut(`/exercises/${libraryEditExerciseId}`, { name, description, exercise_type: exerciseType });
    } else {
      const sportId = parseInt(document.getElementById('lib-exercise-sport').value, 10);
      await apiPost('/exercises', { name, description, sport_id: sportId, exercise_type: exerciseType });
    }
    showLibraryForm(null);
    await loadExerciseLibrary();
  } catch (err) {
    showError('lib-exercise-form-error', err.message);
  } finally {
    btn.disabled = false;
  }
}

async function handleLibraryDeleteExercise(exerciseId) {
  if (!confirm('Excluir este exercício da biblioteca?')) return;
  hideLibraryFeedback();
  try {
    await apiDelete(`/exercises/${exerciseId}`);
    if (libraryEditExerciseId === exerciseId) showLibraryForm(null);
    await loadExerciseLibrary();
  } catch (err) {
    showLibraryFeedback(err.message);
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
