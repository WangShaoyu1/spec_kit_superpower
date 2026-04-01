from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.constants import CAPABILITY_ROWS, ROLE_CAPABILITIES, ROLE_LABELS
from app.models import CapabilityDefinition, RoleCapabilityBinding, RoleDefinition, UserAccount
from app.security import hash_password


def seed_database(session: Session, settings: Settings):
    if session.execute(select(func.count()).select_from(RoleDefinition)).scalar_one() == 0:
        for role_key, role_label in ROLE_LABELS.items():
            session.add(RoleDefinition(role_key=role_key, role_label=role_label, is_builtin=True))

    if session.execute(select(func.count()).select_from(CapabilityDefinition)).scalar_one() == 0:
        for capability_key, description, condition_note, module_key in CAPABILITY_ROWS:
            session.add(
                CapabilityDefinition(
                    capability_key=capability_key,
                    description=description,
                    condition_note=condition_note,
                    module_key=module_key,
                )
            )

    session.flush()

    if session.execute(select(func.count()).select_from(RoleCapabilityBinding)).scalar_one() == 0:
        for role_key, capability_map in ROLE_CAPABILITIES.items():
            for capability_key, condition_note in capability_map.items():
                session.add(
                    RoleCapabilityBinding(
                        role_key=role_key,
                        capability_key=capability_key,
                        condition_note=condition_note,
                    )
                )

    admin_user = session.execute(select(UserAccount).where(UserAccount.username == "admin")).scalar_one_or_none()
    if admin_user is None:
        session.add(
            UserAccount(
                id="user_001",
                username="admin",
                display_name="管理员",
                password_hash=hash_password(settings.seed_admin_password),
                role_key="admin",
                status="active",
                token_version=1,
                is_builtin_admin=True,
            )
        )

    session.commit()
