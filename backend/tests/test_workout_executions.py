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
