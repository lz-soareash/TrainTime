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


# ========== TEAM CREATION ==========

def test_coach_creates_team():
    register_coach(email="coach_team1@test.com")
    resp, token = create_team_helper("coach_team1@test.com", "Sub-18 Volei", 1)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Sub-18 Volei"
    assert data["sport"]["name"] == "Volei"
    assert data["athletes"] == []


def test_athlete_cannot_create_team():
    register_athlete(email="ath_team@test.com")
    login_resp = login(email="ath_team@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/teams", headers=auth_header(token), json={
        "name": "Equipe Invalida", "sport_id": 1,
    })
    assert resp.status_code == 403


def test_create_team_invalid_sport():
    register_coach(email="coach_team2@test.com")
    login_resp = login(email="coach_team2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/teams", headers=auth_header(token), json={
        "name": "Equipe Sport Errado", "sport_id": 999,
    })
    assert resp.status_code == 400


def test_create_team_invalid_name():
    register_coach(email="coach_team3@test.com")
    login_resp = login(email="coach_team3@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post("/api/teams", headers=auth_header(token), json={
        "name": "A", "sport_id": 1,
    })
    assert resp.status_code == 422


# ========== TEAM LISTING ==========

def test_coach_sees_own_teams():
    register_coach(email="coach_list1@test.com")
    create_team_helper("coach_list1@test.com", "Equipe A")
    create_team_helper("coach_list1@test.com", "Equipe B")
    login_resp = login(email="coach_list1@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/teams", headers=auth_header(token))
    assert resp.status_code == 200
    teams = resp.json()
    assert len(teams) == 2
    names = [t["name"] for t in teams]
    assert "Equipe A" in names
    assert "Equipe B" in names


def test_coach_does_not_see_other_teams():
    register_coach(email="coach_list_a@test.com")
    register_coach(email="coach_list_b@test.com")
    create_team_helper("coach_list_a@test.com", "Equipe A")
    create_team_helper("coach_list_b@test.com", "Equipe B")
    login_resp = login(email="coach_list_a@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/teams", headers=auth_header(token))
    teams = resp.json()
    assert len(teams) == 1
    assert teams[0]["name"] == "Equipe A"


def test_athlete_cannot_list_teams():
    register_athlete(email="ath_list@test.com")
    login_resp = login(email="ath_list@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/teams", headers=auth_header(token))
    assert resp.status_code == 403


# ========== TEAM VIEW ==========

def test_coach_views_own_team():
    register_coach(email="coach_view@test.com")
    create_resp, _ = create_team_helper("coach_view@test.com", "Visualizar")
    team_id = create_resp.json()["id"]
    login_resp = login(email="coach_view@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Visualizar"


def test_coach_cannot_view_other_team():
    register_coach(email="coach_view_a@test.com")
    register_coach(email="coach_view_b@test.com")
    create_resp, _ = create_team_helper("coach_view_b@test.com", "Equipe B")
    team_id = create_resp.json()["id"]
    login_resp = login(email="coach_view_a@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_athlete_views_team_in():
    register_coach(email="coach_view2@test.com")
    register_athlete(email="ath_view@test.com", sport_id=1, position_id=1)
    create_resp, _ = create_team_helper("coach_view2@test.com", "Time Volei")
    team_id = create_resp.json()["id"]

    login_resp = login(email="ath_view@test.com")
    ath_token = login_resp.json()["access_token"]
    ath_profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = ath_profile["id"]

    login_resp = login(email="coach_view2@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/{ath_id}", headers=auth_header(token))

    resp = client.get(f"/api/teams/{team_id}", headers=auth_header(ath_token))
    assert resp.status_code == 200


def test_athlete_cannot_view_team_not_in():
    register_coach(email="coach_view3@test.com")
    register_athlete(email="ath_view2@test.com", sport_id=1, position_id=1)
    create_resp, _ = create_team_helper("coach_view3@test.com", "Time Fechado")
    team_id = create_resp.json()["id"]

    login_resp = login(email="ath_view2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 403


# ========== TEAM UPDATE ==========

def test_coach_updates_team_name():
    register_coach(email="coach_upd@test.com")
    create_resp, _ = create_team_helper("coach_upd@test.com", "Nome Antigo")
    team_id = create_resp.json()["id"]
    login_resp = login(email="coach_upd@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put(f"/api/teams/{team_id}", headers=auth_header(token), json={
        "name": "Nome Novo",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Nome Novo"


def test_coach_cannot_update_other_team():
    register_coach(email="coach_upd_a@test.com")
    register_coach(email="coach_upd_b@test.com")
    create_resp, _ = create_team_helper("coach_upd_b@test.com", "Equipe B")
    team_id = create_resp.json()["id"]
    login_resp = login(email="coach_upd_a@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put(f"/api/teams/{team_id}", headers=auth_header(token), json={
        "name": "Tentativa",
    })
    assert resp.status_code == 403


def test_athlete_cannot_update_team():
    register_coach(email="coach_upd2@test.com")
    register_athlete(email="ath_upd@test.com")
    create_resp, _ = create_team_helper("coach_upd2@test.com", "Equipe X")
    team_id = create_resp.json()["id"]
    login_resp = login(email="ath_upd@test.com")
    token = login_resp.json()["access_token"]
    resp = client.put(f"/api/teams/{team_id}", headers=auth_header(token), json={
        "name": "Hacker",
    })
    assert resp.status_code == 403


# ========== TEAM DELETE ==========

def test_coach_deletes_team():
    register_coach(email="coach_del@test.com")
    create_resp, _ = create_team_helper("coach_del@test.com", "Para Deletar")
    team_id = create_resp.json()["id"]
    login_resp = login(email="coach_del@test.com")
    token = login_resp.json()["access_token"]
    resp = client.delete(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 204


def test_coach_cannot_delete_other_team():
    register_coach(email="coach_del_a@test.com")
    register_coach(email="coach_del_b@test.com")
    create_resp, _ = create_team_helper("coach_del_b@test.com", "Equipe B")
    team_id = create_resp.json()["id"]
    login_resp = login(email="coach_del_a@test.com")
    token = login_resp.json()["access_token"]
    resp = client.delete(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_athlete_cannot_delete_team():
    register_coach(email="coach_del2@test.com")
    register_athlete(email="ath_del@test.com")
    create_resp, _ = create_team_helper("coach_del2@test.com", "Equipe Segura")
    team_id = create_resp.json()["id"]
    login_resp = login(email="ath_del@test.com")
    token = login_resp.json()["access_token"]
    resp = client.delete(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_delete_team_removes_links():
    register_coach(email="coach_del3@test.com")
    register_athlete(email="ath_del2@test.com", sport_id=1, position_id=1)
    create_resp, _ = create_team_helper("coach_del3@test.com", "Com Atleta")
    team_id = create_resp.json()["id"]

    login_resp = login(email="coach_del3@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))

    resp = client.delete(f"/api/teams/{team_id}", headers=auth_header(token))
    assert resp.status_code == 204

    from app.models.models import Athlete
    db = TestingSessionLocal()
    ath = db.query(Athlete).filter(Athlete.id == 1).first()
    assert ath is not None
    db.close()


# ========== ADD/REMOVE ATHLETES ==========

def test_coach_adds_compatible_athlete():
    register_coach(email="coach_add@test.com")
    register_athlete(email="ath_add@test.com", sport_id=1, position_id=3)
    create_resp, _ = create_team_helper("coach_add@test.com", "Time Add")
    team_id = create_resp.json()["id"]

    login_resp = login(email="coach_add@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))
    assert resp.status_code == 200
    athletes = resp.json()["athletes"]
    assert len(athletes) == 1


def test_coach_rejects_incompatible_athlete():
    register_coach(email="coach_incompat@test.com")
    register_athlete(email="ath_basketball@test.com", sport_id=2, position_id=6)
    create_resp, _ = create_team_helper("coach_incompat@test.com", "Time Volei", 1)
    team_id = create_resp.json()["id"]

    login_resp = login(email="ath_basketball@test.com")
    ath_token = login_resp.json()["access_token"]
    ath_profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = ath_profile["id"]

    login_resp = login(email="coach_incompat@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post(f"/api/teams/{team_id}/athletes/{ath_id}", headers=auth_header(token))
    assert resp.status_code == 400


def test_coach_rejects_duplicate_athlete():
    register_coach(email="coach_dup@test.com")
    register_athlete(email="ath_dup@test.com", sport_id=1, position_id=1)
    create_resp, _ = create_team_helper("coach_dup@test.com", "Time Dup")
    team_id = create_resp.json()["id"]

    login_resp = login(email="coach_dup@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))
    resp = client.post(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))
    assert resp.status_code == 409


def test_coach_removes_athlete():
    register_coach(email="coach_rem@test.com")
    register_athlete(email="ath_rem@test.com", sport_id=1, position_id=1)
    create_resp, _ = create_team_helper("coach_rem@test.com", "Time Rem")
    team_id = create_resp.json()["id"]

    login_resp = login(email="coach_rem@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))
    resp = client.delete(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.json()["athletes"]) == 0


def test_coach_cannot_add_to_other_team():
    register_coach(email="coach_add_a@test.com")
    register_coach(email="coach_add_b@test.com")
    register_athlete(email="ath_cross@test.com", sport_id=1, position_id=1)
    create_resp, _ = create_team_helper("coach_add_b@test.com", "Equipe B")
    team_id = create_resp.json()["id"]

    login_resp = login(email="coach_add_a@test.com")
    token = login_resp.json()["access_token"]
    resp = client.post(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))
    assert resp.status_code == 403


# ========== ATHLETE TEAMS VIEW ==========

def test_athlete_views_own_teams():
    register_coach(email="coach_ath_teams@test.com")
    register_athlete(email="ath_teams@test.com", sport_id=1, position_id=1)
    create_resp, _ = create_team_helper("coach_ath_teams@test.com", "Time 1")
    team_id = create_resp.json()["id"]

    login_resp = login(email="ath_teams@test.com")
    ath_token = login_resp.json()["access_token"]
    ath_profile = client.get("/api/athletes/me", headers=auth_header(ath_token)).json()
    ath_id = ath_profile["id"]

    login_resp = login(email="coach_ath_teams@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/{ath_id}", headers=auth_header(token))

    resp = client.get("/api/athletes/me/teams", headers=auth_header(ath_token))
    assert resp.status_code == 200
    teams = resp.json()
    assert len(teams) == 1
    assert teams[0]["name"] == "Time 1"


def test_coach_cannot_view_athlete_teams():
    register_coach(email="coach_ath_teams2@test.com")
    login_resp = login(email="coach_ath_teams2@test.com")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/athletes/me/teams", headers=auth_header(token))
    assert resp.status_code == 403


# ========== TEAM LIST RESPONSE ==========

def test_team_list_shows_athlete_count():
    register_coach(email="coach_count@test.com")
    register_athlete(email="ath_count1@test.com", sport_id=1, position_id=1)
    register_athlete(email="ath_count2@test.com", sport_id=1, position_id=2)
    create_resp, _ = create_team_helper("coach_count@test.com", "Time Count")
    team_id = create_resp.json()["id"]

    login_resp = login(email="coach_count@test.com")
    token = login_resp.json()["access_token"]
    client.post(f"/api/teams/{team_id}/athletes/1", headers=auth_header(token))
    client.post(f"/api/teams/{team_id}/athletes/2", headers=auth_header(token))

    resp = client.get("/api/teams", headers=auth_header(token))
    assert resp.status_code == 200
    teams = resp.json()
    team = next(t for t in teams if t["id"] == team_id)
    assert team["athlete_count"] == 2


# ========== UNAUTHENTICATED ==========

def test_team_endpoint_no_token():
    resp = client.get("/api/teams")
    assert resp.status_code == 401

    resp = client.post("/api/teams", json={"name": "X", "sport_id": 1})
    assert resp.status_code == 401
