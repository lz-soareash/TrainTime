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


def register_coach(name="Treinador Teste", email="treinador@test.com", password="123456", sport_ids=None):
    if sport_ids is None:
        sport_ids = [1, 2]
    return client.post("/api/auth/register/coach", json={
        "name": name, "email": email, "password": password,
        "sport_ids": sport_ids,
    })


def register_athlete(name="Atleta Teste", email="atleta@test.com", password="123456", sport_id=1, position_id=1):
    return client.post("/api/auth/register/athlete", json={
        "name": name, "email": email, "password": password,
        "sport_id": sport_id, "position_id": position_id,
    })


def login(email="treinador@test.com", password="123456"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def create_exercise_helper(token, name="Exercicio Teste", sport_id=1, exercise_type="repetitions"):
    return client.post("/api/exercises", headers=auth_header(token), json={
        "name": name,
        "sport_id": sport_id,
        "exercise_type": exercise_type,
    })


def create_team_helper(coach_email, name="Equipe Teste", sport_id=1):
    login_resp = login(email=coach_email)
    token = login_resp.json()["access_token"]
    return client.post("/api/teams", headers=auth_header(token), json={
        "name": name, "sport_id": sport_id,
    }), token


def create_workout_helper(token, team_id, title="Treino Teste"):
    return client.post("/api/workouts", headers=auth_header(token), json={
        "team_id": team_id,
        "title": title,
        "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
    })


# ========== EXERCISE CREATION ==========

def test_coach_creates_exercise():
    register_coach(email="coach_ex1@test.com")
    login_resp = login(email="coach_ex1@test.com")
    token = login_resp.json()["access_token"]
    resp = create_exercise_helper(token, "Agachamento")
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Agachamento"
    assert data["exercise_type"] == "repetitions"
    assert data["sport_id"] == 1
    assert "created_by" in data


def test_athlete_cannot_create_exercise():
    register_athlete(email="ath_ex1@test.com")
    login_resp = login(email="ath_ex1@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/exercises", headers=auth_header(token), json={
        "name": "Flexao", "sport_id": 1, "exercise_type": "repetitions",
    })
    assert resp.status_code == 403


def test_create_exercise_invalid_name():
    register_coach(email="coach_ex2@test.com")
    login_resp = login(email="coach_ex2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/exercises", headers=auth_header(token), json={
        "name": "", "sport_id": 1, "exercise_type": "repetitions",
    })
    assert resp.status_code == 422


def test_create_exercise_invalid_type():
    register_coach(email="coach_ex3@test.com")
    login_resp = login(email="coach_ex3@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/exercises", headers=auth_header(token), json={
        "name": "Teste", "sport_id": 1, "exercise_type": "invalido",
    })
    assert resp.status_code == 422


# ========== EXERCISE LISTING ==========

def test_coach_sees_own_exercises():
    register_coach(email="coach_ex_list@test.com")
    login_resp = login(email="coach_ex_list@test.com")
    token = login_resp.json()["access_token"]
    create_exercise_helper(token, "Exercicio A")
    create_exercise_helper(token, "Exercicio B")
    resp = client.get("/api/exercises", headers=auth_header(token))
    assert resp.status_code == 200
    exercises = resp.json()
    names = [e["name"] for e in exercises]
    assert "Exercicio A" in names
    assert "Exercicio B" in names


def test_exercises_filter_by_sport():
    register_coach(email="coach_ex_filt@test.com")
    login_resp = login(email="coach_ex_filt@test.com")
    token = login_resp.json()["access_token"]
    create_exercise_helper(token, "Volei Ex", sport_id=1)
    create_exercise_helper(token, "Basquete Ex", sport_id=2)
    resp = client.get("/api/exercises?sport_id=1", headers=auth_header(token))
    exercises = resp.json()
    assert all(e["sport_id"] == 1 for e in exercises)


def test_exercises_filter_by_type():
    register_coach(email="coach_ex_filt2@test.com")
    login_resp = login(email="coach_ex_filt2@test.com")
    token = login_resp.json()["access_token"]
    create_exercise_helper(token, "Rep Ex", exercise_type="repetitions")
    create_exercise_helper(token, "Dur Ex", exercise_type="duration")
    resp = client.get("/api/exercises?exercise_type=duration", headers=auth_header(token))
    exercises = resp.json()
    assert all(e["exercise_type"] == "duration" for e in exercises)


# ========== EXERCISE VIEW ==========

def test_view_exercise():
    register_coach(email="coach_ex_view@test.com")
    login_resp = login(email="coach_ex_view@test.com")
    token = login_resp.json()["access_token"]
    create_resp = create_exercise_helper(token, "Visivel")
    exercise_id = create_resp.json()["id"]
    resp = client.get(f"/api/exercises/{exercise_id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Visivel"


def test_view_nonexistent_exercise():
    register_coach(email="coach_ex_view2@test.com")
    login_resp = login(email="coach_ex_view2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/exercises/999", headers=auth_header(token))
    assert resp.status_code == 404


# ========== EXERCISE UPDATE ==========

def test_coach_updates_own_exercise():
    register_coach(email="coach_ex_upd@test.com")
    login_resp = login(email="coach_ex_upd@test.com")
    token = login_resp.json()["access_token"]
    create_resp = create_exercise_helper(token, "Antigo")
    exercise_id = create_resp.json()["id"]
    resp = client.put(f"/api/exercises/{exercise_id}", headers=auth_header(token), json={
        "name": "Novo Nome",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Novo Nome"


def test_coach_cannot_update_other_exercise():
    register_coach(email="coach_ex_u_a@test.com")
    register_coach(email="coach_ex_u_b@test.com")
    login_resp = login(email="coach_ex_u_b@test.com")
    token_b = login_resp.json()["access_token"]
    create_resp = create_exercise_helper(token_b, "Privado")
    exercise_id = create_resp.json()["id"]
    login_resp = login(email="coach_ex_u_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.put(f"/api/exercises/{exercise_id}", headers=auth_header(token_a), json={
        "name": "Hacker",
    })
    assert resp.status_code == 403


def test_update_nonexistent_exercise():
    register_coach(email="coach_ex_upd2@test.com")
    login_resp = login(email="coach_ex_upd2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/exercises/999", headers=auth_header(token), json={
        "name": "X",
    })
    assert resp.status_code == 404


# ========== EXERCISE DELETE ==========

def test_coach_deletes_own_exercise():
    register_coach(email="coach_ex_del@test.com")
    login_resp = login(email="coach_ex_del@test.com")
    token = login_resp.json()["access_token"]
    create_resp = create_exercise_helper(token, "Para Deletar")
    exercise_id = create_resp.json()["id"]
    resp = client.delete(f"/api/exercises/{exercise_id}", headers=auth_header(token))
    assert resp.status_code == 204


def test_coach_cannot_delete_other_exercise():
    register_coach(email="coach_ex_d_a@test.com")
    register_coach(email="coach_ex_d_b@test.com")
    login_resp = login(email="coach_ex_d_b@test.com")
    token_b = login_resp.json()["access_token"]
    create_resp = create_exercise_helper(token_b, "Privado")
    exercise_id = create_resp.json()["id"]
    login_resp = login(email="coach_ex_d_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.delete(f"/api/exercises/{exercise_id}", headers=auth_header(token_a))
    assert resp.status_code == 403


def test_athlete_cannot_delete_exercise():
    register_coach(email="coach_ex_d2@test.com")
    register_athlete(email="ath_ex_del@test.com")
    login_resp = login(email="coach_ex_d2@test.com")
    token = login_resp.json()["access_token"]
    create_resp = create_exercise_helper(token, "Protegido")
    exercise_id = create_resp.json()["id"]
    login_resp = login(email="ath_ex_del@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.delete(f"/api/exercises/{exercise_id}", headers=auth_header(ath_token))
    assert resp.status_code == 403


def test_delete_nonexistent_exercise():
    register_coach(email="coach_ex_del2@test.com")
    login_resp = login(email="coach_ex_del2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.delete("/api/exercises/999", headers=auth_header(token))
    assert resp.status_code == 404


# ========== EXERCISE DELETION BLOCKED BY WORKOUT USAGE ==========

def test_delete_exercise_blocked_when_used_in_workout():
    register_coach(email="coach_ex_block@test.com")
    login_resp = login(email="coach_ex_block@test.com")
    token = login_resp.json()["access_token"]
    create_resp = create_exercise_helper(token, "Em Uso")
    exercise_id = create_resp.json()["id"]
    create_resp, _ = create_team_helper("coach_ex_block@test.com")
    team_id = create_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    client.post(f"/api/workouts/{workout_id}/exercises", headers=auth_header(token), json={
        "exercise_id": exercise_id, "order": 1,
    })
    resp = client.delete(f"/api/exercises/{exercise_id}", headers=auth_header(token))
    assert resp.status_code == 409


# ========== UNAUTHENTICATED ==========

def test_exercise_endpoint_no_token():
    resp = client.get("/api/exercises")
    assert resp.status_code == 401

    resp = client.post("/api/exercises", json={
        "name": "X", "sport_id": 1, "exercise_type": "repetitions",
    })
    assert resp.status_code == 401
