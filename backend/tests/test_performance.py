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


def register_coach(email="coach_perf@test.com", password="123456"):
    return client.post("/api/auth/register/coach", json={
        "name": "Treinador Perf", "email": email, "password": password,
        "sport_ids": [1, 2],
    })


def register_athlete(email="ath_perf@test.com", password="123456",
                     sport_id=1, position_id=1):
    return client.post("/api/auth/register/athlete", json={
        "name": "Atleta Perf", "email": email, "password": password,
        "sport_id": sport_id, "position_id": position_id,
    })


def login(email="treinador@test.com", password="123456"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def create_team_helper(coach_email, name="Equipe Perf", sport_id=1):
    login_resp = login(email=coach_email)
    token = login_resp.json()["access_token"]
    return client.post("/api/teams", headers=auth_header(token), json={
        "name": name, "sport_id": sport_id,
    }), token


def create_workout_helper(token, team_id, title="Treino Perf"):
    return client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": team_id, "title": title,
        "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
    })


def setup_perf_happy(coach_email, ath_email):
    register_coach(email=coach_email)
    register_athlete(email=ath_email)
    team_resp, token = create_team_helper(coach_email)
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    login_resp = login(email=ath_email)
    ath_token = login_resp.json()["access_token"]
    profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = profile["id"]
    client.post(f"/api/teams/{team_id}/athletes/{ath_id}", headers=auth_header(token))
    return workout_id, ath_token


# ========== RECORD PERFORMANCE ==========

def test_athlete_records_performance():
    workout_id, ath_token = setup_perf_happy("coach_prf@test.com",
                                             "ath_prf@test.com")
    resp = client.post("/api/performance", headers=auth_header(ath_token), json={
        "athlete_id": 1000, "metric": "velocidade", "value": 12.5,
    })
    # athlete_id no body deve ser ignorado: a rota usa o ath_logado
    assert resp.status_code == 201
    data = resp.json()
    assert data["metric"] == "velocidade"
    assert data["value"] == 12.5


def test_athlete_records_performance_with_execution():
    workout_id, ath_token = setup_perf_happy("coach_prf_ex@test.com",
                                             "ath_prf_ex@test.com")
    start_resp = client.post(f"/api/workouts/{workout_id}/executions",
                             headers=auth_header(ath_token), json={})
    execution_id = start_resp.json()["id"]
    resp = client.post("/api/performance", headers=auth_header(ath_token), json={
        "execution_id": execution_id, "metric": "distancia", "value": 5.0,
    })
    assert resp.status_code == 201
    assert resp.json()["execution_id"] == execution_id


def test_coach_cannot_record_performance():
    register_coach(email="coach_prf_co@test.com")
    register_athlete(email="ath_prf_co@test.com")
    login_resp = login(email="coach_prf_co@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/performance", headers=auth_header(token), json={
        "metric": "velocidade", "value": 1.0,
    })
    assert resp.status_code == 403


def test_performance_endpoint_requires_token():
    resp = client.post("/api/performance", json={
        "metric": "velocidade", "value": 1.0,
    })
    assert resp.status_code == 401


def test_performance_invalid_metric():
    register_coach(email="coach_prf_im@test.com")
    register_athlete(email="ath_prf_im@test.com")
    login_resp = login(email="ath_prf_im@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.post("/api/performance", headers=auth_header(ath_token),
                       json={"metric": "", "value": 1.0})
    assert resp.status_code == 422


# ========== LIST RECORDS ==========

def test_athlete_lists_own_records():
    register_coach(email="coach_prf_ls@test.com")
    register_athlete(email="ath_prf_ls@test.com")
    login_resp = login(email="ath_prf_ls@test.com")
    ath_token = login_resp.json()["access_token"]
    client.post("/api/performance", headers=auth_header(ath_token), json={
        "metric": "velocidade", "value": 9.0,
    })
    resp = client.get("/api/performance/records", headers=auth_header(ath_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_coach_lists_team_aggregate():
    workout_id, ath_token = setup_perf_happy("coach_prf_ag@test.com",
                                             "ath_prf_ag@test.com")
    client.post("/api/performance", headers=auth_header(ath_token), json={
        "metric": "velocidade", "value": 7.0,
    })
    login_resp = login(email="coach_prf_ag@test.com")
    coach_token = login_resp.json()["access_token"]
    resp = client.get("/api/performance", headers=auth_header(coach_token))
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) >= 1
    assert all("athlete_name" in r for r in records)


def test_athlete_cannot_list_coach_aggregate():
    register_coach(email="coach_prf_na@test.com")
    register_athlete(email="ath_prf_na@test.com")
    login_resp = login(email="ath_prf_na@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.get("/api/performance", headers=auth_header(ath_token))
    # atleta nao ve agregado por treinador diretamente
    assert resp.status_code == 200
    assert all(r.get("athlete_name") for r in resp.json())
