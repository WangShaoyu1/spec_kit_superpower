#!/usr/bin/env python3
"""
将业务数据收敛为「单条」：1 个指令库、1 个训练数据集、1 个评测数据集、1 个对话方案；
并删除关联数据（模型版本、评测运行、测试会话、批量测试、请求日志等）。

不删除：用户/角色/权限、知识库（knowledge_*）、告警规则等全局配置。

用法（在 smartchef-v2/backend 目录下）::

    python scripts/prune_dev_data.py --dry-run    # 仅打印计划
    python scripts/prune_dev_data.py --yes        # 执行清理

环境变量 DATABASE_URL 或 .env 与 app 一致（默认见 app.core.config）。
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# 确保可导入 app
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# 预加载 ORM 依赖，避免 relationship 解析失败
import app.models.intent  # noqa: F401
import app.models.slot  # noqa: F401
import app.models.evaluation  # noqa: F401
import app.models.test_session  # noqa: F401

from sqlalchemy import and_, delete, exists, or_, select

from app.core import database as db
from app.models.batch_test import BatchTest
from app.models.dataset import EvaluationDataset, TrainingDataset
from app.models.dialog_profile import DialogProfile, ProfileLibraryBinding
from app.models.evaluation import EvaluationRun
from app.models.intent_library import IntentLibrary
from app.models.model_version import LibraryModelVersion
from app.models.request_log import RequestLog
from app.models.test_session import IntentTestSession


async def _pick_keep_ids(session) -> tuple[UUID, UUID, UUID, UUID, UUID | None]:
    """各保留 1 条：选定「同时有训练集+评测集」的最早指令库，再各取最早一条数据集。"""
    has_train = exists().where(TrainingDataset.library_id == IntentLibrary.id)
    has_eval = exists().where(EvaluationDataset.library_id == IntentLibrary.id)
    r_lib = await session.execute(
        select(IntentLibrary.id)
        .where(has_train, has_eval)
        .order_by(IntentLibrary.created_at.asc())
        .limit(1)
    )
    row_lib = r_lib.scalar_one_or_none()
    if row_lib is None:
        raise RuntimeError(
            "没有「同时包含至少一个训练数据集和一个评测数据集」的指令库；"
            "请在同一指令库下补齐两类数据集后再运行。"
        )
    keep_lib_id: UUID = row_lib

    r_td = await session.execute(
        select(TrainingDataset.id)
        .where(TrainingDataset.library_id == keep_lib_id)
        .order_by(TrainingDataset.created_at.asc())
        .limit(1)
    )
    keep_train_id: UUID = r_td.scalar_one()

    r_ed = await session.execute(
        select(EvaluationDataset.id)
        .where(EvaluationDataset.library_id == keep_lib_id)
        .order_by(EvaluationDataset.created_at.asc())
        .limit(1)
    )
    keep_eval_id: UUID = r_ed.scalar_one()

    r_prof = await session.execute(
        select(DialogProfile.id).order_by(DialogProfile.created_at.asc()).limit(1)
    )
    row_prof = r_prof.scalar_one_or_none()
    if row_prof is None:
        raise RuntimeError("数据库中没有任何对话方案，无法执行清理。")
    keep_profile_id: UUID = row_prof

    r_mv = await session.execute(
        select(LibraryModelVersion.id)
        .where(LibraryModelVersion.library_id == keep_lib_id)
        .order_by(LibraryModelVersion.created_at.asc())
        .limit(1)
    )
    keep_model_id: UUID | None = r_mv.scalar_one_or_none()

    return keep_lib_id, keep_train_id, keep_eval_id, keep_profile_id, keep_model_id


async def prune(*, dry_run: bool) -> None:
    await db.init_db()
    if db.async_session_factory is None:
        raise RuntimeError("init_db failed")

    async with db.async_session_factory() as session:
        keep_lib_id, keep_train_id, keep_eval_id, keep_profile_id, keep_model_id = await _pick_keep_ids(
            session
        )

        plan = f"""
保留项（按 created_at 最早的一条）:
  intent_library_id      = {keep_lib_id}
  training_dataset_id    = {keep_train_id}
  evaluation_dataset_id  = {keep_eval_id}
  dialog_profile_id      = {keep_profile_id}
  model_version_id       = {keep_model_id or '(无，将删除该库下全部模型版本)'}

将删除:
  - 全部 batch_tests / request_logs
  - 全部 evaluation_runs / intent_test_sessions（含消息）
  - 除保留外的 library_model_versions
  - 除保留外的 training_datasets / evaluation_datasets
  - 除保留外的 intent_libraries
  - 除保留外的 dialog_profiles 及 profile 侧关联
  - profile_library_bindings（最后为保留 profile + 保留 library 补一条绑定）
"""
        print(plan)

        if dry_run:
            print("[dry-run] 未执行任何 DELETE。")
            await session.rollback()
            return

        # 1) 批量测试、请求日志
        await session.execute(delete(BatchTest))
        await session.execute(delete(RequestLog))

        # 2) 评测运行、意图测试会话
        await session.execute(delete(EvaluationRun))
        await session.execute(delete(IntentTestSession))

        # 3) 模型版本：非保留库全删；保留库只留最早一条（若存在）
        if keep_model_id is not None:
            mv_cond = or_(
                LibraryModelVersion.library_id != keep_lib_id,
                and_(
                    LibraryModelVersion.library_id == keep_lib_id,
                    LibraryModelVersion.id != keep_model_id,
                ),
            )
        else:
            mv_cond = LibraryModelVersion.library_id != keep_lib_id
        await session.execute(delete(LibraryModelVersion).where(mv_cond))

        # 4) 方案-库绑定：先去掉将删除的库上的绑定
        await session.execute(
            delete(ProfileLibraryBinding).where(ProfileLibraryBinding.library_id != keep_lib_id)
        )

        # 5) 数据集（训练 / 评测）
        await session.execute(
            delete(TrainingDataset).where(
                (TrainingDataset.library_id != keep_lib_id)
                | (
                    (TrainingDataset.library_id == keep_lib_id)
                    & (TrainingDataset.id != keep_train_id)
                )
            )
        )
        await session.execute(
            delete(EvaluationDataset).where(
                (EvaluationDataset.library_id != keep_lib_id)
                | (
                    (EvaluationDataset.library_id == keep_lib_id)
                    & (EvaluationDataset.id != keep_eval_id)
                )
            )
        )

        # 6) 其它指令库
        await session.execute(delete(IntentLibrary).where(IntentLibrary.id != keep_lib_id))

        # 7) 其它对话方案上的绑定与方案本身
        await session.execute(
            delete(ProfileLibraryBinding).where(ProfileLibraryBinding.profile_id != keep_profile_id)
        )
        await session.execute(delete(DialogProfile).where(DialogProfile.id != keep_profile_id))

        # 8) 确保保留方案绑定到保留库
        bind_exists = await session.execute(
            select(ProfileLibraryBinding.id).where(
                ProfileLibraryBinding.profile_id == keep_profile_id,
                ProfileLibraryBinding.library_id == keep_lib_id,
            )
        )
        if bind_exists.scalar_one_or_none() is None:
            session.add(
                ProfileLibraryBinding(
                    profile_id=keep_profile_id,
                    library_id=keep_lib_id,
                    priority=0,
                    confidence_threshold=0.7,
                )
            )

        await session.commit()
        print("清理完成并已提交。")

    await db.close_db()


def main() -> None:
    p = argparse.ArgumentParser(description="收敛指令库/数据集/对话方案为各一条")
    p.add_argument("--dry-run", action="store_true", help="只打印计划，不执行删除")
    p.add_argument("--yes", action="store_true", help="确认执行（非 dry-run 时必须）")
    args = p.parse_args()

    if not args.dry_run and not args.yes:
        print("未指定 --yes，拒绝执行。可用 --dry-run 查看计划。")
        sys.exit(1)

    asyncio.run(prune(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
