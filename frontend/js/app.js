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
      await loadAthleteWorkouts();
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
      noWorkouts.style.display = 'block';
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
      noWorkouts.style.display = 'block';
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
      noExercises.style.display = 'block';
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

function renderExerciseCard(we, isCoach) {
  const params = [];
  if (we.sets) params.push(`${we.sets} series`);
  if (we.repetitions) params.push(`${we.repetitions} reps`);
  if (we.duration_seconds) params.push(`${we.duration_seconds}s`);
  if (we.distance_meters) params.push(`${we.distance_meters}m`);
  if (we.rest_seconds) params.push(`${we.rest_seconds}s descanso`);

  const actionsHtml = isCoach ? `
    <div class="exercise-card-actions">
      <button class="btn-icon" onclick="showEditWorkoutExercise(${we.id})" title="Editar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </button>
      <button class="btn-icon" onclick="handleDeleteWorkoutExercise(${we.id})" title="Excluir">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
      </button>
    </div>
  ` : '';

  return `
    <div class="exercise-card">
      <div class="exercise-card-header">
        <div>
          <span class="exercise-card-order">${we.order}.</span>
          <span class="exercise-card-name">${we.exercise.name}</span>
          <span class="exercise-card-type">${we.exercise.exercise_type}</span>
        </div>
        ${actionsHtml}
      </div>
      <div class="exercise-card-params">
        ${params.map(p => `<span>${p}</span>`).join('')}
        ${we.notes ? `<span>${we.notes}</span>` : ''}
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
      noExercises.style.display = 'block';
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
      noExercises.style.display = 'block';
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

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (token) {
    loadDashboard();
  } else {
    showPage('page-home');
  }
});
