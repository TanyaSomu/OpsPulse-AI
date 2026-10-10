import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

@pytest.fixture(scope="session")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def admin_user(db_session: Session):
    user = db_session.query(User).filter(User.email == "admin@opspulse.local").first()
    return user

@pytest.fixture(scope="session")
def responder_user(db_session: Session):
    user = db_session.query(User).filter(User.email == "responder@opspulse.local").first()
    return user

@pytest.fixture(scope="session")
def admin_headers(admin_user):
    token = create_access_token(subject=admin_user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="session")
def responder_headers(responder_user):
    token = create_access_token(subject=responder_user.id)
    return {"Authorization": f"Bearer {token}"}
