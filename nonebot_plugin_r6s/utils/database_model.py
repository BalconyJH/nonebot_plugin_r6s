from collections.abc import Sequence
from datetime import datetime
from enum import Enum as PyEnum

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
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from nonebot_plugin_r6s.utils import log_return_msg


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
    async def check_user_occupation(session: AsyncSession, bind_id: str) -> bool:
        stmt = select(exists().where(LoginUserSessionBind.bind_id == bind_id))
        async with session as db_session:
            return await db_session.scalar(stmt) or False


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
    @log_return_msg
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
    @log_return_msg
    async def get_group_permission_group(
        session: AsyncSession, group_id: str, platform: str
    ) -> tuple[Sequence[str], str]:
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
        bot_users = await PermissionGroup.get_bot_permission_group(session)

        # 查询指定 group_id 和 platform 下的 GROUPOWNER 和 GROUPADMIN 用户
        stmt = select(PermissionGroup.user_id).where(
            and_(
                PermissionGroup.permission.in_(["2", "3"]),
                PermissionGroup.platform == platform,
                PermissionGroup.group_id == group_id,
            )
        )

        async with session as db_session:
            group_users = (await db_session.scalars(stmt)).all()

        if all_users := bot_users + group_users:
            return (
                all_users,
                f"Permissions retrieved successfully, including {len(all_users)} users",
            )
        return [], "No user permissions found"

    @staticmethod
    @log_return_msg
    async def update_group_permission_group(
        session: AsyncSession,
        group_id: str,
        platform: str,
        user_id: str,
        permission: str,
    ) -> tuple[bool, str]:
        """
        Update or add user permission in a specific group.

        This method checks if the user already has a permission in the specified group.
        If the user exists and the permission is different, it updates the permission.
        If the user does not exist, it adds a new permission record.

        Args:
            session (AsyncSession): The database session to use for the operation.
            group_id (str): The ID of the group.
            platform (str): The platform associated with the group.
            user_id (str): The ID of the user whose permission is being updated or
            added.
            permission (str): The permission level to be set for the user.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or
            failure,
            and a string message describing the result of the operation.
        """
        stmt = select(PermissionGroup).where(
            PermissionGroup.platform == platform,
            PermissionGroup.group_id == group_id,
            PermissionGroup.user_id == user_id,
        )

        async with session as db_session:
            result: ScalarResult[PermissionGroup] = await db_session.scalars(stmt)
            if existing_user := result.first():
                if existing_user.permission == permission:
                    return False, "User permission already exists"
                existing_user.permission = permission
                existing_user.updated_at = datetime.now()
                await db_session.commit()
                return True, "User permission updated successfully"

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
            return True, "User permission added successfully"
