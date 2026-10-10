from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.organization import Organization
from app.models.enums import UserRole
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.audit_service import record_audit_event

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()

def authenticate_user(db: Session, credentials: LoginRequest) -> User:
    user = get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return user

def register_user(db: Session, request: RegisterRequest) -> User:
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    # Find or create organization
    org = db.query(Organization).first()
    if not org:
        org_name = request.organization_name or "OpsPulse Engineering"
        slug = org_name.lower().replace(" ", "-")
        org = Organization(name=org_name, slug=slug)
        db.add(org)
        db.flush()

    new_user = User(
        organization_id=org.id,
        email=request.email.lower(),
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        role=request.role,
        is_active=True
    )
    db.add(new_user)
    db.flush()

    record_audit_event(
        db=db,
        organization_id=org.id,
        event_type="USER_REGISTERED",
        target_type="USER",
        details=f"User {new_user.email} registered with role {new_user.role.value}",
        actor=new_user,
        target_id=new_user.id
    )

    db.commit()
    db.refresh(new_user)
    return new_user
