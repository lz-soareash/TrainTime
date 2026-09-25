import sys
import os

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


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def login(email, password="123456"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def register_athlete(email, name="Atleta Goal"):
    resp = client.post("/api/auth/register/athlete", json={
        "name": name, "email": email, "password": "123456",
        "sport_id": 1, "position_id": 1,
    })
    assert resp.status_code == 201
    login_resp = client.post("/api/auth/login", json={"email": email, "password": "123456"})
    assert login_resp.status_code == 200
    return login_resp.json()["access_token"]


def register_coach(email, name="Coach Goal"):
    resp = client.post("/api/auth/register/coach", json={
        "name": name, "email": email, "password": "123456",
        "sport_ids": [1],
    })
    assert resp.status_code == 201
    login_resp = client.post("/api/auth/login", json={"email": email, "password": "123456"})
    assert login_resp.status_code == 200
    return login_resp.json()["access_token"]


def resolve_athlete_id(token):
    resp = client.get("/api/athletes/me", headers=auth_header(token))
    assert resp.status_code == 200
    return resp.json()["id"]


def create_goal(token, athlete_id=None, title="Melhorar recepcao",
                metric="recepcao", target_value=85, current_value=72,
                deadline="2026-11-30T00:00:00", **extra):
    body = {
        "title": title, "metric": metric,
        "target_value": target_value, "current_value": current_value,
        "unit": "pts", "deadline": deadline,
    }
    if athlete_id is not None:
        body["athlete_id"] = athlete_id
    body.update(extra)
    return client.post("/api/goals", headers=auth_header(token), json=body)


def register_coach_team_with_athlete(ath_token, coach_token):
    coach_id = client.get("/api/coaches/me", headers=auth_header(coach_token)).json()["id"]
    team_resp = client.post("/api/teams", headers=auth_header(coach_token), json={
        "name": "Equipe Goal", "sport_id": 1,
    })
    assert team_resp.status_code == 201
    team_id = team_resp.json()["id"]
    athlete_id = resolve_athlete_id(ath_token)
    add_resp = client.post(
        f"/api/teams/{team_id}/athletes/{athlete_id}",
        headers=auth_header(coach_token),
    )
    assert add_resp.status_code == 200
    return team_id, athlete_id, coach_id


def test_athlete_creates_own_goal():
    ath_token = register_athlete("ath_goal@test.com")
    resp = create_goal(ath_token)
    assert resp.status_code == 201
    data = resp.json()
    assert data["athlete_id"] == resolve_athlete_id(ath_token)
    assert data["title"] == "Melhorar recepcao"
    assert data["status"] == "active"


def test_athlete_lists_own_goals():
    ath_token = register_athlete("ath_goal_list@test.com")
    create_goal(ath_token)
    resp = client.get("/api/goals", headers=auth_header(ath_token))
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) >= 1
    assert all(g["athlete_id"] == resolve_athlete_id(ath_token) for g in records)


def test_athlete_cannot_create_goal_for_other_athlete():
    other_athlete = register_athlete("ath_goal_other@test.com")
    other_id = resolve_athlete_id(other_athlete)
    coach_token = register_coach("coach_goal_forbid@test.com")
    create_goal(coach_token, athlete_id=other_id)
    resp = client.post("/api/goals", headers=auth_header(other_athlete), json={
        "title": "Meta alheia", "metric": "recepcao",
        "target_value": 10, "current_value": 0, "deadline": "2026-12-31T00:00:00",
        "athlete_id": other_id + 1,
    })
    assert resp.status_code in (403, 409, 422)


def test_athlete_cannot_access_other_goal():
    ath_b = register_athlete("ath_goal_b@test.com")
    create_goal(ath_b)
    goal_id = client.get("/api/goals", headers=auth_header(ath_b)).json()[0]["id"]

    ath_a = register_athlete("ath_goal_a@test.com")
    resp = client.get(f"/api/goals/{goal_id}", headers=auth_header(ath_a))
    assert resp.status_code in (403, 404)
    resp = client.delete(f"/api/goals/{goal_id}", headers=auth_header(ath_a))
    assert resp.status_code in (403, 404)


def test_goal_progress_percentage_examples():
    ath_token = register_athlete("ath_goal_prog@test.com")

    g = create_goal(ath_token, target_value=100, current_value=0).json()
    assert g["progress_percentage"] == 0

    g = create_goal(ath_token, target_value=100, current_value=50).json()
    assert g["progress_percentage"] == 50

    g = create_goal(ath_token, target_value=100, current_value=100).json()
    assert g["progress_percentage"] == 100

    g = create_goal(ath_token, target_value=100, current_value=150).json()
    assert g["progress_percentage"] == 100


def test_goal_auto_complete_marks_completed():
    ath_token = register_athlete("ath_goal_done@test.com")
    resp = create_goal(ath_token, target_value=80, current_value=80)
    assert resp.status_code == 201
    data = resp.json()
    assert data["progress_percentage"] == 100
    assert data["status"] == "completed"


def test_athlete_updates_own_progress():
    ath_token = register_athlete("ath_goal_upd@test.com")
    gid = create_goal(ath_token, current_value=10).json()["id"]
    resp = client.put(f"/api/goals/{gid}", headers=auth_header(ath_token), json={
        "current_value": 85,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_value"] == 85
    assert data["progress_percentage"] == 100
    assert data["status"] == "completed"


def test_goal_cancel_sets_cancelled_status():
    ath_token = register_athlete("ath_goal_cancel@test.com")
    gid = create_goal(ath_token).json()["id"]
    resp = client.delete(f"/api/goals/{gid}", headers=auth_header(ath_token))
    assert resp.status_code in (200, 204, 202)
    if resp.status_code == 200:
        assert resp.json()["status"] in ("cancelled", "cancelled")


def test_coach_creates_goal_for_team_athlete():
    ath_token = register_athlete("ath_goal_team@test.com")
    coach_token = register_coach("coach_goal_team@test.com")
    _, athlete_id, _ = register_coach_team_with_athlete(ath_token, coach_token)
    resp = create_goal(coach_token, athlete_id=athlete_id, title="Meta do coach")
    assert resp.status_code == 201
    assert resp.json()["athlete_id"] == athlete_id


def test_coach_cannot_create_goal_for_outside_athlete():
    outside_token = register_athlete("ath_goal_out@test.com")
    outside_id = resolve_athlete_id(outside_token)
    coach_token = register_coach("coach_goal_out@test.com")
    resp = create_goal(coach_token, athlete_id=outside_id)
    assert resp.status_code in (403, 404, 409, 422)


def test_coach_lists_team_goals_aggregate():
    ath_token = register_athlete("ath_goal_coach@test.com")
    coach_token = register_coach("coach_goal_coach@test.com")
    register_coach_team_with_athlete(ath_token, coach_token)
    create_goal(ath_token)

    resp = client.get("/api/goals", headers=auth_header(coach_token))
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) >= 1
    for r in records:
        assert "athlete_id" in r


def test_validation_negative_target_rejected():
    ath_token = register_athlete("ath_goal_neg@test.com")
    resp = create_goal(ath_token, target_value=-10)
    assert resp.status_code in (400, 422)


def test_validation_empty_title_rejected():
    ath_token = register_athlete("ath_goal_vtitle@test.com")
    resp = create_goal(ath_token, title="")
    assert resp.status_code in (400, 422)
