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
        "name": name, "sport_id": sport_id, "exercise_type": exercise_type,
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


def add_we_helper(token, workout_id, exercise_id, order=1, **kwargs):
    data = {"exercise_id": exercise_id, "order": order, **kwargs}
    return client.post(f"/api/workouts/{workout_id}/exercises", headers=auth_header(token), json=data)


# ========== ADD EXERCISE TO WORKOUT ==========

def test_coach_adds_exercise_to_workout():
    register_coach(email="coach_we1@test.com")
    login_resp = login(email="coach_we1@test.com")
    token = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(token, "Agachamento")
    exercise_id = exercise_resp.json()["id"]
    team_resp, _ = create_team_helper("coach_we1@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = add_we_helper(token, workout_id, exercise_id, order=1, sets=3, repetitions=12)
    assert resp.status_code == 201
    data = resp.json()
    assert data["order"] == 1
    assert data["sets"] == 3
    assert data["repetitions"] == 12
    assert data["exercise"]["name"] == "Agachamento"


def test_coach_adds_duration_exercise():
    register_coach(email="coach_we2@test.com")
    login_resp = login(email="coach_we2@test.com")
    token = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(token, "Corrida", exercise_type="duration")
    exercise_id = exercise_resp.json()["id"]
    team_resp, _ = create_team_helper("coach_we2@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = add_we_helper(token, workout_id, exercise_id, order=1, duration_seconds=600, rest_seconds=60)
    assert resp.status_code == 201
    data = resp.json()
    assert data["duration_seconds"] == 600
    assert data["rest_seconds"] == 60


def test_coach_adds_mixed_exercise():
    register_coach(email="coach_we3@test.com")
    login_resp = login(email="coach_we3@test.com")
    token = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(token, "Circuito", exercise_type="mixed")
    exercise_id = exercise_resp.json()["id"]
    team_resp, _ = create_team_helper("coach_we3@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = add_we_helper(token, workout_id, exercise_id, order=1, sets=4, repetitions=10, duration_seconds=300)
    assert resp.status_code == 201


def test_athlete_cannot_add_exercise_to_workout():
    register_coach(email="coach_we4@test.com")
    register_athlete(email="ath_we1@test.com")
    login_resp = login(email="coach_we4@test.com")
    token = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(token, "Protegido")
    exercise_id = exercise_resp.json()["id"]
    team_resp, _ = create_team_helper("coach_we4@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    login_resp = login(email="ath_we1@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = add_we_helper(ath_token, workout_id, exercise_id)
    assert resp.status_code == 403


def test_add_exercise_wrong_sport():
    register_coach(email="coach_we5@test.com")
    login_resp = login(email="coach_we5@test.com")
    token = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(token, "Basquete Ex", sport_id=2)
    exercise_id = exercise_resp.json()["id"]
    team_resp, _ = create_team_helper("coach_we5@test.com", "Equipe Volei", sport_id=1)
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = add_we_helper(token, workout_id, exercise_id)
    assert resp.status_code == 400


def test_add_exercise_workout_not_owned():
    register_coach(email="coach_we_a@test.com")
    register_coach(email="coach_we_b@test.com")
    login_resp = login(email="coach_we_a@test.com")
    token_a = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(token_a, "Ex A")
    exercise_id = exercise_resp.json()["id"]
    login_resp = login(email="coach_we_b@test.com")
    token_b = login_resp.json()["access_token"]
    team_resp, _ = create_team_helper("coach_we_b@test.com", "Equipe B")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token_b, team_id)
    workout_id = workout_resp.json()["id"]
    resp = add_we_helper(token_a, workout_id, exercise_id)
    assert resp.status_code == 403


def test_add_exercise_invalid_workout():
    register_coach(email="coach_we6@test.com")
    login_resp = login(email="coach_we6@test.com")
    token = login_resp.json()["access_token"]
    exercise_resp = create_exercise_helper(token, "Ex")
    exercise_id = exercise_resp.json()["id"]
    resp = add_we_helper(token, 999, exercise_id)
    assert resp.status_code == 404


def test_add_exercise_invalid_exercise():
    register_coach(email="coach_we7@test.com")
    login_resp = login(email="coach_we7@test.com")
    token = login_resp.json()["access_token"]
    team_resp, _ = create_team_helper("coach_we7@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = add_we_helper(token, workout_id, 999)
    assert resp.status_code == 404


# ========== LIST WORKOUT EXERCISES ==========

def test_coach_sees_exercises_ordered_by_order():
    register_coach(email="coach_we_list@test.com")
    login_resp = login(email="coach_we_list@test.com")
    token = login_resp.json()["access_token"]
    ex_a = create_exercise_helper(token, "Ex A").json()["id"]
    ex_b = create_exercise_helper(token, "Ex B").json()["id"]
    team_resp, _ = create_team_helper("coach_we_list@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    add_we_helper(token, workout_id, ex_b, order=2)
    add_we_helper(token, workout_id, ex_a, order=1)
    resp = client.get(f"/api/workouts/{workout_id}/exercises", headers=auth_header(token))
    assert resp.status_code == 200
    wes = resp.json()
    assert len(wes) == 2
    assert wes[0]["order"] == 1
    assert wes[1]["order"] == 2


def test_athlete_sees_workout_exercises():
    register_coach(email="coach_we_l2@test.com")
    register_athlete(email="ath_we_list@test.com")
    login_resp = login(email="coach_we_l2@test.com")
    token = login_resp.json()["access_token"]
    ex = create_exercise_helper(token, "Ex List").json()["id"]
    team_resp, _ = create_team_helper("coach_we_l2@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    add_we_helper(token, workout_id, ex)
    login_resp = login(email="ath_we_list@test.com")
    ath_token = login_resp.json()["access_token"]
    ath_profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = ath_profile["id"]
    login_resp = login(email="coach_we_l2@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/{ath_id}", headers=auth_header(token))
    resp = client.get(f"/api/workouts/{workout_id}/exercises", headers=auth_header(ath_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_athlete_cannot_see_exercises_not_in_team():
    register_coach(email="coach_we_l3@test.com")
    register_athlete(email="ath_we_l2@test.com")
    login_resp = login(email="coach_we_l3@test.com")
    token = login_resp.json()["access_token"]
    ex = create_exercise_helper(token, "Privado").json()["id"]
    team_resp, _ = create_team_helper("coach_we_l3@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    add_we_helper(token, workout_id, ex)
    login_resp = login(email="ath_we_l2@test.com")
    ath_token = login_resp.json()["access_token"]
    resp = client.get(f"/api/workouts/{workout_id}/exercises", headers=auth_header(ath_token))
    assert resp.status_code == 403


def test_list_exercises_invalid_workout():
    register_coach(email="coach_we_l4@test.com")
    login_resp = login(email="coach_we_l4@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/workouts/999/exercises", headers=auth_header(token))
    assert resp.status_code == 404


# ========== UPDATE WORKOUT EXERCISE ==========

def test_coach_updates_workout_exercise():
    register_coach(email="coach_we_upd@test.com")
    login_resp = login(email="coach_we_upd@test.com")
    token = login_resp.json()["access_token"]
    ex = create_exercise_helper(token, "Upd Ex").json()["id"]
    team_resp, _ = create_team_helper("coach_we_upd@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    we_resp = add_we_helper(token, workout_id, ex, order=1, sets=3)
    we_id = we_resp.json()["id"]
    resp = client.put(f"/api/workouts/{workout_id}/exercises/{we_id}", headers=auth_header(token), json={
        "order": 2, "sets": 5, "repetitions": 15,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["order"] == 2
    assert data["sets"] == 5
    assert data["repetitions"] == 15


def test_coach_cannot_update_other_workout_exercise():
    register_coach(email="coach_we_u_a@test.com")
    register_coach(email="coach_we_u_b@test.com")
    login_resp = login(email="coach_we_u_b@test.com")
    token_b = login_resp.json()["access_token"]
    ex = create_exercise_helper(token_b, "Privado Upd").json()["id"]
    team_resp, _ = create_team_helper("coach_we_u_b@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token_b, team_id)
    workout_id = workout_resp.json()["id"]
    we_resp = add_we_helper(token_b, workout_id, ex)
    we_id = we_resp.json()["id"]
    login_resp = login(email="coach_we_u_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.put(f"/api/workouts/{workout_id}/exercises/{we_id}", headers=auth_header(token_a), json={
        "order": 99,
    })
    assert resp.status_code == 403


def test_update_nonexistent_workout_exercise():
    register_coach(email="coach_we_upd2@test.com")
    login_resp = login(email="coach_we_upd2@test.com")
    token = login_resp.json()["access_token"]
    team_resp, _ = create_team_helper("coach_we_upd2@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = client.put(f"/api/workouts/{workout_id}/exercises/999", headers=auth_header(token), json={
        "order": 1,
    })
    assert resp.status_code == 404


# ========== DELETE WORKOUT EXERCISE ==========

def test_coach_deletes_workout_exercise():
    register_coach(email="coach_we_del@test.com")
    login_resp = login(email="coach_we_del@test.com")
    token = login_resp.json()["access_token"]
    ex = create_exercise_helper(token, "Del Ex").json()["id"]
    team_resp, _ = create_team_helper("coach_we_del@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    we_resp = add_we_helper(token, workout_id, ex)
    we_id = we_resp.json()["id"]
    resp = client.delete(f"/api/workouts/{workout_id}/exercises/{we_id}", headers=auth_header(token))
    assert resp.status_code == 204
    list_resp = client.get(f"/api/workouts/{workout_id}/exercises", headers=auth_header(token))
    assert len(list_resp.json()) == 0


def test_coach_cannot_delete_other_workout_exercise():
    register_coach(email="coach_we_d_a@test.com")
    register_coach(email="coach_we_d_b@test.com")
    login_resp = login(email="coach_we_d_b@test.com")
    token_b = login_resp.json()["access_token"]
    ex = create_exercise_helper(token_b, "Privado Del").json()["id"]
    team_resp, _ = create_team_helper("coach_we_d_b@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token_b, team_id)
    workout_id = workout_resp.json()["id"]
    we_resp = add_we_helper(token_b, workout_id, ex)
    we_id = we_resp.json()["id"]
    login_resp = login(email="coach_we_d_a@test.com")
    token_a = login_resp.json()["access_token"]
    resp = client.delete(f"/api/workouts/{workout_id}/exercises/{we_id}", headers=auth_header(token_a))
    assert resp.status_code == 403


def test_delete_nonexistent_workout_exercise():
    register_coach(email="coach_we_del2@test.com")
    login_resp = login(email="coach_we_del2@test.com")
    token = login_resp.json()["access_token"]
    team_resp, _ = create_team_helper("coach_we_del2@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = client.delete(f"/api/workouts/{workout_id}/exercises/999", headers=auth_header(token))
    assert resp.status_code == 404


# ========== SAME EXERCISE MULTIPLE TIMES ==========

def test_same_exercise_added_multiple_times():
    register_coach(email="coach_we_multi@test.com")
    login_resp = login(email="coach_we_multi@test.com")
    token = login_resp.json()["access_token"]
    ex = create_exercise_helper(token, "Multi Ex").json()["id"]
    team_resp, _ = create_team_helper("coach_we_multi@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp1 = add_we_helper(token, workout_id, ex, order=1, sets=3)
    resp2 = add_we_helper(token, workout_id, ex, order=2, sets=5)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    list_resp = client.get(f"/api/workouts/{workout_id}/exercises", headers=auth_header(token))
    assert len(list_resp.json()) == 2


# ========== NOTES AND OPTIONAL FIELDS ==========

def test_add_exercise_with_all_optional_fields():
    register_coach(email="coach_we_opt@test.com")
    login_resp = login(email="coach_we_opt@test.com")
    token = login_resp.json()["access_token"]
    ex = create_exercise_helper(token, "Opt Ex").json()["id"]
    team_resp, _ = create_team_helper("coach_we_opt@test.com")
    team_id = team_resp.json()["id"]
    workout_resp = create_workout_helper(token, team_id)
    workout_id = workout_resp.json()["id"]
    resp = add_we_helper(token, workout_id, ex, order=1, sets=4, repetitions=10,
                         duration_seconds=300, distance_meters=100, rest_seconds=60,
                         notes="Foco na tecnica")
    assert resp.status_code == 201
    data = resp.json()
    assert data["sets"] == 4
    assert data["repetitions"] == 10
    assert data["duration_seconds"] == 300
    assert data["distance_meters"] == 100
    assert data["rest_seconds"] == 60
    assert data["notes"] == "Foco na tecnica"


# ========== UNAUTHENTICATED ==========

def test_workout_exercise_endpoint_no_token():
    resp = client.get("/api/workouts/1/exercises")
    assert resp.status_code == 401

    resp = client.post("/api/workouts/1/exercises", json={
        "exercise_id": 1, "order": 1,
    })
    assert resp.status_code == 401
