import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from userauth.common.roles import Role
from userauth.database.manager import DatabaseManager
from userauth.database.models import Base, LoginEntry, UserEntry

################################################################################
# SETUP DB IN MEMORY
################################################################################

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(create_db())

################################################################################
# UNIT TESTS - USERS
################################################################################


@pytest.mark.asyncio
async def test_create_user():
    """Test that users can be created in the database."""
    test_session = AsyncSession(engine, autocommit=False, autoflush=False)
    manager = DatabaseManager(test_session)

    created_user = await manager.create_user(
        username="first_user",
        email="first_user@email.com",
        password="password",
    )

    querystr = select(UserEntry).filter_by(uuid=created_user.uuid)
    results = await test_session.execute(querystr)
    results = [result[0] for result in results]
    assert created_user in results

    await test_session.close()


@pytest.mark.asyncio
async def test_get_users():
    """Test that users can fetched from the database."""
    test_session = AsyncSession(engine, autocommit=False, autoflush=False)
    manager = DatabaseManager(test_session)

    user_1 = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="user_1",
        email="user_1@email.com",
        name="name",
        surname="surname",
        hashed_password="password",
    )
    test_session.add(user_1)
    await test_session.commit()
    await test_session.refresh(user_1)

    user_2 = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="user_2",
        email="user_2@email.com",
        name="name",
        surname="surname",
        hashed_password="password",
    )
    test_session.add(user_2)
    await test_session.commit()
    await test_session.refresh(user_2)

    all_users = await manager.get_users()
    assert user_1 in all_users
    assert user_2 in all_users

    one_user = await manager.get_user(uuid=user_1.uuid)
    assert one_user.uuid == user_1.uuid

    one_user = await manager.get_user(email=user_1.email)
    assert one_user.uuid == user_1.uuid

    one_user = await manager.get_user(username=user_1.username)
    assert one_user.uuid == user_1.uuid

    await test_session.close()


@pytest.mark.asyncio
async def test_update_user():
    """Test that users can be updated."""
    test_session = AsyncSession(engine, autocommit=False, autoflush=False)
    manager = DatabaseManager(test_session)

    updatable_user = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="updatable_user",
        email="updatable_user@email.com",
        name="name",
        surname="surname",
        hashed_password="password",
    )
    test_session.add(updatable_user)
    await test_session.commit()
    await test_session.refresh(updatable_user)

    output_user = await manager.update_user(
        uuid=updatable_user.uuid,
        new_role=Role.celebrity,
    )
    assert output_user.role == Role.celebrity

    querystr = select(UserEntry).filter_by(uuid=output_user.uuid)
    results = await test_session.execute(querystr)
    result = results.scalars().first()
    assert result.role == Role.celebrity

    output_user = await manager.update_user(
        uuid=updatable_user.uuid,
        new_username="updated_username",
    )
    assert output_user.username == "updated_username"

    querystr = select(UserEntry).filter_by(uuid=output_user.uuid)
    results = await test_session.execute(querystr)
    result = results.scalars().first()
    assert output_user.username == "updated_username"

    await test_session.close()


@pytest.mark.asyncio
async def test_delete_user():
    """Test that users can be deleted."""
    test_session = AsyncSession(engine, autocommit=False, autoflush=False)
    manager = DatabaseManager(test_session)

    removable_user = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="removable_user",
        email="removable_user@email.com",
        name="name",
        surname="surname",
        hashed_password="password",
    )
    test_session.add(removable_user)
    await test_session.commit()
    await test_session.refresh(removable_user)

    await manager.delete_user(uuid=removable_user.uuid)
    querystr = select(UserEntry).filter_by(uuid=removable_user.uuid)
    results = await test_session.execute(querystr)
    assert len(list(results)) == 0

    await test_session.close()


@pytest.mark.asyncio
async def test_authenticate_user():
    """Test that users can authenticate."""
    from userauth.database.manager import hash_password

    test_session = AsyncSession(engine, autocommit=False, autoflush=False)
    manager = DatabaseManager(test_session)

    user_auth = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="user_auth",
        email="user_auth@email.com",
        name="name",
        surname="surname",
        hashed_password=hash_password("password"),
    )
    test_session.add(user_auth)
    await test_session.commit()
    await test_session.refresh(user_auth)

    output_user = await manager.authenticate_user(
        username="user_auth",
        password="password",
    )
    assert output_user.uuid == user_auth.uuid

    output_user = await manager.authenticate_user(
        username="user_auth",
        password="wrong_pass",
    )
    assert output_user is None

    await test_session.close()


################################################################################
# UNIT TESTS - LOGINS
################################################################################


@pytest.mark.asyncio
async def test_record_login():
    """Test logins can be recorded."""
    test_session = AsyncSession(engine, autocommit=False, autoflush=False)
    manager = DatabaseManager(test_session)

    loggin_user = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="loggin_user",
        email="loggin_user@email.com",
        name="name",
        surname="surname",
        hashed_password="password",
    )
    test_session.add(loggin_user)
    await test_session.commit()
    await test_session.refresh(loggin_user)

    login_record = await manager.record_login(loggin_user)

    querystr = select(LoginEntry).filter_by(uuid=login_record.uuid)
    result = await test_session.execute(querystr)
    found_record = result.scalars().first()
    assert login_record.uuid == found_record.uuid

    await test_session.close()


@pytest.mark.asyncio
async def test_get_logins():
    """Test logins can be gotten."""
    # Here I need expire_on_commit=False or second login commit excepts
    # https://github.com/sqlalchemy/sqlalchemy/discussions/6165#discussioncomment-550636
    test_session = AsyncSession(
        engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    manager = DatabaseManager(test_session)

    loggin_user = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="loggin_user_base",
        email="loggin_user_base@email.com",
        name="name",
        surname="surname",
        hashed_password="password",
    )
    test_session.add(loggin_user)
    await test_session.commit()
    await test_session.refresh(loggin_user)

    login_01 = LoginEntry(uuid=uuid4(), user=loggin_user.uuid)
    test_session.add(login_01)
    await test_session.commit()
    await test_session.refresh(login_01)

    login_02 = LoginEntry(uuid=uuid4(), user=loggin_user.uuid)
    test_session.add(login_02)
    await test_session.commit()
    await test_session.refresh(login_02)

    loggin_user_alt = UserEntry(
        uuid=uuid4(),
        role=Role.normal,
        username="loggin_user_alt",
        email="loggin_user_alt@email.com",
        name="name",
        surname="surname",
        hashed_password="password",
    )
    test_session.add(loggin_user_alt)
    await test_session.commit()
    await test_session.refresh(loggin_user_alt)

    login_alt = LoginEntry(uuid=uuid4(), user=loggin_user_alt.uuid)
    test_session.add(login_alt)
    await test_session.commit()
    await test_session.refresh(login_alt)

    login_record = await manager.get_login(uuid=login_01.uuid)
    assert login_record.uuid == login_01.uuid

    login_records = await manager.get_logins(user_uuid=loggin_user.uuid)
    assert login_01 in login_records
    assert login_02 in login_records

    login_records = await manager.get_logins(user_uuid=None)
    assert login_01 in login_records
    assert login_02 in login_records
    assert login_alt in login_records

    await test_session.close()
