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


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "TrainTime API"


def test_list_sports():
    response = client.get("/api/sports")
    assert response.status_code == 200
    sports = response.json()
    assert len(sports) == 2
    names = [s["name"] for s in sports]
    assert "Volei" in names
    assert "Basquete" in names


def test_get_sport_volleyball():
    response = client.get("/api/sports/1")
    assert response.status_code == 200
    sport = response.json()
    assert sport["name"] == "Volei"
    assert sport["icon"] == "\U0001f3d0"
    assert len(sport["positions"]) == 5
    assert len(sport["attributes"]) == 8


def test_get_sport_basketball():
    response = client.get("/api/sports/2")
    assert response.status_code == 200
    sport = response.json()
    assert sport["name"] == "Basquete"
    assert sport["icon"] == "\U0001f3c0"
    assert len(sport["positions"]) == 5
    assert len(sport["attributes"]) == 8


def test_volleyball_positions():
    response = client.get("/api/sports/1/positions")
    assert response.status_code == 200
    positions = response.json()
    names = [p["name"] for p in positions]
    assert "Levantador" in names
    assert "Oposto" in names
    assert "Ponteiro" in names
    assert "Central" in names
    assert "Libero" in names


def test_basketball_positions():
    response = client.get("/api/sports/2/positions")
    assert response.status_code == 200
    positions = response.json()
    names = [p["name"] for p in positions]
    assert "Armador" in names
    assert "Ala-armador" in names
    assert "Ala" in names
    assert "Ala-pivo" in names
    assert "Pivo" in names


def test_volleyball_attributes():
    response = client.get("/api/sports/1/attributes")
    assert response.status_code == 200
    attributes = response.json()
    names = [a["name"] for a in attributes]
    assert "Saque" in names
    assert "Recepcao" in names
    assert "Ataque" in names
    assert "Bloqueio" in names
    assert "Defesa" in names
    assert "Levantamento" in names
    assert "Velocidade" in names
    assert "Resistencia" in names


def test_basketball_attributes():
    response = client.get("/api/sports/2/attributes")
    assert response.status_code == 200
    attributes = response.json()
    names = [a["name"] for a in attributes]
    assert "Arremesso" in names
    assert "Passe" in names
    assert "Drible" in names
    assert "Defesa" in names
    assert "Rebote" in names
    assert "Velocidade" in names
    assert "Resistencia" in names
    assert "Controle de bola" in names


def test_sport_not_found():
    response = client.get("/api/sports/999")
    assert response.status_code == 404


def test_positions_not_found():
    response = client.get("/api/sports/999/positions")
    assert response.status_code == 404
