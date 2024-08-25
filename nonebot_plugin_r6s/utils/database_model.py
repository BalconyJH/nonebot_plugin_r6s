from collections.abc import Sequence
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from nonebot import logger
from nonebot_plugin_orm import Model as ORMModel
from sqlalchemy import (
    INT,
    String,
    select,
    exists,
    Enum,
    DateTime,
    and_,
    ScalarResult,
    Text,
    Boolean,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column


class LoginUserSessionBind(ORMModel):
    id: Mapped[int] = mapped_column(
        INT,
        nullable=False,
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="ID",
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False, comment="Token")
    ubi_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Ubi ID",
    )
    platform: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Platform"
    )
    bind_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Group ID"
    )
    bind_account: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Bind User"
    )
    sessionid: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Session ID"
    )
    key: Mapped[str] = mapped_column(Text, nullable=False, comment="Session Key")
    new_key: Mapped[str] = mapped_column(
        Text, nullable=False, comment="New Session Key"
    )
    expiration: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Expiration"
    )
    new_expiration: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="New Expiration"
    )
    spaceid: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Space ID"
    )
    profileid: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Profile ID"
    )

    @staticmethod
    async def check_user_occupation(
        session: AsyncSession, bind_id: str, bind_account: str
    ) -> bool:
        stmt = select(
            exists()
            .where(LoginUserSessionBind.bind_id == bind_id)
            .where(LoginUserSessionBind.bind_account == bind_account)
        )
        async with session as db_session:
            return await db_session.scalar(stmt) or False

    @staticmethod
    async def unbind_user(
        session: AsyncSession, bind_id: str, bind_account: str
    ) -> bool:
        stmt = (
            select(LoginUserSessionBind)
            .where(LoginUserSessionBind.bind_id == bind_id)
            .where(LoginUserSessionBind.bind_account == bind_account)
        )
        async with session as db_session:
            result = await db_session.scalars(stmt)
            if user := result.first():
                await db_session.delete(user)
                await db_session.commit()
                return True
            return False

    @staticmethod
    async def get_session(
        session: AsyncSession, bind_id: str
    ) -> Optional["LoginUserSessionBind"]:
        stmt = select(LoginUserSessionBind).where(
            LoginUserSessionBind.bind_id == bind_id
        )
        async with session as db_session:
            result = await db_session.scalars(stmt)
            if user := result.first():
                logger.info(f"Session found for group '{bind_id}'")
                return user
            logger.warning(f"No session found for group '{bind_id}'")
            return None


class PermissionEnum(PyEnum):
    """
    Enumeration of permission levels.
    """

    SUPERUSER = "0"
    ADMIN = "1"
    GROUPOWNER = "2"
    GROUPADMIN = "3"
    UNKNOWN = "4"


class PermissionGroup(ORMModel):
    id: Mapped[int] = mapped_column(
        INT,
        nullable=False,
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="ID",
    )
    group_id: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="Group ID"
    )
    platform: Mapped[str] = mapped_column(String(10), nullable=True, comment="Platform")
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="User ID")
    permission: Mapped[str] = mapped_column(
        Enum(PermissionEnum), nullable=False, comment="Permission (0-5)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="Created At"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="Updated At"
    )

    @staticmethod
    async def get_bot_permission_group(session: AsyncSession) -> Sequence[str]:
        """
        Get all SUPERUSER and ADMIN users globally.

        Args:
            session (AsyncSession): The database session to use for the operation.

        Returns:
            Sequence[str]: A Sequence of user IDs with SUPERUSER and ADMIN
            permissions globally.
        """
        stmt = select(PermissionGroup.user_id).where(
            PermissionGroup.permission.in_(["0", "1"])
        )

        async with session as db_session:
            return (await db_session.scalars(stmt)).all()

    @staticmethod
    async def get_group_permission_group(
        session: AsyncSession, group_id: str, platform: str
    ) -> Sequence[str]:
        """
        Get all SUPERUSER and ADMIN users globally, as well as GROUPOWNER and GROUPADMIN
        users in a specific group and platform.

        Args:
            session (AsyncSession): The database session to use for the operation.
            group_id (str): The ID of the group.
            platform (str): The platform associated with the group.

        Returns:
            Tuple[Sequence[str], str]: A tuple containing a Sequence of user IDs
            with permissions in the specified group and platform, or globally,
            and a message describing the result.
        """
        # 获取全局的 SUPERUSER 和 ADMIN 用户
        bot_users = list(await PermissionGroup.get_bot_permission_group(session))

        # 查询指定 group_id 和 platform 下的 GROUPOWNER 和 GROUPADMIN 用户
        stmt = select(PermissionGroup.user_id).where(
            and_(
                PermissionGroup.permission.in_(["2", "3"]),
                PermissionGroup.platform == platform,
                PermissionGroup.group_id == group_id,
            )
        )

        async with session as db_session:
            group_users = list((await db_session.scalars(stmt)).all())

        if all_users := bot_users + group_users:
            logger.info(f"Permissions found, users length: {len(all_users)}")
            return all_users
        logger.warning("No permissions found")
        return []

    @staticmethod
    async def update_group_permission_group(
        session: AsyncSession,
        group_id: str,
        platform: str,
        user_id: str,
        permission: str,
    ) -> bool:
        """
        Update the permission of a user in a group and platform.

        Args:
            session (AsyncSession): The database session to use for the operation.
            group_id (str): The ID of the group.
            platform (str): The platform associated with the group.
            user_id (str): The ID of the user.
            permission (str): The new permission level.

        Returns:
            bool: A boolean indicating success or failure.
        """
        stmt = (
            select(PermissionGroup)
            .where(PermissionGroup.platform == platform)
            .where(PermissionGroup.group_id == group_id)
            .where(PermissionGroup.user_id == user_id)
        )

        async with session as db_session:
            try:
                result: ScalarResult[PermissionGroup] = await db_session.scalars(stmt)
                if existing_user := result.first():
                    if existing_user.permission == permission:
                        logger.info(
                            f"User '{user_id}' in group '{group_id}' already has "
                            f"permission '{permission}'"
                        )
                        return False
                    existing_user.permission = permission
                    existing_user.updated_at = datetime.now()
                    await db_session.commit()
                    logger.info(
                        f"Updated user permission for '{user_id}' in group '{group_id}'"
                    )
                    return True

                new_user = PermissionGroup(
                    group_id=group_id,
                    platform=platform,
                    user_id=user_id,
                    permission=permission,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db_session.add(new_user)
                await db_session.commit()
                logger.info(
                    f"Added user permission for '{user_id}' in group '{group_id}'"
                )
                return True
            except SQLAlchemyError:
                await db_session.rollback()
                logger.exception(
                    f"Failed to update or add user permission for '{user_id}' in "
                    f"group '{group_id}'"
                )
                return False


class EncryptionKey(ORMModel):
    id: Mapped[int] = mapped_column(
        INT,
        nullable=False,
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="ID",
    )
    key_name: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="Key Name", unique=True
    )
    secret_key: Mapped[str] = mapped_column(Text, nullable=False, comment="Session Key")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="Created At"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="Updated At"
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Key Active State",
    )
    description: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="Description"
    )

    @staticmethod
    async def get_encryption_key(
        session: AsyncSession, key_name: str
    ) -> Optional["EncryptionKey"]:
        """
        Get an encryption key by its name.

        Args:
            session (AsyncSession): The database session to use for the operation.
            key_name (str): The name of the encryption key to retrieve.

        Returns:
            Tuple[Optional["EncryptionKey"], str]: A tuple containing the encryption key
            object if found, or None if not found, and a message describing the result.
        """
        stmt = (
            select(EncryptionKey)
            .where(EncryptionKey.active == True)  # noqa: E712
            .where(EncryptionKey.key_name == key_name)
        )
        async with session as db_session:
            result = await db_session.scalars(stmt)
            if key := result.first():
                logger.info(f"Retrieved encryption key '{key_name}'")
                return key
            logger.warning(f"Encryption key '{key_name}' not found")
            return None

    @staticmethod
    async def update_encryption_key(
        session: AsyncSession,
        key_name: str,
        secret_key: Optional[str] = None,
        description: Optional[str] = None,
        active: bool = True,
    ) -> bool:
        """
        Update an encryption key by its name.

        Args:
            session (AsyncSession): The database session to use for the operation.
            key_name (str): The name of the encryption key to update.
            secret_key (Optional[str], optional): The new secret key value.
            Defaults to None.
            description (Optional[str], optional): The new description of the encryption
            key. Defaults to None.
            active (bool, optional): The new active state of the encryption key.
            Defaults to True.

        Returns:
            bool: A boolean indicating success or failure.
        """
        stmt = select(EncryptionKey).where(EncryptionKey.key_name == key_name)
        async with session as db_session:
            try:
                result = await db_session.scalars(stmt)
                if existing_key := result.first():
                    if secret_key is not None:
                        existing_key.secret_key = secret_key
                    if description is not None:
                        existing_key.description = description
                    if active is not None:
                        existing_key.active = active

                    existing_key.updated_at = datetime.now()
                    await db_session.commit()
                    logger.info(f"Updated encryption key '{key_name}'")
                    return True
                else:
                    logger.warning(f"Encryption key '{key_name}' not found")
                    return False
            except SQLAlchemyError:
                await db_session.rollback()
                logger.exception(f"Failed to update or add encryption key '{key_name}'")
                return False

    @staticmethod
    async def delete_encryption_key(session: AsyncSession, key_name: str) -> bool:
        """
        Delete an encryption key by its name.

        Args:
            session (AsyncSession): The database session to use for the operation.
            key_name (str): The name of the encryption key to delete.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or
            failure, and a string message describing the result of the operation.
        """
        stmt = select(EncryptionKey).where(EncryptionKey.key_name == key_name)
        async with session as db_session:
            try:
                result = await db_session.scalars(stmt)
                if key := result.first():
                    await db_session.delete(key)
                    await db_session.commit()
                    logger.info(f"Deleted encryption key '{key_name}'")
                    return True
                logger.warning(f"Encryption key '{key_name}' not found")
                return False
            except SQLAlchemyError:
                await db_session.rollback()
                logger.exception(f"Failed to delete encryption key '{key_name}'")
                return False

    @staticmethod
    async def add_encryption_key(
        session: AsyncSession,
        key_name: str,
        secret_key: str,
        description: Optional[str] = None,
        active: bool = True,
    ) -> bool:
        """
        Add a new encryption key.

        Args:
            session (AsyncSession): The database session to use for the operation.
            key_name (str): The name of the encryption key.
            secret_key (str): The secret key value.
            description (Optional[str], optional): A description of the encryption key.
            Defaults to None.
            active (bool, optional): The active state of the encryption key.
            Defaults to True.

        Returns:
            bool: A boolean indicating success or failure.
        """
        stmt = select(EncryptionKey).where(EncryptionKey.key_name == key_name)
        async with session as db_session:
            try:
                result = await db_session.scalars(stmt)
                if result.first():
                    logger.warning(f"Encryption key '{key_name}' already exists")
                    return False
                now = datetime.now()
                new_key = EncryptionKey(
                    key_name=key_name,
                    secret_key=secret_key,
                    description=description,
                    active=active,
                    created_at=now,
                    updated_at=now,
                )
                db_session.add(new_key)
                await db_session.commit()
                logger.info(f"Added encryption key '{key_name}'")
                return True
            except SQLAlchemyError:
                await db_session.rollback()
                logger.exception(f"Failed to add encryption key '{key_name}'")
                return False
