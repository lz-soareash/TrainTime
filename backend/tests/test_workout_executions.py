import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.main import app
from app.services.seed import seed_sports

TEST_DATABASE_URL = "sqlite:///./test_train_time.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_sports(db)
    finally:
        db.close()


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    try:
        if os.path.exists("test_train_time.db"):
            os.remove("test_train_time.db")
    except PermissionError:
        pass


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def register_coach(email="coach_exc@test.com", password="123456"):
    return client.post("/api/auth/register/coach", json={
        "name": "Treinador Execucao", "email": email, "password": password,
        "sport_ids": [1, 2],
    })


def register_athlete(email="ath_exc@test.com", password="123456", sport_id=1, position_id=1):
    return client.post("/api/auth/register/athlete", json={
        "name": "Atleta Execucao", "email": email, "password": password,
        "sport_id": sport_id, "position_id": position_id,
    })


def login(email="treinador@test.com", password="123456"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def create_team_helper(coach_email, name="Equipe Execucao"):
    login_resp = login(email=coach_email)
    token = login_resp.json()["access_token"]
    return client.post("/api/teams", headers=auth_header(token), json={
        "name": name, "sport_id": 1,
    }), token


def create_workout_helper(token, team_id, title="Treino Execucao"):
    return client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": team_id, "title": title,
        "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
    })


def create_exercise_helper(token, name="Exercicio Execucao"):
    return client.post("/api/exercises", headers=auth_header(token), json={
        "name": name, "sport_id": 1, "exercise_type": "repetitions",
    })


def add_we_helper(token, workout_id, exercise_id, order=1):
    return client.post(f"/api/workouts/{workout_id}/exercises",
                       headers=auth_header(token), json={
                           "exercise_id": exercise_id, "order": order,
                           "sets": 3, "repetitions": 12,
                       })


def add_athlete_to_team(coach_token, team_id, ath_token):
    profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = profile["id"]
    return client.post(f"/api/teams/{team_id}/athletes/{ath_id}",
                       headers=auth_header(coach_token))


def setup_execution_happy(coach_email, ath_email):
    register_coach(email=coach_email)
    register_athlete(email=ath_email)
    team_resp, token = create_team_helper(coach_email)
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    login_resp = login(email=ath_email)
    ath_token = login_resp.json()["access_token"]
    add_athlete_to_team(token, team_id, ath_token)
    return workout_id, ath_token


# ========== START EXECUTION ==========

def test_athlete_starts_workout_execution():
    workout_id, ath_token = setup_execution_happy(
        "coach_ex_st@test.com", "ath_ex_st@test.com")
    resp = client.post(f"/api/workouts/{workout_id}/executions",
                       headers=auth_header(ath_token), json={"notes": "Comecei o treino",
                                                             "started_at": datetime.now().isoformat()})
    assert resp.status_code == 201
    data = resp.json()
    assert data["workout_id"] == workout_id
    assert data["status"] == "in_progress"
    assert data["started_at"] is not None


def test_athlete_cannot_start_execution_not_in_team():
    register_coach(email="coach_ex_nt@test.com")
    register_athlete(email="ath_ex_nt@test.com")
    team_resp, token = create_team_helper("coach_ex_nt@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    login_resp = login(email="ath_ex_nt@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.post(f"/api/workouts/{workout_id}/executions",
                       headers=auth_header(ath_token), json={})
    assert resp.status_code == 403


def test_execution_endpoint_requires_token():
    register_coach(email="coach_ex_tk@test.com")
    register_athlete(email="ath_ex_tk@test.com")
    team_resp, token = create_team_helper("coach_ex_tk@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = client.post(f"/api/workouts/{workout_id}/executions", json={})
    assert resp.status_code == 401


# ========== LIST + VIEW EXECUTION ==========

def test_athlete_lists_own_executions():
    workout_id, ath_token = setup_execution_happy(
        "coach_ex_ls@test.com", "ath_ex_ls@test.com")
    client.post(f"/api/workouts/{workout_id}/executions",
                headers=auth_header(ath_token), json={})
    resp = client.get(f"/api/workouts/{workout_id}/executions",
                      headers=auth_header(ath_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_coach_lists_team_executions():
    register_coach(email="coach_ex_lc@test.com")
    register_athlete(email="ath_ex_lc@test.com")
    team_resp, token = create_team_helper("coach_ex_lc@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    login_resp = login(email="ath_ex_lc@test.com")
    ath_token = login_resp.json()["access_token"]
    add_athlete_to_team(token, team_id, ath_token)
    client.post(f"/api/workouts/{workout_id}/executions",
                headers=auth_header(ath_token), json={})
    resp = client.get(f"/api/workouts/{workout_id}/executions",
                      headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_athlete_views_own_execution_detail():
    workout_id, ath_token = setup_execution_happy(
        "coach_ex_vw@test.com", "ath_ex_vw@test.com")
    start_resp = client.post(f"/api/workouts/{workout_id}/executions",
                             headers=auth_header(ath_token), json={})
    execution_id = start_resp.json()["id"]
    resp = client.get(f"/api/workouts/{workout_id}/executions/{execution_id}",
                      headers=auth_header(ath_token))
    assert resp.status_code == 200
    assert resp.json()["id"] == execution_id


# ========== UPDATE / COMPLETE ==========

def test_athlete_completes_execution():
    workout_id, ath_token = setup_execution_happy(
        "coach_ex_cm@test.com", "ath_ex_cm@test.com")
    start_resp = client.post(f"/api/workouts/{workout_id}/executions",
                             headers=auth_header(ath_token), json={})
    execution_id = start_resp.json()["id"]
    resp = client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
                      headers=auth_header(ath_token),
                      json={"status": "completed"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["finished_at"] is not None


def test_invalid_execution_status():
    workout_id, ath_token = setup_execution_happy(
        "coach_ex_iv@test.com", "ath_ex_iv@test.com")
    start_resp = client.post(f"/api/workouts/{workout_id}/executions",
                             headers=auth_header(ath_token), json={})
    execution_id = start_resp.json()["id"]
    resp = client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
                      headers=auth_header(ath_token), json={"status": "invalido"})
    assert resp.status_code == 422


# ========== EXERCISE RESULTS ==========

def test_athlete_adds_exercise_result():
    workout_id, ath_token = setup_execution_happy(
        "coach_ex_er@test.com", "ath_ex_er@test.com")
    login_resp = login(email="coach_ex_er@test.com")
    coach_token = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(coach_token)
    exercise_id = exercise_resp.json()["id"]
    we_resp = add_we_helper(coach_token, workout_id, exercise_id)
    workout_exercise_id = we_resp.json()["id"]
    start_resp = client.post(f"/api/workouts/{workout_id}/executions",
                             headers=auth_header(ath_token), json={})
    execution_id = start_resp.json()["id"]
    resp = client.post(f"/api/workouts/{workout_id}/executions/{execution_id}"
                       f"/exercises/{workout_exercise_id}",
                       headers=auth_header(ath_token),
                       json={"status": "done", "actual_sets": 3,
                             "actual_repetitions": 12})
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["actual_sets"] == 3
    assert data["status"] == "done"


# ========== REGRESSAO FASE 9 (bug 4: upsert) ==========

def _setup_exercise_with_result(email_suffix):
    workout_id, ath_token = setup_execution_happy(
        f"coach_up_{email_suffix}@test.com", f"ath_up_{email_suffix}@test.com")
    coach_token = login(email=f"coach_up_{email_suffix}@test.com").json()["access_token"]
    exercise_id = create_exercise_helper(coach_token).json()["id"]
    workout_exercise_id = add_we_helper(
        coach_token, workout_id, exercise_id).json()["id"]
    execution_id = client.post(f"/api/workouts/{workout_id}/executions",
                               headers=auth_header(ath_token), json={}).json()["id"]
    return workout_id, execution_id, workout_exercise_id, ath_token


def _post_result(workout_id, execution_id, we_id, token, payload):
    return client.post(
        f"/api/workouts/{workout_id}/executions/{execution_id}/exercises/{we_id}",
        headers=auth_header(token), json=payload)


def _results(workout_id, execution_id, token):
    resp = client.get(f"/api/workouts/{workout_id}/executions/{execution_id}",
                      headers=auth_header(token))
    return resp.json()["exercise_results"]


def test_saving_same_exercise_twice_does_not_duplicate():
    """Bug 4: cada POST criava uma nova linha, duplicando o resultado."""
    workout_id, execution_id, we_id, ath_token = _setup_exercise_with_result("dup")
    for _ in range(3):
        resp = _post_result(workout_id, execution_id, we_id, ath_token,
                            {"status": "done", "actual_sets": 3,
                             "actual_repetitions": 12})
        assert resp.status_code in (200, 201)
    results = _results(workout_id, execution_id, ath_token)
    assert len(results) == 1, f"duplicou: {len(results)} linhas"
    assert results[0]["actual_sets"] == 3


def test_resaving_updates_existing_result():
    """Bug 4: re-salvar deve atualizar, nao acumular."""
    workout_id, execution_id, we_id, ath_token = _setup_exercise_with_result("upd")
    _post_result(workout_id, execution_id, we_id, ath_token,
                 {"status": "pending", "actual_sets": 3, "actual_repetitions": 12})
    _post_result(workout_id, execution_id, we_id, ath_token,
                 {"status": "done", "actual_sets": 5, "actual_repetitions": 15,
                  "actual_weight_kg": 80.0})
    results = _results(workout_id, execution_id, ath_token)
    assert len(results) == 1
    row = results[0]
    assert row["status"] == "done"
    assert row["actual_sets"] == 5
    assert row["actual_repetitions"] == 15
    assert row["actual_weight_kg"] == 80.0


def test_result_id_is_stable_across_saves():
    """Bug 4: o id do resultado nao deve mudar ao re-salvar."""
    workout_id, execution_id, we_id, ath_token = _setup_exercise_with_result("id")
    first = _post_result(workout_id, execution_id, we_id, ath_token,
                         {"status": "done", "actual_sets": 3}).json()
    second = _post_result(workout_id, execution_id, we_id, ath_token,
                          {"status": "done", "actual_sets": 4}).json()
    assert first["id"] == second["id"]


def test_skipping_after_done_marks_row_skipped():
    """Bug 4: pular depois de feito deve reaproveitar a mesma linha."""
    workout_id, execution_id, we_id, ath_token = _setup_exercise_with_result("skip")
    _post_result(workout_id, execution_id, we_id, ath_token,
                 {"status": "done", "actual_sets": 3})
    _post_result(workout_id, execution_id, we_id, ath_token, {"status": "skipped"})
    results = _results(workout_id, execution_id, ath_token)
    assert len(results) == 1
    assert results[0]["status"] == "skipped"


def test_distinct_exercises_keep_separate_results():
    """Bug 4: exercicios diferentes nao podem ser confundidos no upsert."""
    workout_id, ath_token = setup_execution_happy(
        "coach_up_multi@test.com", "ath_up_multi@test.com")
    coach_token = login(email="coach_up_multi@test.com").json()["access_token"]
    ex_a = create_exercise_helper(coach_token, "Exercicio A").json()["id"]
    ex_b = create_exercise_helper(coach_token, "Exercicio B").json()["id"]
    we_a = add_we_helper(coach_token, workout_id, ex_a, order=1).json()["id"]
    we_b = add_we_helper(coach_token, workout_id, ex_b, order=2).json()["id"]
    execution_id = client.post(f"/api/workouts/{workout_id}/executions",
                               headers=auth_header(ath_token), json={}).json()["id"]
    _post_result(workout_id, execution_id, we_a, ath_token,
                 {"status": "done", "actual_sets": 3})
    _post_result(workout_id, execution_id, we_b, ath_token,
                 {"status": "done", "actual_sets": 5})
    _post_result(workout_id, execution_id, we_a, ath_token,
                 {"status": "done", "actual_sets": 4})
    results = _results(workout_id, execution_id, ath_token)
    assert len(results) == 2
    by_we = {r["workout_exercise_id"]: r["actual_sets"] for r in results}
    assert by_we[we_a] == 4
    assert by_we[we_b] == 5


# ========== FASE 10: metricas reais, escopo da URL e comparacao ==========

def _perf_records(ath_token, metric=None):
    resp = client.get("/api/performance", headers=auth_header(ath_token))
    assert resp.status_code == 200
    records = resp.json()
    if metric:
        records = [r for r in records if r["metric"] == metric]
    return records


def _setup_done_execution(suffix, sets=3, reps=12, weight=80.0):
    """Execucao em andamento com 1 exercicio e resultado ja registrado."""
    workout_id, execution_id, we_id, ath_token = _setup_exercise_with_result(suffix)
    payload = {"status": "done", "actual_sets": sets, "actual_repetitions": reps}
    if weight is not None:
        payload["actual_weight_kg"] = weight
    _post_result(workout_id, execution_id, we_id, ath_token, payload)
    return workout_id, execution_id, we_id, ath_token


# --- 1. workout_id da URL precisa bater com a execucao ---

def test_get_execution_rejects_wrong_workout_in_url():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_g@test.com", "ath_f10_g@test.com")
    execution_id = client.post(f"/api/workouts/{workout_id}/executions",
                               headers=auth_header(ath_token), json={}).json()["id"]
    resp = client.get(f"/api/workouts/{workout_id + 999}/executions/{execution_id}",
                      headers=auth_header(ath_token))
    assert resp.status_code == 404, "workout_id da URL foi ignorado"


def test_update_execution_rejects_wrong_workout_in_url():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_u@test.com", "ath_f10_u@test.com")
    execution_id = client.post(f"/api/workouts/{workout_id}/executions",
                               headers=auth_header(ath_token), json={}).json()["id"]
    resp = client.put(f"/api/workouts/{workout_id + 999}/executions/{execution_id}",
                      headers=auth_header(ath_token), json={"notes": "x"})
    assert resp.status_code == 404, "workout_id da URL foi ignorado"


def test_exercise_result_rejects_wrong_workout_in_url():
    workout_id, execution_id, we_id, ath_token = _setup_done_execution("urlres")
    resp = _post_result(workout_id + 999, execution_id, we_id, ath_token,
                        {"status": "done", "actual_sets": 1})
    assert resp.status_code == 404, "workout_id da URL foi ignorado"


def test_coach_get_execution_rejects_wrong_workout_in_url():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_c@test.com", "ath_f10_c@test.com")
    execution_id = client.post(f"/api/workouts/{workout_id}/executions",
                               headers=auth_header(ath_token), json={}).json()["id"]
    coach_token = login(email="coach_f10_c@test.com").json()["access_token"]
    resp = client.get(f"/api/workouts/{workout_id + 999}/executions/{execution_id}",
                      headers=auth_header(coach_token))
    assert resp.status_code == 404, "workout_id da URL foi ignorado"


# --- 2. volume e carga usam valores REALIZADOS ---

def test_volume_uses_actual_values_not_planned():
    """Planejado 3x12 sem peso; realizado 5x10 com 40kg."""
    workout_id, execution_id, we_id, ath_token = _setup_done_execution(
        "vol", sets=5, reps=10, weight=40.0)
    client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
               headers=auth_header(ath_token), json={"status": "completed"})
    volumes = _perf_records(ath_token, "volume")
    assert len(volumes) == 1
    assert volumes[0]["value"] == 50.0, "volume planejado (36) em vez do realizado (50)"


def test_carga_is_generated_from_actual_weight():
    workout_id, execution_id, we_id, ath_token = _setup_done_execution(
        "carga", sets=5, reps=10, weight=40.0)
    client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
               headers=auth_header(ath_token), json={"status": "completed"})
    cargas = _perf_records(ath_token, "carga")
    assert len(cargas) == 1
    assert cargas[0]["value"] == 2000.0, "5x10x40 = 2000"


def test_no_carga_record_without_actual_weight():
    workout_id, execution_id, we_id, ath_token = _setup_done_execution(
        "semcarga", sets=4, reps=10, weight=None)
    client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
               headers=auth_header(ath_token), json={"status": "completed"})
    assert _perf_records(ath_token, "carga") == []


def test_skipped_exercise_does_not_add_volume():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_sk@test.com", "ath_f10_sk@test.com")
    coach_token = login(email="coach_f10_sk@test.com").json()["access_token"]
    exercise_id = create_exercise_helper(coach_token, "Ex Pulado").json()["id"]
    we_id = add_we_helper(coach_token, workout_id, exercise_id).json()["id"]
    execution_id = client.post(f"/api/workouts/{workout_id}/executions",
                               headers=auth_header(ath_token), json={}).json()["id"]
    _post_result(workout_id, execution_id, we_id, ath_token, {"status": "skipped"})
    client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
               headers=auth_header(ath_token), json={"status": "completed"})
    assert _perf_records(ath_token, "volume") == [], "exercicio pulado contou volume"


# --- 3. concluir duas vezes nao duplica desempenho ---

def test_completing_twice_does_not_duplicate_performance():
    workout_id, execution_id, we_id, ath_token = _setup_done_execution("dupperf")
    for _ in range(3):
        resp = client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
                          headers=auth_header(ath_token),
                          json={"status": "completed"})
        assert resp.status_code == 200
    assert len(_perf_records(ath_token, "volume")) == 1, "volume duplicado"
    assert len(_perf_records(ath_token, "carga")) == 1, "carga duplicada"


def test_cannot_reopen_completed_execution():
    workout_id, execution_id, we_id, ath_token = _setup_done_execution("reopen")
    client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
               headers=auth_header(ath_token), json={"status": "completed"})
    resp = client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
                      headers=auth_header(ath_token),
                      json={"status": "in_progress"})
    assert resp.status_code == 400, "execucao concluida voltou para in_progress"


# --- 4. resumo/comparacao/previsao ---

def test_summary_returns_metrics_per_execution():
    workout_id, execution_id, we_id, ath_token = _setup_done_execution("sum1")
    client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
               headers=auth_header(ath_token), json={"status": "completed"})
    resp = client.get(f"/api/workouts/{workout_id}/executions/summary",
                      headers=auth_header(ath_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["workout_id"] == workout_id
    assert len(data["executions"]) == 1
    item = data["executions"][0]
    assert item["id"] == execution_id
    assert item["volume"] == 36.0
    assert item["carga"] == 2880.0
    assert item["exercicios_planejados"] == 1
    assert item["exercicios_feitos"] == 1
    assert item["aderencia_pct"] == 100.0
    assert item["duracao_s"] is not None and item["duracao_s"] >= 0


def test_summary_delta_compares_with_previous_execution():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_d@test.com", "ath_f10_d@test.com")
    coach_token = login(email="coach_f10_d@test.com").json()["access_token"]
    exercise_id = create_exercise_helper(coach_token, "Ex Delta").json()["id"]
    we_id = add_we_helper(coach_token, workout_id, exercise_id).json()["id"]

    e1 = client.post(f"/api/workouts/{workout_id}/executions",
                     headers=auth_header(ath_token), json={}).json()["id"]
    _post_result(workout_id, e1, we_id, ath_token,
                 {"status": "done", "actual_sets": 3, "actual_repetitions": 10,
                  "actual_weight_kg": 50.0})
    client.put(f"/api/workouts/{workout_id}/executions/{e1}",
               headers=auth_header(ath_token), json={"status": "completed"})

    e2 = client.post(f"/api/workouts/{workout_id}/executions",
                     headers=auth_header(ath_token), json={}).json()["id"]
    _post_result(workout_id, e2, we_id, ath_token,
                 {"status": "done", "actual_sets": 5, "actual_repetitions": 10,
                  "actual_weight_kg": 50.0})
    client.put(f"/api/workouts/{workout_id}/executions/{e2}",
               headers=auth_header(ath_token), json={"status": "completed"})

    data = client.get(f"/api/workouts/{workout_id}/executions/summary",
                      headers=auth_header(ath_token)).json()
    by_id = {e["id"]: e for e in data["executions"]}
    assert by_id[e1]["volume"] == 30.0
    assert by_id[e2]["volume"] == 50.0
    assert by_id[e2]["delta"]["volume"] == 20.0
    assert by_id[e1]["delta"] is None, "primeira execucao nao tem execucao anterior"
    assert by_id[e2]["delta"]["carga"] == 1000.0, "50 reps x 50kg = 2500 - 1500"


def test_summary_forecast_averages_completed_executions():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_f@test.com", "ath_f10_f@test.com")
    coach_token = login(email="coach_f10_f@test.com").json()["access_token"]
    exercise_id = create_exercise_helper(coach_token, "Ex Prev").json()["id"]
    we_id = add_we_helper(coach_token, workout_id, exercise_id).json()["id"]
    for sets in (3, 5):
        eid = client.post(f"/api/workouts/{workout_id}/executions",
                          headers=auth_header(ath_token), json={}).json()["id"]
        _post_result(workout_id, eid, we_id, ath_token,
                     {"status": "done", "actual_sets": sets,
                      "actual_repetitions": 10})
        client.put(f"/api/workouts/{workout_id}/executions/{eid}",
                   headers=auth_header(ath_token), json={"status": "completed"})
    data = client.get(f"/api/workouts/{workout_id}/executions/summary",
                      headers=auth_header(ath_token)).json()
    forecast = data["forecast"]
    assert forecast["amostra"] == 2
    assert forecast["volume"] == 40.0, "media de 30 e 50"


def test_summary_ignores_executions_in_progress():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_i@test.com", "ath_f10_i@test.com")
    client.post(f"/api/workouts/{workout_id}/executions",
                headers=auth_header(ath_token), json={})
    data = client.get(f"/api/workouts/{workout_id}/executions/summary",
                      headers=auth_header(ath_token)).json()
    assert data["forecast"]["amostra"] == 0
    assert data["forecast"]["volume"] == 0.0


def test_summary_limit_is_respected():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_l@test.com", "ath_f10_l@test.com")
    coach_token = login(email="coach_f10_l@test.com").json()["access_token"]
    exercise_id = create_exercise_helper(coach_token, "Ex Lim").json()["id"]
    we_id = add_we_helper(coach_token, workout_id, exercise_id).json()["id"]
    for _ in range(4):
        eid = client.post(f"/api/workouts/{workout_id}/executions",
                          headers=auth_header(ath_token), json={}).json()["id"]
        _post_result(workout_id, eid, we_id, ath_token,
                     {"status": "done", "actual_sets": 3, "actual_repetitions": 10})
        client.put(f"/api/workouts/{workout_id}/executions/{eid}",
                   headers=auth_header(ath_token), json={"status": "completed"})
    data = client.get(f"/api/workouts/{workout_id}/executions/summary?limit=2",
                      headers=auth_header(ath_token)).json()
    assert len(data["executions"]) == 2


def test_coach_summary_requires_athlete_id():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_cs@test.com", "ath_f10_cs@test.com")
    coach_token = login(email="coach_f10_cs@test.com").json()["access_token"]
    resp = client.get(f"/api/workouts/{workout_id}/executions/summary",
                      headers=auth_header(coach_token))
    assert resp.status_code == 400, "treinador sem athlete_id deveria ser barrado"


def test_coach_summary_of_own_athlete():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_ca@test.com", "ath_f10_ca@test.com")
    coach_token = login(email="coach_f10_ca@test.com").json()["access_token"]
    eid = client.post(f"/api/workouts/{workout_id}/executions",
                      headers=auth_header(ath_token), json={}).json()["id"]
    client.put(f"/api/workouts/{workout_id}/executions/{eid}",
               headers=auth_header(ath_token), json={"status": "completed"})
    athlete_id = client.get("/api/athletes/me",
                            headers=auth_header(ath_token)).json()["id"]
    resp = client.get(
        f"/api/workouts/{workout_id}/executions/summary?athlete_id={athlete_id}",
        headers=auth_header(coach_token))
    assert resp.status_code == 200
    assert len(resp.json()["executions"]) == 1


def test_coach_summary_rejects_athlete_from_other_team():
    workout_id, ath_token = setup_execution_happy(
        "coach_f10_x@test.com", "ath_f10_x@test.com")
    # outro treinador com atleta proprio
    setup_execution_happy("coach_f10_y@test.com", "ath_f10_y@test.com")
    coach_x = login(email="coach_f10_x@test.com").json()["access_token"]
    other_athlete_id = client.get(
        "/api/athletes/me",
        headers=auth_header(login(email="ath_f10_y@test.com").json()["access_token"])
    ).json()["id"]
    resp = client.get(
        f"/api/workouts/{workout_id}/executions/summary?athlete_id={other_athlete_id}",
        headers=auth_header(coach_x))
    assert resp.status_code == 403


def test_performance_aggregate_exposes_execution_id():
    workout_id, execution_id, we_id, ath_token = _setup_done_execution("execid")
    client.put(f"/api/workouts/{workout_id}/executions/{execution_id}",
               headers=auth_header(ath_token), json={"status": "completed"})
    volumes = _perf_records(ath_token, "volume")
    assert volumes[0]["execution_id"] == execution_id
