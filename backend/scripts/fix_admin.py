import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.security import get_password_hash
from app.db.session import dispose_engine, get_session_factory
from app.models.user import User

ADMIN_EMAIL = "admin@uniforma.app"
ADMIN_PASSWORD = "admin123"


async def fix_admin() -> User:
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
            user = result.scalar_one_or_none()

            if user is None:
                user = User(
                    email=ADMIN_EMAIL,
                    hashed_password=get_password_hash(ADMIN_PASSWORD),
                    is_active=True,
                    is_superuser=True,
                )
                session.add(user)
                action = "created"
            else:
                user.hashed_password = get_password_hash(ADMIN_PASSWORD)
                user.is_active = True
                user.is_superuser = True
                action = "updated"

            await session.commit()
            await session.refresh(user)
        except Exception:
            await session.rollback()
            raise

    print(
        f"Admin user {action}: email={user.email} id={user.id} "
        f"is_active={user.is_active} is_superuser={user.is_superuser}"
    )
    return user


async def main() -> None:
    try:
        await fix_admin()
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
