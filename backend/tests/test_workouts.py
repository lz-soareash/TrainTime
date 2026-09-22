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


def register_athlete(name="Atleta Teste", email="atleta@test.com", password="123456", sport_id=1, position_id=3):
    return client.post("/api/auth/register/athlete", json={
        "name": name, "email": email, "password": password,
        "sport_id": sport_id, "position_id": position_id,
    })


def register_coach(name="Treinador Teste", email="treinador@test.com", password="123456", sport_ids=None):
    if sport_ids is None:
        sport_ids = [1, 2]
    return client.post("/api/auth/register/coach", json={
        "name": name, "email": email, "password": password,
        "sport_ids": sport_ids,
    })


def login(email="atleta@test.com", password="123456"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def create_team_helper(coach_email, name="Equipe Teste", sport_id=1):
    login_resp = login(email=coach_email)
    token = login_resp.json()["access_token"]
    return client.post("/api/teams", headers=auth_header(token), json={
        "name": name, "sport_id": sport_id,
    }), token


def create_workout_helper(token, team_id, title="Treino Teste", scheduled_at=None):
    if scheduled_at is None:
        scheduled_at = (datetime.now() + timedelta(days=1)).isoformat()
    return client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": team_id,
        "title": title,
        "description": "Treino de teste",
        "scheduled_at": scheduled_at,
        "duration_minutes": 90,
    })


# ========== WORKOUT CREATION ==========

def test_coach_creates_workout():
    register_coach(email="coach_wk1@test.com")
    create_resp, token = create_team_helper("coach_wk1@test.com")
    team_id = create_resp.json()["id"]
    resp = create_workout_helper(token, team_id)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Treino Teste"
    assert data["status"] == "scheduled"
    assert data["team"]["id"] == team_id


def test_athlete_cannot_create_workout():
    register_athlete(email="ath_wk@test.com")
    login_resp = login(email="ath_wk@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": 1, "title": "X", "scheduled_at": datetime.now().isoformat(),
    })
    assert resp.status_code == 403


def test_create_workout_invalid_team():
    register_coach(email="coach_wk2@test.com")
    login_resp = login(email="coach_wk2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": 999, "title": "X", "scheduled_at": datetime.now().isoformat(),
    })
    assert resp.status_code == 404


def test_create_workout_invalid_title():
    register_coach(email="coach_wk3@test.com")
    create_resp, token = create_team_helper("coach_wk3@test.com")
    team_id = create_resp.json()["id"]
    resp = client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": team_id, "title": "", "scheduled_at": datetime.now().isoformat(),
    })
    assert resp.status_code == 422


def test_create_workout_invalid_duration():
    register_coach(email="coach_wk4@test.com")
    create_resp, token = create_team_helper("coach_wk4@test.com")
    team_id = create_resp.json()["id"]
    resp = client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": team_id, "title": "X", "scheduled_at": datetime.now().isoformat(),
        "duration_minutes": -10,
    })
    assert resp.status_code == 422


def test_create_workout_no_permission():
    register_coach(email="coach_wk_a@test.com")
    register_coach(email="coach_wk_b@test.com")
    create_resp, token_b = create_team_helper("coach_wk_b@test.com", "Equipe B")
    team_id = create_resp.json()["id"]
    login_resp = login(email="coach_wk_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.post("/api/workouts", headers=auth_header(token_a), json={
        "team_id": team_id, "title": "X", "scheduled_at": datetime.now().isoformat(),
    })
    assert resp.status_code == 403


# ========== WORKOUT LISTING ==========

def test_coach_sees_own_workouts():
    register_coach(email="coach_wk_list@test.com")
    create_resp, token = create_team_helper("coach_wk_list@test.com")
    team_id = create_resp.json()["id"]
    create_workout_helper(token, team_id, "Treino A")
    create_workout_helper(token, team_id, "Treino B")
    resp = client.get("/api/workouts", headers=auth_header(token))
    assert resp.status_code == 200
    workouts = resp.json()
    assert len(workouts) >= 2
    titles = [w["title"] for w in workouts]
    assert "Treino A" in titles
    assert "Treino B" in titles


def test_coach_filters_by_team():
    register_coach(email="coach_wk_filt@test.com")
    create_resp_a, token = create_team_helper("coach_wk_filt@test.com", "Equipe A")
    team_a = create_resp_a.json()["id"]
    create_resp_b, _ = create_team_helper("coach_wk_filt@test.com", "Equipe B")
    team_b = create_resp_b.json()["id"]
    create_workout_helper(token, team_a, "Treino A")
    create_workout_helper(token, team_b, "Treino B")
    resp = client.get(f"/api/workouts?team_id={team_a}", headers=auth_header(token))
    workouts = resp.json()
    assert all(w["team_id"] == team_a for w in workouts)


def test_coach_filters_by_status():
    register_coach(email="coach_wk_filt2@test.com")
    create_resp, token = create_team_helper("coach_wk_filt2@test.com")
    team_id = create_resp.json()["id"]
    create_workout_helper(token, team_id, "Agendado")
    resp_list = client.get(f"/api/workouts?status=scheduled", headers=auth_header(token))
    workouts = resp_list.json()
    assert all(w["status"] == "scheduled" for w in workouts)


def test_athlete_sees_own_team_workouts():
    register_coach(email="coach_wk_ath@test.com")
    register_athlete(email="ath_wk_list@test.com", sport_id=1, position_id=1)
    create_resp, token = create_team_helper("coach_wk_ath@test.com")
    team_id = create_resp.json()["id"]

    login_resp = login(email="ath_wk_list@test.com")
    ath_token = login_resp.json()["access_token"]
    ath_profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = ath_profile["id"]

    login_resp = login(email="coach_wk_ath@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/{ath_id}", headers=auth_header(token))
    create_workout_helper(token, team_id, "Treino Athlete")

    resp = client.get("/api/workouts", headers=auth_header(ath_token))
    assert resp.status_code == 200
    workouts = resp.json()
    titles = [w["title"] for w in workouts]
    assert "Treino Athlete" in titles


# ========== WORKOUT VIEW ==========

def test_coach_views_own_workout():
    register_coach(email="coach_wk_view@test.com")
    create_resp, token = create_team_helper("coach_wk_view@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id, "Visualizar")
    workout_id = create_resp.json()["id"]
    resp = client.get(f"/api/workouts/{workout_id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Visualizar"


def test_coach_cannot_view_other_workout():
    register_coach(email="coach_wk_v_a@test.com")
    register_coach(email="coach_wk_v_b@test.com")
    create_resp, token_b = create_team_helper("coach_wk_v_b@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token_b, team_id, "Privado")
    workout_id = create_resp.json()["id"]
    login_resp = login(email="coach_wk_v_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.get(f"/api/workouts/{workout_id}", headers=auth_header(token_a))
    assert resp.status_code == 403


def test_athlete_views_workout_in_team():
    register_coach(email="coach_wk_v2@test.com")
    register_athlete(email="ath_wk_view@test.com", sport_id=1, position_id=1)
    create_resp, token = create_team_helper("coach_wk_v2@test.com")
    team_id = create_resp.json()["id"]

    login_resp = login(email="ath_wk_view@test.com")
    ath_token = login_resp.json()["access_token"]
    ath_profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = ath_profile["id"]

    login_resp = login(email="coach_wk_v2@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/{ath_id}", headers=auth_header(token))
    create_resp = create_workout_helper(token, team_id, "Atleta View")
    workout_id = create_resp.json()["id"]

    resp = client.get(f"/api/workouts/{workout_id}", headers=auth_header(ath_token))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Atleta View"


def test_athlete_cannot_view_workout_not_in_team():
    register_coach(email="coach_wk_v3@test.com")
    register_athlete(email="ath_wk_v2@test.com", sport_id=1, position_id=1)
    create_resp, token = create_team_helper("coach_wk_v3@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id, "Secreto")
    workout_id = create_resp.json()["id"]
    login_resp = login(email="ath_wk_v2@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.get(f"/api/workouts/{workout_id}", headers=auth_header(ath_token))
    assert resp.status_code == 403


# ========== WORKOUT UPDATE ==========

def test_coach_updates_workout():
    register_coach(email="coach_wk_upd@test.com")
    create_resp, token = create_team_helper("coach_wk_upd@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id, "Antigo")
    workout_id = create_resp.json()["id"]
    resp = client.put(f"/api/workouts/{workout_id}", headers=auth_header(token), json={
        "title": "Novo Titulo",
        "status": "completed",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Novo Titulo"
    assert data["status"] == "completed"


def test_coach_cannot_update_other_workout():
    register_coach(email="coach_wk_u_a@test.com")
    register_coach(email="coach_wk_u_b@test.com")
    create_resp, token_b = create_team_helper("coach_wk_u_b@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token_b, team_id)
    workout_id = create_resp.json()["id"]
    login_resp = login(email="coach_wk_u_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.put(f"/api/workouts/{workout_id}", headers=auth_header(token_a), json={
        "title": "Hacker",
    })
    assert resp.status_code == 403


def test_athlete_cannot_update_workout():
    register_coach(email="coach_wk_u2@test.com")
    register_athlete(email="ath_wk_upd@test.com")
    create_resp, token = create_team_helper("coach_wk_u2@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id)
    workout_id = create_resp.json()["id"]
    login_resp = login(email="ath_wk_upd@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.put(f"/api/workouts/{workout_id}", headers=auth_header(ath_token), json={
        "title": "Tentativa",
    })
    assert resp.status_code == 403


def test_update_workout_invalid_status():
    register_coach(email="coach_wk_u3@test.com")
    create_resp, token = create_team_helper("coach_wk_u3@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id)
    workout_id = create_resp.json()["id"]
    resp = client.put(f"/api/workouts/{workout_id}", headers=auth_header(token), json={
        "status": "invalido",
    })
    assert resp.status_code == 422


# ========== WORKOUT DELETE ==========

def test_coach_deletes_workout():
    register_coach(email="coach_wk_del@test.com")
    create_resp, token = create_team_helper("coach_wk_del@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id, "Para Deletar")
    workout_id = create_resp.json()["id"]
    resp = client.delete(f"/api/workouts/{workout_id}", headers=auth_header(token))
    assert resp.status_code == 204


def test_coach_cannot_delete_other_workout():
    register_coach(email="coach_wk_d_a@test.com")
    register_coach(email="coach_wk_d_b@test.com")
    create_resp, token_b = create_team_helper("coach_wk_d_b@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token_b, team_id)
    workout_id = create_resp.json()["id"]
    login_resp = login(email="coach_wk_d_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.delete(f"/api/workouts/{workout_id}", headers=auth_header(token_a))
    assert resp.status_code == 403


def test_athlete_cannot_delete_workout():
    register_coach(email="coach_wk_d2@test.com")
    register_athlete(email="ath_wk_del@test.com")
    create_resp, token = create_team_helper("coach_wk_d2@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id)
    workout_id = create_resp.json()["id"]
    login_resp = login(email="ath_wk_del@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.delete(f"/api/workouts/{workout_id}", headers=auth_header(ath_token))
    assert resp.status_code == 403


def test_delete_workout_does_not_delete_team():
    register_coach(email="coach_wk_del2@test.com")
    create_resp, token = create_team_helper("coach_wk_del2@test.com")
    team_id = create_resp.json()["id"]
    create_resp = create_workout_helper(token, team_id)
    workout_id = create_resp.json()["id"]
    client.delete(f"/api/workouts/{workout_id}", headers=auth_header(token))
    resp = client.get(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 200


# ========== WORKOUT ORDERING ==========

def test_workouts_ordered_by_scheduled_at():
    register_coach(email="coach_wk_ord@test.com")
    create_resp, token = create_team_helper("coach_wk_ord@test.com")
    team_id = create_resp.json()["id"]
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    next_week = (datetime.now() + timedelta(days=7)).isoformat()
    create_workout_helper(token, team_id, "Segundo", next_week)
    create_workout_helper(token, team_id, "Primeiro", tomorrow)
    resp = client.get("/api/workouts", headers=auth_header(token))
    workouts = resp.json()
    titles = [w["title"] for w in workouts]
    assert titles.index("Primeiro") < titles.index("Segundo")


# ========== UNAUTHENTICATED ==========

def test_workout_endpoint_no_token():
    resp = client.get("/api/workouts")
    assert resp.status_code == 401

    resp = client.post("/api/workouts", json={
        "team_id": 1, "title": "X", "scheduled_at": datetime.now().isoformat(),
    })
    assert resp.status_code == 401
