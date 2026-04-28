from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    password: str,
    role: UserRole = UserRole.viewer,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def ensure_admin_exists(db: AsyncSession, email: str, password: str) -> None:
    result = await db.execute(select(User).where(User.email == email))
    if not result.scalar_one_or_none():
        await create_user(db, email, "Admin", password, UserRole.admin)
