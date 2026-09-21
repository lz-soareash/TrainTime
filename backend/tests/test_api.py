import sys
import os
import time

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


# ========== HEALTH & SPORTS (Phase 1) ==========

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_sports():
    response = client.get("/api/sports")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ========== REGISTER ==========

def test_register_athlete():
    resp = register_athlete()
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "athlete"
    assert data["email"] == "atleta@test.com"
    assert "password_hash" not in data
    assert "password" not in data


def test_register_coach():
    resp = register_coach()
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "coach"
    assert data["email"] == "treinador@test.com"


def test_register_duplicate_email():
    resp = register_athlete(email="dup@test.com")
    assert resp.status_code == 201
    resp2 = register_athlete(email="dup@test.com")
    assert resp2.status_code == 400


def test_register_invalid_role():
    resp = client.post("/api/auth/register", json={
        "name": "Test", "email": "role@test.com", "password": "123456", "role": "admin"
    })
    assert resp.status_code == 422


def test_register_short_password():
    resp = register_athlete(password="123")
    assert resp.status_code == 422


def test_register_invalid_sport():
    resp = client.post("/api/auth/register/athlete", json={
        "name": "Test", "email": "sport@test.com", "password": "123456",
        "sport_id": 999, "position_id": 1,
    })
    assert resp.status_code == 400


def test_register_invalid_position_for_sport():
    resp = client.post("/api/auth/register/athlete", json={
        "name": "Test", "email": "pos@test.com", "password": "123456",
        "sport_id": 1, "position_id": 6,
    })
    assert resp.status_code == 400


def test_register_coach_invalid_sport():
    resp = client.post("/api/auth/register/coach", json={
        "name": "Test", "email": "csport@test.com", "password": "123456",
        "sport_ids": [999],
    })
    assert resp.status_code == 400


# ========== LOGIN ==========

def test_login_success():
    register_athlete(email="login@test.com")
    resp = login(email="login@test.com")
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password():
    register_athlete(email="wrongpw@test.com")
    resp = login(email="wrongpw@test.com", password="wrongpassword")
    assert resp.status_code == 401


def test_login_nonexistent_user():
    resp = login(email="noexist@test.com")
    assert resp.status_code == 401


def test_login_returns_token():
    register_athlete(email="token@test.com")
    resp = login(email="token@test.com")
    token = resp.json()["access_token"]
    assert len(token) > 20


# ========== AUTH /me ==========

def test_me_authenticated():
    register_athlete(email="me@test.com")
    login_resp = login(email="me@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@test.com"
    assert resp.json()["role"] == "athlete"
    assert "password_hash" not in resp.json()


def test_me_no_token():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token():
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken123"})
    assert resp.status_code == 401


def test_me_inactive_user():
    from app.models.models import User
    from app.core.security import hash_password
    db = TestingSessionLocal()
    user = User(email="inactive@test.com", name="Inactive", password_hash=hash_password("123456"), role="athlete", is_active=False)
    db.add(user)
    db.commit()
    db.close()
    login_resp = login(email="inactive@test.com")
    assert login_resp.status_code == 403


# ========== AUTHORIZATION ==========

def test_athlete_cannot_access_coach_endpoint():
    register_athlete(email="ath_coach@test.com")
    login_resp = login(email="ath_coach@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/coaches/me", headers=auth_header(token))
    assert resp.status_code == 403


def test_coach_cannot_access_athlete_endpoint():
    register_coach(email="coach_ath@test.com")
    login_resp = login(email="coach_ath@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/athletes/me", headers=auth_header(token))
    assert resp.status_code == 403


# ========== ATHLETE PROFILE ==========

def test_athlete_get_profile():
    register_athlete(email="profile@test.com", sport_id=1, position_id=3)
    login_resp = login(email="profile@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/athletes/me", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["sport"]["name"] == "Volei"
    assert data["position"]["name"] == "Ponteiro"


def test_athlete_update_name():
    register_athlete(email="updatename@test.com")
    login_resp = login(email="updatename@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/athletes/me", headers=auth_header(token), json={"name": "Novo Nome"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Novo Nome"


def test_athlete_update_sport_and_position():
    register_athlete(email="updatesport@test.com", sport_id=1, position_id=1)
    login_resp = login(email="updatesport@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/athletes/me", headers=auth_header(token), json={
        "sport_id": 2, "position_id": 10,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["sport"]["name"] == "Basquete"
    assert data["position"]["name"] == "Pivo"


def test_athlete_invalid_position_for_sport():
    register_athlete(email="invpos@test.com", sport_id=1, position_id=1)
    login_resp = login(email="invpos@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/athletes/me", headers=auth_header(token), json={
        "sport_id": 1, "position_id": 6,
    })
    assert resp.status_code == 400


def test_athlete_clear_sport():
    register_athlete(email="clearsport@test.com", sport_id=1, position_id=1)
    login_resp = login(email="clearsport@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/athletes/me", headers=auth_header(token), json={
        "sport_id": None,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["sport"] is None
    assert data["position"] is None


# ========== COACH PROFILE ==========

def test_coach_get_profile():
    register_coach(email="coachprofile@test.com", sport_ids=[1])
    login_resp = login(email="coachprofile@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/coaches/me", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sports"]) == 1
    assert data["sports"][0]["name"] == "Volei"


def test_coach_update_sports():
    register_coach(email="coachupdate@test.com", sport_ids=[1])
    login_resp = login(email="coachupdate@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/coaches/me", headers=auth_header(token), json={"sport_ids": [2]})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sports"]) == 1
    assert data["sports"][0]["name"] == "Basquete"


def test_coach_update_name():
    register_coach(email="coachname@test.com")
    login_resp = login(email="coachname@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/coaches/me", headers=auth_header(token), json={"name": "Coach Novo"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Coach Novo"


def test_coach_invalid_sport_update():
    register_coach(email="coachinv@test.com")
    login_resp = login(email="coachinv@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/coaches/me", headers=auth_header(token), json={"sport_ids": [999]})
    assert resp.status_code == 400


# ========== ATHLETE ATTRIBUTES ==========

def test_athlete_get_attributes_empty():
    register_athlete(email="attrget@test.com", sport_id=1, position_id=1)
    login_resp = login(email="attrget@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/athletes/me/attributes", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_athlete_update_attributes():
    register_athlete(email="attrupd@test.com", sport_id=1, position_id=1)
    login_resp = login(email="attrupd@test.com")
    token = login_resp.json()["access_token"]

    resp = client.put("/api/athletes/me/attributes", headers=auth_header(token), json={
        "attributes": [
            {"attribute_id": 1, "value": 70},
            {"attribute_id": 2, "value": 80},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    values = {a["attribute_name"]: a["value"] for a in data}
    assert values["Saque"] == 70
    assert values["Recepcao"] == 80


def test_athlete_invalid_attribute_value_too_high():
    register_athlete(email="attrhigh@test.com", sport_id=1, position_id=1)
    login_resp = login(email="attrhigh@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/athletes/me/attributes", headers=auth_header(token), json={
        "attributes": [{"attribute_id": 1, "value": 150}]
    })
    assert resp.status_code == 400


def test_athlete_invalid_attribute_value_negative():
    register_athlete(email="attrneg@test.com", sport_id=1, position_id=1)
    login_resp = login(email="attrneg@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/athletes/me/attributes", headers=auth_header(token), json={
        "attributes": [{"attribute_id": 1, "value": -10}]
    })
    assert resp.status_code == 400


def test_athlete_wrong_sport_attribute():
    register_athlete(email="attrwrong@test.com", sport_id=1, position_id=1)
    login_resp = login(email="attrwrong@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put("/api/athletes/me/attributes", headers=auth_header(token), json={
        "attributes": [{"attribute_id": 9, "value": 50}]
    })
    assert resp.status_code == 400


def test_athlete_attributes_without_sport():
    register_athlete(email="attrnosport@test.com", sport_id=1, position_id=1)
    login_resp = login(email="attrnosport@test.com")
    token = login_resp.json()["access_token"]

    client.put("/api/athletes/me", headers=auth_header(token), json={"sport_id": None})
    resp = client.put("/api/athletes/me/attributes", headers=auth_header(token), json={
        "attributes": [{"attribute_id": 1, "value": 50}]
    })
    assert resp.status_code == 400
